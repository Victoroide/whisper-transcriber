package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"syscall"

	"github.com/Victoroide/whisper-transcriber/core/internal/audio"
	"github.com/Victoroide/whisper-transcriber/core/internal/cleanup"
	"github.com/Victoroide/whisper-transcriber/core/internal/hardware"
	"github.com/Victoroide/whisper-transcriber/core/internal/ipc"
	"github.com/Victoroide/whisper-transcriber/core/internal/models"
)

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU())

	verbose := flag.Bool("v", false, "enable verbose logging")
	flag.Parse()

	if !*verbose {
		log.SetOutput(os.Stderr)
	}

	appDir := appDataDir()
	if err := os.MkdirAll(appDir, 0o755); err != nil {
		log.Fatalf("failed to create app directory: %v", err)
	}

	logFile := setupLogging(appDir)
	if logFile != nil {
		defer logFile.Close()
	}

	tempDir := filepath.Join(appDir, "temp")
	cleaner, err := cleanup.NewManager(tempDir)
	if err != nil {
		log.Fatalf("failed to initialize cleanup manager: %v", err)
	}
	defer cleaner.Cleanup()

	modelsDir := filepath.Join(appDir, "models")
	downloader, err := models.NewDownloader(modelsDir)
	if err != nil {
		log.Fatalf("failed to initialize model downloader: %v", err)
	}

	extractor, extractorErr := audio.NewExtractor()

	hwInfo := hardware.Detect()
	log.Printf("hardware: %s", hwInfo.String())

	var server *ipc.Server
	server, err = ipc.NewServer(func(msgType string, data json.RawMessage) *ipc.Message {
		return handleMessage(msgType, data, server, extractor, extractorErr, downloader, cleaner)
	})
	if err != nil {
		log.Fatalf("failed to create IPC server: %v", err)
	}
	defer server.Shutdown()

	// Print the listening address so the Python process can connect
	fmt.Println(server.PipePath())

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigCh
		log.Println("received shutdown signal")
		server.Shutdown()
	}()

	log.Println("waiting for client connection...")
	if err := server.Accept(); err != nil {
		log.Fatalf("failed to accept connection: %v", err)
	}
	log.Println("client connected")

	hwMsg := ipc.Message{Type: "hardware_info", Data: hwInfo}
	if err := server.Send(hwMsg); err != nil {
		log.Printf("failed to send hardware info: %v", err)
	}

	if err := server.Listen(); err != nil {
		log.Printf("IPC listen error: %v", err)
	}

	log.Println("shutting down")
}

// handleMessage dispatches inbound messages from the Python client.
func handleMessage(
	msgType string,
	data json.RawMessage,
	server *ipc.Server,
	extractor *audio.Extractor,
	extractorErr error,
	downloader *models.Downloader,
	cleaner *cleanup.Manager,
) *ipc.Message {
	switch msgType {
	case "extract_audio":
		go handleExtractAudio(data, server, extractor, extractorErr, cleaner)
		return nil
	case "download_model":
		go handleDownloadModel(data, server, downloader)
		return nil
	case "cancel":
		log.Println("cancel requested by client")
		return nil
	case "shutdown":
		log.Println("shutdown requested by client")
		go func() {
			server.Shutdown()
		}()
		return nil
	default:
		log.Printf("unknown message type: %s", msgType)
		return nil
	}
}

