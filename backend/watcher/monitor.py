"""Filesystem watcher for monitoring Downloads folder."""

import asyncio
import logging
from pathlib import Path
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from backend.config import settings

logger = logging.getLogger(__name__)


class FileEventHandler(FileSystemEventHandler):
    """Handles filesystem events from watchdog."""
    
    def __init__(self, callback: Callable, debounce_seconds: float = 2.0):
        """
        Initialize event handler.
        
        Args:
            callback: Async function to call when file event occurs
            debounce_seconds: Seconds to debounce rapid events
        """
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.pending_files = {}  # {file_path: timestamp}
        self.debounce_task = None
    
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        logger.debug(f"File created: {file_path}")
        self._schedule_callback(file_path)
    
    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification event."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        logger.debug(f"File modified: {file_path}")
        self._schedule_callback(file_path)
    
    def _schedule_callback(self, file_path: str):
        """Schedule callback with debouncing."""
        import time
        
        self.pending_files[file_path] = time.time()
        
        # Debounce: wait N seconds before processing
        # If file is modified again, reset the timer
        logger.debug(f"Debouncing {file_path} for {self.debounce_seconds}s")
    
    async def process_pending_files(self):
        """Process debounced files after debounce timeout."""
        import time
        
        while True:
            await asyncio.sleep(self.debounce_seconds + 0.5)
            
            current_time = time.time()
            files_to_process = []
            
            for file_path, timestamp in list(self.pending_files.items()):
                if current_time - timestamp >= self.debounce_seconds:
                    files_to_process.append(file_path)
                    del self.pending_files[file_path]
            
            for file_path in files_to_process:
                try:
                    logger.info(f"Processing file: {file_path}")
                    await self.callback(file_path)
                except Exception as e:
                    logger.error(f"Callback failed for {file_path}: {e}")


class DownloadMonitor:
    """Watches Downloads folder for new files."""
    
    def __init__(
        self,
        watch_path: Optional[str] = None,
        debounce_seconds: float = 2.0,
    ):
        """
        Initialize monitor.
        
        Args:
            watch_path: Path to monitor (default: ~/Downloads)
            debounce_seconds: Debounce timeout
        """
        if watch_path is None:
            watch_path = str(Path.home() / "Downloads")
        
        self.watch_path = Path(watch_path)
        self.debounce_seconds = debounce_seconds
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[FileEventHandler] = None
        self.is_running = False
    
    async def start(self, callback: Callable) -> bool:
        """
        Start monitoring folder.
        
        Args:
            callback: Async function to call for each new file
            
        Returns:
            True if monitor started successfully
        """
        try:
            if not self.watch_path.exists():
                logger.error(f"Watch path doesn't exist: {self.watch_path}")
                return False
            
            if not self.watch_path.is_dir():
                logger.error(f"Watch path is not a directory: {self.watch_path}")
                return False
            
            # Create event handler
            self.event_handler = FileEventHandler(callback, self.debounce_seconds)
            
            # Start watchdog observer
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler,
                str(self.watch_path),
                recursive=False,  # Don't monitor subdirectories
            )
            self.observer.start()
            self.is_running = True
            
            # Start debounce processor in background
            asyncio.create_task(self.event_handler.process_pending_files())
            
            logger.info(f"Started monitoring: {self.watch_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitor: {e}")
            return False
    
    async def stop(self):
        """Stop monitoring folder."""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.is_running = False
            logger.info("Stopped monitoring")
        except Exception as e:
            logger.error(f"Error stopping monitor: {e}")
    
    def get_status(self) -> dict:
        """
        Get monitor status.
        
        Returns:
            Dict with status info
        """
        return {
            "is_running": self.is_running,
            "watch_path": str(self.watch_path),
            "watch_path_exists": self.watch_path.exists(),
            "debounce_seconds": self.debounce_seconds,
        }


async def get_monitor() -> DownloadMonitor:
    """
    Get global monitor instance.
    
    Used as FastAPI dependency.
    """
    # This would be called from app lifespan
    pass
