import configparser
import os
from constants import *
import utils

from tests.conftest import FakeBoolVar, FakeWindow


def test_get_file_when_not_frozen_returns_script_path(monkeypatch, tmp_path):
    monkeypatch.setattr(utils.sys, 'frozen', False, raising=False)
    path = utils.get_file('example.txt')
    assert path.endswith('example.txt')
    assert os.path.isabs(path)


def test_config_exists_depends_on_filesystem(monkeypatch):
    monkeypatch.setattr(utils.os.path, 'isfile', lambda path: True)
    assert utils.config_exists() is True
    monkeypatch.setattr(utils.os.path, 'isfile', lambda path: False)
    assert utils.config_exists() is False


def test_get_file_when_frozen_returns_executable_path(monkeypatch, tmp_path):
    monkeypatch.setattr(utils.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(utils.sys, 'executable', str(tmp_path / 'fake.exe'), raising=False)
    path = utils.get_file('example.txt')
    assert path == str(tmp_path / 'example.txt')


def test_generate_config_skips_when_config_exists(monkeypatch):
    monkeypatch.setattr(utils, 'config_exists', lambda: True)
    window = type('W', (), {'config': configparser.ConfigParser()})()
    utils.generate_config(window)


def test_generate_config_writes_defaults(tmp_path, monkeypatch):
    config_file = tmp_path / 'circuitsentry.conf'
    monkeypatch.setattr(utils, 'get_file', lambda filename: str(config_file))
    window = type('Window', (), {'config': configparser.ConfigParser()})()
    utils.generate_config(window)
    assert config_file.exists()
    config = configparser.ConfigParser()
    config.read(config_file)
    assert config.has_section(CONFIGNAME_OPTIONS)
    assert config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_WIDTH] == DEFAULT_WINDOW_WIDTH


def test_save_and_get_config_store_values(tmp_path, monkeypatch):
    config_file = tmp_path / 'circuitsentry.conf'
    monkeypatch.setattr(utils, 'get_file', lambda filename: str(config_file))
    config = configparser.ConfigParser()
    config.add_section(CONFIGNAME_OPTIONS)
    utils.save_config(config, CONFIGNAME_WINDOW_WIDTH, '300')
    assert config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_WIDTH] == '300'
    read_config = configparser.ConfigParser()
    read_config.add_section(CONFIGNAME_OPTIONS)
    assert utils.get_config(read_config, CONFIGNAME_WINDOW_WIDTH, DEFAULT_WINDOW_WIDTH) == '300'


def test_save_config_creates_options_section(tmp_path, monkeypatch):
    config_file = tmp_path / 'circuitsentry.conf'
    monkeypatch.setattr(utils, 'get_file', lambda filename: str(config_file))
    config = configparser.ConfigParser()
    utils.save_config(config, CONFIGNAME_WINDOW_WIDTH, '400')
    assert config.has_section(CONFIGNAME_OPTIONS)
    assert config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_WIDTH] == '400'


def test_get_window_geometry_as_json_returns_nonexpanded_when_config_exists(monkeypatch):
    monkeypatch.setattr(utils, 'config_exists', lambda: True)
    monkeypatch.setattr(utils, 'get_config_bool', lambda config, name, default: False)
    monkeypatch.setattr(utils, 'get_config', lambda config, name, default: default)
    json = utils.get_window_geometry_as_json(configparser.ConfigParser())
    assert json['width'] == DEFAULT_WINDOW_WIDTH
    assert json['height'] == DEFAULT_WINDOW_HEIGHT


def test_get_config_writes_default_when_missing(tmp_path, monkeypatch):
    config_file = tmp_path / 'circuitsentry.conf'
    monkeypatch.setattr(utils, 'get_file', lambda filename: str(config_file))
    config = configparser.ConfigParser()
    config.add_section(CONFIGNAME_OPTIONS)
    assert utils.get_config(config, 'MissingOption', 'fallback') == 'fallback'
    config.read(config_file)
    assert config[CONFIGNAME_OPTIONS]['MissingOption'] == 'fallback'


