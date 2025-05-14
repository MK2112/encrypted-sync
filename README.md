# encrypted-sync

encrypted-sync is an encryption layer for cloud sync services. Files are automatically encrypted with PGP before they sync, and decrypted locally when needed. All encryption and decryption happens on your device, ensuring your data remains private and secure. encrypted-sync makes zero-trust cloud storage effortless for individuals and teams.

## Features

- Automatic PGP encryption of files before they sync
- Automatic decryption of files when they're updated
- Works with your existing cloud sync client installation
- Monitoring for local changes
- Event-based checking for remote changes

## Requirements

- Python 3.10.x or higher
- GnuPG installed on your system
- Some cloud sync client installed and configured on your computer

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/MK2112/encrypted-sync.git
   cd encrypted-sync
   ```

2. Install the package:
   ```
   pip install -r requirements.txt
   ```

3. Create a PGP key if you don't already have one:
   ```
   gpg --full-generate-key
   ```
   Follow the prompts to create your key. Remember the name you use for your key.

4. Create or update the configuration file (`config.json`):
   ```json
   {
     "local": {
       "monitored_path": "./secure_files",
       "decrypted_path": "./secure_files"
     },
     "sync_folder": {
       "path": "",
       "encrypted_folder": "encrypted_files"
     },
     "pgp": {
       "key_name": "your_key_name",
       "passphrase": "",
       "gnupghome": "~/.gnupg"
     },
     "sync": {
       "check_interval": 60
     }
   }
   ```
   
   **Notes:**
   - Use `sync_folder.path` to specify the full path to your cloud sync folder (e.g. for Dropbox, Google Drive, Syncthing, etc.)
   - Set `pgp.key_name` to the name you used when creating your PGP key
   - Leave `pgp.passphrase` empty to be prompted each time, or set it for automatic operation (less secure)
   - All files in the monitored directory, including hidden files, are encrypted and synced.
   - The tool automatically handles file overwrites and creates conflict files if both local and remote versions change independently.

## Usage

### Quick Start

1. **Add files to encrypt:**  
   Place any files you want to keep secure into your chosen "monitored" directory (e.g. `secure_files/`).  
   
   *An example could be:*  
   ```bash
   echo "my-secret-password" > secure_files/passwords.txt
   ```

2. **Start encrypted-sync:**  
   Run the application to automatically encrypt new or changed files in your monitored directory:

   ```bash
   encrypted-sync
   ```
   You can specify a custom config file if needed:
   ```bash
   encrypted-sync --config /path/to/your/config.json
   ```

3. **Encrypted files appear:**  
   encrypted-sync will automatically:
   - Detect new or updated files in your monitored directory.
   - Encrypt them using your PGP key.
   - Place the encrypted versions (e.g. `passwords.txt.gpg`) in the configured encrypted folder (e.g. `encrypted_files/`).

4. **Accessing your files elsewhere:**  
   - To decrypt a file, encrypted-sync will automatically detect new encrypted files in your encrypted folder and decrypt them back to your monitored directory.
   - You can safely sync the encrypted folder (`encrypted_files/`) with any cloud service (e.g. Dropbox, Google Drive, OneDrive, Syncthing, etc.), knowing only encrypted data leaves your device.

### Tests

Run the tests with:
```bash
pytest ./tests/
```

### Example Workflow

- Add a file to `secure_files/`  
  - encrypted-sync encrypts it to `encrypted_files/filename.gpg`.

- Sync `encrypted_files/filename.gpg` to another device  
  - encrypted-sync decrypts it back to `secure_files/filename`.

Your files are always encrypted before leaving your device. Only you, with your PGP key, can decrypt them.

## Security Considerations

- Your files are only stored in encrypted state in the cloud
- Decryption happens locally on your device
- Your PGP private key never leaves your device
- It is recommended to use a strong, unique passphrase for your PGP key
- If you specify your passphrase in the config file, which isn't recommended, ensure the file is properly secured
- Only you should know your passphrase and private key, nobody else, at any point

## Troubleshooting

- Check the log file (`sync_folder_pgp.log`) for detailed information
- Ensure your PGP key is properly set up and accessible
- Verify your sync folder folder path is correct
- Make sure the sync folder client is running and properly syncing
- Make sure you have proper permissions for the directories in your config

## License

MIT.
