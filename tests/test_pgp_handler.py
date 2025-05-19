import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
import pytest
from unittest import mock
from src.pgp_handler import PGPHandler

class DummyGPG:
    def __init__(self, *a, **kw):
        self.encrypt_file_called = False
        self.decrypt_file_called = False
        self.list_keys = lambda priv: [{"uids": ["dummy-key"]}]
    def encrypt_file(self, f, recipients, output, always_trust):
        self.encrypt_file_called = True
        class Status:
            ok = True
            status = "encryption ok"
            stderr = None
        return Status()
    def decrypt_file(self, f, passphrase, output):
        self.decrypt_file_called = True
        class Status:
            ok = True
            status = "decryption ok"
            stderr = None
        return Status()

@mock.patch("src.pgp_handler.gnupg.GPG", new=DummyGPG)
def test_encrypt_file_success(dummy_config, tmp_path):
    handler = PGPHandler(dummy_config)
    test_file = tmp_path / "test.txt"
    test_file.write_text("secret")
    out = handler.encrypt_file(str(test_file))
    assert out.endswith(".gpg")
    assert handler.gpg.encrypt_file_called

@mock.patch("src.pgp_handler.gnupg.GPG", new=DummyGPG)
def test_decrypt_file_success(dummy_config, tmp_path):
    handler = PGPHandler(dummy_config)
    enc_file = tmp_path / "secret.txt.gpg"
    enc_file.write_bytes(b"dummy")
    out = handler.decrypt_file(str(enc_file))
    assert str(out).endswith("secret.txt")
    assert handler.gpg.decrypt_file_called

def test_missing_key_raises(dummy_config):
    class NoKeyGPG:
        def __init__(self, *a, **kw):
            pass
        def list_keys(self, priv):
            return []
    with mock.patch("src.pgp_handler.gnupg.GPG", new=NoKeyGPG):
        with mock.patch("subprocess.run") as m:
            m.return_value.returncode = 0
            m.return_value.stdout = "gpg (GnuPG) 2.2.0\n"
            with pytest.raises(ValueError, match="PGP key 'dummy-key' not found"):
                PGPHandler(dummy_config)


@mock.patch("src.pgp_handler.gnupg.GPG")
def test_encrypt_invalid_file(MockGPG, dummy_config, tmp_path):
    MockGPG.return_value.list_keys.return_value = [{"uids": ["dummy-key"]}]
    handler = PGPHandler(dummy_config)
    with pytest.raises(FileNotFoundError):
        handler.encrypt_file(str(tmp_path / "doesnotexist.txt"))


@mock.patch("src.pgp_handler.gnupg.GPG")
def test_decrypt_invalid_file(MockGPG, dummy_config, tmp_path):
    MockGPG.return_value.list_keys.return_value = [{"uids": ["dummy-key"]}]
    handler = PGPHandler(dummy_config)
    with pytest.raises(FileNotFoundError):
        handler.decrypt_file(str(tmp_path / "doesnotexist.txt.gpg"))


@mock.patch("src.pgp_handler.gnupg.GPG")
def test_missing_passphrase_prompts(MockGPG, dummy_config, tmp_path, monkeypatch):
    MockGPG.return_value.list_keys.return_value = [{"uids": ["dummy-key"]}]
    from src.pgp_handler import PGPHandler
    handler = PGPHandler(dummy_config)
    test_file = tmp_path / "test.txt"
    test_file.write_text("secret")
    monkeypatch.setattr("getpass.getpass", lambda prompt: "dummy-pass")
    handler.passphrase = None
    # Should not raise, will use dummy-pass
    handler.encrypt_file(str(test_file))
