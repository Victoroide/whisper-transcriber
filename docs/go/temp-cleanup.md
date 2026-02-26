# Temp Cleanup (`core/internal/cleanup/tempfiles.go`)

The `Manager` struct is responsible for securely allocating, tracking, and eventually purging the temporary WAV fragments strictly belonging to the transcriber process. It handles both graceful exits and catastrophic crashes.

## Core Component: Manager

### Initialization: `NewManager(tempDir string)`

When the Go core starts, it initializes the manager in a designated `wt-core-*` temporary folder. Crucially, the manager writes a `wt-core.pid` file containing the current OS Process ID.

**Crash Recovery (`cleanStaleFiles`)**:
If the application previously crashed without completing its cleanup routines, `NewManager` will locate the old PID file. It utilizes `os.FindProcess(pid)` to probe the operating system. If the OS confirms that the previous PID is dead, the manager iterates over the `tempDir`, forcibly deleting any abandoned `.wav` chunks left behind, preventing massive disk space leaks over time.

### Tracking: `Track(path string)`

As the `AudioExtractor` worker pool yields new 30-second chunk files, it registers their absolute directory paths dynamically into the `Manager.tracked` slice.

### Teardown: `Cleanup()`

Invoked either upon a graceful `audio_extraction_complete` success signal, explicit `cancel` requests via IPC, or OS-level `SIGINT`/`SIGTERM` interrupts.
It ranges over the `tracked` paths, deletes them sequentially, nullifies the slice to free memory, and finally destroys the `wt-core.pid` file to cleanly conclude the session.
