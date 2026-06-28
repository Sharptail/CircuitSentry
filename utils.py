from constants import *
import os, sys, json

# different file path for running as .exe and running as .py
def get_file(filename):
    if getattr(sys, 'frozen', False):
        return os.path.dirname( sys.executable) + "\\" + filename
    elif __file__:
        return os.path.abspath( os.path.dirname( __file__ ) ) + "\\"  + filename

def config_exists():
    return os.path.isfile(get_file(CONFIG_FILENAME))

def generate_config(window):
    if config_exists():
        return
    
    window.config.add_section(CONFIGNAME_OPTIONS)
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_OPEN_ON_STARTUP] = DEFAULT_WINDOW_OPEN_ON_STARTUP
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_WIDTH] = DEFAULT_WINDOW_WIDTH
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_HEIGHT] = DEFAULT_WINDOW_HEIGHT
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_EXPANDED_WIDTH] = DEFAULT_WINDOW_EXPANDED_WIDTH
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_EXPANDED_HEIGHT] = DEFAULT_WINDOW_EXPANDED_HEIGHT
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_X] = DEFAULT_WINDOW_X
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_Y] = DEFAULT_WINDOW_Y
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_IS_EXPANDED] = DEFAULT_WINDOW_IS_EXPANDED
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_BACKGROUND] = DEFAULT_WINDOW_BACKGROUND
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_BG_IS_TRANSPARENT] = DEFAULT_WINDOW_BG_IS_TRANSPARENT
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_TEXT] = DEFAULT_WINDOW_TEXT
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_TEXT_IS_TRANSPARENT] = DEFAULT_WINDOW_TEXT_IS_TRANSPARENT
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_ALWAYS_ON_TOP] = DEFAULT_WINDOW_ALWAYS_ON_TOP
    with open(get_file(CONFIG_FILENAME), 'w') as configfile:
        window.config.write(configfile)

def save_config(config, config_name:str, config_value):
    if not config.has_section(CONFIGNAME_OPTIONS):
        config.add_section(CONFIGNAME_OPTIONS)
    config[CONFIGNAME_OPTIONS][config_name] = config_value
    with open(get_file(CONFIG_FILENAME), 'w') as configfile:
        config.write(configfile)

def get_config(config, config_name, default_config):
    if config.has_option(CONFIGNAME_OPTIONS, config_name):
        return config[CONFIGNAME_OPTIONS][config_name]
    config.read(get_file(CONFIG_FILENAME))
    if config.has_option(CONFIGNAME_OPTIONS, config_name):
        return config[CONFIGNAME_OPTIONS][config_name]
    save_config(config, config_name, default_config)
    return default_config

def get_config_bool(config, config_name, default_config):
    if config.has_option(CONFIGNAME_OPTIONS, config_name):
        return config.getboolean(CONFIGNAME_OPTIONS, config_name)
    config.read(get_file(CONFIG_FILENAME))
    if config.has_option(CONFIGNAME_OPTIONS, config_name):
        return config.getboolean(CONFIGNAME_OPTIONS, config_name)
    save_config(config, config_name, default_config)
    return default_config
    
def save_window_geometry_config(window):
    window.update()
    if get_config_bool(window.config, CONFIGNAME_WINDOW_IS_EXPANDED, DEFAULT_WINDOW_IS_EXPANDED):
        window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_EXPANDED_WIDTH] = str(window.winfo_width())
        window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_EXPANDED_HEIGHT] = str(window.winfo_height())
    else:
        window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_WIDTH] = str(window.winfo_width())
        window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_HEIGHT] = str(window.winfo_height())
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_X] = str(window.winfo_x())
    window.config[CONFIGNAME_OPTIONS][CONFIGNAME_WINDOW_Y] = str(window.winfo_y())
    with open(get_file(CONFIG_FILENAME), 'w') as configfile:
        window.config.write(configfile)

def get_window_dimensions_as_geometry(config):
    dim = get_window_geometry_as_json(config)
    return "%sx%s+%s+%s" % (dim["width"], dim["height"], dim["x"], dim["y"])

def get_window_geometry_as_json(config):
    if config_exists(): 
        if get_config_bool(config, CONFIGNAME_WINDOW_IS_EXPANDED, DEFAULT_WINDOW_IS_EXPANDED):
            return {
                "width": get_config(config, CONFIGNAME_WINDOW_EXPANDED_WIDTH, DEFAULT_WINDOW_EXPANDED_WIDTH),
                "height": get_config(config, CONFIGNAME_WINDOW_EXPANDED_HEIGHT, DEFAULT_WINDOW_EXPANDED_HEIGHT),
                "x": get_config(config, CONFIGNAME_WINDOW_X, DEFAULT_WINDOW_X),
                "y": get_config(config, CONFIGNAME_WINDOW_Y, DEFAULT_WINDOW_Y),
            }
        else:
            return {
                "width": get_config(config, CONFIGNAME_WINDOW_WIDTH, DEFAULT_WINDOW_WIDTH),
                "height": get_config(config, CONFIGNAME_WINDOW_HEIGHT, DEFAULT_WINDOW_HEIGHT),
                "x": get_config(config, CONFIGNAME_WINDOW_X, DEFAULT_WINDOW_X),
                "y": get_config(config, CONFIGNAME_WINDOW_Y, DEFAULT_WINDOW_Y),
            }
    else:
        return {
            "width": DEFAULT_WINDOW_WIDTH,
            "height": DEFAULT_WINDOW_HEIGHT,
            "x": DEFAULT_WINDOW_X,
            "y": DEFAULT_WINDOW_Y,
        }
    
