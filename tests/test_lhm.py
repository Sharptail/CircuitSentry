import sys
import types
import importlib
import pytest

if 'clr' not in sys.modules:
    sys.modules['clr'] = types.SimpleNamespace(AddReference=lambda path: None)

import lhm
from tests.conftest import FakeWindow


class DummySensor:
    def __init__(self, name, sensor_type, value):
        self.Name = name
        self.SensorType = sensor_type
        self.Value = value


class DummyHardware:
    def __init__(self, hardware_type, sensors):
        self.HardwareType = hardware_type
        self.Sensors = sensors
    def Update(self):
        self.updated = True


class DummyWindowHW(FakeWindow):
    def __init__(self):
        super().__init__()
        self.is_dragging = False
        self.after_args = None
    def after(self, delay, callback):
        self.after_args = (delay, callback)


def test_import_libre_hm_loads_hardware_class(monkeypatch):
    fake_hardware = type('FakeHardware', (), {})
    fake_module = types.SimpleNamespace(Hardware=fake_hardware)
    sys.modules['LibreHardwareMonitor'] = fake_module
    captured = {}
    monkeypatch.setattr(lhm.clr, 'AddReference', lambda path: captured.setdefault('path', path))
    monitor = object.__new__(lhm.HardwareMonitor)
    result = monitor.import_libre_hm()
    assert result is fake_hardware
    assert captured['path']


def test_init_libre_hm_updates_gpu_usage_label(monkeypatch):
    monitor = object.__new__(lhm.HardwareMonitor)
    monitor.handle = types.SimpleNamespace(Hardware=[
        DummyHardware('Motherboard', [
            DummySensor('GPU Core', 'Load', 35),
        ])
    ])
    window = DummyWindowHW()
    monitor.init_libre_hm(window)
    assert window.gpu_usage_label.config_values['text'] == 'GPU\n35%'
    assert window.after_args is not None


def test_hardware_monitor_init_uses_computer_and_opens(monkeypatch):
    class FakeComputer:
        def __init__(self):
            self.opened = False
        def Open(self):
            self.opened = True
    fake_hardware = types.SimpleNamespace(Computer=FakeComputer)
    sys.modules['LibreHardwareMonitor'] = types.SimpleNamespace(Hardware=fake_hardware)
    monkeypatch.setattr(lhm.utils, 'get_file', lambda filename: 'dummy.dll')
    monitor = lhm.HardwareMonitor.__new__(lhm.HardwareMonitor)
    monitor.__init__(window=None)
    assert isinstance(monitor.handle, FakeComputer)
    assert monitor.handle.opened is True


def test_init_libre_hm_updates_temperature_and_usage_labels(monkeypatch):
    monitor = object.__new__(lhm.HardwareMonitor)
    monitor.handle = types.SimpleNamespace(Hardware=[
        DummyHardware('Motherboard', [
            DummySensor('Core (Tctl/Tdie)', 'Temperature', 42),
            DummySensor('GPU Core', 'Temperature', 51),
            DummySensor('CPU Total', 'Load', 11),
        ])
    ])
    window = DummyWindowHW()
    monitor.init_libre_hm(window)
    assert window.cpu_temp_label.config_values['text'] == 'CPU\n42°'
    assert window.gpu_temp_label.config_values['text'] == 'GPU\n51°'
    assert window.cpu_usage_label.config_values['text'] == 'CPU\n11%'
    assert window.after_args is not None


def test_init_libre_hm_does_nothing_while_dragging(monkeypatch):
    monitor = object.__new__(lhm.HardwareMonitor)
    monitor.handle = types.SimpleNamespace(Hardware=[DummyHardware('Motherboard', [DummySensor('GPU Core', 'Temperature', 60)])])
    window = DummyWindowHW()
    window.is_dragging = True
    monitor.init_libre_hm(window)
    assert window.cpu_temp_label.config_values == {}
    assert window.after_args is not None
