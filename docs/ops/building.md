# Building Deployments (`.github/workflows/release.yml`)

Distributing a hybrid Go/Python codebase requires a two-step compilation process. This dual compilation is fully automated via GitHub Actions on every tag push starting with `v*` (e.g., `git tag v1.0.0`, then `git push origin v1.0.0`).

## Stage 1: The Go Binary (`core/`)

Before Python can be packaged, the Go IPC orchestrator must be pre-compiled natively for the target operating system (Windows `.exe`, Linux ELF, macOS Mach-O).

The Go compiler explicitly injects linking flags `-ldflags="-s -w"` to dramatically reduce the binary footprint by stripping debug symbols. It places the resulting binary explicitly into `ui/app/bin/wt-core`.

## Stage 2: PyInstaller (`ui/app/`)

Once the Go core is built and copied into the `bin/` folder, Pyinstaller is invoked against `ui/app/main.py`.

### Execution Command

```bash
python -m PyInstaller --noconfirm --clean --name WhisperTranscriber --noconsole --windowed ui/app/main.py
```

### Critical Flags

- `--noconsole` / `--windowed`: Suppresses the lingering, ugly black terminal window that usually accompanies Pyinstaller builds on Windows machines. The CustomTkinter graphical window boots standalone.
- **The Go Payload Constraint**: Because `ui/app/main.py` utilizes relative dynamic paths `sys._MEIPASS` at runtime, Pyinstaller implicitly bundles the `bin/wt-core` executable inside its temporary extraction `.exe`. If the Go binary isn't compiled exactly before Pyinstaller runs, the deployment will crash immediately upon launching with a `BINARY_NOT_FOUND` error.
