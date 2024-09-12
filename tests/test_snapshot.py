import os
import shutil
import tempfile
import unittest
from pyfilesnap.snapshot import Snapshot, CompressionTier
import base64
from pyfilesnap.compression import compress_data

class TestSnapshot(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_test_files(self):
        with open(os.path.join(self.test_dir, 'file1.txt'), 'w') as f:
            f.write('Content of file 1')
        with open(os.path.join(self.test_dir, 'file2.txt'), 'w') as f:
            f.write('Content of file 2')

    def test_snapshot_no_compression(self):
        self._create_test_files()
        snapshot = Snapshot(self.test_dir, compression=CompressionTier.NONE)
        snapshot_time = snapshot.take_snapshot()
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')))

    def test_snapshot_minimal_compression(self):
        self._create_test_files()
        snapshot = Snapshot(self.test_dir, compression=CompressionTier.MINIMAL)
        snapshot_time = snapshot.take_snapshot()
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')))

    def test_snapshot_maximal_compression(self):
        self._create_test_files()
        snapshot = Snapshot(self.test_dir, compression=CompressionTier.MAXIMAL)
        snapshot_time = snapshot.take_snapshot()
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time}.json')))

    def test_multiple_snapshots_with_compression(self):
        self._create_test_files()
        snapshot = Snapshot(self.test_dir, compression=CompressionTier.MINIMAL)
        
        # Take first snapshot
        snapshot_time1 = snapshot.take_snapshot()
        
        # Modify a file
        with open(os.path.join(self.test_dir, 'file1.txt'), 'w') as f:
            f.write('Modified content of file 1')
        
        # Take second snapshot
        snapshot_time2 = snapshot.take_snapshot()
        
        # Check if both snapshots exist
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time1}.json')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, '.pyfilesnap', f'snapshot_{snapshot_time2}.json')))

    def test_load_snapshot_data(self):
        for compression in CompressionTier:
            with self.subTest(compression=compression):
                snapshot = Snapshot(self.test_dir, compression=compression)
                
                # Create a test file
                with open(os.path.join(self.test_dir, 'file1.txt'), 'w') as f:
                    f.write('Test content')
                
                # Take a snapshot
                snapshot_time = snapshot.take_snapshot()
                
                # Load the snapshot data
                snapshot_file = os.path.join(self.test_dir, '.snapshots', f'{snapshot_time}.json')
                loaded_data = snapshot._load_snapshot_data(snapshot_file)
                
                # Check if the file is in the loaded data
                self.assertIn('file1.txt', loaded_data['data'])
                
                # Check if the content is correct
                if compression == CompressionTier.NONE:
                    self.assertEqual(loaded_data['data']['file1.txt'], 'Test content')
                else:
                    compressed_content = base64.b64encode(compress_data('Test content'.encode())).decode()
                    self.assertEqual(loaded_data['data']['file1.txt'], compressed_content)

if __name__ == '__main__':
    unittest.main()