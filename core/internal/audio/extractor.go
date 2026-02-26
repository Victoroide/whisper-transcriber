package audio

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"sync"
)

// Extractor wraps ffmpeg to convert media files into 16kHz mono WAV.
type Extractor struct {
	ffmpegPath string
}

// ProgressFunc receives extraction progress as a percentage (0-100) and a
// human-readable status message.
type ProgressFunc func(percent int, message string)

// Chunk represents a segment of extracted audio.
type Chunk struct {
	Index     int     `json:"index"`
	StartTime float64 `json:"start_time"`
	Duration  float64 `json:"duration"`
	Path      string  `json:"path"`
	Error     error   `json:"-"`
}

// NewExtractor locates the ffmpeg binary on the system and returns a
// configured Extractor. Returns an error if ffmpeg cannot be found.
func NewExtractor() (*Extractor, error) {
	path, err := findFFmpeg()
	if err != nil {
		return nil, fmt.Errorf("ffmpeg not found: %w", err)
	}
	return &Extractor{ffmpegPath: path}, nil
}

// Extract converts the input file to a 16kHz mono WAV at outputPath.
// The progress callback receives periodic updates during conversion.
func (e *Extractor) Extract(inputPath, outputPath string, progress ProgressFunc) error {
	if _, err := os.Stat(inputPath); err != nil {
		return fmt.Errorf("input file not readable: %w", err)
	}

	dir := filepath.Dir(outputPath)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return fmt.Errorf("creating output directory: %w", err)
	}

	if progress != nil {
		progress(0, "Starting audio extraction...")
	}

	args := []string{
		"-i", inputPath,
		"-vn",
		"-acodec", "pcm_s16le",
		"-ar", "16000",
		"-ac", "1",
		"-y",
		"-progress", "pipe:2",
		outputPath,
	}

	cmd := exec.Command(e.ffmpegPath, args...)
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("creating stderr pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("starting ffmpeg: %w", err)
	}

	duration := ProbeDuration(e.ffmpegPath, inputPath)

	scanner := bufio.NewScanner(stderr)
	timePattern := regexp.MustCompile(`out_time_ms=(\d+)`)

	for scanner.Scan() {
		line := scanner.Text()
		if progress == nil || duration <= 0 {
			continue
		}
		matches := timePattern.FindStringSubmatch(line)
		if len(matches) < 2 {
			continue
		}
		timeUs, err := strconv.ParseInt(matches[1], 10, 64)
		if err != nil {
			continue
		}
		pct := int(float64(timeUs) / float64(duration*1000) * 100)
		if pct > 100 {
			pct = 100
		}
		progress(pct, "Extracting audio...")
	}

	if err := cmd.Wait(); err != nil {
		return fmt.Errorf("ffmpeg exited with error: %w", err)
	}

	if progress != nil {
		progress(100, "Audio extraction complete")
	}
	return nil
}

