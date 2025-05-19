import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
import pytest
from src.sync_manager import SyncManager
from src.sync_folder_client import SyncFolderClient

class DummyPGP:
    def encrypt_file(self, file_path, output_path=None):
        out = str(file_path) + ".gpg"
        with open(out, "w") as f:
            f.write("encrypted")
        return out
    def decrypt_file(self, encrypted_path, output_path=None):
        out = output_path or str(encrypted_path).replace('.gpg', '')
        with open(out, "w") as f:
            f.write("decrypted")
        return out

@pytest.fixture
def dummy_config(tmp_path):
    return {
        "local": {"monitored_path": str(tmp_path / "mon"), "decrypted_path": str(tmp_path / "dec")},
        "sync_folder": {"path": str(tmp_path / "sync"), "encrypted_folder": "encrypted_files"},
        "pgp": {"key_name": "dummy", "passphrase": "", "gnupghome": str(tmp_path)},
    }


def test_full_workflow(tmp_path, dummy_config):
    # Setup dirs
    os.makedirs(tmp_path / "mon", exist_ok=True)
    os.makedirs(tmp_path / "dec", exist_ok=True)
    os.makedirs(tmp_path / "sync" / "encrypted_files", exist_ok=True)
    pgp = DummyPGP()
    client = SyncFolderClient(dummy_config)
    sm = SyncManager(dummy_config, client, pgp)
    sm.local_path = tmp_path / "mon"
    sm.decrypted_path = tmp_path / "dec"
    sm.sync_folder_encrypted_path = str(tmp_path / "sync" / "encrypted_files")

    # Simulate local file change
    test_file = tmp_path / "mon" / "secret.txt"
    test_file.write_text("plain")
    sm.handle_local_change(test_file)
    enc_file = tmp_path / "sync" / "encrypted_files" / "secret.txt.gpg"
    assert enc_file.exists()
    # Simulate remote change (new encrypted file)
    sm.handle_sync_folder_change(enc_file)
    dec_file = tmp_path / "dec" / "secret.txt"
    assert dec_file.exists()
    assert dec_file.read_text() == "decrypted"
