import os
import sys
import json
import logging
import argparse
import signal
from pathlib import Path

from pgp_handler import PGPHandler
from sync_folder_client import SyncFolderClient
from file_monitor import FileMonitor
from sync_manager import SyncManager

def load_config(config_path):
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('paragon.log')
        ]
    )

def check_android_permissions():
    """Check if running on Android and request necessary permissions."""
    try:
        # Check if we're running on Android via Termux
        if os.path.exists("/data/data/com.termux"):
            logging.info("Running on Android via Termux")
            
            # Check if we have storage access
            if not os.access("/storage/emulated/0", os.R_OK | os.W_OK):
                logging.warning("Storage access not available. Please run 'termux-setup-storage' first.")
                print("Storage access not available. Please run 'termux-setup-storage' in Termux and restart the app.")
                sys.exit(1)
    except Exception as e:
        logging.warning(f"Error checking Android permissions: {str(e)}")

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='Paragon: PGP Encryption Middleman for any cloud sync folder')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    try:
        # Check Android permissions
        check_android_permissions()
        
        # Load configuration
        config = load_config(args.config)
        
        # Initialize components
        pgp_handler = PGPHandler(config)
        sync_folder_client = SyncFolderClient(config)
        
        # Initialize sync manager
        sync_manager = SyncManager(config, sync_folder_client, pgp_handler)
        
        # Initialize file monitor
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
        
        logging.info("Paragon: PGP Encryption Middleman started")
        
        # Keep the main thread alive
        while True:
            signal.pause()
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 