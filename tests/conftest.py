import configparser
from constants import CONFIGNAME_OPTIONS

class FakeBoolVar:
    def __init__(self, value=False):
        self._value = value
    def get(self):
        return self._value
    def set(self, value):
        self._value = value

class FakeLabel:
    def __init__(self):
        self.config_values = {}
        self.grid_state = None
    def config(self, **kwargs):
        self.config_values.update(kwargs)
    def grid(self, **kwargs):
        self.grid_state = 'grid'
    def grid_forget(self):
        self.grid_state = 'forgotten'

class FakeCanvas:
    def __init__(self):
        self.config_values = {}
        self.deleted_tags = []
        self.created = []
    def config(self, **kwargs):
        self.config_values.update(kwargs)
    def delete(self, tag):
        self.deleted_tags.append(tag)
    def create_polygon(self, points, **kwargs):
        self.created.append((points, kwargs))

class FakeWindow:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.add_section(CONFIGNAME_OPTIONS)
        self.canvas = FakeCanvas()
        self.cpu_usage_label = FakeLabel()
        self.gpu_usage_label = FakeLabel()
        self.cpu_temp_label = FakeLabel()
        self.gpu_temp_label = FakeLabel()
        self.attributes_calls = []
        self.wm_attributes_calls = []
        self.round_rectangle_calls = []
        self.updated = False
        self._geometry = "+0+0"
    def update(self):
        self.updated = True
    def winfo_width(self):
        return 100
    def winfo_height(self):
        return 200
    def winfo_x(self):
        return 10
    def winfo_y(self):
        return 20
    def round_rectangle(self, canvas, dim, radius=30):
        self.round_rectangle_calls.append((canvas, dim, radius))
    def wm_attributes(self, key, value=None):
        self.wm_attributes_calls.append((key, value))
    def attributes(self, key, value):
        self.attributes_calls.append((key, value))
    def geometry(self, value):
        self._geometry = value
    def after(self, delay, callback):
        self.after_args = (delay, callback)
