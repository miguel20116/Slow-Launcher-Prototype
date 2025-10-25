# plugins/cpu_pacer.py
PLUGIN_NAME = "cpu_pacer (suspend/resume)"

import time
from plugin_api import PluginContext

def run(ctx: PluginContext):
    """
    Periodically suspend and resume the launched process to slow its effective CPU time.
    config: 'on_ms' (ms to run), 'off_ms' (ms to suspend)
    """
    proc = ctx.proc
    conf = ctx.config
    # Default cycle: run 1000ms, suspend 3000ms -> ~25% CPU allowance
    on_ms = conf.get("on_ms", 1000)
    off_ms = conf.get("off_ms", 3000)

    pid = proc.pid
    ctx.logger(f"cpu_pacer: pid={pid}, on={on_ms}ms off={off_ms}ms")

    try:
        import psutil
    except ImportError:
        ctx.logger("cpu_pacer requires 'psutil'. Install with: pip install psutil")
        proc.wait()
        return

    p = psutil.Process(pid)
    # keep going while process alive
    while True:
        if proc.poll() is not None:
            break
        try:
            # resume (if suspended)
            try:
                p.resume()
            except Exception:
                pass
            ctx.logger(f"cpu_pacer: running for {on_ms} ms")
            time.sleep(on_ms / 1000.0)
            # suspend
            try:
                p.suspend()
            except Exception as e:
                ctx.logger(f"cpu_pacer: suspend failed: {e}")
            ctx.logger(f"cpu_pacer: suspended for {off_ms} ms")
            time.sleep(off_ms / 1000.0)
        except Exception as e:
            ctx.logger(f"cpu_pacer loop error: {e}")
            break

    # cleanup: ensure process is resumed when finished
    try:
        p.resume()
    except Exception:
        pass
    ctx.logger("cpu_pacer finished.")
