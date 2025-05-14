import os
import shutil
import logging
from pathlib import Path

class SyncFolderClient:
    def __init__(self, config):
        """Initialize OneDrive client with configuration."""
        self.config = config
        
        # Get OneDrive folder path from config or try to detect it
        self.sync_folder_path = config.get('sync_folder', {}).get('path')
        if not self.sync_folder_path:
            self.sync_folder_path = self._detect_sync_folder_path()
            
        if not self.sync_folder_path or not os.path.exists(self.sync_folder_path):
            raise ValueError("OneDrive folder not found. Please specify the full path in config.json using the 'sync_folder.path' setting.")
            
        self.encrypted_path = os.path.join(
            self.sync_folder_path, 
            config.get('sync_folder', {}).get('encrypted_folder', 'encrypted_files')
        )
        
        # Create encrypted folder if it doesn't exist
        os.makedirs(self.encrypted_path, exist_ok=True)
        
    def _detect_sync_folder_path(self):
        """Try to detect the OneDrive folder path."""
        # Common OneDrive locations
        possible_paths = [
            os.path.expanduser("~/OneDrive"),
            os.path.expanduser("~/OneDrive - Personal"),
            os.path.expanduser("~/OneDrive - Business"),
            # Windows-specific paths
            os.path.join(os.environ.get('USERPROFILE', ''), 'OneDrive'),
            # macOS-specific paths
            os.path.expanduser("~/Library/CloudStorage/OneDrive-Personal"),
            # Android-specific paths (Termux)
            "/storage/emulated/0/OneDrive",
            "/sdcard/OneDrive",
            # Add more common paths as needed
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                logging.info(f"Detected OneDrive folder at: {path}")
                return path
                
        return None
        
    def list_files(self, folder_path=None):
        """List files in a OneDrive folder."""
        if folder_path is None:
            folder_path = self.encrypted_path
            
        if not os.path.exists(folder_path):
            return []
            
        files = []
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                files.append({
                    'name': item,
                    'id': item,  # Use filename as ID
                    'lastModifiedDateTime': os.path.getmtime(item_path)
                })
                
        return files
        
    def download_file(self, file_id, output_path):
        """Download a file from OneDrive."""
        source_path = os.path.join(self.encrypted_path, file_id)
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"File not found: {source_path}")
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy2(source_path, output_path)
        logging.info(f"Downloaded file to {output_path}")
        
        return output_path
        
    def upload_file(self, file_path, remote_path=None):
        """Upload a file to OneDrive."""
        if remote_path is None:
            file_name = os.path.basename(file_path)
            remote_path = os.path.join(self.encrypted_path, file_name)
            
        os.makedirs(os.path.dirname(remote_path), exist_ok=True)
        shutil.copy2(file_path, remote_path)
        logging.info(f"Uploaded {file_path} to {remote_path}")
        
        return {
            'name': os.path.basename(remote_path),
            'id': os.path.basename(remote_path),
            'lastModifiedDateTime': os.path.getmtime(remote_path)
        }
        
    def ensure_folder_exists(self, folder_path):
        """Ensure a folder exists in OneDrive."""
        # Handle both absolute paths and paths relative to OneDrive root
        if folder_path.startswith('/'):
            folder_path = folder_path.lstrip('/')
        
        full_path = os.path.join(self.sync_folder_path, folder_path)
        os.makedirs(full_path, exist_ok=True)
        return {'id': folder_path, 'name': os.path.basename(folder_path)} 