def test_get_config_bool_returns_boolean_and_saves_default(tmp_path, monkeypatch):
    config_file = tmp_path / 'circuitsentry.conf'
    monkeypatch.setattr(utils, 'get_file', lambda filename: str(config_file))
    config = configparser.ConfigParser()
    config.add_section(CONFIGNAME_OPTIONS)
    assert utils.get_config_bool(config, 'MissingBool', 'True') == 'True'
    config.read(config_file)
    assert config[CONFIGNAME_OPTIONS]['MissingBool'] == 'True'


def test_save_window_geometry_config_saved_expanded_and_normal(tmp_path, monkeypatch):
    config_file = tmp_path / 'circuitsentry.conf'
    monkeypatch.setattr(utils, 'get_file', lambda filename: str(config_file))
    window = FakeWindow()
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_IS_EXPANDED] = 'True'
    utils.save_window_geometry_config(window)
    config = configparser.ConfigParser()
    config.read(config_file)
    assert config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_EXPANDED_WIDTH] == '100'
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_IS_EXPANDED] = 'False'
    utils.save_window_geometry_config(window)
    config.read(config_file)
    assert config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_WIDTH] == '100'


def test_get_window_geometry_as_json_returns_defaults_when_no_config(monkeypatch):
    monkeypatch.setattr(utils, 'config_exists', lambda: False)
    config = configparser.ConfigParser()
    json = utils.get_window_geometry_as_json(config)
    assert json['width'] == DEFAULT_WINDOW_WIDTH
    assert json['height'] == DEFAULT_WINDOW_HEIGHT


def test_get_window_dimensions_as_geometry_formats_values(monkeypatch):
    monkeypatch.setattr(utils, 'get_window_geometry_as_json', lambda config: {'width': '10', 'height': '20', 'x': '1', 'y': '2'})
    assert utils.get_window_dimensions_as_geometry(configparser.ConfigParser()) == '10x20+1+2'


def test_load_window_size_hides_or_shows_labels(monkeypatch):
    window = FakeWindow()
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_IS_EXPANDED] = 'False'
    monkeypatch.setattr(utils, 'get_window_geometry_as_json', lambda config: {'width': '100', 'height': '200', 'x': '0', 'y': '0'})
    monkeypatch.setattr(utils, 'get_window_dimensions_as_geometry', lambda config: '100x200+0+0')
    utils.load_window_size(window)
    assert window.cpu_usage_label.grid_state == 'forgotten'
    assert window.gpu_usage_label.grid_state == 'forgotten'
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_IS_EXPANDED] = 'True'
    utils.load_window_size(window)
    assert window.cpu_usage_label.grid_state == 'grid'
    assert window.gpu_usage_label.grid_state == 'grid'


def test_load_window_background_applies_transparency(monkeypatch):
    window = FakeWindow()
    monkeypatch.setattr(utils, 'config_exists', lambda: True)
    monkeypatch.setattr(utils, 'get_config', lambda config, name, default: '#123456')
    monkeypatch.setattr(utils, 'get_config_bool', lambda config, name, default: True)
    monkeypatch.setattr(utils, 'invert_color', lambda color: '#FFFFFF')
    utils.load_window_background(window)
    assert window.wm_attributes_calls[-1] == ('-transparentcolor', '#123456')
    assert window.canvas.config_values['bg'] == '#123456'


def test_load_window_background_uses_default_when_missing_config(monkeypatch):
    window = FakeWindow()
    monkeypatch.setattr(utils, 'config_exists', lambda: False)
    utils.load_window_background(window)
    assert window.wm_attributes_calls[-1] == ('-transparentcolor', DEFAULT_WINDOW_BACKGROUND)


