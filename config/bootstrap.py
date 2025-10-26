import sys
from pathlib import Path

def add_src_to_sys_path(markers=(".project-root", "README.md", ".git")):
    current = Path().resolve()
    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            src_path = parent / "src"
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))
            return
    raise FileNotFoundError("Could not find project root to add src to sys.path.")

add_src_to_sys_path()
