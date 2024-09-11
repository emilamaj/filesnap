import unittest
from pyfilesnap.diff import create_diff, apply_diff

class TestDiff(unittest.TestCase):
    def test_create_diff(self):
        old_data = {'file1': b'content1', 'file2': b'content2'}
        new_data = {'file1': b'content1', 'file2': b'modified', 'file3': b'new'}
        
        diff = create_diff(old_data, new_data)
        
        self.assertEqual(diff, {'file2': b'modified', 'file3': b'new'})

    def test_apply_diff(self):
        base_data = {'file1': b'content1', 'file2': b'content2'}
        diff_data = {'file2': b'modified', 'file3': b'new'}
        
        result = apply_diff(base_data, diff_data)
        
        expected = {'file1': b'content1', 'file2': b'modified', 'file3': b'new'}
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()