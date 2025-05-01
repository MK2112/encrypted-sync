import pytest
import tempfile
import shutil
import os

@pytest.fixture(scope="function")
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

@pytest.fixture(scope="function")
def dummy_config(temp_dir):
    return {
        "local": {
            "monitored_path": temp_dir,
            "decrypted_path": temp_dir
        },
        "onedrive": {
            "path": temp_dir,
            "encrypted_folder": "encrypted_files"
        },
        "pgp": {
            "key_name": "dummy-key",
            "passphrase": "dummy-passphrase",
            "gnupghome": temp_dir
        },
        "sync": {
            "check_interval": 1
        }
    }
