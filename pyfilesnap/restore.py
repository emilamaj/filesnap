import os
import json
from datetime import datetime
from typing import List, Union
from .utils import apply_snapshot, decode_data, extract_archive
from .snapshot import Snapshot
import logging

class Restore:
    def __init__(self, target_dir: str, backup_dir: str = '.pyfilesnap'):
        self.target_dir = os.path.abspath(target_dir)
        self.backup_dir = os.path.join(self.target_dir, backup_dir)
        self.snapshot = Snapshot(target_dir, backup_dir)

    def restore_to_date(self, target_date: str, direction: str = 'exact') -> bool:
        target_datetime = datetime.strptime(target_date, "%Y%m%d_%H%M%S")
        snapshots = self._get_snapshots()
        
        closest_snapshot = self._find_closest_snapshot(snapshots, target_datetime, direction)
        
        if closest_snapshot:
            return self._restore_snapshot(closest_snapshot)
        return False

    def _restore_snapshot(self, snapshot_file: str) -> bool:
        snapshot_chain = self._get_snapshot_chain(snapshot_file)
        logging.debug(f"Restoring snapshot chain: {snapshot_chain}")
        full_state = {}
        
        for snapshot in snapshot_chain:
            snapshot_data = self._load_snapshot_data(snapshot)
            diff_data = decode_data(snapshot_data['data'])
            full_state.update(diff_data)
        
        apply_snapshot(self.target_dir, full_state)
        return True

    def _get_snapshots(self) -> List[str]:
        snapshots = []
        if os.path.exists(os.path.join(self.backup_dir, 'snapshots.tar.gz')):
            with open(os.path.join(self.backup_dir, 'snapshots.tar.gz'), 'rb') as f:
                archive_data = f.read()
            extracted_data = extract_archive(archive_data)
            snapshots = sorted(extracted_data.keys())
        else:
            snapshots = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('snapshot_') and f.endswith('.json')])
        logging.debug(f"Found snapshots: {snapshots}")
        return snapshots

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
                logging.debug(f"Closest snapshot found: {closest_snapshot}")
        
        return closest_snapshot

    def _get_snapshot_chain(self, snapshot_file: str) -> List[str]:
        snapshot_chain = []
        current_snapshot = snapshot_file

        while current_snapshot is not None:
            if current_snapshot in snapshot_chain:
                print(f"Circular reference detected in snapshot chain: {current_snapshot}")
                break
            snapshot_chain.append(current_snapshot)
            snapshot_data = self._load_snapshot_data(current_snapshot)
            current_snapshot = snapshot_data.get('prev_snapshot')

        return snapshot_chain[::-1]

    def _load_snapshot_data(self, snapshot_file: str) -> dict:
        return self.snapshot._load_snapshot_data(snapshot_file)

    def restore_last(self) -> str:
        snapshots = self._get_snapshots()
        if not snapshots:
            raise ValueError("No snapshots found")
        
        latest_snapshot = snapshots[-1]
        return self._restore_snapshot(latest_snapshot)