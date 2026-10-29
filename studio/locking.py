"""Local process locks and atomic replacement resilient to brief Windows file locks."""
import os
import time
from pathlib import Path

from .models import StudioError


def replace_file(temporary: Path, target: Path):
    """Keep the previous file intact while a scanner/indexer briefly holds it open."""
    for attempt in range(5):
        try:
            temporary.replace(target)
            return
        except PermissionError as exc:
            if getattr(exc, "winerror", None) not in (5, 32, 33) or attempt == 4:
                raise
            time.sleep(.05 * 2 ** attempt)


class FileLock:
    def __init__(self, path: Path, message: str):
        self.path, self.message, self.handle = path, message, None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        if os.fstat(handle.fileno()).st_size == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise StudioError(self.message) from None
        self.handle = handle
        return self

    def release(self):
        if self.handle is None:
            return
        handle, self.handle = self.handle, None
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN, )
        finally:
            handle.close()

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *_):
        self.release()
