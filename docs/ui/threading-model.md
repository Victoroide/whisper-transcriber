# Python Threading Model (`ui/app/window.py` & `ui/app/core/ipc_client.py`)

A graphical desktop application building interfaces via `tkinter` must maintain a continuous, unblocked `mainloop()` at all times to render window movements, button hover states, and window resizing appropriately.

In Whisper Transcriber, achieving a seamless UI while simultaneously parsing JSON sockets and executing multi-gigabyte neural network calculations dictates a strict asynchronous triage system utilizing three core threads.

## The Tri-Thread Implementation

### 1. The Main Event Thread (UI)

- **Role**: Exclusively handles all `customtkinter` display updates, button bindings, progress-bar setting mathematically, and OS-level Drag/Drop events.
- **Safety Measure**: Never invokes blocking I/O calls (e.g., `requests.get()` or socket reads).
- **The Bridge**: Subscribes to the `ipc_client` via a recursive `after(100, _poll_ipc_queue)` loop. Every 100 milliseconds, it interrogates a thread-safe `queue.Queue` looking for newly decoded chunks or progress indicators.

### 2. The Socket IPC Daemon Thread (`ipc_client.py`)

- **Role**: Spawns globally when the core launches as `daemon=True` so it natively dies when the host UI window is forcibly closed.
- **Behavior**: Sits completely blocked in a perpetual `readline()` wait loop connected to the Go server payload.
- **Execution Rule**: It is explicitly forbidden from calling _any_ TKinter methods. It exclusively deserializes the incoming JSON string to a standard Python dictionary and `.put()`'s it into the synchronized `Queue`.

### 3. The Transcriber Action Thread (`transcription.py`)

- **Role**: Spawns strictly on-demand when `_on_file_selected` triggers, managing the chunk loop and launching `faster-whisper`.
- **Behavior**: Operates inside a `while not cancel_event.is_set():` infinite loop. Dequeues individual `/temp/*.wav` chunks from an internal queue fed directly by the `_poll_ipc_queue` handler.
- **The Callback Strategy**: Every time a transcription segment returns text, this thread fires a lambda function injecting `self.after(0, update_ui_func)` back onto the Main Event Thread in a strictly non-blocking fashion. This creates the "real-time streaming" typewriter aesthetic.
