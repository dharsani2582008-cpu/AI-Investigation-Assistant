"""
Small shared helper functions.
"""

import os
from utils.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES


def get_extension(filename: str) -> str:
    """Return the lowercase file extension including the leading dot."""
    return os.path.splitext(filename)[1].lower()


def validate_uploaded_file(uploaded_file) -> tuple[bool, str]:
    """
    Validate a Streamlit UploadedFile object.

    Returns (is_valid, message). This only checks extension and size
    (fast, cheap checks) so obviously-bad files are rejected before we
    even attempt to parse their content in services/file_loader.py.
    """
    if uploaded_file is None:
        return False, "No file provided."

    ext = get_extension(uploaded_file.name)
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"Unsupported file type '{ext}'. Allowed types: {allowed}"

    size = getattr(uploaded_file, "size", None)
    if size is not None and size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        return False, f"File is too large. Maximum allowed size is {max_mb} MB."

    if size == 0:
        return False, "The uploaded file is empty."

    return True, "File looks valid."


def human_readable_size(num_bytes: int) -> str:
    """Convert a byte count into a human-readable string (e.g. '1.4 MB')."""
    if num_bytes is None:
        return "Unknown size"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def build_stored_filename(evidence_id: str, original_filename: str) -> str:
    """
    Prefix the original filename with its evidence_id so two uploads
    with the same name never overwrite each other in data/uploads/,
    while keeping the filename human-readable.
    """
    return f"{evidence_id}__{original_filename}"