def test_load_window_background_applies_nontransparent_background(monkeypatch):
    window = FakeWindow()
    monkeypatch.setattr(utils, 'config_exists', lambda: True)
    monkeypatch.setattr(utils, 'get_config', lambda config, name, default: '#123456')
    monkeypatch.setattr(utils, 'get_config_bool', lambda config, name, default: False)
    monkeypatch.setattr(utils, 'invert_color', lambda color: '#FFFFFF')
    utils.load_window_background(window)
    assert window.wm_attributes_calls[-1] == ('-transparentcolor', '#FFFFFF')
    assert window.canvas.config_values['bg'] == '#FFFFFF'


def test_set_txt_transparency_calls_set_window_text_color_when_disabled(monkeypatch):
    window = FakeWindow()
    txt_transparent_cb_value = FakeBoolVar(False)
    monkeypatch.setattr(utils, 'save_config', lambda config, name, value: None)
    called = {}
    def fake_set_window_text_color(win, color, should_save=True):
        called['args'] = (win, color, should_save)
    monkeypatch.setattr(utils, 'set_window_text_color', fake_set_window_text_color)
    monkeypatch.setattr(utils, 'get_window_txt_color', lambda config: '#abcdef')
    utils.set_txt_transparency(window, txt_transparent_cb_value)
    assert called['args'][2] is True


def test_get_window_txt_color_returns_default_when_no_config(monkeypatch):
    monkeypatch.setattr(utils, 'config_exists', lambda: False)
    assert utils.get_window_txt_color(configparser.ConfigParser()) == DEFAULT_WINDOW_BACKGROUND


def test_get_window_bg_color_returns_default_when_no_config(monkeypatch):
    monkeypatch.setattr(utils, 'config_exists', lambda: False)
    assert utils.get_window_bg_color(configparser.ConfigParser()) == DEFAULT_WINDOW_BACKGROUND


def test_get_window_bg_color_returns_config_value_when_exists(monkeypatch):
    monkeypatch.setattr(utils, 'config_exists', lambda: True)
    monkeypatch.setattr(utils, 'get_config', lambda config, name, default: '#654321')
    assert utils.get_window_bg_color(configparser.ConfigParser()) == '#654321'


def test_get_window_txt_color_returns_config_value_when_not_transparent(monkeypatch):
    monkeypatch.setattr(utils, 'config_exists', lambda: True)
    monkeypatch.setattr(utils, 'get_config_bool', lambda config, name, default: False)
    monkeypatch.setattr(utils, 'get_config', lambda config, name, default: '#112233')
    assert utils.get_window_txt_color(configparser.ConfigParser()) == '#112233'


def test_set_bg_transparency_calls_save_and_load(monkeypatch):
    window = FakeWindow()
    bg_transparent_cb_value = FakeBoolVar(True)
    captured = {}
    monkeypatch.setattr(utils, 'save_config', lambda config, name, value: captured.setdefault('saved', (name, value)))
    monkeypatch.setattr(utils, 'load_window_background', lambda win: captured.setdefault('loaded', True))
    utils.set_bg_transparency(window, bg_transparent_cb_value)
    assert captured['saved'][0] == CONFIGNAME_WINDOW_BG_IS_TRANSPARENT
    assert captured['loaded'] is True


def test_toggle_window_expanded_switches_state_and_reloads(monkeypatch):
    window = FakeWindow()
    bg_transparent_cb_value = FakeBoolVar(True)
    captured = {}
    monkeypatch.setattr(utils, 'save_config', lambda config, name, value: captured.setdefault('saved', (name, value)))
    monkeypatch.setattr(utils, 'load_window_background', lambda win: captured.setdefault('loaded', True))
    utils.set_bg_transparency(window, bg_transparent_cb_value)
    assert captured['saved'][0] == CONFIGNAME_WINDOW_BG_IS_TRANSPARENT
    assert captured['loaded'] is True


