import zlib

def compress_data(data: bytes) -> bytes:
    """
    Compress the given data using zlib.

    Args:
        data (bytes): The data to compress.

    Returns:
        bytes: The compressed data.
    """
    return zlib.compress(data)

def decompress_data(compressed_data: bytes) -> bytes:
    """
    Decompress the given data using zlib.

    Args:
        compressed_data (bytes): The compressed data to decompress.

    Returns:
        bytes: The decompressed data.
    """
    return zlib.decompress(compressed_data)