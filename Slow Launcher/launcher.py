import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
from PIL import Image, ImageTk, ImageEnhance
import pygame

# === CONFIG === #
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")


# === SPLASH SCREEN === #
def show_splash(root, callback=None):
    # Initialize pygame for MP3 sound
    pygame.mixer.init()
    sound_path = "start.mp3"
    if os.path.exists(sound_path):
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()

    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.configure(bg="black")

    # Center window
    w, h = 500, 300
    sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    splash.geometry(f"{w}x{h}+{int(sw/2-w/2)}+{int(sh/2-h/2)}")

    # Load logo
    if os.path.exists("logo.png"):
        base_img = Image.open("logo.png").resize((400, 200))
    else:
        base_img = Image.new("RGB", (400, 200), "black")

    label = tk.Label(splash, bg="black")
    label.pack(expand=True)

    # Fade in/out animation without blocking the UI
    alpha = 0.0
    step = 0.05
    fade_in = True

    def animate():
        nonlocal alpha, fade_in
        if fade_in:
            alpha += step
            if alpha >= 1.0:
                alpha = 1.0
                splash.after(1500, lambda: set_fade_out())
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
        self.command_var = tk.StringVar(
            value="ping 127.0.0.1 -n 10" if os.name == "nt" else "echo Hello && sleep 1 && echo World"
        )
        self.selected_plugin = tk.StringVar(value="")
        self.plugins = {}

        frm = ttk.Frame(root, padding=12)
        frm.grid(sticky="nsew")

        # Command entry
        ttk.Label(frm, text="Command to run:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, width=60, textvariable=self.command_var).grid(row=1, column=0, sticky="we", columnspan=2)

        # Plugin selection
        ttk.Label(frm, text="Plugin:").grid(row=2, column=0, sticky="w")
        self.plugin_menu = ttk.Combobox(frm, values=[], textvariable=self.selected_plugin, state="readonly")
        self.plugin_menu.grid(row=3, column=0, sticky="we")
        ttk.Button(frm, text="Reload plugins", command=self.load_plugins).grid(row=3, column=1, sticky="e")

        # Run button
        run_btn = ttk.Button(frm, text="Launch with plugin", command=self.launch_with_plugin)
        run_btn.grid(row=4, column=0, pady=8, sticky="w")

        # Log box
        self.log = tk.Text(frm, width=80, height=20)
        self.log.grid(row=5, column=0, columnspan=2)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Load plugins after creating log and plugin menu
        self.load_plugins()

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
                name = fname.replace(".py", "")
                self.plugins[name] = {"path": path}

        # Update Combobox
        self.plugin_menu['values'] = list(self.plugins.keys())
        self.selected_plugin.set("")
        self.log_msg("Plugins reloaded.")

    def launch_with_plugin(self):
        cmd = self.command_var.get().strip()
        if not cmd:
            messagebox.showerror("Error", "No command given.")
            return
        plugin_name = self.selected_plugin.get()
        if not plugin_name:
            messagebox.showerror("Error", "Select a plugin.")
            return

        self.log_msg(f"Launching: {cmd}")
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            self.log_msg(f"Error launching command: {e}")
            return

        self.log_msg(f"Running plugin: {plugin_name}")
        # For demo, just simulate plugin running
        self.root.after(2000, lambda: self.log_msg("Plugin finished."))

    def on_close(self):
        self.root.destroy()


# === STARTUP === #
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window during splash

    def start_main():
        root.deiconify()  # Show main window
        app = SlowLauncherApp(root)

    show_splash(root, start_main)
    root.mainloop()
