import os
import json
import base64  # Add this import
from datetime import datetime
from typing import Dict, Union, Optional, List, Set
import tarfile  # Add this import
from .utils import ensure_backup_dir, collect_files_data, create_archive, update_archive, decode_data, extract_archive, encode_data  # Add encode_data import
from .diff import create_diff, apply_diff  # Ensure apply_diff is imported here as well
import logging
import time
import concurrent.futures
from fnmatch import fnmatch

class SnapshotConfig:
    def __init__(self, compress: bool = False, excluded_patterns: List[str] = None):
        self.compress = compress
        self.excluded_patterns = excluded_patterns or []

class Snapshot:
    def __init__(self, target_dir: str, backup_dir: str = '.pyfilesnap', config: SnapshotConfig = None):
        self.target_dir = os.path.abspath(target_dir)
        if not os.path.exists(self.target_dir):
            raise FileNotFoundError(f"The target directory '{self.target_dir}' does not exist.")
        self.backup_dir = os.path.join(self.target_dir, backup_dir)
        self.config = config or SnapshotConfig()
        ensure_backup_dir(self.backup_dir)

    def take_snapshot(self) -> str:
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        current_data = collect_files_data(self.target_dir, self.backup_dir)
        
        prev_snapshot = self._get_last_snapshot()
        if prev_snapshot:
            prev_snapshot_time = prev_snapshot.split('_', 1)[1].split('.')[0]  # Extract timestamp from filename
            prev_data = self._load_snapshot_data(prev_snapshot)
            if prev_data and 'data' in prev_data:
                prev_full_data = decode_data(prev_data['data'])
                diff_data = create_diff(prev_full_data, current_data)
                if not diff_data:  # No changes detected
                    logging.debug(f"No changes detected, returning previous snapshot time: {prev_data['time']}")
                    return prev_data['time']  # Return the time of the previous snapshot
            else:
                diff_data = current_data
                prev_snapshot_time = None  # Set to None if prev_data is invalid
        else:
            diff_data = current_data
            prev_snapshot_time = None  # Set to None for the first snapshot
        
        encoded_diff_data = encode_data(diff_data)
        
        snapshot_data = {
            'time': current_time,
            'data': encoded_diff_data,
            'compression': self.config.compress,
            'prev_snapshot': prev_snapshot_time
        }
        
        # Save the new snapshot
        new_snapshot_file = f'snapshot_{current_time}.json'
        if self.config.compress:
            self._save_compressed_snapshot(snapshot_data, current_time)
        else:
            self._save_uncompressed_snapshot(snapshot_data, current_time)
        
        logging.debug(f"New snapshot created: {new_snapshot_file}")
        return current_time

    def _get_last_snapshot(self) -> Optional[str]:
        if self.config.compress:
            archive_path = os.path.join(self.backup_dir, 'snapshots.tar.gz')
            if os.path.exists(archive_path):
                with open(archive_path, 'rb') as f:
                    archive_data = f.read()
                extracted_data = extract_archive(archive_data)
                return max(extracted_data.keys()) if extracted_data else None
        
        snapshots = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('snapshot_') and f.endswith('.json')], reverse=True)
        return snapshots[0] if snapshots else None

    def _load_snapshot_data(self, snapshot_file: str) -> dict:
        if self.config.compress:
            archive_path = os.path.join(self.backup_dir, 'snapshots.tar.gz')
            with tarfile.open(archive_path, 'r:gz') as tar:
                # Remove the '.json' extension if present
                snapshot_name = snapshot_file.rsplit('.', 1)[0]
                try:
                    f = tar.extractfile(snapshot_name)
                    if f is None:
                        raise KeyError(f"File {snapshot_name} is not a regular file")
                    snapshot_content = f.read()
                except KeyError:
                    # If the exact name is not found, try to find a matching snapshot
                    matching_members = [m for m in tar.getmembers() if m.name.startswith(snapshot_name)]
                    if not matching_members:
                        raise ValueError(f"No snapshot found matching {snapshot_name}")
                    f = tar.extractfile(matching_members[0])
                    if f is None:
                        raise ValueError(f"Failed to extract {matching_members[0].name}")
                    snapshot_content = f.read()
                return json.loads(snapshot_content)
        else:
            # Try with .json extension first, then without
            snapshot_path = os.path.join(self.backup_dir, f"{snapshot_file}.json")
            if not os.path.exists(snapshot_path):
                snapshot_path = os.path.join(self.backup_dir, snapshot_file)
            
            if not os.path.exists(snapshot_path):
                raise FileNotFoundError(f"No snapshot file found for {snapshot_file}")
            
            with open(snapshot_path, 'r') as f:
                return json.load(f)

    def _save_compressed_snapshot(self, snapshot_data: dict, current_time: str):
        archive_path = os.path.join(self.backup_dir, 'snapshots.tar.gz')
        snapshot_content = json.dumps(snapshot_data).encode()
        if os.path.exists(archive_path):
            update_archive(archive_path, f'snapshot_{current_time}', snapshot_content)
        else:
            create_archive(archive_path, f'snapshot_{current_time}', snapshot_content)

    def _save_uncompressed_snapshot(self, snapshot_data: dict, current_time: str):
        snapshot_file = os.path.join(self.backup_dir, f'snapshot_{current_time}.json')
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot_data, f)

    def get_stored_diff(self, snapshot_time: str) -> Dict[str, bytes]:
        """Get the stored diff for a given snapshot."""
        snapshot_data = self._load_snapshot_data(f'snapshot_{snapshot_time}.json')
        return decode_data(snapshot_data['data'])

    def get_full_state(self, snapshot_time: str) -> Dict[str, bytes]:
        start_time = time.time()
        snapshot_file = f'snapshot_{snapshot_time}.json'
        snapshot_data = self._load_snapshot_data(snapshot_file)
        current_state = decode_data(snapshot_data['data'])
        
        prev_snapshot_time = snapshot_data.get('prev_snapshot')
        chain_length = 0
        processed_snapshots = set()
        
        while prev_snapshot_time:
            chain_length += 1
            if chain_length > 100:  # Arbitrary limit to prevent excessive looping
                logging.warning(f"Snapshot chain exceeds maximum length of 100")
                break
            
            if prev_snapshot_time in processed_snapshots:
                logging.warning(f"Circular reference detected in snapshot chain: {prev_snapshot_time}")
                break
            
            processed_snapshots.add(prev_snapshot_time)
            
            logging.debug(f"Processing previous snapshot: {prev_snapshot_time}")
            prev_snapshot_file = f'snapshot_{prev_snapshot_time}.json'
            prev_data = self._load_snapshot_data(prev_snapshot_file)
            prev_diff = decode_data(prev_data['data'])
            current_state = apply_diff(current_state, prev_diff)
            
            prev_snapshot_time = prev_data.get('prev_snapshot')
        
        end_time = time.time()
        logging.debug(f"Got full state in {end_time - start_time:.2f} seconds (chain length: {chain_length})")
        return current_state

    def _get_files_to_snapshot(self) -> Set[str]:
        files = set()
        for root, _, filenames in os.walk(self.target_dir):
            if root == self.backup_dir:
                continue
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if not any(fnmatch.fnmatch(file_path, pattern) for pattern in self.config.excluded_patterns):
                    files.add(file_path)
        return files

    def _process_file(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as f:
            return f.read()