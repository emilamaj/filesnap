from typing import Dict, Optional

def create_diff(old_data: Dict[str, bytes], new_data: Dict[str, bytes]) -> Dict[str, Optional[bytes]]:
    """
    Create a diff between two sets of file data.

    Args:
        old_data (Dict[str, bytes]): The old file data.
        new_data (Dict[str, bytes]): The new file data.

    Returns:
        Dict[str, Optional[bytes]]: The diff between old and new data.
        None values indicate file deletions.
    """
    diff = {}
    # Find modified or new files
    for file_path, new_content in new_data.items():
        if file_path not in old_data or old_data[file_path] != new_content:
            diff[file_path] = new_content
    
    # Find deleted files
    for file_path in old_data:
        if file_path not in new_data:
            diff[file_path] = None
    
    return diff

def apply_diff(base_data: Dict[str, bytes], diff_data: Dict[str, Optional[bytes]]) -> Dict[str, bytes]:
    """
    Apply a diff to base data.

    Args:
        base_data (Dict[str, bytes]): The base file data.
        diff_data (Dict[str, Optional[bytes]]): The diff to apply.

    Returns:
        Dict[str, bytes]: The result of applying the diff to the base data.
    """
    result = base_data.copy()
    for file_path, content in diff_data.items():
        if content is None:
            result.pop(file_path, None)  # Remove the file if it exists
        else:
            result[file_path] = content
    return result