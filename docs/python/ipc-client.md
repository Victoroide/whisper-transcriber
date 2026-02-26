# IPC Client (`ui/app/core/ipc_client.py`)

The `IPCClient` manages a background Python daemon thread that continuously listens for JSON strings formatted via `\n` across the socket connection back to Go.

## Primary Class: IPCClient

### `__init__(socket_path)`

Stores a list of dynamic handlers. On Unix-based OS, `socket_path` acts as a filepath to `core-app.sock`. On Windows, it handles standard IPv4.

### `connect()`

Forks the background daemon using `threading.Thread(target=self._reader_thread, daemon=True)`.

### `send(msg_type: str, data: dict)`

A straightforward thread-safe socket writer passing arbitrary payload to Go.

### `update()`

A non-blocking queue consumer. This method is the crucial element preventing Tkinter interface locks.

1.  **Read Action**: Loops indefinitely retrieving `self._queue.get_nowait()`.
2.  **Dispatch**: Resolves the `msg['type']` property to execute functions mapped to the event dictionary.
3.  **UI Interruption**: A Tkinter app MUST run `self._ipc_client.update()` utilizing the `after()` ticker every 100 milliseconds recursively.

## Background Reader Thread

`_reader_thread()` perpetually reads `\n` blocked fragments via `self._socket.makefile('r').readline()`.
Upon completion, it pushes the `dict` onto the thread-safe `Queue` object exactly once to prevent concurrent UI alterations directly from the daemon context.
