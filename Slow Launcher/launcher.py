# launcher.py
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import time
import importlib.util
from plugin_api import load_plugin, PluginContext
import tkinter as tk
from PIL import Image, ImageTk

root = tk.Tk()
root.title("Slow Launcher")

# Load logo
logo = Image.open("logo.png").resize((400, 200))
photo = ImageTk.PhotoImage(logo)

# Add logo to window
label = tk.Label(root, image=photo)
label.pack(pady=10)

root.mainloop()

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")

class SlowLauncherApp:
    def __init__(self, root):
        self.root = root
        root.title("Slow Launcher")
        self.command_var = tk.StringVar(value="ping 127.0.0.1 -n 10" if os.name == "nt" else "echo Hello && sleep 1 && echo World")
        self.bps_var = tk.IntVar(value=1)
        self.selected_plugin = tk.StringVar(value="")
        self.plugins = {}
        self.load_plugins()

        frm = ttk.Frame(root, padding=12)
        frm.grid(sticky="nsew")
        ttk.Label(frm, text="Command to run:").grid(row=0,column=0,sticky="w")
        ttk.Entry(frm, width=60, textvariable=self.command_var).grid(row=1,column=0,sticky="we",columnspan=2)
        ttk.Label(frm, text="Plugin:").grid(row=2,column=0,sticky="w")
        plugin_menu = ttk.Combobox(frm, values=list(self.plugins.keys()), textvariable=self.selected_plugin, state="readonly")
        plugin_menu.grid(row=3,column=0,sticky="we")
        ttk.Button(frm, text="Add plugin folder...", command=self.add_plugin_folder).grid(row=3,column=1,sticky="e")
        ttk.Label(frm, text="Plugin config (bps or other):").grid(row=4,column=0,sticky="w")
        ttk.Entry(frm, width=20, textvariable=self.bps_var).grid(row=5,column=0,sticky="w")

        run_btn = ttk.Button(frm, text="Launch with plugin", command=self.launch_with_plugin)
        run_btn.grid(row=6,column=0, pady=8, sticky="w")

        self.log = tk.Text(frm, width=80, height=20)
        self.log.grid(row=7,column=0,columnspan=2)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def log_msg(self, msg):
        self.log.insert("end", f"{msg}\n")
        self.log.see("end")

    def load_plugins(self):
        self.plugins = {}
        if not os.path.exists(PLUGINS_DIR):
            os.makedirs(PLUGINS_DIR)
        for fname in os.listdir(PLUGINS_DIR):
            if fname.endswith(".py"):
                path = os.path.join(PLUGINS_DIR, fname)
                try:
                    mod = load_plugin(path)
                    name = getattr(mod, "PLUGIN_NAME", fname)
                    self.plugins[name] = {"module": mod, "path": path}
                except Exception as e:
                    print("Failed loading plugin", path, e)

    def add_plugin_folder(self):
        messagebox.showinfo("Info", f"Put plugin .py files into this folder:\n{PLUGINS_DIR}\nThen click OK to reload.")
        self.load_plugins()

    def launch_with_plugin(self):
        cmd = self.command_var.get().strip()
        if not cmd:
            messagebox.showerror("Error", "No command given.")
            return
        plugin_name = self.selected_plugin.get()
        plugin_data = self.plugins.get(plugin_name)
        if not plugin_data:
            messagebox.showerror("Error", "Select a plugin.")
            return

        # Launch process (shell mode)
        self.log_msg(f"Launching: {cmd}")
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ctx = PluginContext(proc=proc, config={"bps": self.bps_var.get()}, logger=self.log_msg)

        # Start plugin in a separate thread so GUI remains responsive
        def runner():
            try:
                mod = plugin_data["module"]
                # plugin must expose run(context) function
                if not hasattr(mod, "run"):
                    self.log_msg(f"Plugin {plugin_name} has no run(ctx) function.")
                    return
                self.log_msg(f"Starting plugin: {plugin_name}")
                mod.run(ctx)
            except Exception as e:
                self.log_msg(f"Plugin error: {e}")
            finally:
                # ensure process is cleaned up
                try:
                    proc.wait(timeout=0.1)
                except Exception:
                    pass
                self.log_msg("Plugin finished.")

        t = threading.Thread(target=runner, daemon=True)
        t.start()

    def on_close(self):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SlowLauncherApp(root)
    root.mainloop()
