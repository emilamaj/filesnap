import os
import shutil
import tempfile
import unittest
import json
import base64
from pyfilesnap.snapshot import Snapshot, CompressionTier
from pyfilesnap.utils import decompress_data

class TestSnapshot(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_test_file(self, content='Test content'):
        with open(os.path.join(self.test_dir, 'file1.txt'), 'w') as f:
            f.write(content)

    def test_snapshot_creation(self):
        for compression in CompressionTier:
            with self.subTest(compression=compression):
                self._create_test_file()
                snapshot = Snapshot(self.test_dir, compression=compression)
                snapshot_time = snapshot.take_snapshot()

                # Check if snapshot file exists
                snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')
                self.assertTrue(os.path.exists(snapshot_path))

                # Load and verify snapshot content
                with open(snapshot_path, 'r') as f:
                    snapshot_data = json.load(f)

                self.assertEqual(snapshot_data['compression'], compression.value)
                self.assertIn('data', snapshot_data)

                if compression == CompressionTier.MAXIMAL:
                    decompressed = decompress_data(base64.b64decode(snapshot_data['data']))
                    file_data = json.loads(decompressed.decode())
                    file_data = {k: base64.b64decode(v).decode() for k, v in file_data.items()}
                elif compression == CompressionTier.MINIMAL:
                    file_data = {k: decompress_data(base64.b64decode(v)).decode() for k, v in snapshot_data['data'].items()}
                else:
                    file_data = {k: base64.b64decode(v).decode() for k, v in snapshot_data['data'].items()}

                self.assertIn('file1.txt', file_data)
                self.assertEqual(file_data['file1.txt'], 'Test content')

    def test_multiple_snapshots(self):
        snapshot = Snapshot(self.test_dir)
        
        # First snapshot
        self._create_test_file('Initial content')
        snapshot_time1 = snapshot.take_snapshot()
        
        # Second snapshot
        self._create_test_file('Modified content')
        snapshot_time2 = snapshot.take_snapshot()
        
        # Verify both snapshots exist
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time1}.json')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time2}.json')))
        
        # Verify content of second snapshot
        snapshot_path = os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time2}.json')
        with open(snapshot_path, 'r') as f:
            snapshot_data = json.load(f)
        
        file_data = {k: base64.b64decode(v) for k, v in snapshot_data['data'].items()}
        self.assertEqual(file_data['file1.txt'], b'Modified content')

if __name__ == '__main__':
    unittest.main()