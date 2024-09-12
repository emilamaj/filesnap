import os
from typing import Dict
import base64
import zlib

def ensure_backup_dir(backup_dir: str) -> None:
    """Ensure that the backup directory exists."""
    os.makedirs(backup_dir, exist_ok=True)

def collect_files_data(target_dir: str, backup_dir: str) -> Dict[str, bytes]:
    """Collect data from all files in the target directory."""
    files_data = {}
    for root, _, files in os.walk(target_dir):
        if root == backup_dir:
            continue
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                files_data[os.path.relpath(file_path, target_dir)] = f.read()
    return files_data

def apply_snapshot(target_dir: str, snapshot_data: Dict[str, bytes]) -> None:
    """Apply the snapshot data to the target directory."""
    for file_path, content in snapshot_data.items():
        full_path = os.path.join(target_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(content)

def encode_data(data: Dict[str, bytes]) -> Dict[str, str]:
    """Encode binary data as base64 strings."""
    return {k: base64.b64encode(v).decode('utf-8') for k, v in data.items()}

def decode_data(data: Dict[str, str]) -> Dict[str, bytes]:
    """Decode base64 strings to binary data."""
    return {k: base64.b64decode(v) for k, v in data.items()}

def compress_data(data: bytes) -> bytes:
    """Compress binary data using zlib."""
    return zlib.compress(data)

def decompress_data(compressed_data: bytes) -> bytes:
    """Decompress binary data using zlib."""
    return zlib.decompress(compressed_data)