def load_window_size(window):
    window.geometry(get_window_dimensions_as_geometry(window.config))
    window.round_rectangle(window.canvas, get_window_geometry_as_json(window.config), radius=30)

    if get_config_bool(window.config, CONFIGNAME_WINDOW_IS_EXPANDED, DEFAULT_WINDOW_IS_EXPANDED):
        window.cpu_usage_label.grid(row=1, column=0)
        window.gpu_usage_label.grid(row=1, column=1)
    else:
        window.cpu_usage_label.grid_forget()
        window.gpu_usage_label.grid_forget()
        

def load_window_background(window):
    if config_exists(): 
        bg_color = get_config(window.config, CONFIGNAME_WINDOW_BACKGROUND, DEFAULT_WINDOW_BACKGROUND)
        if get_config_bool(window.config, CONFIGNAME_WINDOW_BG_IS_TRANSPARENT, DEFAULT_WINDOW_BG_IS_TRANSPARENT):
            window.wm_attributes("-transparentcolor", bg_color)
            window.canvas.config(bg=bg_color)
        else:
            window.wm_attributes("-transparentcolor", invert_color(bg_color))
            window.canvas.config(bg=invert_color(bg_color))
    else:
        window.wm_attributes("-transparentcolor", DEFAULT_WINDOW_BACKGROUND)

def set_bg_transparency(window, bg_transparent_cb_value):
    save_config(window.config, CONFIGNAME_WINDOW_BG_IS_TRANSPARENT, str(bg_transparent_cb_value.get()))
    load_window_background(window)

def set_txt_transparency(window, txt_transparent_cb_value):
    save_config(window.config, CONFIGNAME_WINDOW_TEXT_IS_TRANSPARENT, str(txt_transparent_cb_value.get()))
    if(txt_transparent_cb_value.get()):
        set_window_text_color(window, get_window_txt_color(window.config), False)
    else:
        set_window_text_color(window, get_window_txt_color(window.config))

def get_window_bg_color(config):
    if config_exists():
        # if get_config_bool(config, CONFIGNAME_WINDOW_BG_IS_TRANSPARENT, DEFAULT_WINDOW_BG_IS_TRANSPARENT):
        #     return DEFAULT_WINDOW_BACKGROUND
        # else:
        return get_config(config, CONFIGNAME_WINDOW_BACKGROUND, DEFAULT_WINDOW_BACKGROUND)
    else:
        return DEFAULT_WINDOW_BACKGROUND

def get_window_txt_color(config):
    if config_exists():
        if get_config_bool(config, CONFIGNAME_WINDOW_TEXT_IS_TRANSPARENT, DEFAULT_WINDOW_TEXT_IS_TRANSPARENT):
            return invert_color(get_window_bg_color(config))
        else:
            return get_config(config, CONFIGNAME_WINDOW_TEXT, DEFAULT_WINDOW_TEXT)
    else:
        return DEFAULT_WINDOW_BACKGROUND

def set_window_bg_color(window, color):
    save_config(window.config, CONFIGNAME_WINDOW_BG_IS_TRANSPARENT, "False")
    save_config(window.config, CONFIGNAME_WINDOW_BACKGROUND, color)
    load_window_background(window)
    window.round_rectangle(window.canvas, get_window_geometry_as_json(window.config), radius=30)
    window.canvas.config(bg=invert_color(color))
    window.cpu_temp_label.config(bg=color)
    window.gpu_temp_label.config(bg=color)
    window.cpu_usage_label.config(bg=color)
    window.gpu_usage_label.config(bg=color)

def set_window_text_color(window, color, should_save=True):
    window.cpu_temp_label.config(fg=color)
    window.gpu_temp_label.config(fg=color)
    window.cpu_usage_label.config(fg=color)
    window.gpu_usage_label.config(fg=color)
    if should_save:
        save_config(window.config, CONFIGNAME_WINDOW_TEXT, color)

def toggle_window_expanded(window):
    save_config(window.config, CONFIGNAME_WINDOW_IS_EXPANDED, str(int(not get_config_bool(window.config, CONFIGNAME_WINDOW_IS_EXPANDED, DEFAULT_WINDOW_IS_EXPANDED))))
    load_window_size(window)

def invert_color(color_to_convert): 
    table = str.maketrans('0123456789abcdef', 'fedcba9876543210')
    return '#' + color_to_convert[1:].lower().translate(table).upper()

def set_windows_always_on_top(window, always_on_top_cb_value, options_window):
    save_config(window.config, CONFIGNAME_WINDOW_ALWAYS_ON_TOP, str(always_on_top_cb_value.get()))
    window.attributes('-topmost', always_on_top_cb_value.get())
    options_window.attributes('-topmost', True)