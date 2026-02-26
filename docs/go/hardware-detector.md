# Hardware Detector (`core/internal/hardware/detector.go`)

The `HardwareDetector` struct is responsible for probing the host system to determine the availability of NVIDIA CUDA resources, which are required for GPU-accelerated transcription.

## Primary Function: `Detect()`

- **Purpose**: Scans the system for NVIDIA hardware and CUDA libraries.
- **Return Value**: Returns a `HardwareInfo` struct containing boolean flags (`HasGPU`, `HasCUDA`) and a list of detected devices.

## How It Works

1.  **Execution**: The function executes the `nvidia-smi` command-line utility.
2.  **Parsing**: It parses the standard output of `nvidia-smi` to identify GPU devices and verify the presence of the CUDA driver.
3.  **Error Handling**: If `nvidia-smi` is not found or fails to execute, it gracefully handles the error and returns `HasGPU: false`.

## HardwareInfo Struct

```go
type HardwareInfo struct {
    HasGPU  bool     `json:"has_gpu"`
    HasCUDA bool     `json:"has_cuda"`
    Devices []string `json:"devices"`
}
```

- `HasGPU`: True if NVIDIA GPUs are detected.
- `HasCUDA`: True if the CUDA driver is available.
- `Devices`: A list of detected GPU device names (e.g., "NVIDIA GeForce RTX 3060").
