import pytest
import os
import shutil
from src.onedrive_client import OneDriveClient

@pytest.fixture
def odir(tmp_path):
    d = tmp_path / "onedrive"
    d.mkdir()
    (d / "encrypted_files").mkdir()
    return str(d)

def test_detect_onedrive_path(monkeypatch, tmp_path):
    # Simulate OneDrive folder detection
    folder = tmp_path / "OneDrive"
    folder.mkdir()
    config = {"onedrive": {"path": str(folder), "encrypted_folder": "encrypted_files"}}
    client = OneDriveClient(config)
    assert os.path.exists(client.onedrive_path)

def test_upload_and_list_files(tmp_path):
    config = {"onedrive": {"path": str(tmp_path), "encrypted_folder": "encrypted_files"}}
    client = OneDriveClient(config)
    test_file = tmp_path / "foo.txt"
    test_file.write_text("bar")
    result = client.upload_file(str(test_file))
    files = client.list_files()
    assert any(f["name"] == "foo.txt" for f in files)

def test_download_file(tmp_path):
    config = {"onedrive": {"path": str(tmp_path), "encrypted_folder": "encrypted_files"}}
    client = OneDriveClient(config)
    src = tmp_path / "foo.txt"
    src.write_text("bar")
    client.upload_file(str(src))
    out = tmp_path / "out.txt"
    client.download_file("foo.txt", str(out))
    assert out.read_text() == "bar"

def test_ensure_folder_exists(tmp_path):
    config = {"onedrive": {"path": str(tmp_path), "encrypted_folder": "encrypted_files"}}
    client = OneDriveClient(config)
    folder = "custom_folder"
    result = client.ensure_folder_exists(folder)
    assert os.path.exists(os.path.join(tmp_path, folder))
