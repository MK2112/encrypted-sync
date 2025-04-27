# Paragon

Paragon is a transparent encryption layer for OneDrive files. It works with your existing OneDrive client installation and requires no special configuration on OneDrive's side. Paragon automatically encrypts files with PGP before they sync to OneDrive and decrypts them when updated there. All encryption and decryption happens locally on your device, ensuring your sensitive data remains private.

## Features

- Automatic PGP encryption of files before they sync to OneDrive
- Automatic decryption of files when they're updated on OneDrive
- Works with your existing OneDrive client installation
- Real-time file monitoring for local changes
- Event-based checking for remote changes

## Requirements

- Python 3.10 or higher
- GnuPG installed on your system
- OneDrive client installed and configured on your computer

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/MK2112/paragon.git
   cd paragon
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
     "onedrive": {
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
   
   Notes:
   - Use `onedrive.path` to specify the full path
   - Set `pgp.key_name` to the name you used when creating your PGP key
   - Leave `pgp.passphrase` empty to be prompted each time, or set it for automatic operation (less secure)

## Usage

### Quick Start

1. **Add files to encrypt:**  
   Place any files you want to keep secure into your chosen "monitored" directory (e.g. `secure_files/`).  
   *Example:*  
   ```bash
   echo "my-secret-password" > secure_files/passwords.txt
   ```

2. **Start Paragon:**  
   Run the application to automatically encrypt new or changed files in your monitored directory:
   ```bash
   onedrive-pgp
   ```
   You can specify a custom config file if needed:
   ```bash
   onedrive-pgp --config /path/to/your/config.json
   ```

3. **Encrypted files appear:**  
   Paragon will automatically:
   - Detect new or updated files in your monitored directory.
   - Encrypt them using your PGP key.
   - Place the encrypted versions (e.g. `passwords.txt.gpg`) in the configured encrypted folder (e.g. `encrypted_files/`).

4. **Accessing your files elsewhere:**  
   - To decrypt a file, Paragon will automatically detect new encrypted files in your encrypted folder and decrypt them back to your monitored directory.
   - You can safely sync the encrypted folder (`encrypted_files/`) with any cloud service (e.g. OneDrive, Dropbox, etc.), knowing only encrypted data leaves your device.

### Example Workflow

- Add a file to `secure_files/`  
  - Paragon encrypts it to `encrypted_files/filename.gpg`.

- Copy `encrypted_files/filename.gpg` to another device and place it in that device’s encrypted folder  
  - Paragon decrypts it back to `secure_files/filename`.

---

**Tip:**  
Your files are always encrypted before leaving your device. Only you, with your PGP key, can decrypt them.

## Security Considerations

- Your files are only stored in encrypted state in the cloud
- Decryption happens locally on your device
- Your PGP private key never leaves your device
- It is recommended to use a strong passphrase for your PGP key
- If you specify your passphrase in the config file, which isn't recommended, ensure the file is properly secured
- Only you should know your passphrase and private key, nobody else, at any point

## Troubleshooting

- Check the log file (`onedrive_pgp.log`) for detailed information
- Ensure your PGP key is properly set up and accessible
- Verify your OneDrive folder path is correct
- Make sure the OneDrive client is running and properly syncing
- Make sure you have proper permissions for the directories in your config

## License

MIT.
