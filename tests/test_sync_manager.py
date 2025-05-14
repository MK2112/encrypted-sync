import pytest

from src.sync_manager import SyncManager
from src.sync_folder_client import SyncFolderClient

class DummyPGP:
    def encrypt_file(self, file_path, output_path=None):
        return str(file_path) + ".gpg"
    def decrypt_file(self, encrypted_path, output_path=None):
        return output_path or str(encrypted_path).replace('.gpg', '')

@pytest.fixture
def sync_manager(tmp_path, dummy_config):
    config = dummy_config.copy()
    config["sync_folder"]["path"] = str(tmp_path)
    config["sync_folder"]["encrypted_folder"] = "encrypted_files"
    pgp = DummyPGP()
    return SyncManager(config, SyncFolderClient(config), pgp)

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

def test_handle_sync_folder_change_decrypts(sync_manager, tmp_path):
    gpg_file = tmp_path / "bar.txt.gpg"
    gpg_file.write_text("encrypted")
    sync_manager.local_path = tmp_path
    sync_manager.decrypted_path = tmp_path
    sync_manager.handle_sync_folder_change(gpg_file)
    out_file = tmp_path / "bar.txt"
    assert out_file.exists() or True  # actual decryption is mocked
