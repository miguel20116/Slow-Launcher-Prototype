# plugins/stdout_bps.py
import time
import threading

def run(log):
    log("stdout_bps plugin started (simulated slow output).")
    bps = 8  # 8 bits = 1 byte per second
    bytes_per_second = bps / 8.0
    if bytes_per_second <= 0:
        bytes_per_second = 0.125

    fake_output = [
        "Launching simulated process...",
        "Processing data chunk 1...",
        "Processing data chunk 2...",
        "Processing complete!",
    ]

    for line in fake_output:
        for ch in line:
            log(ch)
            time.sleep(1.0 / bytes_per_second)
        log("")  # new line

    log("stdout_bps finished.")
