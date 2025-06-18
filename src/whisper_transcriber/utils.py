import os
import sys
import platform
import tempfile

def get_temp_directory():
    return tempfile.gettempdir()

def is_frozen():
    return getattr(sys, 'frozen', False)

def get_base_dir():
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_platform():
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }