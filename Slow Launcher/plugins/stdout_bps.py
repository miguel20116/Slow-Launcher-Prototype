# plugins/stdout_bps.py
PLUGIN_NAME = "stdout_bps (throttle STDOUT/ERR)"

import time
from plugin_api import PluginContext

def run(ctx: PluginContext):
    """
    Read process stdout/stderr and emit it slowly according to ctx.config['bps'] (bits per sec).
    Note: this only controls what the launcher shows; programs still run at normal rate underneath.
    """
    proc = ctx.proc
    bps = ctx.config.get("bps", 1)
    if bps <= 0:
        bps = 1
    bytes_per_second = bps / 8.0
    if bytes_per_second <= 0:
        bytes_per_second = 0.125  # 1 bps => 0.125 B/s

    # read bytes from stdout/stderr and print slowly
    def reader(pipe, name):
        while True:
            chunk = pipe.read(1)  # read 1 byte
            if not chunk:
                break
            # write as soon as we read, but pace according to bps
            ctx.logger(f"[{name}] {chunk.decode(errors='ignore')}",)
            # sleep for time per byte
            time.sleep(1.0 / bytes_per_second)

    # Note: using small threads for stdout/stderr
    import threading
    t1 = threading.Thread(target=reader, args=(proc.stdout, "OUT"), daemon=True)
    t2 = threading.Thread(target=reader, args=(proc.stderr, "ERR"), daemon=True)
    t1.start(); t2.start()
    # Wait until process finishes
    proc.wait()
    t1.join(timeout=0.1); t2.join(timeout=0.1)
