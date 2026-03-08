"""
Custom exception classes for Giti Tire AI Pattern Analysis System.

This module provides a comprehensive exception hierarchy for handling errors
across all components of the system.
"""


class GitiTireException(Exception):
    """Base exception class for all Giti Tire system errors."""

    def __init__(self, message: str, details: str = None):
        """
        Initialize the base exception.

        Args:
            message: Human-readable error message
            details: Additional technical details about the error
        """
        super().__init__(message)
        self.details = details
        self.message = message

    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ImageProcessingError(GitiTireException):
    """Exception raised for errors during image processing operations."""
    pass


class ImageLoadError(ImageProcessingError):
    """Exception raised when an image file cannot be loaded."""

    def __init__(self, file_path: str, reason: str = None):
        message = f"Failed to load image: {file_path}"
        super().__init__(message, reason)


class ImageSaveError(ImageProcessingError):
    """Exception raised when an image cannot be saved."""

    def __init__(self, file_path: str, reason: str = None):
        message = f"Failed to save image: {file_path}"
        super().__init__(message, reason)


class ImageDimensionError(ImageProcessingError):
    """Exception raised when image dimensions don't meet requirements."""

    def __init__(self, expected: tuple, actual: tuple, image_name: str = "image"):
        message = f"Invalid dimensions for {image_name}: expected {expected}, got {actual}"
        super().__init__(message)


class AnalysisError(GitiTireException):
    """Exception raised for errors during pattern analysis operations."""
    pass


class PatternDetectionError(AnalysisError):
    """Exception raised when pattern detection fails."""
    pass


class ContinuityAnalysisError(AnalysisError):
    """Exception raised during continuity analysis."""
    pass


class PostProcessingError(GitiTireException):
    """Exception raised for errors during post-processing operations."""
    pass


class StitchingError(PostProcessingError):
    """Exception raised during vertical stitching operations."""

    def __init__(self, reason: str = None):
        message = "Vertical stitching failed"
        super().__init__(message, reason)


class ValidationError(GitiTireException):
    """Exception raised when data validation fails."""

    def __init__(self, field: str, reason: str):
        message = f"Validation failed for field '{field}'"
        super().__init__(message, reason)


class ConfigurationError(GitiTireException):
    """Exception raised for configuration-related errors."""

    def __init__(self, config_file: str = None, reason: str = None):
        if config_file:
            message = f"Configuration error in {config_file}"
        else:
            message = "Configuration error"
        super().__init__(message, reason)


class IOError(GitiTireException):
    """Exception raised for file I/O operations."""

    def __init__(self, operation: str, file_path: str, reason: str = None):
        message = f"Failed to {operation} file: {file_path}"
        super().__init__(message, reason)