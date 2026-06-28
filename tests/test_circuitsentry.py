import configparser
import importlib
import os
import pytest
import runpy
import sys
import types
from constants import (
    CONFIGNAME_OPTIONS,
    CONFIGNAME_WINDOW_ALWAYS_ON_TOP,
    CONFIGNAME_WINDOW_OPEN_ON_STARTUP,
    CONFIGNAME_WINDOW_BG_IS_TRANSPARENT,
    CONFIGNAME_WINDOW_TEXT_IS_TRANSPARENT,
    DEFAULT_WINDOW_BACKGROUND,
    DEFAULT_WINDOW_OPEN_ON_STARTUP,
    DEFAULT_WINDOW_TEXT,
    DEFAULT_WINDOW_BG_IS_TRANSPARENT,
    DEFAULT_WINDOW_ALWAYS_ON_TOP,
    DEFAULT_WINDOW_TEXT_IS_TRANSPARENT,
)

if 'clr' not in sys.modules:
    sys.modules['clr'] = types.SimpleNamespace(AddReference=lambda path: None)

import circuitsentry
from tests.conftest import FakeBoolVar


class DummyMenu:
    def __init__(self):
        self.popup_calls = []
        self.released = False
    def tk_popup(self, x, y):
        self.popup_calls.append((x, y))
    def grab_release(self):
        self.released = True


class DummyEvent:
    def __init__(self, x, y, x_root=0, y_root=0):
        self.x = x
        self.y = y
        self.x_root = x_root
        self.y_root = y_root


class DummyWindow:
    def __init__(self):
        self.geometry_calls = []
    def winfo_x(self):
        return 20
    def winfo_y(self):
        return 30
    def geometry(self, value):
        self.geometry_calls.append(value)


class DummyButton:
    def __init__(self):
        self.config_values = {}
    def config(self, **kwargs):
        self.config_values.update(kwargs)


class DummyOptionsWindow:
    def __init__(self):
        self.destroyed = False
    def destroy(self):
        self.destroyed = True


class FakeTkCanvas:
    def __init__(self, master=None, **kwargs):
        self.master = master
        self.config_values = {}
    def pack(self, **kwargs):
        pass
    def rowconfigure(self, *args, **kwargs):
        pass
    def columnconfigure(self, *args, **kwargs):
        pass
    def config(self, **kwargs):
        self.config_values.update(kwargs)
    def bind(self, *args, **kwargs):
        pass


class FakeTkLabel:
    def __init__(self, master=None, **kwargs):
        self.master = master
        self.config_values = kwargs.copy()
        self.grid_kwargs = {}
        self.grid_state = None
    def grid(self, **kwargs):
        self.grid_kwargs = kwargs
        self.grid_state = 'grid'
    def bind(self, *args, **kwargs):
        pass
    def config(self, **kwargs):
        self.config_values.update(kwargs)
    def grid_forget(self):
        self.grid_state = 'forgotten'


class FakeTkMenu:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.commands = []
    def add_command(self, **kwargs):
        self.commands.append(kwargs)
    def add_separator(self):
        self.commands.append({'separator': True})
    def tk_popup(self, x, y):
        self.last_popup = (x, y)
    def grab_release(self):
        self.grab_released = True


class FakeTkBooleanVar:
    def __init__(self):
        self._value = False
    def set(self, value):
        self._value = value
    def get(self):
        return self._value


class FakeTkCheckbutton:
    def __init__(self, master=None, **kwargs):
        self.master = master
        self.kwargs = kwargs
    def grid(self, **kwargs):
        self.grid_kwargs = kwargs


class FakeTkFrame:
    def __init__(self, master=None):
        self.master = master
    def columnconfigure(self, *args, **kwargs):
        pass
    def grid(self, **kwargs):
        self.grid_kwargs = kwargs


class FakeTkButton:
    def __init__(self, master=None, **kwargs):
        self.master = master
        self.kwargs = kwargs
        self.config_values = {}
    def grid(self, **kwargs):
        self.grid_kwargs = kwargs
    def config(self, **kwargs):
        self.config_values.update(kwargs)