// handleExtractAudio processes an audio extraction request.
func handleExtractAudio(
	data json.RawMessage,
	server *ipc.Server,
	extractor *audio.Extractor,
	extractorErr error,
	cleaner *cleanup.Manager,
) {
	if extractorErr != nil {
		sendError(server, "FFMPEG_NOT_FOUND",
			"FFmpeg not found. Install it or add to PATH.", true)
		return
	}

	var req ipc.ExtractAudioRequest
	if err := json.Unmarshal(data, &req); err != nil {
		sendError(server, "INVALID_REQUEST",
			fmt.Sprintf("Invalid extract_audio request: %v", err), true)
		return
	}

	outputDir := filepath.Join(cleaner.TempDir(), fmt.Sprintf("wt_%d", os.Getpid()))
	cleaner.Track(outputDir)

	progress := func(percent int, message string) {
		msg := ipc.Message{
			Type: "audio_extract_progress",
			Data: ipc.AudioExtractProgress{Percent: percent, Message: message},
		}
		if err := server.Send(msg); err != nil {
			log.Printf("failed to send extraction progress: %v", err)
		}
	}

	chunksChan, err := extractor.ExtractChunks(req.InputPath, outputDir, 30.0, progress)
	if err != nil {
		sendError(server, "EXTRACTION_FAILED",
			fmt.Sprintf("Audio extraction failed to start: %v", err), true)
		return
	}

	totalChunks := 0
	for chunk := range chunksChan {
		if chunk.Error != nil {
			sendError(server, "EXTRACTION_FAILED",
				fmt.Sprintf("Audio extraction chunk failed: %v", chunk.Error), true)
			return
		}

		msg := ipc.Message{
			Type: "audio_chunk",
			Data: ipc.AudioChunk{
				Index:     chunk.Index,
				StartTime: chunk.StartTime,
				Duration:  chunk.Duration,
				Path:      chunk.Path,
			},
		}
		if err := server.Send(msg); err != nil {
			log.Printf("failed to send audio_chunk: %v", err)
		}
		totalChunks++
	}

	durationMs := audio.ProbeDuration(extractor.FFmpegPath(), req.InputPath)
	duration := float64(durationMs) / 1000.0

	msg := ipc.Message{
		Type: "audio_extraction_complete",
		Data: ipc.AudioExtractionComplete{
			TotalChunks:     totalChunks,
			DurationSeconds: duration,
		},
	}
	if err := server.Send(msg); err != nil {
		log.Printf("failed to send audio_extraction_complete: %v", err)
	}
}

// handleDownloadModel processes a model download request.
func handleDownloadModel(
	data json.RawMessage,
	server *ipc.Server,
	downloader *models.Downloader,
) {
	var req ipc.DownloadModelRequest
	if err := json.Unmarshal(data, &req); err != nil {
		sendError(server, "INVALID_REQUEST",
			fmt.Sprintf("Invalid download_model request: %v", err), true)
		return
	}

	progress := func(downloaded, total int64) {
		pct := 0
		if total > 0 {
			pct = int(float64(downloaded) / float64(total) * 100)
		}
		msg := ipc.Message{
			Type: "model_download_progress",
			Data: ipc.ModelDownloadProgress{
				Model:        req.Model,
				Percent:      pct,
				MBDownloaded: int(downloaded / (1024 * 1024)),
				MBTotal:      int(total / (1024 * 1024)),
			},
		}
		if err := server.Send(msg); err != nil {
			log.Printf("failed to send download progress: %v", err)
		}
	}

	// faster-whisper models are downloaded by the Python side via
	// huggingface_hub. This handler is a placeholder for custom model
	// management if needed in the future.
	_ = progress
	_ = downloader

	msg := ipc.Message{
		Type: "model_ready",
		Data: ipc.ModelReady{Model: req.Model},
	}
	if err := server.Send(msg); err != nil {
		log.Printf("failed to send model_ready: %v", err)
	}
}

// sendError sends an error message to the Python client.
func sendError(server *ipc.Server, code, message string, recoverable bool) {
	msg := ipc.Message{
		Type: "error",
		Data: ipc.ErrorData{Code: code, Message: message, Recoverable: recoverable},
	}
	if err := server.Send(msg); err != nil {
		log.Printf("failed to send error message: %v", err)
	}
}

// appDataDir returns the path to ~/.whisper_transcriber/.
func appDataDir() string {
	home, err := os.UserHomeDir()
	if err != nil {
		home = "."
	}
	return filepath.Join(home, ".whisper_transcriber")
}

// setupLogging configures log output to both stderr and a rotating log file.
func setupLogging(appDir string) *os.File {
	logDir := filepath.Join(appDir, "logs")
	if err := os.MkdirAll(logDir, 0o755); err != nil {
		log.Printf("failed to create log directory: %v", err)
		return nil
	}

	logPath := filepath.Join(logDir, "core.log")

	// Truncate log file if it exceeds 5MB
	if info, err := os.Stat(logPath); err == nil && info.Size() > 5*1024*1024 {
		os.Remove(logPath)
	}

	f, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		log.Printf("failed to open log file: %v", err)
		return nil
	}

	log.SetOutput(f)
	return f
}