// ExtractChunks divides the audio into chunks of maxChunkDurationSeconds and extracts
// them concurrently using a worker pool. It yields ordered Chunk results on the returned channel.
func (e *Extractor) ExtractChunks(inputPath, outputDir string, chunkDurationSeconds float64, progress ProgressFunc) (<-chan Chunk, error) {
	if _, err := os.Stat(inputPath); err != nil {
		return nil, fmt.Errorf("input file not readable: %w", err)
	}

	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		return nil, fmt.Errorf("creating output directory: %w", err)
	}

	durationMs := ProbeDuration(e.ffmpegPath, inputPath)
	if durationMs <= 0 {
		return nil, fmt.Errorf("could not determine audio duration")
	}
	totalDuration := float64(durationMs) / 1000.0

	numChunks := int(math.Ceil(totalDuration / chunkDurationSeconds))

	if progress != nil {
		progress(0, fmt.Sprintf("Preparing %d audio chunks...", numChunks))
	}

	// Determine number of workers: total logical cores minus 1 (for IPC server/main), min 1.
	numWorkers := runtime.NumCPU() - 1
	if numWorkers < 1 {
		numWorkers = 1
	}
	if numWorkers > numChunks {
		numWorkers = numChunks
	}

	outChan := make(chan Chunk)

	go func() {
		defer close(outChan)

		// Create a job queue and an unordered results channel
		jobs := make(chan Chunk, numChunks)
		results := make(chan Chunk, numChunks)

		// Start worker pool
		var wg sync.WaitGroup
		for w := 0; w < numWorkers; w++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for job := range jobs {
					args := []string{
						"-ss", strconv.FormatFloat(job.StartTime, 'f', 3, 64),
						"-i", inputPath,
						"-t", strconv.FormatFloat(job.Duration, 'f', 3, 64),
						"-vn",
						"-acodec", "pcm_s16le",
						"-ar", "16000",
						"-ac", "1",
						"-y",
						job.Path,
					}

					cmd := exec.Command(e.ffmpegPath, args...)
					if output, err := cmd.CombinedOutput(); err != nil {
						job.Error = fmt.Errorf("ffmpeg chunk failed: %w, %s", err, string(output))
					}
					results <- job
				}
			}()
		}

		// Enqueue all jobs
		for i := 0; i < numChunks; i++ {
			startTime := float64(i) * chunkDurationSeconds
			duration := chunkDurationSeconds
			if startTime+duration > totalDuration {
				duration = totalDuration - startTime
			}

			chunkPath := filepath.Join(outputDir, fmt.Sprintf("chunk_%04d.wav", i))
			jobs <- Chunk{
				Index:     i,
				StartTime: startTime,
				Duration:  duration,
				Path:      chunkPath,
			}
		}
		close(jobs)

		// Start a collector to wait for workers and close results
		go func() {
			wg.Wait()
			close(results)
		}()

		// Collect unordered results into a map and stream chronologically
		receivedChunks := make(map[int]Chunk)
		nextExpected := 0
		completed := 0

		for chunk := range results {
			if chunk.Error != nil {
				outChan <- chunk
				return // Abort on first error
			}

			receivedChunks[chunk.Index] = chunk
			completed++

			// Drain consecutive chunks that are ready
			for {
				if readyChunk, ok := receivedChunks[nextExpected]; ok {
					outChan <- readyChunk
					delete(receivedChunks, nextExpected)
					nextExpected++

					if progress != nil {
						pct := int(float64(completed) / float64(numChunks) * 100)
						progress(pct, fmt.Sprintf("Extracted %d/%d chunks...", completed, numChunks))
					}
				} else {
					break // Gap in sequence, wait for next expected
				}
			}
		}
	}()

	return outChan, nil
}

// FFmpegPath returns the resolved path to the ffmpeg binary.
func (e *Extractor) FFmpegPath() string {
	return e.ffmpegPath
}

// ProbeDuration uses ffprobe to get the total duration in milliseconds.
// Returns 0 if the duration cannot be determined.
func ProbeDuration(ffmpegPath, inputPath string) int64 {
	ffprobePath := strings.TrimSuffix(ffmpegPath, filepath.Ext(ffmpegPath))
	if runtime.GOOS == "windows" {
		ffprobePath += ".exe"
	}
	ffprobePath = strings.Replace(ffprobePath, "ffmpeg", "ffprobe", 1)

	var durationMs int64

	if _, err := os.Stat(ffprobePath); err == nil {
		args := []string{
			"-v", "error",
			"-show_entries", "format=duration",
			"-of", "default=noprint_wrappers=1:nokey=1",
			inputPath,
		}
		if out, err := exec.Command(ffprobePath, args...).Output(); err == nil {
			if seconds, err := strconv.ParseFloat(strings.TrimSpace(string(out)), 64); err == nil {
				durationMs = int64(seconds * 1000)
			}
		}
	}

	// Fallback for test fixtures (lavfi generated synths, etc) and raw WAV files
	// if ffprobe fails or isn't available.
	if durationMs <= 0 && strings.HasSuffix(strings.ToLower(inputPath), ".wav") {
		if info, err := os.Stat(inputPath); err == nil {
			// Estimate duration from file size for 16kHz 16-bit mono WAV
			// 32000 bytes per second + 44 bytes header
			if info.Size() > 44 {
				durationMs = int64(float64(info.Size()-44) / 32.0)
			}
		}
	}

	return durationMs
}

// findFFmpeg searches for ffmpeg on the system PATH and in common install
// locations. Returns the full path or an error if not found.
func findFFmpeg() (string, error) {
	if path, err := exec.LookPath("ffmpeg"); err == nil {
		return path, nil
	}

	var candidates []string
	switch runtime.GOOS {
	case "windows":
		candidates = []string{
			`C:\ffmpeg\bin\ffmpeg.exe`,
			`C:\Program Files\ffmpeg\bin\ffmpeg.exe`,
			`C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe`,
		}
	case "darwin":
		candidates = []string{
			"/usr/local/bin/ffmpeg",
			"/opt/homebrew/bin/ffmpeg",
		}
	default:
		candidates = []string{
			"/usr/bin/ffmpeg",
			"/usr/local/bin/ffmpeg",
			"/snap/bin/ffmpeg",
		}
	}

	for _, path := range candidates {
		if _, err := os.Stat(path); err == nil {
			return path, nil
		}
	}

	return "", fmt.Errorf("ffmpeg not found on PATH or in common locations")
}
