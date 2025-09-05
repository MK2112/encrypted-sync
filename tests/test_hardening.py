import os
import sys
import stat
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from src.sync_manager import SyncManager
from src.sync_folder_client import SyncFolderClient


class PGPWriteDummy:
    def encrypt_file(self, file_path, output_path=None):
        out = (output_path or (str(file_path) + ".gpg"))
        with open(out, "w") as f:
            f.write("encrypted")
        return out

    def decrypt_file(self, encrypted_path, output_path=None):
        out = output_path or str(encrypted_path).replace('.gpg', '')
        with open(out, "w") as f:
            f.write("decrypted")
        return out


def make_config(base: Path):
    return {
        "local": {"monitored_path": str(base / "mon"), "decrypted_path": str(base / "dec")},
        "sync_folder": {"path": str(base / "sync"), "encrypted_folder": "encrypted_files"},
        "pgp": {"key_name": "dummy", "passphrase": "", "gnupghome": str(base)},
    }


def test_symlink_protection_in_local_changes(tmp_path):
    mon = tmp_path / "mon"
    dec = tmp_path / "dec"
    sync = tmp_path / "sync"
    (sync / "encrypted_files").mkdir(parents=True)
    mon.mkdir()
    dec.mkdir()

    cfg = make_config(tmp_path)
    sm = SyncManager(cfg, SyncFolderClient(cfg), PGPWriteDummy())

    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    link = mon / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        # Filesystem may not support symlinks; skip
        return

    # Should be skipped and not raise
    sm.handle_local_change(link)

    # No encrypted file should be created
    assert not (sync / "encrypted_files" / "link.txt.gpg").exists()


def test_secure_permissions_on_decrypted_file(tmp_path):
    mon = tmp_path / "mon"
    dec = tmp_path / "dec"
    sync = tmp_path / "sync" / "encrypted_files"
    mon.mkdir()
    dec.mkdir()
    sync.mkdir(parents=True)

    cfg = make_config(tmp_path)
    sm = SyncManager(cfg, SyncFolderClient(cfg), PGPWriteDummy())

    enc = sync / "afile.txt.gpg"
    enc.write_text("encrypted")

    sm.handle_sync_folder_change(enc)

    out = Path(cfg["local"]["decrypted_path"]) / "afile.txt"
    assert out.exists()
    mode = stat.S_IMODE(os.lstat(out).st_mode)
    assert mode & 0o077 == 0, f"Permissions too permissive: {oct(mode)}"