def test_set_txt_transparency_uses_text_color(monkeypatch):
    window = FakeWindow()
    txt_transparent_cb_value = FakeBoolVar(True)
    monkeypatch.setattr(utils, 'save_config', lambda config, name, value: None)
    monkeypatch.setattr(utils, 'get_window_txt_color', lambda config: '#abcdef')
    called = {}
    def fake_set_text_color(w, color, should_save=True):
        called['color'] = color
        called['should_save'] = should_save
    monkeypatch.setattr(utils, 'set_window_text_color', fake_set_text_color)
    utils.set_txt_transparency(window, txt_transparent_cb_value)
    assert called['color'] == '#abcdef'
    assert called['should_save'] is False


def test_get_window_bg_color_returns_default_when_no_config(monkeypatch):
    monkeypatch.setattr(utils, 'config_exists', lambda: False)
    assert utils.get_window_bg_color(configparser.ConfigParser()) == DEFAULT_WINDOW_BACKGROUND


def test_get_window_txt_color_returns_inverted_when_transparent(monkeypatch):
    monkeypatch.setattr(utils, 'config_exists', lambda: True)
    monkeypatch.setattr(utils, 'get_config_bool', lambda config, name, default: True)
    monkeypatch.setattr(utils, 'get_window_bg_color', lambda config: '#112233')
    assert utils.get_window_txt_color(configparser.ConfigParser()) == '#EEDDCC'


def test_set_window_bg_color_updates_ui(monkeypatch):
    window = FakeWindow()
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_BACKGROUND] = '#000000'
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_BG_IS_TRANSPARENT] = 'False'
    monkeypatch.setattr(utils, 'save_config', lambda config, name, value: None)
    monkeypatch.setattr(utils, 'load_window_background', lambda win: None)
    utils.set_window_bg_color(window, '#112233')
    assert window.canvas.config_values['bg'] == '#EEDDCC'
    assert window.cpu_temp_label.config_values['bg'] == '#112233'
    assert window.gpu_usage_label.config_values['bg'] == '#112233'


def test_set_window_text_color_saves_when_required(monkeypatch):
    window = FakeWindow()
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_TEXT] = '#000000'
    saved = {}
    monkeypatch.setattr(utils, 'save_config', lambda config, name, value: saved.setdefault('saved', (name, value)))
    utils.set_window_text_color(window, '#123456')
    assert window.cpu_temp_label.config_values['fg'] == '#123456'
    assert saved['saved'] == (CONFIGNAME_WINDOW_TEXT, '#123456')


def test_toggle_window_expanded_switches_state_and_reloads(monkeypatch):
    window = FakeWindow()
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_IS_EXPANDED] = 'False'
    monkeypatch.setattr(utils, 'get_config_bool', lambda config, name, default: False)
    reloaded = {}
    monkeypatch.setattr(utils, 'load_window_size', lambda win: reloaded.setdefault('loaded', True))
    monkeypatch.setattr(utils, 'save_config', lambda config, name, value: reloaded.setdefault('saved', (name, value)))
    utils.toggle_window_expanded(window)
    assert reloaded['saved'][0] == CONFIGNAME_WINDOW_IS_EXPANDED
    assert reloaded['loaded'] is True


def test_invert_color_converts_hex():
    assert utils.invert_color('#012345') == '#FEDCBA'


def test_set_windows_always_on_top_updates_attributes(monkeypatch):
    window = FakeWindow()
    options_window = FakeWindow()
    cb = FakeBoolVar(True)
    recorded = {}
    monkeypatch.setattr(utils, 'save_config', lambda config, name, value: recorded.setdefault('saved', (name, value)))
    utils.set_windows_always_on_top(window, cb, options_window)
    assert recorded['saved'] == (CONFIGNAME_WINDOW_ALWAYS_ON_TOP, 'True')
    assert ('-topmost', True) in options_window.attributes_calls
