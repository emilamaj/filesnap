# PyFileSnap

PyFileSnap is a lightweight Python library that allows users to take snapshots of a targeted directory and its contents. It provides an easy way to revert or rollback any changes made within the directory.

## Features

- Take snapshots of a directory
- Restore to the previous snapshot
- Restore to the closest snapshot before/after a specified date
- Optimized storage using diff-based snapshots
- Optional light compression for snapshot data

## Installation

To install PyFileSnap, use pip:

    pip install pyfilesnap

## Usage

### Taking a Snapshot

    from pyfilesnap import Snapshot

    # Initialize a Snapshot object
    snapshot = Snapshot('/path/to/target/directory')

    # Take a snapshot
    snapshot_time = snapshot.take_snapshot()
    print(f"Snapshot taken at: {snapshot_time}")

### Restoring from a Snapshot

    from pyfilesnap import Restore

    # Initialize a Restore object
    restore = Restore('/path/to/target/directory')

    # Restore to the last snapshot
    restore.restore_last()

    # Restore to a specific date (closest snapshot)
    restore.restore_to_date('20230515_120000')

    # Restore to the closest snapshot before a specific date
    restore.restore_to_date('20230515_120000', direction='before')

    # Restore to the closest snapshot after a specific date
    restore.restore_to_date('20230515_120000', direction='after')

### Using Compression

To enable compression for snapshots:

    snapshot = Snapshot('/path/to/target/directory', compress=True)
    snapshot.take_snapshot()

## Notes

- Snapshot data is stored in a `.pyfilesnap` directory within the target directory.
- The library uses an optimized diff-based approach to minimize storage usage.
- Compression is optional and can be enabled to further reduce storage requirements.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
