"""
Utility functions for patient profile management.
"""

from PIL import Image
from django.core.exceptions import ValidationError


def validate_image_file(file):
    """
    Validate that the uploaded file is a valid image.
    
    Accepts: JPEG, PNG, GIF, WebP
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: If file is not a valid image or unsupported format
        
    Requirements: 3.3, 3.4
    """
    try:
        # Open the image to verify it's valid
        img = Image.open(file)
        img.verify()
        
        # Check format
        allowed_formats = ['JPEG', 'PNG', 'GIF', 'WEBP']
        if img.format not in allowed_formats:
            raise ValidationError(
                f"Invalid file type. Only image files are allowed (JPEG, PNG, GIF, WebP). Got: {img.format}"
            )
        
        # Reset file pointer after verify()
        file.seek(0)
        
        return True
        
    except (IOError, SyntaxError) as e:
        raise ValidationError("Invalid image file. File may be corrupted or not an image.")


def validate_file_size(file, max_size_mb=5):
    """
    Validate that the uploaded file does not exceed the size limit.
    
    Args:
        file: UploadedFile object
        max_size_mb: Maximum file size in megabytes (default: 5MB)
        
    Raises:
        ValidationError: If file exceeds size limit
        
    Requirements: 3.5
    """
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    
    if file.size > max_size_bytes:
        raise ValidationError(
            f"File size exceeds {max_size_mb}MB limit. File size: {file.size / (1024 * 1024):.2f}MB"
        )
    
    return True


def validate_profile_photo(file):
    """
    Validate profile photo upload.
    
    Combines image format and size validation.
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: If validation fails
        
    Returns:
        True if validation passes
    """
    validate_file_size(file, max_size_mb=5)
    validate_image_file(file)
    return True
