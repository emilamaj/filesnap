import os
import json
import base64  # Add this import
from datetime import datetime
from typing import Dict, Union, Optional
from .utils import ensure_backup_dir, collect_files_data, compress_data, decompress_data
from .diff import create_diff  # Add this import
from enum import Enum

class CompressionTier(Enum):
    NONE = 0
    MINIMAL = 1
    MAXIMAL = 2

class Snapshot:
    def __init__(self, target_dir: str, backup_dir: str = '.pyfilesnap', compression: CompressionTier = CompressionTier.NONE):
        self.target_dir = os.path.abspath(target_dir)
        self.backup_dir = os.path.join(self.target_dir, backup_dir)
        self.compression = compression
        ensure_backup_dir(self.backup_dir)

    def _get_snapshot_path(self, snapshot_time: str) -> str:
        return os.path.join(self.backup_dir, f'snapshot_{snapshot_time}.json')

    def _load_snapshot_data(self, snapshot_file: str) -> Dict[str, Union[str, Dict[str, bytes]]]:
        try:
            with open(os.path.join(self.backup_dir, snapshot_file), 'r') as f:
                snapshot_data = json.load(f)
            
            compression = CompressionTier(snapshot_data['compression'])
            
            if compression == CompressionTier.MAXIMAL:
                decompressed_data = decompress_data(base64.b64decode(snapshot_data['data']))
                decoded_data = json.loads(decompressed_data.decode())
            elif compression == CompressionTier.MINIMAL:
                decoded_data = {k: decompress_data(base64.b64decode(v)) for k, v in snapshot_data['data'].items()}
            else:
                decoded_data = snapshot_data['data']

            return {
                'time': snapshot_data['time'],
                'data': decoded_data,
                'compression': compression,
                'prev_snapshot': snapshot_data.get('prev_snapshot')
            }
        except Exception as e:
            print(f"Error loading snapshot data: {str(e)}")
            raise

    def _save_snapshot_data(self, snapshot_time: str, data: Dict[str, bytes], prev_snapshot: Optional[str] = None):
        try:
            encoded_data = {k: base64.b64encode(v).decode() for k, v in data.items()}
            
            if self.compression == CompressionTier.MAXIMAL:
                compressed_data = compress_data(json.dumps(encoded_data).encode())
                encoded_data = base64.b64encode(compressed_data).decode()
            elif self.compression == CompressionTier.MINIMAL:
                encoded_data = {k: base64.b64encode(compress_data(v)).decode() for k, v in data.items()}

            snapshot_data = {
                'time': snapshot_time,
                'data': encoded_data,
                'compression': self.compression.value,
                'prev_snapshot': prev_snapshot
            }

            with open(self._get_snapshot_path(snapshot_time), 'w') as f:
                json.dump(snapshot_data, f)
        except Exception as e:
            print(f"Error saving snapshot data: {str(e)}")
            raise

    def take_snapshot(self) -> str:
        try:
            snapshot_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_data = collect_files_data(self.target_dir, self.backup_dir)
            
            snapshots = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('snapshot_')])
            if not snapshots:
                diff_data = current_data
                prev_snapshot = None
            else:
                prev_snapshot = snapshots[-1]
                prev_data = self._load_snapshot_data(prev_snapshot)['data']
                diff_data = create_diff(prev_data, current_data)

            self._save_snapshot_data(snapshot_time, diff_data, prev_snapshot)
            return snapshot_time
        except Exception as e:
            print(f"Error taking snapshot: {str(e)}")
            raise