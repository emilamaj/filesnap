import os
from typing import Dict, Union
import base64
import zlib
import tarfile
import io
from typing import Optional

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
                # Use os.path.relpath to get the relative path, then replace backslashes with forward slashes
                relative_path = os.path.relpath(file_path, target_dir).replace(os.path.sep, '/')
                files_data[relative_path] = f.read()
    return files_data

def apply_snapshot(target_dir: str, snapshot_data: Dict[str, bytes]) -> None:
    """Apply the snapshot data to the target directory."""
    for file_path, content in snapshot_data.items():
        full_path = os.path.join(target_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(content)

def encode_data(data: Dict[str, Optional[bytes]]) -> Dict[str, Optional[str]]:
    """Encode binary data as base64 strings."""
    return {k: base64.b64encode(v).decode('utf-8') if v is not None else None for k, v in data.items()}

def decode_data(data: Dict[str, Optional[Union[str, bytes]]]) -> Dict[str, Optional[bytes]]:
    """Decode base64 strings to binary data."""
    def safe_decode(v):
        if v is None:
            return None
        if isinstance(v, str):
            # Add padding if necessary
            v += '=' * (-len(v) % 4)
            return base64.b64decode(v)
        return v
    return {k: safe_decode(v) for k, v in data.items()}

def compress_data(data: bytes) -> bytes:
    """Compress binary data using zlib."""
    return zlib.compress(data)

def decompress_data(compressed_data: bytes) -> bytes:
    """Decompress binary data using zlib."""
    return zlib.decompress(compressed_data)

def create_archive(archive_path: str, file_name: str, data: bytes) -> None:
    with tarfile.open(archive_path, "w:gz") as tar:
        info = tarfile.TarInfo(name=file_name)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))

def add_to_archive(archive_path: str, file_name: str, data: bytes) -> None:
    with tarfile.open(archive_path, "a:gz") as tar:
        info = tarfile.TarInfo(name=file_name)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))

def extract_archive(archive_data: bytes, file_name: Optional[str] = None) -> Union[Dict[str, bytes], bytes]:
    """Extract files from a tar archive."""
    with tarfile.open(fileobj=io.BytesIO(archive_data), mode='r:gz') as tar:
        if file_name:
            member = tar.getmember(file_name)
            f = tar.extractfile(member)
            if f:
                return f.read()
            return b''
        else:
            extracted_data = {}
            for member in tar.getmembers():
                f = tar.extractfile(member)
                if f:
                    extracted_data[member.name] = f.read()
            return extracted_data

def update_archive(archive_path: str, file_name: str, data: bytes) -> None:
    temp_archive = archive_path + '.temp'
    with tarfile.open(archive_path, 'r:gz') as src, tarfile.open(temp_archive, 'w:gz') as dst:
        for member in src.getmembers():
            dst.addfile(member, src.extractfile(member))
        info = tarfile.TarInfo(name=file_name)
        info.size = len(data)
        dst.addfile(info, io.BytesIO(data))
    os.replace(temp_archive, archive_path)
