import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pyfilesnap.snapshot import Snapshot
from pyfilesnap.restore import Restore
import time

class TestRestore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, filename, content):
        with open(os.path.join(self.test_dir, filename), 'w') as f:
            f.write(content)

    def _create_and_snapshot(self, snapshot, filename, content):
        self._create_file(filename, content)
        return snapshot.take_snapshot()

    def test_restore_initialization(self):
        restore = Restore(self.test_dir)
        self.assertEqual(restore.target_dir, os.path.abspath(self.test_dir))
        self.assertEqual(restore.backup_dir, os.path.join(self.test_dir, '.pyfilesnap'))

    def test_restore_last_uncompressed(self):
        snapshot = Snapshot(self.test_dir)
        self._create_and_snapshot(snapshot, 'test_file.txt', 'Original content')
        self._create_file('test_file.txt', 'Modified content')
        
        restore = Restore(self.test_dir)
        restored_time = restore.restore_last()
        
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'r') as f:
            self.assertEqual(f.read(), 'Original content')

    def test_restore_last_compressed(self):
        snapshot = Snapshot(self.test_dir, compress=True)
        self._create_and_snapshot(snapshot, 'test_file.txt', 'Original content')
        self._create_file('test_file.txt', 'Modified content')
        
        restore = Restore(self.test_dir)
        restored_time = restore.restore_last()
        
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'r') as f:
            self.assertEqual(f.read(), 'Original content')

    def test_restore_to_date_before_uncompressed(self):
        snapshot = Snapshot(self.test_dir)
        time1 = self._create_and_snapshot(snapshot, 'test_file.txt', 'Version 1')
        time.sleep(1)
        time2 = self._create_and_snapshot(snapshot, 'test_file.txt', 'Version 2')
        self._create_file('test_file.txt', 'Version 3')
        
        restore = Restore(self.test_dir)
        restore.restore_to_date(time2, direction='before')
        
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'r') as f:
            self.assertEqual(f.read(), 'Version 1')

    def test_restore_to_date_after_uncompressed(self):
        snapshot = Snapshot(self.test_dir)
        restore = Restore(self.test_dir)

        # Create initial snapshot
        self._create_file('file1.txt', 'Initial content')
        time1 = snapshot.take_snapshot()

        # Create second snapshot
        self._create_file('file1.txt', 'Updated content')
        time2 = snapshot.take_snapshot()

        # Restore to a date after the first snapshot
        restore_time = datetime.strptime(time1, "%Y%m%d_%H%M%S") + timedelta(seconds=1)
        restore.restore_to_date(restore_time.strftime("%Y%m%d_%H%M%S"), direction='after')

        # Check if the file content matches the second snapshot
        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Updated content')

    def test_restore_to_date_before_compressed(self):
        snapshot = Snapshot(self.test_dir, compress=True)
        time1 = self._create_and_snapshot(snapshot, 'test_file.txt', 'Version 1')
        time.sleep(1)
        time2 = self._create_and_snapshot(snapshot, 'test_file.txt', 'Version 2')
        self._create_file('test_file.txt', 'Version 3')
        
        restore = Restore(self.test_dir)
        restore.restore_to_date(time2, direction='before')
        
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'r') as f:
            self.assertEqual(f.read(), 'Version 1')

    def test_restore_to_date_after_compressed(self):
        snapshot = Snapshot(self.test_dir, compress=True)
        restore = Restore(self.test_dir)

        # Create initial snapshot
        self._create_file('file1.txt', 'Version 1')
        time1 = snapshot.take_snapshot()

        # Create second snapshot
        self._create_file('file1.txt', 'Version 2')
        time2 = snapshot.take_snapshot()

        # Create third snapshot
        self._create_file('file1.txt', 'Version 3')
        time3 = snapshot.take_snapshot()

        # Restore to a date after the second snapshot
        restore_time = datetime.strptime(time2, "%Y%m%d_%H%M%S") + timedelta(seconds=1)
        restore.restore_to_date(restore_time.strftime("%Y%m%d_%H%M%S"), direction='after')

        # Check if the file content matches the third snapshot
        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Version 3')

if __name__ == '__main__':
    unittest.main()