from constants import *
from tendo import singleton
from tkinter.colorchooser import askcolor
import configparser as cp
import tkinter as tk
import tkinter.messagebox as mb
import sys, lhm, utils, os, ctypes, subprocess
import winreg as reg
import time
import pystray
from pystray import Menu, MenuItem
from PIL import Image

# TODO
# - try custom fonts
# - throw exceptions

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    if getattr(sys, 'frozen', False):
        executable = sys.executable
        params = ''
    else:
        executable = sys.executable
        args = [os.path.abspath(sys.argv[0])] + sys.argv[1:]
        params = ' '.join([f'"{arg}"' for arg in args])

    shell32 = ctypes.windll.shell32
    result = shell32.ShellExecuteW(None, 'runas', executable, params, None, 1)
    return result > 32


class CircuitSentry(tk.Tk):
    last_click_x, last_click_y = 0, 0
    is_dragging = False
    def __init__(window):
        super().__init__()
        
        # Config Setup
        window.options_window_opened = False
        window.config = cp.ConfigParser()
        utils.generate_config(window)

        # Right Click Menu
        right_click_menu = tk.Menu(window, tearoff=0)
        right_click_menu.add_command(label="Expand", command=lambda:utils.toggle_window_expanded(window))
        right_click_menu.add_command(label="Open options", command=lambda:window.open_options_window(window))
        right_click_menu.add_separator()
        right_click_menu.add_command(label="Hide in system tray", command=window.withdraw)

        window.canvas = tk.Canvas(window, bg=utils.invert_color(utils.get_window_bg_color(window.config)), highlightthickness=0)
        window.canvas.pack(fill=tk.BOTH, expand=1)
        
        window.canvas.rowconfigure(0, weight=2)
        window.canvas.rowconfigure(1, weight=2)
        window.canvas.columnconfigure(0, weight=2)
        window.canvas.columnconfigure(1, weight=2)

        # CPU Temp Label
        # window.cpu_temp_label = tk.Label(window.canvas, bd=0, fg=utils.get_window_txt_color(window.config), bg=utils.get_window_bg_color(window.config), cursor="hand2", font=("Fixedsys", 30, "bold"), text="CPU\n0°")
        window.cpu_temp_label = tk.Label(window.canvas, bd=0, fg=utils.get_window_txt_color(window.config), bg=utils.get_window_bg_color(window.config), cursor="hand2", font=("Microsoft Yi Baiti", 40, "bold"), text="CPU\n0°")
        window.cpu_temp_label.grid(row=0, column=0)

        # GPU Temp Label
        window.gpu_temp_label = tk.Label(window.canvas, bd=0, fg=utils.get_window_txt_color(window.config), bg=utils.get_window_bg_color(window.config), cursor="hand2", font=("Microsoft Yi Baiti", 40, "bold"), text="GPU\n0°")
        window.gpu_temp_label.grid(row=0, column=1)
        
        # CPU Usage Label
        window.cpu_usage_label = tk.Label(window.canvas, bd=0, fg=utils.get_window_txt_color(window.config), bg=utils.get_window_bg_color(window.config), cursor="hand2", font=("Microsoft Yi Baiti", 40, "bold"), text="CPU\n0%")
        window.cpu_usage_label.grid(row=1, column=0)

        # GPU Usage Label
        window.gpu_usage_label = tk.Label(window.canvas, bd=0, fg=utils.get_window_txt_color(window.config), bg=utils.get_window_bg_color(window.config), cursor="hand2", font=("Microsoft Yi Baiti", 40, "bold"), text="GPU\n0%")
        window.gpu_usage_label.grid(row=1, column=1)

        # Bindings
        window.canvas.bind("<Button-3>", lambda event: window.open_menu(event, right_click_menu))
        window.cpu_temp_label.bind("<Button-3>", lambda event: window.open_menu(event, right_click_menu))
        window.gpu_temp_label.bind("<Button-3>", lambda event: window.open_menu(event, right_click_menu))
        window.cpu_usage_label.bind("<Button-3>", lambda event: window.open_menu(event, right_click_menu))
        window.gpu_usage_label.bind("<Button-3>", lambda event: window.open_menu(event, right_click_menu))
        window.bind('<ButtonPress-1>', window.dragging_started)
        window.bind('<B1-Motion>', window.dragging)
        window.bind('<ButtonRelease-1>', window.dragging_stopped)
        
        # Render window
        utils.load_window_size(window)
        window.overrideredirect(True)
        window.attributes('-topmost', utils.get_config(window.config, CONFIGNAME_WINDOW_ALWAYS_ON_TOP, DEFAULT_WINDOW_ALWAYS_ON_TOP))
        window.attributes("-transparent", "black")
        utils.load_window_background(window)

        # Start Monitoring Hardware
        hwm = lhm.HardwareMonitor(window)
        window.after(1000, lambda : hwm.init_libre_hm(window))

    def round_rectangle(window, canvas, dim, radius=25, **kwargs):
        canvas.delete("round_rectangle") 
        x1 = 0
        y1 = 0
        x2 = int(dim["width"])
        y2 = int(dim["height"])
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius,
                x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2,
                x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1] 
        canvas.create_polygon(points, **kwargs, smooth=True, fill=utils.get_window_bg_color(window.config), tags="round_rectangle")

    def open_menu(self, event, menu):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def dragging_started(self, event=None):
        self.is_dragging = True
        self.last_click_x = event.x
        self.last_click_y = event.y

    def dragging(self, event=None):
        x, y = event.x - self.last_click_x + self.winfo_x(), event.y - self.last_click_y + self.winfo_y()
        self.geometry("+%s+%s" % (x , y))

    def dragging_stopped(window, event=None):
        window.is_dragging = False
        utils.save_window_geometry_config(window)

    def is_admin(window):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def create_startup_task(window):
        task_name = "CircuitSentry"
        if getattr(sys, 'frozen', False):
            task_command = f'"{utils.get_file(APP_FILENAME)}"'
        else:
            task_command = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
        cmd = f'schtasks /Create /TN "{task_name}" /TR "{task_command}" /SC ONLOGON /RL HIGHEST /F'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0

    def delete_startup_task(window):
        task_name = "CircuitSentry"
        cmd = f'schtasks /Delete /TN "{task_name}" /F'
        subprocess.run(cmd, shell=True, capture_output=True, text=True)

    def set_run_on_startup(window, is_run_on_startup):
        if is_run_on_startup.get():
            if not window.is_admin():
                mb.showwarning(
                    title="Administrator required",
                    message="Creating an elevated startup task requires administrator rights. "
                            "Please run CircuitSentry as administrator once, then enable this option."
                )
                is_run_on_startup.set(False)
                return
            if window.create_startup_task():
                utils.save_config(window.config, CONFIGNAME_WINDOW_OPEN_ON_STARTUP, str(is_run_on_startup.get()))
            else:
                mb.showerror(title="Startup task failed", message="Could not create the startup task.")
                is_run_on_startup.set(False)
        else:
            window.delete_startup_task()
            utils.save_config(window.config, CONFIGNAME_WINDOW_OPEN_ON_STARTUP, str(is_run_on_startup.get()))

    def close_options_window(window, options_window ):
        window.options_window_opened = False
        options_window.destroy()
    
    def open_options_window(self, window):
        if window.options_window_opened:
            return
        
        options_window = tk.Toplevel(window)
        options_window.wm_transient(window)
        options_window.title("Options")
        main_win_dim = utils.get_window_geometry_as_json(window.config)
        options_window.geometry("300x160+%d+%d" % (int(main_win_dim["x"]) - 100, int(main_win_dim["y"]) + 100))

        run_on_startup_cb_value = tk.BooleanVar()
        run_on_startup_cb_value.set(utils.get_config(window.config, CONFIGNAME_WINDOW_OPEN_ON_STARTUP, DEFAULT_WINDOW_OPEN_ON_STARTUP))
        startup_checkbox = tk.Checkbutton(options_window, text='Run CircuitSentry on startup (requires admin)',variable=run_on_startup_cb_value, onvalue=True, offvalue=False, command=lambda:window.set_run_on_startup(run_on_startup_cb_value))
        startup_checkbox.grid(row=0, column=0, sticky=tk.W)

        always_on_top_cb_value = tk.BooleanVar()
        always_on_top_cb_value.set(utils.get_config(window.config, CONFIGNAME_WINDOW_ALWAYS_ON_TOP, DEFAULT_WINDOW_ALWAYS_ON_TOP))
        always_on_top_checkbox = tk.Checkbutton(options_window, text='Windows always on top',variable=always_on_top_cb_value, onvalue=True, offvalue=False, command=lambda:utils.set_windows_always_on_top(window, always_on_top_cb_value, options_window))
        always_on_top_checkbox.grid(row=1, column=0, sticky=tk.W)

        bg_transparent_cb_value = tk.BooleanVar()
        bg_transparent_cb_value.set(utils.get_config(window.config, CONFIGNAME_WINDOW_BG_IS_TRANSPARENT, DEFAULT_WINDOW_BG_IS_TRANSPARENT))
        bg_transparent_checkbox = tk.Checkbutton(options_window, text='Transparent Background',variable=bg_transparent_cb_value, onvalue=True, offvalue=False, command=lambda:utils.set_bg_transparency(window, bg_transparent_cb_value))
        bg_transparent_checkbox.grid(row=3, column=0, sticky=tk.W)

        txt_transparent_cb_value = tk.BooleanVar()
        txt_transparent_cb_value.set(utils.get_config(window.config, CONFIGNAME_WINDOW_TEXT_IS_TRANSPARENT, DEFAULT_WINDOW_TEXT_IS_TRANSPARENT))
        txt_transparent_checkbox = tk.Checkbutton(options_window, text='Transparent Text',variable=txt_transparent_cb_value, onvalue=True, offvalue=False, command=lambda:utils.set_txt_transparency(window, txt_transparent_cb_value))
        txt_transparent_checkbox.grid(row=4, column=0, sticky=tk.W)

        bg_frame = tk.Frame(options_window)
        bg_frame.columnconfigure(0, weight=2)
        bg_frame.columnconfigure(1, weight=2)
        bg_frame.columnconfigure(2, weight=1)
        bg_color_label = tk.Label(bg_frame, text="Background Color: ")
        bg_color_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        bg_color_button = tk.Button(bg_frame, command=lambda:(window.bg_color_picker(bg_color_button, bg_transparent_cb_value)), width=3, bg=utils.get_window_bg_color(window.config))
        bg_color_button.grid(row=0, column=1, sticky=tk.EW, padx=1)
        bg_frame.grid(row=4, column=0, sticky=tk.W)

        txt_frame = tk.Frame(options_window)
        txt_frame.columnconfigure(0, weight=2)
        txt_frame.columnconfigure(1, weight=2)
        txt_frame.columnconfigure(2, weight=1)
        txt_color_label = tk.Label(txt_frame, text="Text Color: ")
        txt_color_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        txt_color_button = tk.Button(txt_frame, command=lambda:(window.txt_color_picker(txt_color_button, txt_transparent_cb_value)), width=3, bg=utils.get_window_txt_color(window.config))
        txt_color_button.grid(row=0, column=1, sticky=tk.EW, padx=1)
        txt_frame.grid(row=5, column=0, sticky=tk.W)

        window.options_window_opened = True
        options_window.protocol("WM_DELETE_WINDOW", lambda: window.close_options_window(options_window))
    
    def bg_color_picker(window, bg_color_button, bg_transparent_cb_value):
        color = askcolor(title="Background Color Picker")
        utils.set_window_bg_color(window, color[1])
        bg_color_button.config(bg=color[1])
        bg_transparent_cb_value.set(0)
    
    def txt_color_picker(window, txt_color_button, txt_transparent_cb_value):
        color = askcolor(title="Text Color Picker")
        utils.set_window_text_color(window, color[1])
        txt_color_button.config(bg=color[1])
        txt_transparent_cb_value.set(0)

if __name__ == "__main__":
    if not is_admin():
        if not relaunch_as_admin():
            mb.showerror(title="Administrator required", message="CircuitSentry must be run as administrator.")
            sys.exit()
        sys.exit()

    try:
        me = singleton.SingleInstance()
    except singleton.SingleInstanceException:
        mb.showerror(title="Error", message="Another instance of CircuitSentry is already running!")
        sys.exit()

    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    
    def show_app(app):
        app.deiconify()
        app.update()
        app.lift()
        app.focus_force()
        always_on_top = utils.get_config(app.config, CONFIGNAME_WINDOW_ALWAYS_ON_TOP, DEFAULT_WINDOW_ALWAYS_ON_TOP)
        app.attributes('-topmost', str(always_on_top).lower() in ('true', '1', 'yes'))

    def init_sys_tray(app):
        icon = pystray.Icon('mon')
        icon.menu = Menu(
            MenuItem('Open CircuitSentry', lambda : show_app(app)),
            MenuItem('Exit', lambda : os._exit(0))
        )
        icon.icon = Image.open(resource_path('circuitsentry.ico'))
        icon.title = 'CircuitSentry'

        icon.run_detached()
        app.mainloop()

    app = CircuitSentry()
    init_sys_tray(app)