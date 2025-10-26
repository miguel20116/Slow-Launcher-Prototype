# plugins/live_stream.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading, time

def run(log):
    port = 8081
    bps = 1
    delay_per_byte = 8.0 / max(bps, 1)

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
            try:
                for ch in b" THIS_IS_A_SLOW_STREAM ":
                    self.wfile.write(bytes([ch]))
                    self.wfile.flush()
                    time.sleep(delay_per_byte)
            except BrokenPipeError:
                pass

    def serve():
        server = HTTPServer(("0.0.0.0", port), SlowHandler)
        log(f"Live stream server running at http://localhost:{port} (bps={bps})")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
            log("Live stream server stopped.")

    threading.Thread(target=serve, daemon=True).start()
