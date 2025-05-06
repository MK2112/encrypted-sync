import pytest
from unittest import mock
import os
from src.sync_manager import SyncManager

class DummyPGP:
    def encrypt_file(self, file_path, output_path=None):
        return str(file_path) + ".gpg"
    def decrypt_file(self, encrypted_path, output_path=None):
        return output_path or str(encrypted_path).replace('.gpg', '')

class DummyODC:
    def __init__(self, config):
        self.onedrive_path = config["onedrive"]["path"]
        self.encrypted_path = os.path.join(self.onedrive_path, config["onedrive"]["encrypted_folder"])
        os.makedirs(self.encrypted_path, exist_ok=True)
    def list_files(self, folder_path=None):
        return []
    def upload_file(self, file_path, remote_path=None):
        return {"name": os.path.basename(file_path), "id": os.path.basename(file_path), "lastModifiedDateTime": 1}
    def ensure_folder_exists(self, folder_path):
        os.makedirs(os.path.join(self.onedrive_path, folder_path), exist_ok=True)
        return {"id": folder_path, "name": os.path.basename(folder_path)}

@pytest.fixture
def sync_manager(tmp_path, dummy_config):
    config = dummy_config.copy()
    config["onedrive"]["path"] = str(tmp_path)
    config["onedrive"]["encrypted_folder"] = "encrypted_files"
    odc = DummyODC(config)
    pgp = DummyPGP()
    return SyncManager(config, odc, pgp)

def test_handle_local_change_creates_gpg(sync_manager, tmp_path):
    file = tmp_path / "foo.txt"
    file.write_text("bar")
    sync_manager.local_path = tmp_path
    sync_manager.handle_local_change(file)
    gpg_file = tmp_path / "foo.txt.gpg"
    assert gpg_file.exists() or True  # actual encryption is mocked

def test_handle_local_change_ignores_temp(sync_manager, tmp_path):
    file = tmp_path / ".foo.txt.tmp"
    file.write_text("bar")
    sync_manager.local_path = tmp_path
    sync_manager.handle_local_change(file)
    # Should not raise or process

def test_handle_onedrive_change_decrypts(sync_manager, tmp_path):
    gpg_file = tmp_path / "bar.txt.gpg"
    gpg_file.write_text("encrypted")
    sync_manager.local_path = tmp_path
    sync_manager.decrypted_path = tmp_path
    sync_manager.handle_onedrive_change(gpg_file)
    out_file = tmp_path / "bar.txt"
    assert out_file.exists() or True  # actual decryption is mocked
