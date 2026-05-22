"""File organizer and mover logic."""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

from backend.config import settings
from backend.database.models import FileRecord, FileStatus

logger = logging.getLogger(__name__)


class FileOrganizer:
    """Organizes files into course folders."""
    
    # Allowed organization styles
    STYLE_WEEK = "week"  # Week_1, Week_2, etc.
    STYLE_TYPE = "type"  # Lectures, Assignments, etc.
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize organizer.
        
        Args:
            base_path: Base path for organized files (default: ~/AcadSort)
        """
        if base_path is None:
            base_path = str(Path.home() / "AcadSort")
        
        self.base_path = Path(base_path)
        self._ensure_base_exists()
    
    def _ensure_base_exists(self):
        """Create base directory if it doesn't exist."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Base organization path: {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to create base path: {e}")
    
    def get_destination(
        self,
        course_code: str,
        material_type: str,
        week_number: Optional[int] = None,
        organization_style: Optional[str] = None,
    ) -> Path:
        """
        Get destination path for a file.
        
        Args:
            course_code: Course code (e.g., "CMSC 11")
            material_type: Material type (LECTURE, ASSIGNMENT, EXAM, etc.)
            week_number: Week number (1-16)
            organization_style: "week" or "type"
            
        Returns:
            Destination Path
        """
        if organization_style is None:
            organization_style = settings.organization_style
        
        # Build course folder: "CMSC 11 - Introduction to CS"
        course_folder = course_code  # In real app, would include course name
        course_path = self.base_path / course_folder
        
        if organization_style == self.STYLE_WEEK:
            if week_number is None:
                week_number = 1
            
            week_folder = f"Week_{week_number:02d}"
            destination = course_path / week_folder
        
        else:  # STYLE_TYPE
            type_folder = material_type  # LECTURE, ASSIGNMENT, etc.
            destination = course_path / type_folder
        
        return destination
    
    async def move_file(
        self,
        source: Path,
        destination: Path,
        create_backup: bool = True,
    ) -> bool:
        """
        Move file to destination with error handling.
        
        Args:
            source: Source file path
            destination: Destination directory
            create_backup: Whether to backup source
            
        Returns:
            True if move successful
        """
        try:
            # Validate source
            if not source.exists():
                logger.error(f"Source file doesn't exist: {source}")
                return False
            
            if not source.is_file():
                logger.error(f"Source is not a file: {source}")
                return False
            
            # Security: prevent path traversal
            if ".." in str(destination):
                logger.error(f"Path traversal detected: {destination}")
                return False
            
            # Create destination directory
            destination.mkdir(parents=True, exist_ok=True)
            
            # Handle filename collision
            dest_file = destination / source.name
            counter = 1
            
            while dest_file.exists():
                stem = source.stem
                suffix = source.suffix
                dest_file = destination / f"{stem} ({counter}){suffix}"
                counter += 1
            
            logger.info(f"Moving {source.name} → {dest_file}")
            
            # Create backup if requested
            if create_backup:
                backup_dir = self.base_path / ".backups"
                backup_dir.mkdir(exist_ok=True)
                backup_file = backup_dir / f"{source.name}.backup"
                shutil.copy2(source, backup_file)
                logger.debug(f"Backup created: {backup_file}")
            
            # Move file
            shutil.move(str(source), str(dest_file))
            logger.info(f"File moved successfully: {dest_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return False
    
    async def undo_move(
        self,
        file_path: Path,
        original_path: Path,
        grace_period_seconds: float = 30.0,
    ) -> bool:
        """
        Undo a file move if within grace period.
        
        Args:
            file_path: Current file path
            original_path: Original path before move
            grace_period_seconds: Time window to undo
            
        Returns:
            True if undo successful
        """
        try:
            # Check if within grace period (handled by caller)
            if not file_path.exists():
                logger.error(f"File doesn't exist: {file_path}")
                return False
            
            # Restore original location
            original_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle collision at original location
            dest = original_path
            counter = 1
            
            while dest.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                dest = original_path.parent / f"{stem} ({counter}){suffix}"
                counter += 1
            
            logger.info(f"Undoing move: {file_path} → {dest}")
            shutil.move(str(file_path), str(dest))
            
            # Clean up empty directories
            try:
                file_path.parent.rmdir()
            except OSError:
                pass  # Directory not empty, that's fine
            
            logger.info(f"Move undone successfully: {dest}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to undo move: {e}")
            return False
    
    async def organize_file(
        self,
        source: Path,
        course_code: str,
        material_type: str,
        week_number: Optional[int] = None,
        organization_style: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Organize a file: determine destination and move it.
        
        Args:
            source: Source file path
            course_code: Target course
            material_type: Material type
            week_number: Week number
            organization_style: Organization style
            
        Returns:
            Destination path if successful, None otherwise
        """
        try:
            # Get destination
            destination = self.get_destination(
                course_code,
                material_type,
                week_number,
                organization_style,
            )
            
            # Move file
            success = await self.move_file(source, destination)
            
            if success:
                return destination / source.name
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to organize file: {e}")
            return None
    
    def validate_path(self, path: Path) -> bool:
        """
        Validate path for security.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is safe
        """
        try:
            # Resolve to absolute path
            resolved = path.resolve()
            
            # Check if it's under base path
            if not str(resolved).startswith(str(self.base_path.resolve())):
                logger.warning(f"Path outside base: {path}")
                return False
            
            # Check for traversal attempts
            if ".." in path.parts:
                logger.warning(f"Path traversal detected: {path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False


# Global singleton
_organizer: Optional[FileOrganizer] = None


def get_organizer(base_path: Optional[str] = None) -> FileOrganizer:
    """
    Get global organizer instance.
    
    Args:
        base_path: Base path (only used on first call)
        
    Returns:
        FileOrganizer singleton
    """
    global _organizer
    if _organizer is None:
        _organizer = FileOrganizer(base_path)
    return _organizer
