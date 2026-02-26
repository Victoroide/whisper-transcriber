package ipc

// Message is the envelope for all IPC communication between Go core and Python UI.
// Every message has a Type field indicating the payload kind and a Data field
// containing the type-specific payload as a raw JSON object.
type Message struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}

// InboundMessage is used for deserializing messages received from Python.
// The Data field is kept as raw JSON bytes so it can be decoded based on Type.
type InboundMessage struct {
	Type string `json:"type"`
	Data []byte `json:"data"`
}

// HardwareInfo is sent from Go to Python on startup with system capabilities.
type HardwareInfo struct {
	CUDA             bool   `json:"cuda"`
	MPS              bool   `json:"mps"`
	CPUCores         int    `json:"cpu_cores"`
	RAMGB            int    `json:"ram_gb"`
	RecommendedModel string `json:"recommended_model"`
	RecommendedComp  string `json:"recommended_compute"`
}

// AudioExtractProgress reports ffmpeg extraction progress.
type AudioExtractProgress struct {
	Percent int    `json:"percent"`
	Message string `json:"message"`
}

// AudioChunk reports a single 30s portion of the file has been extracted
type AudioChunk struct {
	Index     int     `json:"index"`
	StartTime float64 `json:"start_time"`
	Duration  float64 `json:"duration"`
	Path      string  `json:"path"`
}

// AudioExtractionComplete signals that all chunks have been created
type AudioExtractionComplete struct {
	TotalChunks     int     `json:"total_chunks"`
	DurationSeconds float64 `json:"duration_seconds"`
}

// ModelDownloadProgress reports model download status.
type ModelDownloadProgress struct {
	Model        string `json:"model"`
	Percent      int    `json:"percent"`
	MBDownloaded int    `json:"mb_downloaded"`
	MBTotal      int    `json:"mb_total"`
}

// ModelReady signals that a model is available locally.
type ModelReady struct {
	Model string `json:"model"`
}

// ErrorData carries error details from Go to Python.
type ErrorData struct {
	Code        string `json:"code"`
	Message     string `json:"message"`
	Recoverable bool   `json:"recoverable"`
}

// TempCleanupDone reports how many stale temp files were removed on startup.
type TempCleanupDone struct {
	FilesRemoved int `json:"files_removed"`
}

// ExtractAudioRequest is sent from Python to Go to start audio extraction.
type ExtractAudioRequest struct {
	InputPath string `json:"input_path"`
}

// DownloadModelRequest is sent from Python to Go to download a model.
type DownloadModelRequest struct {
	Model string `json:"model"`
}
