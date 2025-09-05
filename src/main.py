import os
import sys
import json
import logging
import argparse
import signal

try:
    # Relative imports if running as package
    from .pgp_handler import PGPHandler
    from .sync_folder_client import SyncFolderClient
    from .file_monitor import FileMonitor
    from .sync_manager import SyncManager
except ImportError:
    # Absolute imports if running as script
    from pgp_handler import PGPHandler
    from sync_folder_client import SyncFolderClient
    from file_monitor import FileMonitor
    from sync_manager import SyncManager

def load_config(config_path):
    """Load configuration JSON data"""
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_logging(log_file: str | None):
    """log_file can be None, then disable file logging"""
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
    )

def check_android_permissions():
    """Running on Android requires requesting permissions"""
    try:
        # Check if running on Android through Termux
        if os.path.exists("/data/data/com.termux"):
            logging.info("Running on Android through Termux")
            if not os.access("/storage/emulated/0", os.R_OK | os.W_OK):
                logging.warning("Storage access not available. Please run 'termux-setup-storage' first.")
                print("Storage access not available. Please run 'termux-setup-storage' in Termux and restart the app.")
                sys.exit(1)
    except Exception as e:
        logging.warning(f"Error checking Android permissions: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='encrypted-sync: PGP Encryption Middleware for any cloud sync folder')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    args = parser.parse_args()
    try:
        # Check Android permissions
        check_android_permissions()

        # Load configuration
        config = load_config(args.config)

        # Allow overriding or disabling file logging via config
        log_file = config.get('log_file', None)
        setup_logging(log_file)
        
        # Core components
        pgp_handler = PGPHandler(config)
        sync_folder_client = SyncFolderClient(config)
        
        # Sync manager
        sync_manager = SyncManager(config, sync_folder_client, pgp_handler)
        
        # File monitor
        file_monitor = FileMonitor(
            config['local']['monitored_path'],
            sync_manager.handle_local_change
        )
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logging.info("Shutting down...")
            sync_manager.stop()
            file_monitor.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start components
        sync_manager.start()
        file_monitor.start()
        
        logging.info("encrypted-sync: PGP Encryption Middleware started")
        
        # Keep the main thread alive
        while True:
            signal.pause()
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 