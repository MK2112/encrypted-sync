import os
import gnupg
import logging
from pathlib import Path

class PGPHandler:
    def __init__(self, config):
        """Initialize PGP handler with configuration."""
        self.config = config
        
        # Check if GnuPG is installed
        try:
            import subprocess
            result = subprocess.run(['gpg', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                raise ValueError("GnuPG not found. Please install it first.")
            logging.info(f"Using GnuPG: {result.stdout.splitlines()[0]}")
        except FileNotFoundError:
            raise ValueError("GnuPG not found. Please install it first.")
        
        self.gpg = gnupg.GPG(gnupghome=os.path.expanduser(config['pgp']['gnupghome']))
        self.key_name = config['pgp']['key_name']
        self.passphrase = config['pgp']['passphrase']
        
        # Verify key exists
        self._verify_key()
        
    def _verify_key(self):
        """Verify that the specified key exists."""
        try:
            keys = self.gpg.list_keys(True)  # True for private keys
            key_exists = any(self.key_name in key['uids'][0] for key in keys if key.get('uids'))
            
            if not key_exists:
                logging.error(f"PGP key '{self.key_name}' not found. Please generate or import it.")
                raise ValueError(f"PGP key '{self.key_name}' not found. Use 'gpg --full-generate-key' to create one.")
        except Exception as e:
            logging.error(f"Error accessing GPG keyring: {str(e)}")
            raise ValueError(f"Error accessing GPG keyring. Make sure GnuPG is installed and properly configured: {str(e)}")
    
    def encrypt_file(self, file_path, output_path=None):
        """
        Encrypt a file using PGP.
        
        Args:
            file_path: Path to the file to encrypt
            output_path: Path where to save the encrypted file (default: file_path + .gpg)
            
        Returns:
            Path to the encrypted file
        """
        if output_path is None:
            output_path = str(file_path) + '.gpg'
            
        with open(file_path, 'rb') as f:
            status = self.gpg.encrypt_file(
                f, recipients=[self.key_name],
                output=output_path,
                always_trust=True
            )
            
        if status.ok:
            logging.info(f"Encrypted {file_path} to {output_path}")
            return output_path
        else:
            logging.error(f"Encryption failed: {status.status} - {status.stderr}")
            raise RuntimeError(f"Encryption failed: {status.stderr}")
    
    def decrypt_file(self, encrypted_path, output_path=None):
        """
        Decrypt a PGP encrypted file.
        
        Args:
            encrypted_path: Path to the encrypted file
            output_path: Path where to save the decrypted file
            
        Returns:
            Path to the decrypted file
        """
        if output_path is None:
            # Remove .gpg extension if present
            output_path = str(encrypted_path)
            if output_path.endswith('.gpg'):
                output_path = output_path[:-4]
        
        passphrase = self.passphrase
        if not passphrase:
            # In a real application, you might want to use a secure way to get the passphrase
            import getpass
            passphrase = getpass.getpass("Enter PGP passphrase: ")
            
        with open(encrypted_path, 'rb') as f:
            status = self.gpg.decrypt_file(
                f, passphrase=passphrase,
                output=output_path
            )
            
        if status.ok:
            logging.info(f"Decrypted {encrypted_path} to {output_path}")
            return output_path
        else:
            logging.error(f"Decryption failed: {status.status} - {status.stderr}")
            raise RuntimeError(f"Decryption failed: {status.stderr}") 