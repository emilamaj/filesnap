import os
import json
from datetime import datetime
from typing import List, Union, Optional  # Add Optional to the import
from .utils import apply_snapshot, decode_data, extract_archive
from .snapshot import Snapshot, SnapshotConfig
import logging
import tarfile
from .diff import apply_diff  # Import apply_diff

class Restore:
    def __init__(self, target_dir: str, backup_dir: str = '.pyfilesnap'):
        self.target_dir = os.path.abspath(target_dir)
        self.backup_dir = os.path.join(self.target_dir, backup_dir)
        config = SnapshotConfig(compress=os.path.exists(os.path.join(self.backup_dir, 'snapshots.tar.gz')))
        self.snapshot = Snapshot(target_dir, backup_dir=backup_dir, config=config)

    def restore_to_date(self, target_date: str, direction: str = 'exact') -> bool:
        target_datetime = datetime.strptime(target_date, "%Y%m%d_%H%M%S")
        snapshots = self._get_snapshots()
        logging.debug(f"Available snapshots: {snapshots}")
        
        closest_snapshot = self._find_closest_snapshot(snapshots, target_datetime, direction)
        logging.debug(f"Closest snapshot found: {closest_snapshot}")
        
        if closest_snapshot:
            return self._restore_snapshot(closest_snapshot)
        else:
            logging.warning(f"No suitable snapshot found for date {target_date} with direction {direction}")
            return False

    def _restore_snapshot(self, snapshot_file: str) -> bool:
        snapshot_chain = self._get_snapshot_chain(snapshot_file)
        if not snapshot_chain:
            logging.error(f"Failed to get snapshot chain for {snapshot_file}")
            return False

        logging.debug(f"Restoring snapshot chain: {snapshot_chain}")
        full_state = {}
        
        for snapshot in reversed(snapshot_chain):
            logging.debug(f"Processing snapshot: {snapshot}")
            snapshot_data = self._load_snapshot_data(f"snapshot_{snapshot}")
            if snapshot_data is None:
                logging.error(f"Failed to load snapshot data for {snapshot}")
                return False
            diff_data = decode_data(snapshot_data['data'])
            logging.debug(f"Diff data keys: {list(diff_data.keys())}")
            full_state = apply_diff(full_state, diff_data)
        
        logging.debug(f"Final state keys: {list(full_state.keys())}")
        apply_snapshot(self.target_dir, full_state)
        return True

    def _get_snapshots(self) -> List[str]:
        snapshots = []
        if self.snapshot.config.compress:
            archive_path = os.path.join(self.backup_dir, 'snapshots.tar.gz')
            if os.path.exists(archive_path):
                with tarfile.open(archive_path, 'r:gz') as tar:
                    snapshots = sorted([
                        member.name.replace('snapshot_', '').replace('.json', '')
                        for member in tar.getmembers() 
                        if member.isfile() and member.name.startswith('snapshot_') and member.name.endswith('.json')
                    ])
        else:
            snapshots = sorted([
                f.replace('snapshot_', '').replace('.json', '')
                for f in os.listdir(self.backup_dir)
                if f.startswith('snapshot_') and f.endswith('.json')
            ])
        logging.debug(f"Found snapshots: {snapshots}")
        return snapshots

    def _find_closest_snapshot(self, snapshots: List[str], target_datetime: datetime, direction: str) -> Union[str, None]:
        closest_snapshot = None
        smallest_time_diff = float('inf')

        for snapshot in snapshots:
            try:
                snapshot_time = datetime.strptime(snapshot, "%Y%m%d%H%M%S")
            except ValueError:
                logging.warning(f"Unexpected snapshot name format: {snapshot}")
                continue

            time_diff = (snapshot_time - target_datetime).total_seconds()
            
            if direction == 'before' and time_diff > 0:
                continue
            elif direction == 'after' and time_diff < 0:
                continue
            elif direction == 'exact' and time_diff != 0:
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
                logging.warning(f"Circular reference detected in snapshot chain: {current_snapshot}")
                break
            snapshot_chain.append(current_snapshot)
            snapshot_data = self._load_snapshot_data(current_snapshot)
            if snapshot_data is None:
                logging.error(f"Failed to load snapshot data for {current_snapshot}")
                break
            current_snapshot = snapshot_data.get('prev_snapshot')

        return snapshot_chain[::-1]

    def _load_snapshot_data(self, snapshot_file: str) -> dict:
        if self.snapshot.config.compress:
            return self._load_compressed_snapshot(snapshot_file)
        else:
            return self._load_uncompressed_snapshot(snapshot_file)

    def _load_compressed_snapshot(self, snapshot_file: str) -> dict:
        archive_path = os.path.join(self.backup_dir, 'snapshots.tar.gz')
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Compressed archive not found: {archive_path}")
        
        with tarfile.open(archive_path, 'r:gz') as tar:
            snapshot_name = snapshot_file.split('.')[0]  # Remove file extension if present
            possible_names = [snapshot_name, f'snapshot_{snapshot_name}']
            
            for name in possible_names:
                try:
                    member = tar.getmember(name)
                    f = tar.extractfile(member)
                    if f is None:
                        raise ValueError(f"Failed to extract {name}")
                    snapshot_content = f.read()
                    return json.loads(snapshot_content)
                except KeyError:
                    continue
            
            raise FileNotFoundError(f"No snapshot found matching {snapshot_file} in the compressed archive")

    def _load_uncompressed_snapshot(self, snapshot_file: str) -> dict:
        possible_paths = [
            os.path.join(self.backup_dir, snapshot_file),
            os.path.join(self.backup_dir, f"{snapshot_file}.json"),
            os.path.join(self.backup_dir, f"snapshot_{snapshot_file}"),
            os.path.join(self.backup_dir, f"snapshot_{snapshot_file}.json")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        
        raise FileNotFoundError(f"No snapshot file found for {snapshot_file}")

    def restore_last(self) -> bool:
        snapshots = self._get_snapshots()
        if not snapshots:
            raise ValueError("No snapshots found")
        
        latest_snapshot = snapshots[-1]
        return self._restore_snapshot(latest_snapshot)
