package cleanup

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const pidFileName = "wt-core.pid"

// Manager tracks temporary files and ensures cleanup even after crashes.
// On startup it checks for stale PID files from previous runs and removes
// any orphaned temp files.
type Manager struct {
	tempDir string
	tracked []string
}

// NewManager creates a cleanup manager for the given temp directory and
// writes a PID file to track the current process.
func NewManager(tempDir string) (*Manager, error) {
	if err := os.MkdirAll(tempDir, 0o755); err != nil {
		return nil, fmt.Errorf("creating temp directory: %w", err)
	}

	m := &Manager{tempDir: tempDir}

	removed := m.cleanStaleFiles()
	if removed > 0 {
		log.Printf("cleanup: removed %d stale temp files from previous run", removed)
	}

	pidPath := filepath.Join(tempDir, pidFileName)
	pid := strconv.Itoa(os.Getpid())
	if err := os.WriteFile(pidPath, []byte(pid), 0o644); err != nil {
		return nil, fmt.Errorf("writing PID file: %w", err)
	}

	return m, nil
}

// Track registers a file path for cleanup on shutdown.
func (m *Manager) Track(path string) {
	m.tracked = append(m.tracked, path)
}

// Cleanup removes all tracked temp files and the PID file.
// Returns the number of files successfully removed.
func (m *Manager) Cleanup() int {
	removed := 0
	for _, path := range m.tracked {
		if err := os.Remove(path); err == nil {
			removed++
		}
	}
	m.tracked = nil

	pidPath := filepath.Join(m.tempDir, pidFileName)
	os.Remove(pidPath)

	return removed
}

// TempDir returns the managed temporary directory path.
func (m *Manager) TempDir() string {
	return m.tempDir
}

// cleanStaleFiles checks for a PID file from a previous run. If the process
// is no longer running, it removes all .wav files from the temp directory.
func (m *Manager) cleanStaleFiles() int {
	pidPath := filepath.Join(m.tempDir, pidFileName)
	data, err := os.ReadFile(pidPath)
	if err != nil {
		return 0
	}

	pid, err := strconv.Atoi(strings.TrimSpace(string(data)))
	if err != nil {
		os.Remove(pidPath)
		return 0
	}

	if isProcessRunning(pid) {
		return 0
	}

	os.Remove(pidPath)
	return removeWavFiles(m.tempDir)
}

// removeWavFiles deletes all .wav files in the given directory.
func removeWavFiles(dir string) int {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return 0
	}
	removed := 0
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if filepath.Ext(entry.Name()) == ".wav" {
			path := filepath.Join(dir, entry.Name())
			if err := os.Remove(path); err == nil {
				removed++
			}
		}
	}
	return removed
}

// isProcessRunning checks if a process with the given PID exists.
func isProcessRunning(pid int) bool {
	process, err := os.FindProcess(pid)
	if err != nil {
		return false
	}
	// On Unix, FindProcess always succeeds. We send signal 0 to check
	// if the process actually exists. On Windows, FindProcess fails for
	// non-existent processes so reaching here means it exists.
	err = process.Signal(os.Signal(nil))
	return err == nil
}
