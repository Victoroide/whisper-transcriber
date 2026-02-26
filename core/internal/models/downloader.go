package models

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
)

// DownloadProgressFunc receives download progress as bytes downloaded and
// total bytes expected. Total may be 0 if the server did not provide
// Content-Length.
type DownloadProgressFunc func(downloaded, total int64)

// Downloader manages downloading and caching of model files.
type Downloader struct {
	cacheDir string
}

// NewDownloader creates a Downloader that stores files in the given directory.
// The directory is created if it does not exist.
func NewDownloader(cacheDir string) (*Downloader, error) {
	if err := os.MkdirAll(cacheDir, 0o755); err != nil {
		return nil, fmt.Errorf("creating cache directory %s: %w", cacheDir, err)
	}
	return &Downloader{cacheDir: cacheDir}, nil
}

// Download fetches a file from url and saves it to the cache directory under
// the given filename. If a partial file already exists, it attempts to resume
// the download using HTTP Range requests. The progress callback receives
// periodic updates.
func (d *Downloader) Download(
	url string,
	filename string,
	expectedSHA256 string,
	progress DownloadProgressFunc,
) (string, error) {
	destPath := filepath.Join(d.cacheDir, filename)

	// Check if the file already exists and is valid
	if _, err := os.Stat(destPath); err == nil {
		if expectedSHA256 != "" {
			ok, err := VerifyChecksum(destPath, expectedSHA256)
			if err == nil && ok {
				return destPath, nil
			}
		}
	}

	partPath := destPath + ".part"
	var startByte int64
	if info, err := os.Stat(partPath); err == nil {
		startByte = info.Size()
	}

	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return "", fmt.Errorf("creating request: %w", err)
	}
	if startByte > 0 {
		req.Header.Set("Range", fmt.Sprintf("bytes=%d-", startByte))
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("downloading %s: %w", url, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK &&
		resp.StatusCode != http.StatusPartialContent {
		return "", fmt.Errorf("server returned status %d for %s", resp.StatusCode, url)
	}

	// If the server does not support range requests, start from scratch
	if resp.StatusCode == http.StatusOK && startByte > 0 {
		startByte = 0
	}

	var totalSize int64
	if cl := resp.Header.Get("Content-Length"); cl != "" {
		parsed, err := strconv.ParseInt(cl, 10, 64)
		if err == nil {
			totalSize = parsed + startByte
		}
	}

	flags := os.O_CREATE | os.O_WRONLY
	if startByte > 0 && resp.StatusCode == http.StatusPartialContent {
		flags |= os.O_APPEND
	} else {
		flags |= os.O_TRUNC
		startByte = 0
	}

	out, err := os.OpenFile(partPath, flags, 0o644)
	if err != nil {
		return "", fmt.Errorf("opening part file: %w", err)
	}
	defer out.Close()

	buf := make([]byte, 32*1024)
	downloaded := startByte
	for {
		n, readErr := resp.Body.Read(buf)
		if n > 0 {
			if _, err := out.Write(buf[:n]); err != nil {
				return "", fmt.Errorf("writing to file: %w", err)
			}
			downloaded += int64(n)
			if progress != nil {
				progress(downloaded, totalSize)
			}
		}
		if readErr != nil {
			if readErr == io.EOF {
				break
			}
			return "", fmt.Errorf("reading response body: %w", readErr)
		}
	}

	out.Close()

	if expectedSHA256 != "" {
		ok, err := VerifyChecksum(partPath, expectedSHA256)
		if err != nil {
			return "", fmt.Errorf("verifying checksum: %w", err)
		}
		if !ok {
			os.Remove(partPath)
			return "", fmt.Errorf("checksum mismatch for %s", filename)
		}
	}

	if err := os.Rename(partPath, destPath); err != nil {
		return "", fmt.Errorf("moving part file to final location: %w", err)
	}

	return destPath, nil
}

// CacheDir returns the path to the model cache directory.
func (d *Downloader) CacheDir() string {
	return d.cacheDir
}