class FakeToplevel:
    def __init__(self, master=None):
        self.master = master
        self.protocol_handler = None
    def wm_transient(self, parent):
        self.transient_parent = parent
    def title(self, title):
        self.title_text = title
    def geometry(self, geometry):
        self.geometry_value = geometry
    def protocol(self, name, handler):
        self.protocol_handler = (name, handler)
    def destroy(self):
        self.destroyed = True


class FakeHardwareMonitor:
    def __init__(self, window):
        self.window = window
    def init_libre_hm(self, window):
        pass


class DummyStartupVar(FakeBoolVar):
    pass


def test_circuit_sentry_init_sets_up_main_interface(monkeypatch):
    def fake_tk_init(self):
        self.bind = lambda *args, **kwargs: None
        self.overrideredirect = lambda value: setattr(self, '_overrideredirect', value)
        self.attributes = lambda *args, **kwargs: setattr(self, '_attributes', (args, kwargs))
        self.withdraw = lambda: None
        self.after = lambda delay, callback: setattr(self, 'after_call', (delay, callback))
        self.update = lambda: None
    monkeypatch.setattr(circuitsentry.tk.Tk, '__init__', fake_tk_init)
    monkeypatch.setattr(circuitsentry.tk, 'Menu', FakeTkMenu)
    monkeypatch.setattr(circuitsentry.tk, 'Canvas', FakeTkCanvas)
    monkeypatch.setattr(circuitsentry.tk, 'Label', FakeTkLabel)
    monkeypatch.setattr(circuitsentry.utils, 'get_window_bg_color', lambda config: DEFAULT_WINDOW_BACKGROUND)
    monkeypatch.setattr(circuitsentry.utils, 'get_window_txt_color', lambda config: DEFAULT_WINDOW_TEXT)
    monkeypatch.setattr(circuitsentry.utils, 'generate_config', lambda window: None)
    monkeypatch.setattr(circuitsentry.utils, 'load_window_size', lambda window: None)
    monkeypatch.setattr(circuitsentry.utils, 'load_window_background', lambda window: None)
    monkeypatch.setattr(circuitsentry.lhm, 'HardwareMonitor', FakeHardwareMonitor)
    app = circuitsentry.CircuitSentry()
    assert app.options_window_opened is False
    assert isinstance(app.canvas, FakeTkCanvas)
    assert app.cpu_temp_label.config_values['text'] == 'CPU\n0°'
    assert app.gpu_usage_label.grid_state == 'grid'


def test_open_options_window_creates_option_controls(monkeypatch):
    monkeypatch.setattr(circuitsentry.tk, 'BooleanVar', FakeTkBooleanVar)
    monkeypatch.setattr(circuitsentry.tk, 'Toplevel', FakeToplevel)
    monkeypatch.setattr(circuitsentry.tk, 'Checkbutton', FakeTkCheckbutton)
    monkeypatch.setattr(circuitsentry.tk, 'Frame', FakeTkFrame)
    monkeypatch.setattr(circuitsentry.tk, 'Label', FakeTkLabel)
    monkeypatch.setattr(circuitsentry.tk, 'Button', FakeTkButton)
    monkeypatch.setattr(circuitsentry.utils, 'get_window_bg_color', lambda config: '#112233')
    monkeypatch.setattr(circuitsentry.utils, 'get_window_txt_color', lambda config: '#445566')
    monkeypatch.setattr(circuitsentry.utils, 'get_config', lambda config, name, default: default)
    window = object.__new__(circuitsentry.CircuitSentry)
    window.options_window_opened = False
    window.config = configparser.ConfigParser()
    window.config.add_section(CONFIGNAME_OPTIONS)
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_OPEN_ON_STARTUP] = DEFAULT_WINDOW_OPEN_ON_STARTUP
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_ALWAYS_ON_TOP] = DEFAULT_WINDOW_ALWAYS_ON_TOP
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_BG_IS_TRANSPARENT] = DEFAULT_WINDOW_BG_IS_TRANSPARENT
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_TEXT_IS_TRANSPARENT] = DEFAULT_WINDOW_TEXT_IS_TRANSPARENT
    window.canvas = FakeTkCanvas()
    window.round_rectangle = lambda *args, **kwargs: None
    window.close_options_window = circuitsentry.CircuitSentry.close_options_window
    circuitsentry.CircuitSentry.open_options_window(window, window)
    assert window.options_window_opened is True


