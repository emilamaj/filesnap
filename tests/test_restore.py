import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pyfilesnap.snapshot import Snapshot, SnapshotConfig
from pyfilesnap.restore import Restore
import time

class TestRestore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = '.pyfilesnap'

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_file(self, filename, content):
        with open(os.path.join(self.test_dir, filename), 'w') as f:
            f.write(content)

    def _create_snapshot(self, compress=False):
        config = SnapshotConfig(compress=compress)
        snapshot = Snapshot(self.test_dir, config=config)
        return snapshot.take_snapshot()

    def test_restore_to_date_exact(self):
        self._create_file('file1.txt', 'Initial content')
        time1 = self._create_snapshot()

        self._create_file('file1.txt', 'Modified content')
        time2 = self._create_snapshot()

        restore = Restore(self.test_dir)
        restore.restore_to_date(time1)

        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Initial content')

    def test_restore_to_date_before(self):
        self._create_file('file1.txt', 'Initial content')
        time1 = self._create_snapshot()

        self._create_file('file1.txt', 'Modified content')
        time2 = self._create_snapshot()

        restore_time = (datetime.strptime(time2, "%Y%m%d_%H%M%S") - timedelta(seconds=1)).strftime("%Y%m%d_%H%M%S")
        restore = Restore(self.test_dir)
        restore.restore_to_date(restore_time, direction='before')

        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Initial content')

    def test_restore_to_date_after(self):
        self._create_file('file1.txt', 'Initial content')
        time1 = self._create_snapshot()

        self._create_file('file1.txt', 'Modified content')
        time2 = self._create_snapshot()

        restore_time = (datetime.strptime(time1, "%Y%m%d_%H%M%S") + timedelta(seconds=1)).strftime("%Y%m%d_%H%M%S")
        restore = Restore(self.test_dir)
        restore.restore_to_date(restore_time, direction='after')

        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Modified content')

    def test_restore_to_date_exact_compressed(self):
        self._create_file('file1.txt', 'Initial content')
        time1 = self._create_snapshot(compress=True)

        self._create_file('file1.txt', 'Modified content')
        time2 = self._create_snapshot(compress=True)

        restore = Restore(self.test_dir)
        restore.restore_to_date(time1)

        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Initial content')

    def test_restore_to_date_before_compressed(self):
        self._create_file('file1.txt', 'Initial content')
        time1 = self._create_snapshot(compress=True)

        self._create_file('file1.txt', 'Modified content')
        time2 = self._create_snapshot(compress=True)

        restore_time = (datetime.strptime(time2, "%Y%m%d_%H%M%S") - timedelta(seconds=1)).strftime("%Y%m%d_%H%M%S")
        restore = Restore(self.test_dir)
        restore.restore_to_date(restore_time, direction='before')

        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Initial content')

    def test_restore_to_date_after_compressed(self):
        self._create_file('file1.txt', 'Initial content')
        time1 = self._create_snapshot(compress=True)

        self._create_file('file1.txt', 'Modified content')
        time2 = self._create_snapshot(compress=True)

        restore_time = (datetime.strptime(time1, "%Y%m%d_%H%M%S") + timedelta(seconds=1)).strftime("%Y%m%d_%H%M%S")
        restore = Restore(self.test_dir)
        restore.restore_to_date(restore_time, direction='after')

        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Modified content')

    def test_restore_last(self):
        self._create_file('file1.txt', 'Initial content')
        self._create_snapshot()

        self._create_file('file1.txt', 'Modified content')
        self._create_snapshot()

        restore = Restore(self.test_dir)
        restore.restore_last()

        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Modified content')

    def test_restore_last_compressed(self):
        self._create_file('file1.txt', 'Initial content')
        self._create_snapshot(compress=True)

        self._create_file('file1.txt', 'Modified content')
        self._create_snapshot(compress=True)

        restore = Restore(self.test_dir)
        restore.restore_last()

        with open(os.path.join(self.test_dir, 'file1.txt'), 'r') as f:
            content = f.read()
        self.assertEqual(content, 'Modified content')

if __name__ == '__main__':
    unittest.main()