import os
import json
import base64
from datetime import datetime
from .diff import create_diff
from .compression import compress_data
from .utils import ensure_backup_dir
from typing import Dict, Union

class Snapshot:
    """
    A class for creating and managing snapshots of a directory.

    Args:
        target_dir (str): The directory to snapshot.
        backup_dir (str, optional): The directory to store snapshots. Defaults to '.pyfilesnap'.
        compress (bool, optional): Whether to compress snapshots. Defaults to False.
    """

    def __init__(self, target_dir: str, backup_dir: str = '.pyfilesnap', compress: bool = False):
        self.target_dir = os.path.abspath(target_dir)
        self.backup_dir = os.path.join(self.target_dir, backup_dir)
        self.compress = compress
        ensure_backup_dir(self.backup_dir)

    def take_snapshot(self) -> str:
        """
        Take a snapshot of the target directory.

        Returns:
            str: The timestamp of the created snapshot.
        """
        snapshot_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_data = self._collect_files_data()
        
        snapshots = sorted(os.listdir(self.backup_dir))
        if not snapshots:
            # First snapshot: store full data
            diff_data = current_data
            prev_snapshot = None
        else:
            # Subsequent snapshots: store diff
            prev_snapshot = snapshots[-1]
            with open(os.path.join(self.backup_dir, prev_snapshot), 'r') as f:
                prev_data = json.load(f)
            prev_files = self._decode_snapshot_data(prev_data['data'])
            diff_data = create_diff(prev_files, current_data)

        # Encode binary data as base64 strings
        encoded_diff_data = {k: base64.b64encode(v).decode('utf-8') for k, v in diff_data.items()}
        
        if self.compress:
            compressed_data = compress_data(json.dumps(encoded_diff_data).encode())
            encoded_diff_data = base64.b64encode(compressed_data).decode('utf-8')
        
        snapshot_path = os.path.join(self.backup_dir, f'snapshot_{snapshot_time}.json')
        with open(snapshot_path, 'w') as f:
            json.dump({
                'time': snapshot_time,
                'data': encoded_diff_data,
                'compressed': self.compress,
                'prev_snapshot': prev_snapshot
            }, f)
        
        return snapshot_time

    def _collect_files_data(self) -> Dict[str, bytes]:
        """
        Collect data from all files in the target directory.

        Returns:
            Dict[str, bytes]: A dictionary mapping relative file paths to their contents.
        """
        files_data = {}
        for root, _, files in os.walk(self.target_dir):
            if root == self.backup_dir:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    files_data[os.path.relpath(file_path, self.target_dir)] = f.read()
        return files_data

    @staticmethod
    def _decode_snapshot_data(data: Union[str, Dict[str, str]]) -> Dict[str, bytes]:
        """
        Decode snapshot data from base64 strings.

        Args:
            data (Union[str, Dict[str, str]]): The data to decode.

        Returns:
            Dict[str, bytes]: A dictionary mapping relative file paths to their contents.
        """
        if isinstance(data, str):
            # Decompress if necessary
            decompressed_data = json.loads(decompress_data(base64.b64decode(data)).decode())
        else:
            decompressed_data = data
        return {k: base64.b64decode(v) for k, v in decompressed_data.items()}