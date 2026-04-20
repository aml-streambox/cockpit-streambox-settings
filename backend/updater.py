#!/usr/bin/env python3

import hashlib
import logging
import os
import re
import subprocess
import tempfile
import threading
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

UPDATE_SCRIPT = "/usr/bin/update_swfirmware.sh"
DATA_DIR = Path("/data")
PART_FILE = DATA_DIR / "software.swu.part"
FINAL_FILE = DATA_DIR / "software.swu"
VERSION_FILE = Path("/etc/sw-versions")
HWREVISION_FILE = Path("/etc/hwrevision")
MAX_UPLOAD_SIZE = 1024 * 1024 * 1024  # 1 GB

DRY_RUN_FILE = Path("/data/updater-dry-run")


class UpdaterState(Enum):
    IDLE = "idle"
    UPLOADING = "uploading"
    VERIFYING = "verifying"
    READY = "ready"
    UPDATING = "updating"
    ERROR = "error"


class UpdaterManager:
    def __init__(self):
        self._state = UpdaterState.IDLE
        self._progress = 0.0
        self._total_size = 0
        self._received_size = 0
        self._sha256_ctx = hashlib.sha256()
        self._error_message = ""
        self._lock = threading.Lock()
        self._device_board = self._read_device_board()

    def _read_device_board(self) -> str:
        try:
            if HWREVISION_FILE.exists():
                with open(HWREVISION_FILE, "r") as f:
                    line = f.readline().strip()
                    if line:
                        return line.split()[0]
        except Exception as e:
            logger.error(f"Failed to read hwrevision: {e}")
        return ""

    @property
    def state(self) -> str:
        return self._state.value

    @property
    def progress(self) -> float:
        return round(self._progress, 2)

    @property
    def error_message(self) -> str:
        return self._error_message

    def get_current_version(self) -> str:
        try:
            if VERSION_FILE.exists():
                with open(VERSION_FILE, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("VERSION="):
                            return line.split("=", 1)[1]
            return "unknown"
        except Exception as e:
            logger.error(f"Failed to read version: {e}")
            return "unknown"

    def get_status(self) -> dict:
        return {
            "state": self.state,
            "progress": self.progress,
            "error": self._error_message,
            "current_version": self.get_current_version(),
            "device_board": self._device_board,
            "total_size": self._total_size,
            "received_size": self._received_size,
            "dry_run": self.is_dry_run(),
        }

    @staticmethod
    def is_dry_run() -> bool:
        return DRY_RUN_FILE.exists()

    def set_dry_run(self, enabled: bool) -> None:
        try:
            if enabled:
                DRY_RUN_FILE.touch()
                logger.info("Dry-run mode ENABLED (update will not reboot)")
            else:
                DRY_RUN_FILE.unlink(missing_ok=True)
                logger.info("Dry-run mode DISABLED")
        except Exception as e:
            logger.error(f"Failed to set dry-run: {e}")

    def start_upload(self, total_size: int) -> bool:
        with self._lock:
            if self._state not in (UpdaterState.IDLE, UpdaterState.ERROR):
                logger.warning(f"Cannot start upload in state {self._state}")
                return False

            if total_size > MAX_UPLOAD_SIZE:
                self._error_message = f"File too large ({total_size} bytes, max {MAX_UPLOAD_SIZE} bytes)"
                self._state = UpdaterState.ERROR
                return False

            available = self._get_available_space()
            if available < total_size:
                self._error_message = f"Not enough space on /data ({available} bytes available, {total_size} needed)"
                self._state = UpdaterState.ERROR
                return False

            self._total_size = total_size
            self._received_size = 0
            self._progress = 0.0
            self._sha256_ctx = hashlib.sha256()
            self._error_message = ""
            self._state = UpdaterState.UPLOADING

            try:
                PART_FILE.unlink(missing_ok=True)
            except Exception:
                pass

            logger.info(f"Upload started: {total_size} bytes")
            return True

    def write_chunk(self, data: bytes, offset: int) -> float:
        with self._lock:
            if self._state != UpdaterState.UPLOADING:
                return self._progress

            try:
                mode = "r+b" if PART_FILE.exists() else "wb"
                if mode == "wb" and offset > 0:
                    with open(PART_FILE, "wb") as f:
                        f.seek(offset)
                        f.write(b"\x00" * offset)
                    mode = "r+b"

                with open(PART_FILE, mode) as f:
                    f.seek(offset)
                    f.write(data)

                self._sha256_ctx.update(data)
                self._received_size += len(data)
                self._progress = min(100.0, (self._received_size / self._total_size) * 100.0)

            except Exception as e:
                logger.error(f"Write chunk failed: {e}")
                self._error_message = f"Write failed: {e}"
                self._state = UpdaterState.ERROR

            return self._progress

    def finalize_upload(self, expected_sha256: str) -> bool:
        with self._lock:
            if self._state != UpdaterState.UPLOADING:
                return False

            self._state = UpdaterState.VERIFYING

        computed = self._sha256_ctx.hexdigest()
        logger.info(f"SHA-256 verification: expected={expected_sha256}, computed={computed}")

        with self._lock:
            if computed.lower() != expected_sha256.lower():
                self._error_message = f"SHA-256 mismatch (expected {expected_sha256[:16]}..., got {computed[:16]}...)"
                self._state = UpdaterState.ERROR
                try:
                    PART_FILE.unlink(missing_ok=True)
                except Exception:
                    pass
                logger.error(self._error_message)
                return False

            try:
                PART_FILE.rename(FINAL_FILE)
            except Exception as e:
                self._error_message = f"Failed to finalize: {e}"
                self._state = UpdaterState.ERROR
                return False

            if not self._verify_cpio_signature():
                self._error_message = "Invalid update package: missing sw-description.sig"
                self._state = UpdaterState.ERROR
                try:
                    FINAL_FILE.unlink(missing_ok=True)
                except Exception:
                    pass
                return False

            pkg_board = self._extract_board_from_sw_description()
            if pkg_board and self._device_board:
                pkg_norm = pkg_board.replace("-", "_").replace(".", "_").lower()
                dev_norm = self._device_board.replace("-", "_").replace(".", "_").lower()
                if pkg_norm != dev_norm:
                    self._error_message = (
                        f"Board mismatch: package is for '{pkg_board}' "
                        f"but this device is '{self._device_board}'"
                    )
                    self._state = UpdaterState.ERROR
                    logger.error(self._error_message)
                    try:
                        FINAL_FILE.unlink(missing_ok=True)
                    except Exception:
                        pass
                    return False
                logger.info(f"Board match OK: package={pkg_board} device={self._device_board}")

            self._state = UpdaterState.READY
            logger.info("Upload finalized and verified successfully")
            return True

    def trigger_update(self) -> bool:
        with self._lock:
            if self._state != UpdaterState.READY:
                return False

            if not FINAL_FILE.exists():
                self._error_message = "Update file not found"
                self._state = UpdaterState.ERROR
                return False

            self._state = UpdaterState.UPDATING

        logger.info("Triggering OTA update...")

        thread = threading.Thread(target=self._run_update, daemon=True)
        thread.start()
        return True

    def cancel_upload(self) -> bool:
        with self._lock:
            if self._state not in (UpdaterState.UPLOADING, UpdaterState.READY, UpdaterState.ERROR):
                return False

            try:
                PART_FILE.unlink(missing_ok=True)
                FINAL_FILE.unlink(missing_ok=True)
            except Exception:
                pass

            self._state = UpdaterState.IDLE
            self._progress = 0.0
            self._total_size = 0
            self._received_size = 0
            self._error_message = ""
            logger.info("Upload cancelled")
            return True

    def import_local_file(self, filepath: str, expected_sha256: str) -> bool:
        with self._lock:
            if self._state not in (UpdaterState.IDLE, UpdaterState.ERROR):
                self._error_message = f"Cannot import in state {self._state}"
                return False
            self._state = UpdaterState.VERIFYING
            self._error_message = ""

        src = Path(filepath)
        if not src.exists():
            with self._lock:
                self._error_message = f"File not found: {filepath}"
                self._state = UpdaterState.ERROR
            return False

        try:
            file_size = src.stat().st_size
            self._total_size = file_size
            self._received_size = file_size
            self._progress = 100.0

            sha256 = hashlib.sha256()
            with open(src, "rb") as f:
                while True:
                    chunk = f.read(8 * 1024 * 1024)
                    if not chunk:
                        break
                    sha256.update(chunk)

            computed = sha256.hexdigest()

            if expected_sha256:
                logger.info(f"Local import SHA-256: expected={expected_sha256}, computed={computed}")
                if computed.lower() != expected_sha256.lower():
                    with self._lock:
                        self._error_message = f"SHA-256 mismatch (expected {expected_sha256[:16]}..., got {computed[:16]}...)"
                        self._state = UpdaterState.ERROR
                    return False
            else:
                logger.info(f"Local import SHA-256 (computed only): {computed}, skipping comparison")

            src_resolved = src.resolve()
            dst_resolved = FINAL_FILE.resolve()
            if src_resolved != dst_resolved:
                try:
                    FINAL_FILE.unlink(missing_ok=True)
                except Exception:
                    pass
                import shutil
                shutil.copy2(str(src), str(FINAL_FILE))
            else:
                logger.info("Source is already at destination, skipping copy")

            if not self._verify_cpio_signature():
                with self._lock:
                    self._error_message = "Invalid update package: missing sw-description.sig"
                    self._state = UpdaterState.ERROR
                if src_resolved != dst_resolved:
                    try:
                        FINAL_FILE.unlink(missing_ok=True)
                    except Exception:
                        pass
                return False

            pkg_board = self._extract_board_from_sw_description()
            if pkg_board and self._device_board:
                pkg_norm = pkg_board.replace("-", "_").replace(".", "_").lower()
                dev_norm = self._device_board.replace("-", "_").replace(".", "_").lower()
                if pkg_norm != dev_norm:
                    with self._lock:
                        self._error_message = (
                            f"Board mismatch: package is for '{pkg_board}' "
                            f"but this device is '{self._device_board}'"
                        )
                        self._state = UpdaterState.ERROR
                    logger.error(self._error_message)
                    if src_resolved != dst_resolved:
                        try:
                            FINAL_FILE.unlink(missing_ok=True)
                        except Exception:
                            pass
                    return False
                logger.info(f"Board match OK: package={pkg_board} device={self._device_board}")

            with self._lock:
                self._state = UpdaterState.READY
            logger.info("Local file import verified successfully")
            return True

        except Exception as e:
            with self._lock:
                self._error_message = f"Import failed: {e}"
                self._state = UpdaterState.ERROR
            logger.error(f"Local import error: {e}")
            return False

    def _run_update(self):
        if self.is_dry_run():
            logger.info("DRY-RUN: skipping actual update. Package verified at %s", FINAL_FILE)
            with open(DATA_DIR / "updater-dry-run-result.txt", "w") as f:
                f.write(f"dry_run=true\n")
                f.write(f"package={FINAL_FILE}\n")
                f.write(f"size={FINAL_FILE.stat().st_size}\n")
                f.write(f"board={self._device_board}\n")
            with self._lock:
                self._state = UpdaterState.IDLE
                self._progress = 0.0
                self._error_message = ""
            return

        try:
            result = subprocess.run(
                [UPDATE_SCRIPT],
                capture_output=True,
                text=True,
                timeout=30,
            )
            logger.info(f"Update script exited: rc={result.returncode}")
            logger.info(f"stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"stderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("Update script timed out (device may be rebooting)")
        except Exception as e:
            logger.error(f"Update script failed: {e}")
            with self._lock:
                self._error_message = f"Update failed: {e}"
                self._state = UpdaterState.ERROR

    def _verify_cpio_signature(self) -> bool:
        try:
            result = subprocess.run(
                ["cpio", "-t", "-F", str(FINAL_FILE)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return "sw-description.sig" in result.stdout
        except Exception as e:
            logger.error(f"CPIO verification failed: {e}")
            return False

    def _extract_board_from_sw_description(self) -> Optional[str]:
        try:
            tmpdir = Path(tempfile.mkdtemp(prefix="updater-"))
            result = subprocess.run(
                ["cpio", "-i", "-F", str(FINAL_FILE), "sw-description"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(tmpdir),
            )
            desc_file = tmpdir / "sw-description"
            if not desc_file.exists():
                logger.error(f"Failed to extract sw-description from cpio")
                return None

            with open(desc_file, "r") as f:
                content = f.read()

            desc_file.unlink()
            tmpdir.rmdir()

            for line in content.split("\n"):
                line = line.strip()
                m = re.match(r'^([a-z][a-z0-9_.]*)\s*=\s*\{$', line)
                if m:
                    board = m.group(1)
                    if board != "software":
                        return board
            logger.warning("Could not find board name in sw-description")
            return None
        except Exception as e:
            logger.error(f"Failed to parse sw-description: {e}")
            return None

    def _get_available_space(self) -> int:
        try:
            stat = os.statvfs(DATA_DIR)
            return stat.f_bavail * stat.f_frsize
        except Exception:
            return 0
