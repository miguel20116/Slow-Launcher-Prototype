import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
from PIL import Image, ImageTk, ImageEnhance
import pygame
import importlib.util
import traceback
import datetime

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")
LOG_FILE = os.path.join(os.path.dirname(__file__), "launcher.log")


# === PluginContext (for old-style plugins) === #
class PluginContext:
    def __init__(self, config, logger, proc):
        self.config = config
        self.logger = logger
        self.proc = proc


# === SPLASH SCREEN === #
def show_splash(root, callback=None):
    pygame.mixer.init()
    sound_path = "start.mp3"
    if os.path.exists(sound_path):
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()

    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.configure(bg="black")

    w, h = 500, 300
    sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    splash.geometry(f"{w}x{h}+{int(sw/2-w/2)}+{int(sh/2-h/2)}")

    if os.path.exists("logo.png"):
        base_img = Image.open("logo.png").resize((400, 200))
    else:
        base_img = Image.new("RGB", (400, 200), "black")

    label = tk.Label(splash, bg="black")
    label.pack(expand=True)

    alpha = 0.0
    step = 0.05
    fade_in = True

    def animate():
        nonlocal alpha, fade_in
        if fade_in:
            alpha += step
            if alpha >= 1.0:
                alpha = 1.0
                splash.after(1500, set_fade_out)
        else:
            alpha -= step
            if alpha <= 0.0:
                alpha = 0.0
                splash.destroy()
                if callback:
                    callback()
                return
        img = ImageEnhance.Brightness(base_img).enhance(alpha)
        tk_img = ImageTk.PhotoImage(img)
        label.config(image=tk_img)
        label.image = tk_img
        splash.after(40, animate)

    def set_fade_out():
        nonlocal fade_in
        fade_in = False
        animate()

    animate()


# === MAIN APP === #
class SlowLauncherApp:
    def __init__(self, root):
        self.root = root
        root.title("Slow Launcher")
        root.geometry("900x600")

        self.command_var = tk.StringVar(
            value="ping 127.0.0.1 -n 10" if os.name == "nt" else "echo Hello && sleep 1 && echo World"
        )
        self.selected_plugin = tk.StringVar(value="")
        self.plugins = {}

        frm = ttk.Frame(root, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")
        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=0)
        frm.rowconfigure(5, weight=1)

        ttk.Label(frm, text="Command to run:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, width=60, textvariable=self.command_var).grid(row=1, column=0, sticky="we", columnspan=2)

        ttk.Label(frm, text="Plugin:").grid(row=2, column=0, sticky="w")
        self.plugin_menu = ttk.Combobox(frm, values=[], textvariable=self.selected_plugin, state="readonly")
        self.plugin_menu.grid(row=3, column=0, sticky="we")
        ttk.Button(frm, text="Reload plugins", command=self.load_plugins).grid(row=3, column=1, sticky="e")

        self.run_button = ttk.Button(frm, text="Launch with plugin", command=self.launch_with_plugin)
        self.run_button.grid(row=4, column=0, pady=8, sticky="w")

        self.log = tk.Text(frm, width=80, height=20, bg="black", fg="lime", insertbackground="lime")
        self.log.grid(row=5, column=0, columnspan=2, sticky="nsew")

        # Color tags
        self.log.tag_config("info", foreground="lime")
        self.log.tag_config("warn", foreground="yellow")
        self.log.tag_config("error", foreground="red")

        # Create / append log file
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n=== Launcher started at " + self.timestamp() + " ===\n")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_plugins()

    def timestamp(self):
        """Return formatted timestamp."""
        return datetime.datetime.now().strftime("[%H:%M:%S]")

    def log_msg(self, msg, level="info"):
        """Color-coded, timestamped log with file saving."""
        timestamped = f"{self.timestamp()} {msg}"

        # Log to GUI
        def _append():
            self.log.insert("end", f"{timestamped}\n", level)
            self.log.see("end")
        self.root.after(0, _append)

        # Log to file
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(timestamped + "\n")
        except Exception:
            pass  # Avoid crash if file temporarily locked

    def load_plugins(self):
        self.plugins = {}
        if not os.path.exists(PLUGINS_DIR):
            os.makedirs(PLUGINS_DIR)
        for fname in os.listdir(PLUGINS_DIR):
            if fname.endswith(".py"):
                path = os.path.join(PLUGINS_DIR, fname)
                name = fname.replace(".py", "")
                self.plugins[name] = {"path": path}

        self.plugin_menu["values"] = list(self.plugins.keys())
        self.selected_plugin.set("")
        self.log_msg(f"Plugins reloaded. ({len(self.plugins)} found)", "warn")

    def launch_with_plugin(self):
        cmd = self.command_var.get().strip()
        plugin_name = self.selected_plugin.get()

        if not cmd:
            messagebox.showerror("Error", "No command given.")
            return
        if not plugin_name:
            messagebox.showerror("Error", "Select a plugin.")
            return

        self.run_button.config(state="disabled")
        self.log_msg(f"Launching: {cmd}", "warn")
        self.log_msg(f"Running plugin: {plugin_name}", "warn")

        plugin_path = self.plugins[plugin_name]["path"]

        def run_all():
            proc = None
            try:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout:
                    self.log_msg(line.strip())
                proc.wait()
            except Exception as e:
                self.log_msg(f"⚠ Error running command: {e}", "error")

            # === Load and execute plugin safely ===
            try:
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "run"):
                    arg_names = module.run.__code__.co_varnames
                    if "ctx" in arg_names:
                        ctx = PluginContext(
                            config={"port": 8081, "bps": 8},
                            logger=lambda msg: self.log_msg(f"[{plugin_name}] {msg}"),
                            proc=proc,
                        )
                        self.log_msg(f"🟡 {plugin_name} using old PluginContext API", "warn")
                        module.run(ctx)
                    else:
                        self.log_msg(f"🟢 {plugin_name} using simple log API", "warn")
                        module.run(lambda msg: self.log_msg(f"[{plugin_name}] {msg}"))
                else:
                    self.log_msg(f"⚠ Plugin '{plugin_name}' has no run() function.", "error")
            except Exception as e:
                tb = traceback.format_exc()
                self.log_msg(f"❌ Plugin '{plugin_name}' crashed:\n{tb}", "error")

            self.log_msg("Plugin finished.", "warn")
            self.run_button.config(state="normal")

        threading.Thread(target=run_all, daemon=True).start()

    def on_close(self):
        """Handle window close and save shutdown log."""
        self.log_msg("=== Launcher closed ===", "warn")
        self.root.destroy()


# === STARTUP === #
if __name__ == "__main__":
    root = tk.Tk()
    app = SlowLauncherApp(root)
    root.withdraw()

    def finish():
        root.update_idletasks()
        root.deiconify()
        root.geometry("900x600")
        root.lift()
        root.focus_force()

    show_splash(root, finish)
    root.mainloop()
