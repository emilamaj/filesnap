import os
import shutil
import tempfile
import unittest
import time
from datetime import datetime
from pyfilesnap.snapshot import Snapshot
from pyfilesnap.restore import Restore

class TestRestore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.snapshot = Snapshot(self.test_dir)
        self.restore = Restore(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_restore_last(self):
        # Create and snapshot a file
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'w') as f:
            f.write('Original content')
        self.snapshot.take_snapshot()

        # Modify the file
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'w') as f:
            f.write('Modified content')

        # Restore to last snapshot
        self.restore.restore_last()

        # Check if file content is restored
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'r') as f:
            self.assertEqual(f.read(), 'Original content')

    def test_restore_to_date(self):
        # Create and snapshot a file
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'w') as f:
            f.write('Version 1')
        snapshot_time_1 = self.snapshot.take_snapshot()

        # Wait a bit to ensure different timestamps
        time.sleep(1)

        # Modify and snapshot again
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'w') as f:
            f.write('Version 2')
        snapshot_time_2 = self.snapshot.take_snapshot()

        # Wait a bit more
        time.sleep(1)

        # Modify file again
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'w') as f:
            f.write('Version 3')

        # Test restore to closest date
        middle_time = datetime.strptime(snapshot_time_1, "%Y%m%d_%H%M%S") + (datetime.strptime(snapshot_time_2, "%Y%m%d_%H%M%S") - datetime.strptime(snapshot_time_1, "%Y%m%d_%H%M%S")) / 2
        middle_time_str = middle_time.strftime("%Y%m%d_%H%M%S")
        self.restore.restore_to_date(middle_time_str, direction='closest')

        # Check if file content is restored
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'r') as f:
            self.assertEqual(f.read(), 'Version 1')

        # Test restore to before date
        self.restore.restore_to_date(snapshot_time_2, direction='before')
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'r') as f:
            self.assertEqual(f.read(), 'Version 1')

        # Test restore to after date
        self.restore.restore_to_date(snapshot_time_1, direction='after')
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'r') as f:
            self.assertEqual(f.read(), 'Version 2')

if __name__ == '__main__':
    unittest.main()