def test_circuitsentry_main_guard_runs_without_exceptions(monkeypatch, tmp_path):
    fake_tk = types.ModuleType('tkinter')
    class FakeTkClass:
        def __init__(self):
            self.after_args = None
        def bind(self, *args, **kwargs):
            pass
        def overrideredirect(self, value):
            pass
        def attributes(self, *args, **kwargs):
            pass
        def withdraw(self):
            pass
        def update(self):
            pass
        def lift(self):
            pass
        def focus_force(self):
            pass
        def deiconify(self):
            pass
        def after(self, delay, callback):
            pass
        def mainloop(self):
            pass
    fake_tk.Tk = FakeTkClass
    fake_tk.Menu = FakeTkMenu
    fake_tk.Canvas = FakeTkCanvas
    fake_tk.Frame = FakeTkFrame
    fake_tk.Label = FakeTkLabel
    fake_tk.Button = FakeTkButton
    fake_tk.Checkbutton = FakeTkCheckbutton
    fake_tk.BooleanVar = FakeTkBooleanVar
    fake_tk.Toplevel = FakeToplevel
    fake_tk.W = 'W'
    fake_tk.EW = 'EW'
    fake_tk.BOTH = 'BOTH'
    fake_tk.messagebox = types.SimpleNamespace(showwarning=lambda *args, **kwargs: None, showerror=lambda *args, **kwargs: None)
    fake_tk.colorchooser = types.SimpleNamespace(askcolor=lambda title: ((0, 0, 0), '#000000'))
    fake_pystray = types.ModuleType('pystray')
    fake_pystray.Menu = FakeTkMenu
    fake_pystray.MenuItem = lambda *args, **kwargs: None
    class FakeIcon:
        def __init__(self, *args, **kwargs):
            self.menu = None
            self.title = None
            self.icon = None
        def run_detached(self):
            pass
    fake_pystray.Icon = FakeIcon
    fake_image = types.ModuleType('PIL.Image')
    fake_image.open = lambda path: 'icon'
    fake_pil = types.ModuleType('PIL')
    fake_pil.Image = fake_image
    fake_tendo = types.ModuleType('tendo')
    fake_tendo.singleton = types.SimpleNamespace(SingleInstance=lambda: None, SingleInstanceException=Exception)
    fake_lhm = types.ModuleType('lhm')
    fake_lhm.HardwareMonitor = FakeHardwareMonitor
    fake_utils = types.ModuleType('utils')
    fake_utils.get_window_bg_color = lambda config: '#000000'
    fake_utils.get_window_txt_color = lambda config: '#808080'
    fake_utils.generate_config = lambda window: None
    fake_utils.load_window_size = lambda window: None
    fake_utils.load_window_background = lambda window: None
    fake_utils.get_config = lambda config, name, default: default
    fake_utils.save_config = lambda config, name, value: None
    fake_utils.save_window_geometry_config = lambda window: None
    fake_utils.set_window_bg_color = lambda window, color: None
    fake_utils.set_window_text_color = lambda window, color, should_save=True: None
    fake_utils.set_windows_always_on_top = lambda window, value, options_window: None
    fake_utils.set_bg_transparency = lambda window, value: None
    fake_utils.set_txt_transparency = lambda window, value: None
    fake_utils.invert_color = lambda color: color
    monkeypatch.setitem(sys.modules, 'tkinter', fake_tk)
    monkeypatch.setitem(sys.modules, 'tkinter.colorchooser', fake_tk.colorchooser)
    monkeypatch.setitem(sys.modules, 'tkinter.messagebox', fake_tk.messagebox)
    monkeypatch.setitem(sys.modules, 'pystray', fake_pystray)
    monkeypatch.setitem(sys.modules, 'PIL', fake_pil)
    monkeypatch.setitem(sys.modules, 'PIL.Image', fake_image)
    monkeypatch.setitem(sys.modules, 'tendo', fake_tendo)
    monkeypatch.setitem(sys.modules, 'lhm', fake_lhm)
    monkeypatch.setitem(sys.modules, 'utils', fake_utils)
    fake_ctypes = types.ModuleType('ctypes')
    fake_ctypes.windll = types.SimpleNamespace(shell32=types.SimpleNamespace(IsUserAnAdmin=lambda: True))
    monkeypatch.setitem(sys.modules, 'ctypes', fake_ctypes)
    original_argv = sys.argv.copy()
    sys.argv = [os.path.abspath('circuitsentry.py')]
    module_path = os.path.abspath('circuitsentry.py')
    try:
        module_globals = runpy.run_path(module_path, run_name='__main__')
        resource_path = module_globals['resource_path']
        show_app = module_globals['show_app']
        init_sys_tray = module_globals['init_sys_tray']
        result_path = resource_path('assets/circuitsentry.ico')
        assert result_path.replace('\\', '/').endswith('assets/circuitsentry.ico')

        class FakeApp:
            def __init__(self):
                self.config = configparser.ConfigParser()
                self._attributes = []
                self.deiconified = False
                self.updated = False
                self.lifted = False
                self.focused = False
            def deiconify(self):
                self.deiconified = True
            def update(self):
                self.updated = True
            def lift(self):
                self.lifted = True
            def focus_force(self):
                self.focused = True
            def attributes(self, *args, **kwargs):
                self._attributes.append((args, kwargs))
            def mainloop(self):
                pass
        app = FakeApp()
        show_app(app)
        assert app.deiconified is True
        assert app.updated is True
        assert app.lifted is True
        assert app.focused is True
        init_sys_tray(app)
    finally:
        sys.argv = original_argv


