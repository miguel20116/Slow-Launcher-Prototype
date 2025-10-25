# test_fast.py
import time
import sys

i = 0
try:
    while True:
        i += 1
        print(f"tick {i}", flush=True)
        time.sleep(0.05)  # prints ~20 times per second
except KeyboardInterrupt:
    print("stopped", flush=True)
    sys.exit(0)
