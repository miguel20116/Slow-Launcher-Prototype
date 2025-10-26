# plugins/live_stream.py
PLUGIN_NAME = "live_stream (slow HTTP server)"

from http.server import BaseHTTPRequestHandler, HTTPServer
import threading, time
from plugin_api import PluginContext

def run(ctx: PluginContext):
    port = ctx.config.get("port", 8081)
    bps = ctx.config.get("bps", 1)
    delay_per_byte = 8.0 / max(bps,1)  # seconds per byte for 1 bps => 8 sec per byte

    class SlowHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/favicon.ico":
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            content = b"<html><body style='font-family:monospace;background:#000;color:#0f0;'><pre>LOADING..."
            self.wfile.write(content)
            self.wfile.flush()
            # stream forever (or until client disconnect)
            try:
                for ch in b" THIS_IS_A_SLOW_STREAM ":
                    self.wfile.write(bytes([ch]))
                    self.wfile.flush()
                    time.sleep(delay_per_byte)
            except BrokenPipeError:
                pass

    server = HTTPServer(("0.0.0.0", port), SlowHandler)
    ctx.logger(f"Live stream server running at http://localhost:{port} (bps={bps})")
    # run server until the launcher or user stops the plugin
    # Run server in this thread (blocking) so plugin stays alive
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    ctx.logger("Live stream server stopped.")
