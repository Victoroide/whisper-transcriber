package models

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
)

// VerifyChecksum computes the SHA-256 hash of the file at path and compares
// it to the expected hex-encoded hash string. Returns true if they match.
func VerifyChecksum(path string, expected string) (bool, error) {
	f, err := os.Open(path)
	if err != nil {
		return false, fmt.Errorf("opening file for checksum: %w", err)
	}
	defer f.Close()

	hasher := sha256.New()
	if _, err := io.Copy(hasher, f); err != nil {
		return false, fmt.Errorf("computing checksum: %w", err)
	}

	actual := hex.EncodeToString(hasher.Sum(nil))
	return actual == expected, nil
}

// ComputeChecksum returns the hex-encoded SHA-256 hash of the file at path.
func ComputeChecksum(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", fmt.Errorf("opening file for checksum: %w", err)
	}
	defer f.Close()

	hasher := sha256.New()
	if _, err := io.Copy(hasher, f); err != nil {
		return "", fmt.Errorf("computing checksum: %w", err)
	}

	return hex.EncodeToString(hasher.Sum(nil)), nil
}
