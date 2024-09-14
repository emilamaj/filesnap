import os
import json
import base64  # Add this import
from datetime import datetime
from typing import Dict, Union, List
from .utils import ensure_backup_dir, apply_snapshot, decode_data, decompress_data
from .diff import apply_diff
from .snapshot import CompressionTier

class Restore:
    def __init__(self, target_dir: str, backup_dir: str = '.pyfilesnap'):
        self.target_dir = os.path.abspath(target_dir)
        self.backup_dir = os.path.join(self.target_dir, backup_dir)
        ensure_backup_dir(self.backup_dir)

    def restore_last(self) -> str:
        try:
            snapshots = sorted(os.listdir(self.backup_dir), reverse=True)
            if not snapshots:
                raise ValueError("No snapshots found")
            return self._restore_snapshot(snapshots[0])
        except Exception as e:
            print(f"Error restoring last snapshot: {str(e)}")
            raise

    def restore_to_date(self, target_date: str, direction: str = 'closest') -> str:
        try:
            snapshots = sorted(os.listdir(self.backup_dir))
            target_datetime = datetime.strptime(target_date, "%Y%m%d_%H%M%S")
            
            if direction not in ['before', 'after', 'closest']:
                raise ValueError("Invalid direction. Choose 'before', 'after', or 'closest'.")

            closest_snapshot = self._find_closest_snapshot(snapshots, target_datetime, direction)
            
            if closest_snapshot is None:
                raise ValueError(f"No suitable snapshot found {direction} the specified date")
            
            return self._restore_snapshot(closest_snapshot)
        except Exception as e:
            print(f"Error restoring to date: {str(e)}")
            raise

    def _restore_snapshot(self, snapshot_file: str) -> str:
        try:
            snapshot_chain = self._get_snapshot_chain(snapshot_file)
            reconstructed_data = {}

            for snapshot in snapshot_chain:
                snapshot_data = self._load_snapshot_data(snapshot)
                diff_data = decode_data(snapshot_data['data'])
                reconstructed_data = apply_diff(reconstructed_data, diff_data)

            apply_snapshot(self.target_dir, reconstructed_data)
            print(f"Restored to snapshot {snapshot_data['time']}")
            return snapshot_data['time']
        except Exception as e:
            print(f"Error restoring snapshot: {str(e)}")
            raise

    def _find_closest_snapshot(self, snapshots: List[str], target_datetime: datetime, direction: str) -> Union[str, None]:
        closest_snapshot = None
        smallest_time_diff = float('inf')

        for snapshot in snapshots:
            snapshot_time = datetime.strptime(snapshot.split('_', 1)[1].split('.')[0], "%Y%m%d_%H%M%S")
            time_diff = (snapshot_time - target_datetime).total_seconds()
            
            if direction == 'before' and time_diff >= 0:
                continue
            elif direction == 'after' and time_diff <= 0:
                continue
            
            abs_time_diff = abs(time_diff)
            if abs_time_diff < smallest_time_diff:
                smallest_time_diff = abs_time_diff
                closest_snapshot = snapshot
            elif abs_time_diff == smallest_time_diff:
                if direction == 'after' and time_diff > 0:
                    closest_snapshot = snapshot
                elif direction == 'before' and time_diff < 0:
                    closest_snapshot = snapshot
        
        return closest_snapshot

    def _get_snapshot_chain(self, snapshot_file: str) -> List[str]:
        snapshot_chain = []
        current_snapshot = snapshot_file

        while current_snapshot is not None:
            snapshot_chain.append(current_snapshot)
            snapshot_data = self._load_snapshot_data(current_snapshot)
            current_snapshot = snapshot_data['prev_snapshot']

        return snapshot_chain[::-1]

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

            return {k: base64.b64decode(v) for k, v in decoded_data.items()}
        except Exception as e:
            print(f"Error loading snapshot data: {str(e)}")
            raise