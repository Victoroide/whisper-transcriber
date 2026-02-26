package models

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func TestDownloadAndVerify(t *testing.T) {
	testContent := []byte("this is test model data for verification")

	hasher := sha256.New()
	hasher.Write(testContent)
	expectedHash := hex.EncodeToString(hasher.Sum(nil))

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Length", fmt.Sprintf("%d", len(testContent)))
		w.Write(testContent)
	}))
	defer server.Close()

	cacheDir := t.TempDir()
	dl, err := NewDownloader(cacheDir)
	if err != nil {
		t.Fatalf("failed to create downloader: %v", err)
	}

	var lastDownloaded, lastTotal int64
	progress := func(downloaded, total int64) {
		lastDownloaded = downloaded
		lastTotal = total
	}

	path, err := dl.Download(server.URL+"/model.bin", "test_model.bin", expectedHash, progress)
	if err != nil {
		t.Fatalf("download failed: %v", err)
	}

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read downloaded file: %v", err)
	}

	if string(data) != string(testContent) {
		t.Fatal("downloaded content does not match expected")
	}

	if lastDownloaded != int64(len(testContent)) {
		t.Errorf("expected final downloaded=%d, got %d",
			len(testContent), lastDownloaded)
	}
	if lastTotal != int64(len(testContent)) {
		t.Errorf("expected total=%d, got %d", len(testContent), lastTotal)
	}
}

func TestDownloadBadChecksum(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("some data"))
	}))
	defer server.Close()

	cacheDir := t.TempDir()
	dl, err := NewDownloader(cacheDir)
	if err != nil {
		t.Fatalf("failed to create downloader: %v", err)
	}

	_, err = dl.Download(server.URL+"/model.bin", "bad.bin", "0000000000000000", nil)
	if err == nil {
		t.Fatal("expected checksum mismatch error")
	}

	// The partial/bad file should have been cleaned up
	partPath := filepath.Join(cacheDir, "bad.bin.part")
	if _, err := os.Stat(partPath); err == nil {
		t.Fatal("part file should have been removed after checksum failure")
	}
}

func TestDownloadResumable(t *testing.T) {
	testContent := []byte("0123456789ABCDEF")

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rangeHeader := r.Header.Get("Range")
		if rangeHeader != "" {
			// Parse "bytes=N-" and serve from offset N
			var start int
			fmt.Sscanf(rangeHeader, "bytes=%d-", &start)
			if start < len(testContent) {
				w.Header().Set("Content-Length", fmt.Sprintf("%d", len(testContent)-start))
				w.WriteHeader(http.StatusPartialContent)
				w.Write(testContent[start:])
				return
			}
		}
		w.Header().Set("Content-Length", fmt.Sprintf("%d", len(testContent)))
		w.Write(testContent)
	}))
	defer server.Close()

	cacheDir := t.TempDir()
	dl, err := NewDownloader(cacheDir)
	if err != nil {
		t.Fatalf("failed to create downloader: %v", err)
	}

	// Create a partial file to simulate interrupted download
	partPath := filepath.Join(cacheDir, "resume.bin.part")
	os.WriteFile(partPath, testContent[:8], 0o644)

	hasher := sha256.New()
	hasher.Write(testContent)
	expectedHash := hex.EncodeToString(hasher.Sum(nil))

	path, err := dl.Download(server.URL+"/model.bin", "resume.bin", expectedHash, nil)
	if err != nil {
		t.Fatalf("resumable download failed: %v", err)
	}

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read file: %v", err)
	}

	if string(data) != string(testContent) {
		t.Fatalf("content mismatch: got %q, want %q", string(data), string(testContent))
	}
}

func TestVerifyChecksum(t *testing.T) {
	content := []byte("test data for checksum")

	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "test.bin")
	os.WriteFile(path, content, 0o644)

	hasher := sha256.New()
	hasher.Write(content)
	expected := hex.EncodeToString(hasher.Sum(nil))

	ok, err := VerifyChecksum(path, expected)
	if err != nil {
		t.Fatalf("verify failed: %v", err)
	}
	if !ok {
		t.Fatal("expected checksum to match")
	}

	ok, err = VerifyChecksum(path, "wrong_hash")
	if err != nil {
		t.Fatalf("verify failed: %v", err)
	}
	if ok {
		t.Fatal("expected checksum mismatch")
	}
}

func TestComputeChecksum(t *testing.T) {
	content := []byte("test data")
	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "test.bin")
	os.WriteFile(path, content, 0o644)

	hash, err := ComputeChecksum(path)
	if err != nil {
		t.Fatalf("compute failed: %v", err)
	}
	if hash == "" {
		t.Fatal("expected non-empty hash")
	}
	if len(hash) != 64 {
		t.Fatalf("expected SHA-256 hex string (64 chars), got %d chars", len(hash))
	}
}
