# Adding New Tests

If you are developing a new component for Whisper Transcriber, achieving test coverage is a mandatory step before merging into the main branch.

## 1. Adding Python Tests (`pytest`)

1.  **File Naming**: All new test files must exclusively begin with `test_` (e.g., `test_my_new_module.py`).
2.  **Path Resolution**: Because tests are executed from the repository root `tests/python/` while imports originate in `ui/app/`, use the syspath injection scaffold at the top of your test file to avoid `ImportError` exceptions:
    ```python
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from ui.app.utils.my_new_module import my_function
    ```
3.  **Mocking Filesystems**: Utilize the built-in Pytest `tmp_path` fixture to cleanly create and test file output generations without cluttering the local git repository with dummy files.

## 2. Adding Go Tests (`go test`)

1.  **File Naming**: Go strictly requires that tests live parallel to the source code they cover and follow the `*_test.go` naming structure (e.g., `extractor.go` -> `extractor_test.go`).
2.  **Using `t.TempDir()`**: Identical in philosophy to Python's `tmp_path`, always use `t.TempDir()` for mock extractions or IPC `.sock` creations. Go will automatically purge this directory when the test suite concludes.
3.  **Handling OS Binaries**: Avoid hard-coding paths to dependencies like `ffmpeg` or `nvidia-smi`. Instead, implement robust fallbacks or use `t.Skipf()` if dependencies evaluate false during environmental sweeps.
