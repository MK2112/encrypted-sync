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
