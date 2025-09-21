import os
import time
import shutil
import logging
import threading

from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SyncFolderChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        """Initialize sync folder change handler with callback function."""
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
    def __init__(self, config, sync_folder_client, pgp_handler):
        """
        Initialize sync manager.
        
        Args:
            config: Application configuration
            sync_folder_client: Sync folder client instance
            pgp_handler: PGP handler instance
        """
        self.config = config
        self.sync_folder_client = sync_folder_client
        self.pgp_handler = pgp_handler
        
        self.local_path = Path(config['local']['monitored_path']).resolve()
        self.decrypted_path = Path(config['local']['decrypted_path']).resolve()
        self.encrypted_path = config['sync_folder']['encrypted_folder']
        self.sync_folder_encrypted_path = os.path.join(
            self.sync_folder_client.sync_folder_path, 
            self.encrypted_path
        )
        
        # Create directories if they don't exist
        os.makedirs(self.local_path, exist_ok=True)
        os.makedirs(self.decrypted_path, exist_ok=True)
        
        # Ensure sync folder encrypted folder exists
        self.sync_folder_client.ensure_folder_exists(self.encrypted_path)
        
        # File metadata cache
        self.local_files = {}  # path -> last_modified_time
        self.remote_files = {}  # path -> {id, last_modified_time}
        
        # Sync lock to prevent concurrent sync operations
        self.sync_lock = threading.Lock()
        
        # Set up sync folder folder observer
        self.sync_folder_observer = None
        
    def _is_within(self, base: Path, target: Path) -> bool:
        # Check if target is within base directory
        try:
            base_resolved = base.resolve()
            target_resolved = target.resolve()
            return str(target_resolved).startswith(str(base_resolved) + os.sep) or target_resolved == base_resolved
        except FileNotFoundError:
            # If target doesn't exist, check with absolute normalization
            base_abs = base.absolute()
            target_abs = target.absolute()
            return str(target_abs).startswith(str(base_abs) + os.sep) or target_abs == base_abs

    def _has_symlink_component(self, path: Path) -> bool:
        # Check each component for being symlink, avoid traversal
        current = path
        while True:
            if current.exists() and current.is_symlink():
                return True
            if current == current.parent:
                break
            current = current.parent
        return False

    def handle_local_change(self, file_path):
        # Handle a local file change using the path to the changed file
        with self.sync_lock:
            try:
                # Skip temporary files and hidden files
                if file_path.name.startswith('.') or file_path.name.endswith('.tmp'):
                    return
                    
                # Skip already encrypted files
                if file_path.name.endswith('.gpg'):
                    return

                # Ensure changed path within monitored directory, not a symlink
                if not self._is_within(self.local_path, file_path) or self._has_symlink_component(file_path):
                    logging.warning(f"Skipping file outside monitored directory or containing symlinks: {file_path}")
                    return

                # Get relative path from monitored directory
                rel_path = file_path.relative_to(self.local_path)
                
                logging.info(f"Local file changed: {rel_path}")
                
                # Check if there's a newer version in sync folder
                remote_file_mtime = None
                reported_remote_mtime = None

                # Compute expected full remote path for file (handles nested paths)
                # Check directly for speeeeed
                expected_remote_full_path = os.path.normpath(
                    os.path.join(self.sync_folder_encrypted_path, f"{rel_path}.gpg")
                )
                if os.path.exists(expected_remote_full_path):
                    try:
                        remote_file_mtime = os.path.getmtime(expected_remote_full_path)
                    except OSError:
                        remote_file_mtime = None
                else:
                    # Consult client list_files metadata as fallback
                    try:
                        expected_name = os.path.basename(f"{rel_path}.gpg")
                        for f in self.sync_folder_client.list_files(self.sync_folder_encrypted_path):
                            fid = os.path.normpath(f.get('id', '') or '')
                            fname = f.get('name')
                            if fid == expected_remote_full_path or fname == expected_name:
                                reported_remote_mtime = f.get('lastModifiedDateTime')
                                break
                    except Exception:
                        # Client lookup failed; ignore, proceed
                        pass
                
                # If remote file exists and is newer -> Create a conflict file
                local_mtime = file_path.stat().st_mtime
                conflict_detected = (
                    (remote_file_mtime is not None and remote_file_mtime > local_mtime) or
                    (reported_remote_mtime is not None and reported_remote_mtime > local_mtime)
                )
                if conflict_detected:
                    conflict_path = f"{file_path}.conflict"
                    shutil.copy2(file_path, conflict_path)
                    logging.warning(f"guardian-sync conflict detected for {rel_path}. Local copy saved as {conflict_path}")
                    # Return early: avoid encrypting/uploading on detected conflict
                    return
                
                # Encrypt the file
                temp_encrypted = self.pgp_handler.encrypt_file(file_path)
                
                # Upload to sync folder
                sync_folder_path = os.path.join(self.sync_folder_encrypted_path, f"{rel_path}.gpg")
                self.sync_folder_client.upload_file(temp_encrypted, sync_folder_path)
                
                # Update local file cache
                self.local_files[str(rel_path)] = file_path.stat().st_mtime
                
                # Clean up temporary encrypted file if it's different from the original
                if temp_encrypted != str(file_path) + '.gpg':
                    os.unlink(temp_encrypted)
                    
            except Exception as e:
                logging.error(f"Error handling local change for {file_path}: {str(e)}")
    
    def handle_sync_folder_change(self, file_path):
        # Handle a change to a file (via its path) in the sync folder encrypted folder.
        with self.sync_lock:
            try:
                # Skip non-encrypted files
                if not file_path.name.endswith('.gpg'):
                    return

                # Ensure changed path within encrypted sync folder and not a symlink
                if not self._is_within(Path(self.sync_folder_encrypted_path), file_path) or self._has_symlink_component(file_path):
                    logging.warning(f"Skipping encrypted file outside sync/encrypted folder or containing symlinks: {file_path}")
                    return

                logging.info(f"Sync folder file changed: {file_path.name}")
                
                # Get the decrypted file name (remove .gpg extension)
                decrypted_name = file_path.name.rsplit('.gpg', 1)[0]
                
                # Create a temporary file for decryption
                temp_encrypted = self.local_path / f".temp_{file_path.name}"
                
                # Copy the encrypted file to the temp location
                shutil.copy2(file_path, temp_encrypted)
                
                # Decrypt the file
                decrypted_path = self.decrypted_path / decrypted_name
                os.makedirs(self.decrypted_path, exist_ok=True)
                self.pgp_handler.decrypt_file(temp_encrypted, str(decrypted_path))
                # Harden permissions on decrypted output (owner read/write only)
                try:
                    os.chmod(decrypted_path, 0o600)
                except Exception as e:
                    logging.warning(f"Failed to set secure permissions on {decrypted_path}: {e}")
                
                # Clean up temporary encrypted file
                os.unlink(temp_encrypted)
                
                logging.info(f"Decrypted sync folder file to {decrypted_path}")
                
            except Exception as e:
                logging.error(f"Error handling sync folder change for {file_path}: {str(e)}")
    
    def start(self):
        """Start the sync manager."""
        # Set up sync folder folder observer
        event_handler = SyncFolderChangeHandler(self.handle_sync_folder_change)
        self.sync_folder_observer = Observer()
        self.sync_folder_observer.schedule(event_handler, self.sync_folder_encrypted_path, recursive=True)
        self.sync_folder_observer.start()
        
        logging.info(f"Started monitoring sync folder: {self.sync_folder_encrypted_path}")
        logging.info("Sync manager started")
    
    def stop(self):
        """Stop the sync manager."""
        if self.sync_folder_observer:
            self.sync_folder_observer.stop()
            self.sync_folder_observer.join()
        logging.info("Sync manager stopped") 