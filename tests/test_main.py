import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
import pytest
from unittest import mock

# Patch sys.argv for CLI tests
@mock.patch("main.setup_logging")
@mock.patch("main.check_android_permissions")
@mock.patch("main.load_config")
@mock.patch("main.PGPHandler")
@mock.patch("main.SyncFolderClient")
@mock.patch("main.SyncManager")
@mock.patch("main.FileMonitor")
def test_main_entry(
    MockFileMonitor, MockSyncManager, MockODC, MockPGP, MockLoadConfig, MockCheckAndroid, MockSetupLogging, tmp_path
):
    # Prepare dummy config
    config = {
        "local": {"monitored_path": str(tmp_path), "decrypted_path": str(tmp_path)},
        "sync_folder": {"path": str(tmp_path), "encrypted_folder": "encrypted_files"},
        "pgp": {"key_name": "dummy", "passphrase": "", "gnupghome": str(tmp_path)},
        "sync": {"check_interval": 1}
    }
    MockLoadConfig.return_value = config
    sys_argv = sys.argv
    sys.argv = ["guardian-sync", "--config", "dummy.json"]
    with mock.patch("signal.pause", side_effect=SystemExit):
        import main
        try:
            main.main()
        except SystemExit:
            pass
    sys.argv = sys_argv
    assert MockFileMonitor.called
    assert MockSyncManager.called
    assert MockODC.called
    assert MockPGP.called