def test_circuit_sentry_instance_admin_exception(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    fake_shell = types.SimpleNamespace(IsUserAnAdmin=lambda: (_ for _ in ()).throw(Exception('error')))
    monkeypatch.setattr(circuitsentry.ctypes, 'windll', types.SimpleNamespace(shell32=fake_shell))
    assert circuitsentry.CircuitSentry.is_admin(window) is False


def test_set_run_on_startup_deletes_startup_when_disabled(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    window.config = configparser.ConfigParser()
    window.config.add_section(CONFIGNAME_OPTIONS)
    window.delete_startup_task = lambda: setattr(window, 'deleted', True)
    monkeypatch.setattr(circuitsentry.utils, 'save_config', lambda cfg, name, value: setattr(window, 'saved', (name, value)))
    is_run_on_startup = FakeBoolVar(False)
    window.set_run_on_startup(is_run_on_startup)
    assert getattr(window, 'deleted', False) is True
    assert window.saved[0] == CONFIGNAME_WINDOW_OPEN_ON_STARTUP


def test_open_options_window_early_return_when_already_open():
    window = object.__new__(circuitsentry.CircuitSentry)
    window.options_window_opened = True
    circuitsentry.CircuitSentry.open_options_window(window, window)


def test_relaunch_as_admin_uses_shell_execute(monkeypatch):
    monkeypatch.setattr(circuitsentry.sys, 'frozen', False, raising=False)
    fake_shell = types.SimpleNamespace(ShellExecuteW=lambda *args: 33)
    monkeypatch.setattr(circuitsentry.ctypes, 'windll', types.SimpleNamespace(shell32=fake_shell))
    result = circuitsentry.relaunch_as_admin()
    assert result is True


def test_relaunch_as_admin_when_frozen(monkeypatch):
    monkeypatch.setattr(circuitsentry.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(circuitsentry.sys, 'executable', 'fake.exe', raising=False)
    fake_shell = types.SimpleNamespace(ShellExecuteW=lambda *args: 33)
    monkeypatch.setattr(circuitsentry.ctypes, 'windll', types.SimpleNamespace(shell32=fake_shell))
    assert circuitsentry.relaunch_as_admin() is True


def test_is_admin_returns_false_on_exception(monkeypatch):
    fake_shell = types.SimpleNamespace(IsUserAnAdmin=lambda: (_ for _ in ()).throw(Exception('fail')))
    monkeypatch.setattr(circuitsentry.ctypes, 'windll', types.SimpleNamespace(shell32=fake_shell))
    assert circuitsentry.is_admin() is False


def test_main_guard_shows_error_when_not_admin(monkeypatch):
    fake_tk = types.ModuleType('tkinter')
    fake_tk.messagebox = types.SimpleNamespace(showerror=lambda *args, **kwargs: None)
    fake_tk.colorchooser = types.SimpleNamespace(askcolor=lambda title: ((0, 0, 0), '#000000'))
    class FakeTkRoot:
        def __init__(self, *args, **kwargs):
            pass
    fake_tk.Tk = FakeTkRoot
    fake_tk.Menu = lambda *args, **kwargs: None
    fake_tk.Canvas = lambda *args, **kwargs: None
    fake_tk.Frame = lambda *args, **kwargs: None
    fake_tk.Label = lambda *args, **kwargs: None
    fake_tk.Button = lambda *args, **kwargs: None
    fake_tk.Checkbutton = lambda *args, **kwargs: None
    fake_tk.BooleanVar = lambda *args, **kwargs: None
    fake_tk.Toplevel = lambda *args, **kwargs: None
    fake_tk.W = 'W'
    fake_tk.EW = 'EW'
    fake_tk.BOTH = 'BOTH'
    fake_pystray = types.ModuleType('pystray')
    fake_pystray.Menu = lambda *args, **kwargs: None
    fake_pystray.MenuItem = lambda *args, **kwargs: None
    fake_pystray.Icon = lambda *args, **kwargs: None
    fake_pil = types.ModuleType('PIL')
    fake_image = types.ModuleType('PIL.Image')
    fake_image.open = lambda path: None
    fake_pil.Image = fake_image
    fake_tendo = types.ModuleType('tendo')
    fake_tendo.singleton = types.SimpleNamespace(SingleInstance=lambda: None, SingleInstanceException=Exception)
    fake_lhm = types.ModuleType('lhm')
    fake_lhm.HardwareMonitor = lambda *args, **kwargs: None
    fake_ctypes = types.ModuleType('ctypes')
    fake_ctypes.windll = types.SimpleNamespace(shell32=types.SimpleNamespace(IsUserAnAdmin=lambda: 0, ShellExecuteW=lambda *args: 0))
    monkeypatch.setitem(sys.modules, 'tkinter', fake_tk)
    monkeypatch.setitem(sys.modules, 'tkinter.messagebox', fake_tk.messagebox)
    monkeypatch.setitem(sys.modules, 'tkinter.colorchooser', fake_tk.colorchooser)
    monkeypatch.setitem(sys.modules, 'pystray', fake_pystray)
    monkeypatch.setitem(sys.modules, 'PIL', fake_pil)
    monkeypatch.setitem(sys.modules, 'PIL.Image', fake_image)
    monkeypatch.setitem(sys.modules, 'tendo', fake_tendo)
    monkeypatch.setitem(sys.modules, 'lhm', fake_lhm)
    monkeypatch.setitem(sys.modules, 'ctypes', fake_ctypes)
    monkeypatch.setitem(sys.modules, 'utils', circuitsentry.utils)
    shown = {}
    fake_tk.messagebox.showerror = lambda title, message: shown.setdefault('shown', True)
    monkeypatch.setattr(sys, 'argv', [os.path.abspath('circuitsentry.py')])
    monkeypatch.setattr(sys, 'exit', lambda code=0: (_ for _ in ()).throw(SystemExit(code)))
    with pytest.raises(SystemExit):
        runpy.run_path(os.path.abspath('circuitsentry.py'), run_name='__main__')
    assert shown.get('shown', False) is True


def test_main_guard_relaunches_and_exits_when_not_admin(monkeypatch):
    fake_tk = types.ModuleType('tkinter')
    fake_tk.messagebox = types.SimpleNamespace(showerror=lambda *args, **kwargs: None)
    fake_tk.colorchooser = types.SimpleNamespace(askcolor=lambda title: ((0, 0, 0), '#000000'))
    class FakeTkRoot:
        def __init__(self, *args, **kwargs):
            pass
    fake_tk.Tk = FakeTkRoot
    fake_tk.Menu = lambda *args, **kwargs: None
    fake_tk.Canvas = lambda *args, **kwargs: None
    fake_tk.Frame = lambda *args, **kwargs: None
    fake_tk.Label = lambda *args, **kwargs: None
    fake_tk.Button = lambda *args, **kwargs: None
    fake_tk.Checkbutton = lambda *args, **kwargs: None
    fake_tk.BooleanVar = lambda *args, **kwargs: None
    fake_tk.Toplevel = lambda *args, **kwargs: None
    fake_tk.W = 'W'
    fake_tk.EW = 'EW'
    fake_tk.BOTH = 'BOTH'
    fake_pystray = types.ModuleType('pystray')
    fake_pystray.Menu = lambda *args, **kwargs: None
    fake_pystray.MenuItem = lambda *args, **kwargs: None
    fake_pystray.Icon = lambda *args, **kwargs: None
    fake_pil = types.ModuleType('PIL')
    fake_image = types.ModuleType('PIL.Image')
    fake_image.open = lambda path: None
    fake_pil.Image = fake_image
    fake_tendo = types.ModuleType('tendo')
    fake_tendo.singleton = types.SimpleNamespace(SingleInstance=lambda: None, SingleInstanceException=Exception)
    fake_lhm = types.ModuleType('lhm')
    fake_lhm.HardwareMonitor = lambda *args, **kwargs: None
    fake_ctypes = types.ModuleType('ctypes')
    fake_ctypes.windll = types.SimpleNamespace(shell32=types.SimpleNamespace(IsUserAnAdmin=lambda: 0, ShellExecuteW=lambda *args: 33))
    monkeypatch.setitem(sys.modules, 'tkinter', fake_tk)
    monkeypatch.setitem(sys.modules, 'tkinter.messagebox', fake_tk.messagebox)
    monkeypatch.setitem(sys.modules, 'tkinter.colorchooser', fake_tk.colorchooser)
    monkeypatch.setitem(sys.modules, 'pystray', fake_pystray)
    monkeypatch.setitem(sys.modules, 'PIL', fake_pil)
    monkeypatch.setitem(sys.modules, 'PIL.Image', fake_image)
    monkeypatch.setitem(sys.modules, 'tendo', fake_tendo)
    monkeypatch.setitem(sys.modules, 'lhm', fake_lhm)
    monkeypatch.setitem(sys.modules, 'ctypes', fake_ctypes)
    monkeypatch.setitem(sys.modules, 'utils', circuitsentry.utils)
    monkeypatch.setattr(sys, 'argv', [os.path.abspath('circuitsentry.py')])
    monkeypatch.setattr(sys, 'exit', lambda code=0: (_ for _ in ()).throw(SystemExit(code)))
    with pytest.raises(SystemExit):
        runpy.run_path(os.path.abspath('circuitsentry.py'), run_name='__main__')


def test_main_guard_blocks_duplicate_instance(monkeypatch):
    fake_tk = types.ModuleType('tkinter')
    fake_tk.messagebox = types.SimpleNamespace(showerror=lambda *args, **kwargs: None)
    fake_tk.colorchooser = types.SimpleNamespace(askcolor=lambda title: ((0, 0, 0), '#000000'))
    class FakeTkRoot:
        def __init__(self, *args, **kwargs):
            pass
    fake_tk.Tk = FakeTkRoot
    fake_tk.Menu = lambda *args, **kwargs: None
    fake_tk.Canvas = lambda *args, **kwargs: None
    fake_tk.Frame = lambda *args, **kwargs: None
    fake_tk.Label = lambda *args, **kwargs: None
    fake_tk.Button = lambda *args, **kwargs: None
    fake_tk.Checkbutton = lambda *args, **kwargs: None
    fake_tk.BooleanVar = lambda *args, **kwargs: None
    fake_tk.Toplevel = lambda *args, **kwargs: None
    fake_tk.W = 'W'
    fake_tk.EW = 'EW'
    fake_tk.BOTH = 'BOTH'
    fake_pystray = types.ModuleType('pystray')
    fake_pystray.Menu = lambda *args, **kwargs: None
    fake_pystray.MenuItem = lambda *args, **kwargs: None
    fake_pystray.Icon = lambda *args, **kwargs: None
    fake_pil = types.ModuleType('PIL')
    fake_image = types.ModuleType('PIL.Image')
    fake_image.open = lambda path: None
    fake_pil.Image = fake_image
    fake_tendo = types.ModuleType('tendo')
    fake_tendo.singleton = types.SimpleNamespace(SingleInstance=lambda: (_ for _ in ()).throw(Exception('already running')), SingleInstanceException=Exception)
    fake_lhm = types.ModuleType('lhm')
    fake_lhm.HardwareMonitor = lambda *args, **kwargs: None
    fake_ctypes = types.ModuleType('ctypes')
    fake_ctypes.windll = types.SimpleNamespace(shell32=types.SimpleNamespace(IsUserAnAdmin=lambda: 1, ShellExecuteW=lambda *args: 33))
    monkeypatch.setitem(sys.modules, 'tkinter', fake_tk)
    monkeypatch.setitem(sys.modules, 'tkinter.messagebox', fake_tk.messagebox)
    monkeypatch.setitem(sys.modules, 'tkinter.colorchooser', fake_tk.colorchooser)
    monkeypatch.setitem(sys.modules, 'pystray', fake_pystray)
    monkeypatch.setitem(sys.modules, 'PIL', fake_pil)
    monkeypatch.setitem(sys.modules, 'PIL.Image', fake_image)
    monkeypatch.setitem(sys.modules, 'tendo', fake_tendo)
    monkeypatch.setitem(sys.modules, 'lhm', fake_lhm)
    monkeypatch.setitem(sys.modules, 'ctypes', fake_ctypes)
    monkeypatch.setitem(sys.modules, 'utils', circuitsentry.utils)
    shown = {}
    fake_tk.messagebox.showerror = lambda title, message: shown.setdefault('shown', True)
    monkeypatch.setattr(sys, 'argv', [os.path.abspath('circuitsentry.py')])
    monkeypatch.setattr(sys, 'exit', lambda code=0: (_ for _ in ()).throw(SystemExit(code)))
    with pytest.raises(SystemExit):
        runpy.run_path(os.path.abspath('circuitsentry.py'), run_name='__main__')
    assert shown.get('shown', False) is True


def test_round_rectangle_creates_polygon(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    window.config = configparser.ConfigParser()
    window.config.add_section(CONFIGNAME_OPTIONS)
    class FakeCanvas:
        def __init__(self):
            self.deleted = []
        def delete(self, tag):
            self.deleted.append(tag)
        def create_polygon(self, points, **kwargs):
            setattr(window, 'polygon_args', (points, kwargs))
    fake_canvas = FakeCanvas()
    monkeypatch.setattr(circuitsentry.utils, 'get_window_bg_color', lambda config: '#112233')
    circuitsentry.CircuitSentry.round_rectangle(window, fake_canvas, {'width': '100', 'height': '60'})
    points, kwargs = window.polygon_args
    assert kwargs['fill'] == '#112233'
    assert len(points) > 0


def test_open_menu_calls_grab_release():
    window = object.__new__(circuitsentry.CircuitSentry)
    menu = DummyMenu()
    event = DummyEvent(10, 20, x_root=50, y_root=60)
    window.open_menu(event, menu)
    assert menu.popup_calls == [(50, 60)]
    assert menu.released is True


def test_dragging_started_and_dragging_change_geometry():
    window = object.__new__(circuitsentry.CircuitSentry)
    event = DummyEvent(2, 4)
    window.dragging_started(event)
    assert window.is_dragging is True
    event2 = DummyEvent(12, 24)
    window.winfo_x = lambda: 100
    window.winfo_y = lambda: 200
    window.geometry_calls = []
    window.geometry = lambda value: window.geometry_calls.append(value)
    window.dragging(event2)
    assert window.geometry_calls


def test_dragging_stopped_calls_save_geometry(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    monkeypatch.setattr(circuitsentry.utils, 'save_window_geometry_config', lambda win: setattr(win, 'saved', True))
    window.dragging_stopped()
    assert getattr(window, 'saved', False) is True


def test_circuit_sentry_instance_is_admin_method(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    fake_shell = types.SimpleNamespace(IsUserAnAdmin=lambda: 42)
    monkeypatch.setattr(circuitsentry.ctypes, 'windll', types.SimpleNamespace(shell32=fake_shell))
    assert circuitsentry.CircuitSentry.is_admin(window) == 42


def test_create_startup_task_returns_true_when_successful(monkeypatch):
    monkeypatch.setattr(circuitsentry.sys, 'frozen', False, raising=False)
    monkeypatch.setattr(circuitsentry.subprocess, 'run', lambda cmd, shell, capture_output, text: types.SimpleNamespace(returncode=0))
    window = object.__new__(circuitsentry.CircuitSentry)
    assert window.create_startup_task() is True


def test_create_startup_task_when_frozen_uses_exe_path(monkeypatch):
    monkeypatch.setattr(circuitsentry.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(circuitsentry.sys, 'executable', 'C:\\fake\\path.exe', raising=False)
    monkeypatch.setattr(circuitsentry.utils, 'get_file', lambda filename: 'C:\\fake\\CircuitSentry.exe')
    monkeypatch.setattr(circuitsentry.subprocess, 'run', lambda cmd, shell, capture_output, text: types.SimpleNamespace(returncode=0))
    window = object.__new__(circuitsentry.CircuitSentry)
    assert window.create_startup_task() is True


def test_delete_startup_task_invokes_subprocess(monkeypatch):
    called = {}
    def fake_run(cmd, shell, capture_output, text):
        called['cmd'] = cmd
        return types.SimpleNamespace(returncode=0)
    monkeypatch.setattr(circuitsentry.subprocess, 'run', fake_run)
    window = object.__new__(circuitsentry.CircuitSentry)
    window.delete_startup_task()
    assert 'schtasks /Delete' in called['cmd']


def test_set_run_on_startup_warns_when_not_admin(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    window.config = configparser.ConfigParser()
    window.config.add_section(CONFIGNAME_OPTIONS)
    window.is_admin = lambda: False
    is_run_on_startup = FakeBoolVar(True)
    captured = {}
    monkeypatch.setattr(circuitsentry.mb, 'showwarning', lambda title, message: captured.setdefault('shown', True))
    window.set_run_on_startup(is_run_on_startup)
    assert captured['shown'] is True
    assert is_run_on_startup.get() is False


def test_set_run_on_startup_creates_task_and_saves(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    window.config = configparser.ConfigParser()
    window.config.add_section(CONFIGNAME_OPTIONS)
    window.is_admin = lambda: True
    window.create_startup_task = lambda: True
    saved = {}
    monkeypatch.setattr(circuitsentry.utils, 'save_config', lambda cfg, name, value: saved.setdefault('saved', (name, value)))
    is_run_on_startup = FakeBoolVar(True)
    window.set_run_on_startup(is_run_on_startup)
    assert saved['saved'][0] == CONFIGNAME_WINDOW_OPEN_ON_STARTUP


def test_set_run_on_startup_fails_to_create_task(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    window.config = configparser.ConfigParser()
    window.config.add_section(CONFIGNAME_OPTIONS)
    window.is_admin = lambda: True
    window.create_startup_task = lambda: False
    is_run_on_startup = FakeBoolVar(True)
    shown = {}
    monkeypatch.setattr(circuitsentry.mb, 'showerror', lambda title, message: shown.setdefault('shown', True))
    window.set_run_on_startup(is_run_on_startup)
    assert shown['shown'] is True
    assert is_run_on_startup.get() is False


def test_close_options_window_destroys_window():
    window = object.__new__(circuitsentry.CircuitSentry)
    window.options_window_opened = True
    options_window = DummyOptionsWindow()
    circuitsentry.CircuitSentry.close_options_window(window, options_window)
    assert window.options_window_opened is False
    assert options_window.destroyed is True


def test_bg_color_picker_sets_color(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    button = DummyButton()
    cb = FakeBoolVar(True)
    monkeypatch.setattr(circuitsentry, 'askcolor', lambda title: ((0, 0, 0), '#334455'))
    monkeypatch.setattr(circuitsentry.utils, 'set_window_bg_color', lambda win, color: setattr(win, 'bg_color', color))
    window.bg_color_picker(button, cb)
    assert window.bg_color == '#334455'
    assert button.config_values['bg'] == '#334455'
    assert cb.get() == 0


def test_txt_color_picker_sets_text_color(monkeypatch):
    window = object.__new__(circuitsentry.CircuitSentry)
    button = DummyButton()
    cb = FakeBoolVar(True)
    monkeypatch.setattr(circuitsentry, 'askcolor', lambda title: ((0, 0, 0), '#445566'))
    monkeypatch.setattr(circuitsentry.utils, 'set_window_text_color', lambda win, color: setattr(win, 'text_color', color))
    window.txt_color_picker(button, cb)
    assert window.text_color == '#445566'
    assert button.config_values['bg'] == '#445566'
    assert cb.get() == 0
