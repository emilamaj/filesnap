import os
import json
import base64
from datetime import datetime
from .diff import apply_diff
from .compression import decompress_data
from .utils import ensure_backup_dir
from typing import Dict, Union, List

class Restore:
    """
    A class for restoring snapshots of a directory.

    Args:
        target_dir (str): The directory to restore snapshots to.
        backup_dir (str, optional): The directory where snapshots are stored. Defaults to '.pyfilesnap'.
    """

    def __init__(self, target_dir: str, backup_dir: str = '.pyfilesnap'):
        self.target_dir = os.path.abspath(target_dir)
        self.backup_dir = os.path.join(self.target_dir, backup_dir)
        ensure_backup_dir(self.backup_dir)

    def restore_last(self) -> str:
        """
        Restore the most recent snapshot.

        Returns:
            str: The timestamp of the restored snapshot.

        Raises:
            ValueError: If no snapshots are found.
        """
        snapshots = sorted(os.listdir(self.backup_dir), reverse=True)
        if not snapshots:
            raise ValueError("No snapshots found")
        return self._restore_snapshot(snapshots[0])

    def restore_to_date(self, target_date: str, direction: str = 'closest') -> str:
        """
        Restore to a snapshot closest to the specified date.

        Args:
            target_date (str): The target date in format "YYYYMMDD_HHMMSS".
            direction (str, optional): The direction to search ('before', 'after', or 'closest'). Defaults to 'closest'.

        Returns:
            str: The timestamp of the restored snapshot.

        Raises:
            ValueError: If no suitable snapshot is found or if an invalid direction is provided.
        """
        snapshots = sorted(os.listdir(self.backup_dir))
        target_datetime = datetime.strptime(target_date, "%Y%m%d_%H%M%S")
        
        if direction not in ['before', 'after', 'closest']:
            raise ValueError("Invalid direction. Choose 'before', 'after', or 'closest'.")

        closest_snapshot = self._find_closest_snapshot(snapshots, target_datetime, direction)
        
        if closest_snapshot is None:
            raise ValueError(f"No suitable snapshot found {direction} the specified date")
        
        return self._restore_snapshot(closest_snapshot)

    def _restore_snapshot(self, snapshot_file: str) -> str:
        """
        Restore a specific snapshot.

        Args:
            snapshot_file (str): The filename of the snapshot to restore.

        Returns:
            str: The timestamp of the restored snapshot.
        """
        snapshot_chain = self._get_snapshot_chain(snapshot_file)
        reconstructed_data = {}

        for snapshot in snapshot_chain:
            with open(os.path.join(self.backup_dir, snapshot), 'r') as f:
                snapshot_data = json.load(f)
            
            diff_data = self._decode_snapshot_data(snapshot_data['data'], snapshot_data['compressed'])
            reconstructed_data = apply_diff(reconstructed_data, diff_data)

        self._apply_snapshot(reconstructed_data)
        return snapshot_data['time']

import os
import json
import base64
from datetime import datetime
from .diff import apply_diff
from .compression import decompress_data
from .utils import ensure_backup_dir
from typing import Dict, Union

class Restore:
    """
    A class for restoring snapshots of a directory.

    Args:
        target_dir (str): The directory to restore snapshots to.
        backup_dir (str, optional): The directory where snapshots are stored. Defaults to '.pyfilesnap'.
    """

    def __init__(self, target_dir: str, backup_dir: str = '.pyfilesnap'):
        self.target_dir = os.path.abspath(target_dir)
        self.backup_dir = os.path.join(self.target_dir, backup_dir)
        ensure_backup_dir(self.backup_dir)

    def restore_last(self) -> str:
        """
        Restore the most recent snapshot.

        Returns:
            str: The timestamp of the restored snapshot.

        Raises:
            ValueError: If no snapshots are found.
        """
        snapshots = sorted(os.listdir(self.backup_dir), reverse=True)
        if not snapshots:
            raise ValueError("No snapshots found")
        return self._restore_snapshot(snapshots[0])

    def restore_to_date(self, target_date: str, direction: str = 'closest') -> str:
        """
        Restore to a snapshot closest to the specified date.

        Args:
            target_date (str): The target date in format "YYYYMMDD_HHMMSS".
            direction (str, optional): The direction to search ('before', 'after', or 'closest'). Defaults to 'closest'.

        Returns:
            str: The timestamp of the restored snapshot.

        Raises:
            ValueError: If no suitable snapshot is found or if an invalid direction is provided.
        """
        snapshots = sorted(os.listdir(self.backup_dir))
        target_datetime = datetime.strptime(target_date, "%Y%m%d_%H%M%S")
        
        if direction not in ['before', 'after', 'closest']:
            raise ValueError("Invalid direction. Choose 'before', 'after', or 'closest'.")

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
                # If two snapshots are equally close, choose based on direction
                if direction == 'after' and time_diff > 0:
                    closest_snapshot = snapshot
                elif direction == 'before' and time_diff < 0:
                    closest_snapshot = snapshot
                # For 'closest', we keep the earlier snapshot (no change needed)
        
        if closest_snapshot is None:
            raise ValueError(f"No suitable snapshot found {direction} the specified date")
        
        return self._restore_snapshot(closest_snapshot)

    def _restore_snapshot(self, snapshot_file: str) -> str:
        """
        Restore a specific snapshot.

        Args:
            snapshot_file (str): The filename of the snapshot to restore.

        Returns:
            str: The timestamp of the restored snapshot.
        """
        with open(os.path.join(self.backup_dir, snapshot_file), 'r') as f:
            snapshot_data = json.load(f)
        
        if snapshot_data['compressed']:
            compressed_data = base64.b64decode(snapshot_data['data'])
            snapshot_data['data'] = json.loads(decompress_data(compressed_data).decode())
        
        # Decode base64 strings back to bytes
        decoded_data = {k: base64.b64decode(v) for k, v in snapshot_data['data'].items()}
        
        self._apply_snapshot(decoded_data)
        return snapshot_data['time']

    def _apply_snapshot(self, snapshot_data: Dict[str, bytes]) -> None:
        """
        Apply the snapshot data to the target directory.

        Args:
            snapshot_data (Dict[str, bytes]): The snapshot data to apply.
        """
        for file_path, content in snapshot_data.items():
            full_path = os.path.join(self.target_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(content)