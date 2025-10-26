# plugin_api.py
import subprocess
import threading
import time
import os
from typing import Dict, Any

class PluginContext:
    """
    Passed to plugins so they can control and observe the launched process.
    Fields:
      - proc: subprocess.Popen object (may be None for server plugins)
      - config: dict with plugin configuration
      - logger: callable(msg)
    """
    def __init__(self, proc, config, logger=print):
        self.proc = proc
        self.config = config
        self.logger = logger

def load_plugin(path):
    """Load a plugin module from path (a .py file). Returns module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("plugin", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
