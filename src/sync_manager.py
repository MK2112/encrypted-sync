import os
import time
import logging
import threading
import shutil
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class OneDriveChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        """Initialize OneDrive change handler with callback function."""
        self.callback = callback
        self.last_modified = {}
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        # Get absolute path
        path = Path(event.src_path).resolve()
        
        # Check if this is a duplicate event
        current_time = time.time()
        if path in self.last_modified:
            # Ignore events that happen within 1 second of the last event for this file
            if current_time - self.last_modified[path] < 1:
                return
                
        self.last_modified[path] = current_time
        
        # Call the callback with the modified file path
        self.callback(path)
        
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        # Get absolute path
        path = Path(event.src_path).resolve()
        
        # Call the callback with the created file path
        self.callback(path)

class SyncManager:
    def __init__(self, config, onedrive_client, pgp_handler):
        """
        Initialize sync manager.
        
        Args:
            config: Application configuration
            onedrive_client: OneDrive client instance
            pgp_handler: PGP handler instance
        """
        self.config = config
        self.onedrive_client = onedrive_client
        self.pgp_handler = pgp_handler
        
        self.local_path = Path(config['local']['monitored_path']).resolve()
        self.decrypted_path = Path(config['local']['decrypted_path']).resolve()
        self.encrypted_path = config['onedrive']['encrypted_folder']
        self.onedrive_encrypted_path = os.path.join(
            self.onedrive_client.onedrive_path, 
            self.encrypted_path
        )
        
        # Create directories if they don't exist
        os.makedirs(self.local_path, exist_ok=True)
        os.makedirs(self.decrypted_path, exist_ok=True)
        
        # Ensure OneDrive encrypted folder exists
        self.onedrive_client.ensure_folder_exists(self.encrypted_path)
        
        # File metadata cache
        self.local_files = {}  # path -> last_modified_time
        self.remote_files = {}  # path -> {id, last_modified_time}
        
        # Sync lock to prevent concurrent sync operations
        self.sync_lock = threading.Lock()
        
        # Set up OneDrive folder observer
        self.onedrive_observer = None
        
    def handle_local_change(self, file_path):
        """
        Handle a local file change.
        
        Args:
            file_path: Path to the changed file
        """
        with self.sync_lock:
            try:
                # Skip temporary files and hidden files
                if file_path.name.startswith('.') or file_path.name.endswith('.tmp'):
                    return
                    
                # Skip already encrypted files
                if file_path.name.endswith('.gpg'):
                    return
                    
                # Get relative path from monitored directory
                rel_path = file_path.relative_to(self.local_path)
                
                logging.info(f"Local file changed: {rel_path}")
                
                # Check if there's a newer version in OneDrive
                remote_path = f"{self.encrypted_path}/{rel_path}.gpg"
                remote_file = None
                
                # Find the file in the remote files list
                for file in self.onedrive_client.list_files(self.onedrive_encrypted_path):
                    if file.get('name') == f"{rel_path}.gpg":
                        remote_file = file
                        break
                
                # If remote file exists and is newer, create a conflict file
                if remote_file and remote_file.get('lastModifiedDateTime', 0) > file_path.stat().st_mtime:
                    conflict_path = f"{file_path}.conflict"
                    shutil.copy2(file_path, conflict_path)
                    logging.warning(f"Conflict detected for {rel_path}. Local copy saved as {conflict_path}")
                
                # Encrypt the file
                temp_encrypted = self.pgp_handler.encrypt_file(file_path)
                
                # Upload to OneDrive
                onedrive_path = os.path.join(self.onedrive_encrypted_path, f"{rel_path}.gpg")
                self.onedrive_client.upload_file(temp_encrypted, onedrive_path)
                
                # Update local file cache
                self.local_files[str(rel_path)] = file_path.stat().st_mtime
                
                # Clean up temporary encrypted file if it's different from the original
                if temp_encrypted != str(file_path) + '.gpg':
                    os.unlink(temp_encrypted)
                    
            except Exception as e:
                logging.error(f"Error handling local change for {file_path}: {str(e)}")
    
    def handle_onedrive_change(self, file_path):
        """
        Handle a change to a file in the OneDrive encrypted folder.
        
        Args:
            file_path: Path to the changed file
        """
        with self.sync_lock:
            try:
                # Skip non-encrypted files
                if not file_path.name.endswith('.gpg'):
                    return
                    
                logging.info(f"OneDrive file changed: {file_path.name}")
                
                # Get the decrypted file name (remove .gpg extension)
                decrypted_name = file_path.name[:-4]
                
                # Create a temporary file for decryption
                temp_encrypted = self.local_path / f".temp_{file_path.name}"
                
                # Copy the encrypted file to the temp location
                shutil.copy2(file_path, temp_encrypted)
                
                # Decrypt the file
                decrypted_path = self.decrypted_path / decrypted_name
                self.pgp_handler.decrypt_file(temp_encrypted, str(decrypted_path))
                
                # Clean up temporary encrypted file
                os.unlink(temp_encrypted)
                
                logging.info(f"Decrypted OneDrive file to {decrypted_path}")
                
            except Exception as e:
                logging.error(f"Error handling OneDrive change for {file_path}: {str(e)}")
    
    def start(self):
        """Start the sync manager."""
        # Set up OneDrive folder observer
        event_handler = OneDriveChangeHandler(self.handle_onedrive_change)
        self.onedrive_observer = Observer()
        self.onedrive_observer.schedule(event_handler, self.onedrive_encrypted_path, recursive=True)
        self.onedrive_observer.start()
        
        logging.info(f"Started monitoring OneDrive folder: {self.onedrive_encrypted_path}")
        logging.info("Sync manager started")
    
    def stop(self):
        """Stop the sync manager."""
        if self.onedrive_observer:
            self.onedrive_observer.stop()
            self.onedrive_observer.join()
        logging.info("Sync manager stopped") 