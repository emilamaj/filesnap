from typing import Dict

def create_diff(old_data: Dict[str, bytes], new_data: Dict[str, bytes]) -> Dict[str, bytes]:
    """
    Create a diff between two sets of file data.

    Args:
        old_data (Dict[str, bytes]): The old file data.
        new_data (Dict[str, bytes]): The new file data.

    Returns:
        Dict[str, bytes]: The diff between old and new data.
    """
    diff = {}
    for file_path, new_content in new_data.items():
        if file_path not in old_data or old_data[file_path] != new_content:
            diff[file_path] = new_content
    return diff

def apply_diff(base_data: Dict[str, bytes], diff_data: Dict[str, bytes]) -> Dict[str, bytes]:
    """
    Apply a diff to base data.

    Args:
        base_data (Dict[str, bytes]): The base file data.
        diff_data (Dict[str, bytes]): The diff to apply.

    Returns:
        Dict[str, bytes]: The result of applying the diff to the base data.
    """
    result = base_data.copy()
    result.update(diff_data)
    return result