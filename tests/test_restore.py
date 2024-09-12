import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pyfilesnap.snapshot import Snapshot, CompressionTier
from pyfilesnap.restore import Restore
import time

class TestRestore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_and_snapshot(self, compression):
        snapshot = Snapshot(self.test_dir, compression=compression)
        with open(os.path.join(self.test_dir, 'test_file.txt'), 'w') as f:
            f.write('Original content')
        return snapshot.take_snapshot()

    def test_restore_last_with_compression(self):
        for compression in CompressionTier:
            with self.subTest(compression=compression):
                # Create a new temporary directory for each compression test
                test_dir = tempfile.mkdtemp()
                try:
                    # Create and take initial snapshot
                    snapshot = Snapshot(test_dir, compression=compression)
                    with open(os.path.join(test_dir, 'test_file.txt'), 'w') as f:
                        f.write('Original content')
                    snapshot_time = snapshot.take_snapshot()
                    
                    # Modify the file
                    with open(os.path.join(test_dir, 'test_file.txt'), 'w') as f:
                        f.write('Modified content')
                    
                    # Restore to last snapshot
                    restore = Restore(test_dir)
                    restored_time = restore.restore_last()
                    
                    # Check if file content is restored
                    with open(os.path.join(test_dir, 'test_file.txt'), 'r') as f:
                        self.assertEqual(f.read(), 'Original content')
                    
                    # Verify that the restored time matches the snapshot time
                    self.assertEqual(snapshot_time, restored_time)
                finally:
                    # Clean up the temporary directory
                    shutil.rmtree(test_dir)

    def test_restore_to_date_with_compression(self):
        start_time = time.time()
        timeout = 30  # Set a reasonable timeout in seconds

        for compression in CompressionTier:
            with self.subTest(compression=compression):
                # Create a new temporary directory for each compression test
                test_dir = tempfile.mkdtemp()
                try:
                    snapshot = Snapshot(test_dir, compression=compression)
                    
                    # Create and snapshot a file
                    with open(os.path.join(test_dir, 'test_file.txt'), 'w') as f:
                        f.write('Version 1')
                    snapshot_time_1 = snapshot.take_snapshot()
                    
                    # Modify and snapshot again
                    snapshot_time_2 = (datetime.strptime(snapshot_time_1, "%Y%m%d_%H%M%S") + timedelta(seconds=1)).strftime("%Y%m%d_%H%M%S")
                    with open(os.path.join(test_dir, 'test_file.txt'), 'w') as f:
                        f.write('Version 2')
                    snapshot.take_snapshot()
                    
                    # Modify file again
                    with open(os.path.join(test_dir, 'test_file.txt'), 'w') as f:
                        f.write('Version 3')
                    
                    restore = Restore(test_dir)
                    
                    try:
                        restore.restore_to_date(snapshot_time_2, direction='before')
                    except Exception as e:
                        self.fail(f"Test failed with exception: {str(e)}")
                    finally:
                        end_time = time.time()
                        self.assertLess(end_time - start_time, timeout, "Test exceeded timeout")
                    
                    # Test restore to after date
                    restore.restore_to_date(snapshot_time_1, direction='after')
                    with open(os.path.join(test_dir, 'test_file.txt'), 'r') as f:
                        self.assertEqual(f.read(), 'Version 2')
                finally:
                    # Clean up the temporary directory
                    shutil.rmtree(test_dir)

if __name__ == '__main__':
    unittest.main()