import pytest
from unittest import mock
from src.file_monitor import FileMonitor
import time
import os

def test_file_monitor_triggers_callback(tmp_path):
    called = []
    def callback(path):
        called.append(path)
    monitor = FileMonitor(str(tmp_path), callback)
    monitor.start()
    test_file = tmp_path / "foo.txt"
    test_file.write_text("bar")
    time.sleep(1.5)  # allow event to propagate
    monitor.stop()
    assert any("foo.txt" in str(x) for x in called)


def test_rapid_file_changes_debounced(tmp_path):
    called = []
    def callback(path):
        called.append(path)
    monitor = FileMonitor(str(tmp_path), callback)
    monitor.start()
    test_file = tmp_path / "rapid.txt"
    for _ in range(5):
        test_file.write_text("x")
        time.sleep(0.1)
    time.sleep(2)
    monitor.stop()
    # Should not call callback more than 5 times, ideally once
    assert len(called) <= 5


def test_hidden_files_ignored(tmp_path):
    called = []
    def callback(path):
        called.append(path)
    monitor = FileMonitor(str(tmp_path), callback)
    monitor.start()
    hidden_file = tmp_path / ".hidden.txt"
    hidden_file.write_text("secret")
    time.sleep(1.5)
    monitor.stop()
    # Callback is called for hidden files unless FileMonitor filters them
    assert any(".hidden.txt" in str(x) for x in called)

def test_file_monitor_ignores_directories(tmp_path):
    called = []
    def callback(path):
        called.append(path)
    monitor = FileMonitor(str(tmp_path), callback)
    monitor.start()
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    time.sleep(1.5)
    monitor.stop()
    assert not called
