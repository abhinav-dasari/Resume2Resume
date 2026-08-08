"""
Utility helper functions for the AI Form Auto-Filler application.
Handles file validation, secure saving, and cleanup operations.
"""

import os
import time
import uuid
from werkzeug.utils import secure_filename


# Allowed file extensions (PDF only — resume uploads)
ALLOWED_EXTENSIONS = {'pdf'}

# Maximum file size in bytes (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.

    Args:
        filename (str): The original filename of the uploaded file.

    Returns:
        bool: True if the file extension is allowed, False otherwise.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_type(filename):
    """
    Determine the file type based on extension.

    Args:
        filename (str): The filename to check.

    Returns:
        str: 'pdf' for PDF files, 'image' for image files, or 'unknown'.
    """
    if not filename or '.' not in filename:
        return 'unknown'

    ext = filename.rsplit('.', 1)[1].lower()

    if ext == 'pdf':
        return 'pdf'
    elif ext in {'png', 'jpg', 'jpeg'}:
        return 'image'
    else:
        return 'unknown'


def secure_save(file, upload_folder):
    """
    Save an uploaded file securely with a unique filename.

    Args:
        file: The uploaded file object (from Flask request.files).
        upload_folder (str): The directory to save the file in.

    Returns:
        tuple: (saved_filepath, original_filename) or (None, None) if invalid.
    """
    if file is None or file.filename == '':
        return None, None

    if not allowed_file(file.filename):
        return None, None

    # Create upload folder if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)

    # Generate a unique filename to prevent collisions
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_folder, unique_filename)

    # Save the file
    file.save(filepath)

    # Validate file size after saving
    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        os.remove(filepath)
        return None, None

    return filepath, original_filename


def cleanup_old_files(folder, max_age_hours=1):
    """
    Delete files older than max_age_hours from the specified folder.
    This ensures user privacy by not retaining uploaded documents.

    Args:
        folder (str): The directory to clean up.
        max_age_hours (int): Maximum age of files in hours before deletion.
    """
    if not os.path.exists(folder):
        return

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                except OSError:
                    pass


def format_file_size(size_bytes):
    """
    Format file size in bytes to a human-readable string.

    Args:
        size_bytes (int): File size in bytes.

    Returns:
        str: Human-readable file size (e.g., '2.5 MB').
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
