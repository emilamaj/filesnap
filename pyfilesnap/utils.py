import os

def ensure_backup_dir(backup_dir: str) -> None:
    """
    Ensure that the backup directory exists.

    Args:
        backup_dir (str): The path to the backup directory.
    """
    os.makedirs(backup_dir, exist_ok=True)