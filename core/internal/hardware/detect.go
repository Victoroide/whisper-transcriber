package hardware

import (
	"fmt"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
)

// Info holds detected hardware capabilities for model recommendation.
type Info struct {
	CUDA             bool   `json:"cuda"`
	MPS              bool   `json:"mps"`
	CPUCores         int    `json:"cpu_cores"`
	RAMGB            int    `json:"ram_gb"`
	RecommendedModel string `json:"recommended_model"`
	RecommendedComp  string `json:"recommended_compute"`
}

// Detect probes the system for GPU availability, CPU count, and total RAM,
// then computes a model recommendation based on the available resources.
func Detect() Info {
	info := Info{
		CUDA:     detectCUDA(),
		MPS:      detectMPS(),
		CPUCores: runtime.NumCPU(),
		RAMGB:    detectRAM(),
	}
	info.RecommendedModel, info.RecommendedComp = recommend(info)
	return info
}

// detectCUDA checks for NVIDIA GPU by looking for nvidia-smi on the PATH.
func detectCUDA() bool {
	_, err := exec.LookPath("nvidia-smi")
	if err != nil {
		return false
	}
	out, err := exec.Command("nvidia-smi", "--query-gpu=name", "--format=csv,noheader").Output()
	if err != nil {
		return false
	}
	return len(strings.TrimSpace(string(out))) > 0
}

// detectMPS returns true on Apple Silicon machines where MPS is available.
func detectMPS() bool {
	return runtime.GOOS == "darwin" && runtime.GOARCH == "arm64"
}

// detectRAM returns total system RAM in gigabytes. Platform-specific
// implementations are below. Returns 0 if detection fails.
func detectRAM() int {
	switch runtime.GOOS {
	case "windows":
		return detectRAMWindows()
	case "darwin":
		return detectRAMDarwin()
	default:
		return detectRAMLinux()
	}
}

// detectRAMWindows reads total physical memory via wmic.
func detectRAMWindows() int {
	out, err := exec.Command("wmic", "computersystem", "get", "TotalPhysicalMemory").Output()
	if err != nil {
		return 0
	}
	lines := strings.Split(strings.TrimSpace(string(out)), "\n")
	if len(lines) < 2 {
		return 0
	}
	bytes, err := strconv.ParseUint(strings.TrimSpace(lines[1]), 10, 64)
	if err != nil {
		return 0
	}
	return int(bytes / (1024 * 1024 * 1024))
}

// detectRAMDarwin reads total memory via sysctl on macOS.
func detectRAMDarwin() int {
	out, err := exec.Command("sysctl", "-n", "hw.memsize").Output()
	if err != nil {
		return 0
	}
	bytes, err := strconv.ParseUint(strings.TrimSpace(string(out)), 10, 64)
	if err != nil {
		return 0
	}
	return int(bytes / (1024 * 1024 * 1024))
}

// detectRAMLinux reads total memory from /proc/meminfo.
func detectRAMLinux() int {
	out, err := exec.Command("grep", "MemTotal", "/proc/meminfo").Output()
	if err != nil {
		return 0
	}
	fields := strings.Fields(string(out))
	if len(fields) < 2 {
		return 0
	}
	kb, err := strconv.ParseUint(fields[1], 10, 64)
	if err != nil {
		return 0
	}
	return int(kb / (1024 * 1024))
}

// recommend selects the best model and compute type based on hardware.
func recommend(info Info) (model string, compute string) {
	if info.CUDA {
		if info.RAMGB >= 10 {
			return "large-v3", "float16"
		}
		return "medium", "float16"
	}

	if info.MPS {
		return "medium", "float16"
	}

	// CPU-only recommendations based on available RAM
	if info.RAMGB < 4 {
		return "tiny", "int8"
	}
	if info.RAMGB < 8 {
		return "small", "int8"
	}
	return "medium", "int8"
}

// String returns a human-readable summary of the hardware detection results.
func (i Info) String() string {
	return fmt.Sprintf(
		"CPU cores: %d, RAM: %dGB, CUDA: %v, MPS: %v, recommended: %s (%s)",
		i.CPUCores, i.RAMGB, i.CUDA, i.MPS,
		i.RecommendedModel, i.RecommendedComp,
	)
}
