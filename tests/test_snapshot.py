import os
import shutil
import tempfile
import unittest
import json
import urllib.parse
from pyfilesnap.snapshot import Snapshot
from pyfilesnap.utils import extract_archive, decode_data  # Add decode_data import
from pyfilesnap.diff import create_diff, apply_diff  # Add apply_diff import here
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TestSnapshot(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up the temporary directory after tests
        shutil.rmtree(self.test_dir)

    def _create_test_file(self, filename='file1.txt', content='Test content'):
        # Helper method to create a test file with given content
        with open(os.path.join(self.test_dir, filename), 'w') as f:
            f.write(content)

    def _create_and_snapshot(self, snapshot, filename, content):
        self._create_test_file(filename, content)
        return snapshot.take_snapshot()

    def test_snapshot_initialization(self):
        # Test if Snapshot object is initialized correctly
        snapshot = Snapshot(self.test_dir)
        self.assertEqual(snapshot.target_dir, os.path.abspath(self.test_dir))
        self.assertEqual(snapshot.backup_dir, os.path.join(self.test_dir, '.pyfilesnap'))
        self.assertFalse(snapshot.compress)

    def test_snapshot_initialization_with_compression(self):
        # Test if Snapshot object is initialized correctly with compression
        snapshot = Snapshot(self.test_dir, compress=True)
        self.assertTrue(snapshot.compress)

    def test_snapshot_creation_uncompressed(self):
        # Test creation of an uncompressed snapshot
        self._create_test_file()
        snapshot = Snapshot(self.test_dir)
        snapshot_time = snapshot.take_snapshot()

        snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        self.assertTrue(os.path.exists(snapshot_path))

    def test_snapshot_creation_compressed(self):
        # Test creation of a compressed snapshot
        self._create_test_file()
        snapshot = Snapshot(self.test_dir, compress=True)
        snapshot_time = snapshot.take_snapshot()

        archive_path = os.path.join(self.test_dir, '.pyfilesnap', 'snapshots.tar.gz')
        self.assertTrue(os.path.exists(archive_path))

    def test_snapshot_content_uncompressed(self):
        # Test the content of an uncompressed snapshot
        self._create_test_file()
        snapshot = Snapshot(self.test_dir)
        snapshot_time = snapshot.take_snapshot()

        snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)

        self.assertFalse(snapshot_data['compression'])
        self.assertIn('data', snapshot_data)
        self.assertIn('file1.txt', snapshot_data['data'])

    def test_snapshot_content_compressed(self):
        # Test the content of a compressed snapshot
        self._create_test_file()
        snapshot = Snapshot(self.test_dir, compress=True)
        snapshot_time = snapshot.take_snapshot()

        archive_path = os.path.join(self.test_dir, '.pyfilesnap', 'snapshots.tar.gz')
        with open(archive_path, 'rb') as f:
            archive_data = f.read()
        extracted_data = extract_archive(archive_data)
        
        snapshot_data = json.loads(extracted_data[f'snapshot_{snapshot_time}'].decode())
        self.assertTrue(snapshot_data['compression'])
        self.assertIn('data', snapshot_data)

    def test_multiple_snapshots_uncompressed(self):
        # Test creation of multiple uncompressed snapshots
        snapshot = Snapshot(self.test_dir)
        
        self._create_test_file('file1.txt', 'Initial content')
        snapshot_time1 = snapshot.take_snapshot()
        
        self._create_test_file('file1.txt', 'Modified content')
        snapshot_time2 = snapshot.take_snapshot()
        
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time1}.json')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time2}.json')))

    def test_multiple_snapshots_compressed(self):
        # Test creation of multiple compressed snapshots
        snapshot = Snapshot(self.test_dir, compress=True)
        
        self._create_test_file('file1.txt', 'Initial content')
        snapshot_time1 = snapshot.take_snapshot()
        
        self._create_test_file('file1.txt', 'Modified content')
        snapshot_time2 = snapshot.take_snapshot()
        
        archive_path = os.path.join(self.test_dir, '.pyfilesnap', 'snapshots.tar.gz')
        self.assertTrue(os.path.exists(archive_path))
        
        with open(archive_path, 'rb') as f:
            archive_data = f.read()
        extracted_data = extract_archive(archive_data)
        
        self.assertIn(f'snapshot_{snapshot_time1}', extracted_data)
        self.assertIn(f'snapshot_{snapshot_time2}', extracted_data)

    def test_snapshot_empty_directory(self):
        # Test snapshot creation with an empty directory
        snapshot = Snapshot(self.test_dir)
        snapshot_time = snapshot.take_snapshot()
        
        snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)
        
        self.assertEqual(snapshot_data['data'], {})

    def test_snapshot_nested_directories(self):
        # Test snapshot creation with nested directories
        nested_dir = os.path.join('dir1', 'dir2')
        os.makedirs(os.path.join(self.test_dir, nested_dir))
        self._create_test_file(os.path.join(nested_dir, 'file.txt'), 'Nested content')
        
        snapshot = Snapshot(self.test_dir)
        snapshot_time = snapshot.take_snapshot()
        
        snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)
        
        expected_path = os.path.join('dir1', 'dir2', 'file.txt').replace(os.path.sep, '/')
        self.assertIn(expected_path, snapshot_data['data'])

    def test_snapshot_large_file(self):
        # Test snapshot creation with a large file (10 MB)
        large_file_path = os.path.join(self.test_dir, 'large_file.bin')
        with open(large_file_path, 'wb') as f:
            f.write(os.urandom(10 * 1024 * 1024))  # 10 MB of random data
        
        snapshot = Snapshot(self.test_dir)
        snapshot_time = snapshot.take_snapshot()
        
        snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)
        
        self.assertIn('large_file.bin', snapshot_data['data'])

    def test_snapshot_special_characters(self):
        # Test snapshot creation with special characters in filenames
        special_filename = 'file with spaces_!@#$%^&()_-+=.txt'
        self._create_test_file(special_filename, 'Special content')
        
        snapshot = Snapshot(self.test_dir)
        snapshot_time = snapshot.take_snapshot()
        
        snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)
        
        self.assertIn(special_filename, snapshot_data['data'])

    def test_snapshot_symlinks(self):
        # Test snapshot creation with symbolic links
        self._create_test_file('original.txt', 'Original content')
        os.symlink(os.path.join(self.test_dir, 'original.txt'), os.path.join(self.test_dir, 'link.txt'))
        
        snapshot = Snapshot(self.test_dir)
        snapshot_time = snapshot.take_snapshot()
        
        snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)
        
        self.assertIn('original.txt', snapshot_data['data'])
        self.assertIn('link.txt', snapshot_data['data'])

    def test_snapshot_hidden_files(self):
        # Test snapshot creation with hidden files
        self._create_test_file('.hidden_file', 'Hidden content')
        
        snapshot = Snapshot(self.test_dir)
        snapshot_time = snapshot.take_snapshot()
        
        snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)
        
        self.assertIn('.hidden_file', snapshot_data['data'])

    def test_snapshot_diff(self):
        # Test diff creation between snapshots
        self._create_test_file('file1.txt', 'Initial content')
        snapshot = Snapshot(self.test_dir)
        snapshot_time1 = snapshot.take_snapshot()

        self._create_test_file('file1.txt', 'Modified content')
        self._create_test_file('file2.txt', 'New file')
        snapshot_time2 = snapshot.take_snapshot()

        # Get the actual diff stored for the second snapshot
        try:
            stored_diff = snapshot.get_stored_diff(snapshot_time2)
        except AttributeError:
            self.fail("get_stored_diff method not implemented in Snapshot class")
        
        # Verify the diff only contains the changed and new files
        self.assertEqual(len(stored_diff), 2, "Diff should contain exactly two files")
        self.assertIn('file1.txt', stored_diff, "Modified file should be in the diff")
        self.assertIn('file2.txt', stored_diff, "New file should be in the diff")
        
        # Verify the content of the diff
        self.assertEqual(stored_diff['file1.txt'], b'Modified content', "Content of modified file is incorrect")
        self.assertEqual(stored_diff['file2.txt'], b'New file', "Content of new file is incorrect")
        
        # Verify we can reconstruct the full state from the first snapshot and the diff
        full_state1 = snapshot.get_full_state(snapshot_time1)
        
        reconstructed_state2 = apply_diff(full_state1, stored_diff)
        
        actual_state2 = snapshot.get_full_state(snapshot_time2)
        
        self.assertEqual(reconstructed_state2, actual_state2, "Reconstructed state does not match actual state")

        # Add a check for circular reference warning
        with self.assertLogs(level='WARNING') as cm:
            snapshot.get_full_state(snapshot_time2)
        self.assertTrue(any("Circular reference detected in snapshot chain" in msg for msg in cm.output))

    def test_snapshot_custom_backup_dir(self):
        # Test snapshot creation with custom backup directory name
        custom_backup_dir = '.custom_backup'
        snapshot = Snapshot(self.test_dir, backup_dir=custom_backup_dir)
        self._create_test_file('file1.txt', 'Test content')
        snapshot_time = snapshot.take_snapshot()
        
        snapshot_path = os.path.join(self.test_dir, custom_backup_dir, f'snapshot_{snapshot_time}.json')
        self.assertTrue(os.path.exists(snapshot_path))

    def test_snapshot_relative_path(self):
        # Test snapshot creation with relative paths
        current_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        self._create_test_file('file1.txt', 'Test content')
        snapshot = Snapshot('.')
        snapshot_time = snapshot.take_snapshot()
        
        snapshot_path = os.path.join('.', '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        self.assertTrue(os.path.exists(snapshot_path))
        
        os.chdir(current_dir)

    def test_snapshot_non_existent_dir(self):
        # Test snapshot creation with non-existent target directory
        non_existent_dir = os.path.join(self.test_dir, 'non_existent')
        
        with self.assertRaises(FileNotFoundError):
            Snapshot(non_existent_dir)

    def test_circular_reference_detection(self):
        # Create a circular reference in snapshots
        snapshot = Snapshot(self.test_dir)
        
        time1 = self._create_and_snapshot(snapshot, 'file1.txt', 'Version 1')
        time2 = self._create_and_snapshot(snapshot, 'file1.txt', 'Version 2')
        time3 = self._create_and_snapshot(snapshot, 'file1.txt', 'Version 3')

        # Manually create a circular reference
        snapshot_path1 = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{time1}.json')
        snapshot_path3 = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{time3}.json')

        with open(snapshot_path1, 'r') as f:
            data1 = json.load(f)
        data1['prev_snapshot'] = time3
        with open(snapshot_path1, 'w') as f:
            json.dump(data1, f)

        # Attempt to get full state, which should log a warning
        with self.assertLogs(level='WARNING') as cm:
            snapshot.get_full_state(time3)

        # Check if the warning message about circular reference is in the log
        self.assertTrue(any("Circular reference detected in snapshot chain" in msg for msg in cm.output))

if __name__ == '__main__':
    unittest.main()