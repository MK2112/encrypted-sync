import os
import gnupg
import logging
import subprocess
import getpass

class PGPHandler:
    MAX_PASSPHRASE_RETRIES = 3

    def __init__(self, config):
        """Initialize PGP handler with configuration."""
        self.config = config

        # Check if GnuPG is installed
        try:
            result = subprocess.run(['gpg', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                raise EnvironmentError("GnuPG is installed but returned an error.")
            logging.info(f"Using GnuPG: {result.stdout.splitlines()[0]}")
        except FileNotFoundError:
            raise EnvironmentError("GnuPG binary not found. Please install it and ensure it's on the PATH.")

        self.gpg = gnupg.GPG(gnupghome=os.path.expanduser(config['pgp']['gnupghome']))
        self.key_name = config['pgp']['key_name']
        self.passphrase = config['pgp'].get('passphrase')

        self._verify_key()

    def _verify_key(self):
        """Verify that the specified private key exists."""
        try:
            keys = self.gpg.list_keys(True)
            key_exists = any(self.key_name in key['uids'][0] for key in keys if 'uids' in key)
            if not key_exists:
                raise ValueError(f"PGP key '{self.key_name}' not found in keyring. Use 'gpg --import' or generate it with 'gpg --full-generate-key'.")
        except Exception as e:
            raise RuntimeError(f"Failed to access GPG keyring: {str(e)}")

    def encrypt_file(self, file_path, output_path=None):
        if output_path is None:
            output_path = str(file_path) + '.gpg'

        try:
            with open(file_path, 'rb') as f:
                status = self.gpg.encrypt_file(
                    f, recipients=[self.key_name],
                    output=output_path,
                    always_trust=True
                )
        except Exception as e:
            raise RuntimeError(f"Encryption failed: I/O or GPG error: {str(e)}")

        if status.ok:
            logging.info(f"Encrypted {file_path} to {output_path}")
            return output_path
        else:
            raise RuntimeError(f"Encryption failed: {status.status} — {status.stderr}")

    def decrypt_file(self, encrypted_path, output_path=None):
        if output_path is None:
            output_path = str(encrypted_path)
            if output_path.endswith('.gpg'):
                output_path = output_path[:-4]

        # Retry logic
        for attempt in range(1, self.MAX_PASSPHRASE_RETRIES + 1):
            try:
                passphrase = self.passphrase or getpass.getpass(f"Enter PGP passphrase (attempt {attempt}/{self.MAX_PASSPHRASE_RETRIES}): ")

                with open(encrypted_path, 'rb') as f:
                    status = self.gpg.decrypt_file(
                        f, passphrase=passphrase,
                        output=output_path
                    )

                if status.ok:
                    logging.info(f"Decrypted {encrypted_path} to {output_path}")
                    return output_path
                else:
                    logging.warning(f"Attempt {attempt}: Decryption failed — {status.status}")
            except Exception as e:
                logging.error(f"Attempt {attempt}: Decryption raised an error: {str(e)}")

            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logging.debug(f"Cleaned up partial output file: {output_path}")
                except Exception as e:
                    logging.warning(f"Failed to delete partial output file: {output_path} — {str(e)}")

        raise RuntimeError(f"Decryption failed after {self.MAX_PASSPHRASE_RETRIES} attempts. Check your passphrase and key setup.")
