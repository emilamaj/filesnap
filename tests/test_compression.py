import unittest
from pyfilesnap.compression import compress_data, decompress_data

class TestCompression(unittest.TestCase):
    def test_compression_decompression(self):
        original_data = b'This is some test data for compression. ' * 10  # Make the test string longer
        
        compressed = compress_data(original_data)
        decompressed = decompress_data(compressed)
        
        self.assertEqual(original_data, decompressed)
        self.assertLess(len(compressed), len(original_data))

if __name__ == '__main__':
    unittest.main()