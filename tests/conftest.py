import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
import pytest
import tempfile
import shutil

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
        "sync_folder": {
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
