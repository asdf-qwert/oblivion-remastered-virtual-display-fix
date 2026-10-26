#!/usr/bin/env python3
"""Reversible one-byte Oblivion Remastered fullscreen fix. Python 3.8+, no dependencies."""
import argparse
import hashlib
import os
from pathlib import Path
import sys

ORIGINAL = "b7be7e6ebe9424f6fdf274f5e7a59372de103e043ab5b66c60e021c0c89df457"
PATCHED = "302c436781814c561813ae8bb482dd54d934807da4a9459726755d2869e56682"
SIZE = 160654648
OFFSET = 0x031AAB36
BACKUP_SUFFIX = ".oblivion-resolution-fix.original"
CONTEXT = bytes.fromhex("77 06 44 39 24 0f 7e 2c 8b 46 08")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def get_state(data):
    if len(data) != SIZE:
        raise ValueError("Unsupported EXE size: {} (expected {}).".format(len(data), SIZE))
    digest = sha256(data)
    if digest == ORIGINAL:
        return "Original"
    if digest == PATCHED:
        return "Patched"
    raise ValueError("Unsupported EXE SHA-256: " + digest)


def verify_backup(backup, path):
    if backup.is_symlink() or backup.samefile(path):
        raise ValueError("Backup must be a separate original file; EXE was not changed.")
    if get_state(backup.read_bytes()) != "Original":
        raise ValueError("Backup differs from original; EXE was not changed.")


def run_patch(exe, restore=False, check=False):
    path = Path(exe)
    with path.open("rb" if check else "r+b") as stream:
        before = stream.read()
        state = get_state(before)
        context = bytearray(CONTEXT)
        if state == "Patched":
            context[6] = 0xEB
        if before[OFFSET - 6:OFFSET + 5] != context:
            raise ValueError("Instruction context mismatch; EXE was not changed.")
        if check:
            return state + " (supported EXE)."
        desired = "Original" if restore else "Patched"
        if state == desired:
            return "Already " + desired.lower() + "; unchanged."
        backup = path.with_name(path.name + BACKUP_SUFFIX)
        if restore:
            verify_backup(backup, path)
            replacement = b"\x7e"
            expected = ORIGINAL
        else:
            try:
                with backup.open("xb") as saved:
                    if saved.write(before) != len(before):
                        raise OSError("Incomplete backup write.")
                    saved.flush()
                    os.fsync(saved.fileno())
            except FileExistsError:
                pass
            verify_backup(backup, path)
            replacement = b"\xeb"
            expected = PATCHED
        stream.seek(0)
        if sha256(stream.read()) != sha256(before):
            raise ValueError("EXE changed during preparation; patch was not written.")
        try:
            stream.seek(OFFSET)
            if stream.write(replacement) != 1:
                raise OSError("Incomplete patch write.")
            stream.flush()
            os.fsync(stream.fileno())
            stream.seek(0)
            if sha256(stream.read()) != expected:
                raise ValueError("Result verification failed.")
        except (OSError, ValueError):
            try:
                stream.seek(OFFSET)
                if stream.write(before[OFFSET:OFFSET + 1]) != 1:
                    raise OSError("Incomplete rollback write.")
                stream.flush()
                os.fsync(stream.fileno())
                stream.seek(0)
                if sha256(stream.read()) != sha256(before):
                    raise ValueError("Rollback verification failed.")
            except (OSError, ValueError) as recovery_error:
                raise RuntimeError("Rollback failed. Keep the original backup: " + str(backup)) from recovery_error
            raise
    return desired + ". Original backup: " + str(backup)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path, help="Path to Binaries/Win64/OblivionRemastered-Win64-Shipping.exe")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Check without changing or backing up the EXE")
    mode.add_argument("--restore", action="store_true", help="Restore using the verified original backup")
    args = parser.parse_args()
    try:
        print(run_patch(args.exe, restore=args.restore, check=args.check))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
