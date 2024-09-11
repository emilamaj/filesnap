import os
import shutil
import tempfile
import unittest
from pyfilesnap.snapshot import Snapshot

class TestSnapshot(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.snapshot = Snapshot(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_take_snapshot(self):
        # Create a test file
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'w') as f:
            f.write('Test content')

        # Take a snapshot
        snapshot_time = self.snapshot.take_snapshot()

        # Check if snapshot file was created
        snapshot_file = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        self.assertTrue(os.path.exists(snapshot_file))

    def test_compressed_snapshot(self):
        compressed_snapshot = Snapshot(self.test_dir, compress=True)

        # Create a test file
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'w') as f:
            f.write('Test content')

        # Take a compressed snapshot
        snapshot_time = compressed_snapshot.take_snapshot()

        # Check if snapshot file was created
        snapshot_file = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
        self.assertTrue(os.path.exists(snapshot_file))

if __name__ == '__main__':
    unittest.main()