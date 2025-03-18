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
   git clone https://github.com/mk2112/paragon.git
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

### Starting the Application

Run the application:

```
onedrive-pgp
```

Or with a custom config file, different from the default `config.json`:

```
onedrive-pgp --config /path/to/your/differing/config.json
```

### Basic Usage

1. Place files you want to encrypt in the monitored directory (default: `./secure_files`).
2. The application will automatically:
   - Encrypt the files using your PGP key
   - Copy the encrypted versions to your OneDrive folder
   - OneDrive's own client will sync these encrypted files to the cloud, as usual
   - On other devices, Paragon will detect newly encrypted or updated encrypted files, download and decrypt them for use

### Example Workflow

1. Create a password file:
   ```
   echo "my-secret-password" > secure_files/passwords.txt
   ```

2. Paragon will:
   - Automatically detect the new file
   - Encrypt it with your PGP key
   - Copy the encrypted file to your OneDrive folder at `encrypted_files/passwords.txt.gpg`
   - OneDrive client syncs the encrypted file to the cloud

3. On another device running Paragon:
   - OneDrive client downloads the encrypted file
   - Paragon detects the new encrypted file
   - Paragon decrypts it to `secure_files/passwords.txt`
   - You can now access your password securely on multiple devices

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
