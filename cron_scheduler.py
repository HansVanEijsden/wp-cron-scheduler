#!/usr/bin/env python3
import json
import time
import random
import threading
import hashlib
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# ---------- config ----------
CONFIG_PATH = "/config/sites.json"
HEALTH_PORT = 8080
REQUEST_TIMEOUT = 30  # seconds

# ---------- logging ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("cron-scheduler")

# ---------- healthcheck server ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)

def start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    logger.info(f"Healthcheck server listening on port {HEALTH_PORT}")
    server.serve_forever()

# ---------- site worker ----------
def run_site_worker(url, interval):
    # Fixed offset based on the URL hash (spreads start times evenly)
    hash_digest = hashlib.md5(url.encode()).hexdigest()
    offset = int(hash_digest, 16) % interval
    logger.info(f"Site {url} starts with offset {offset}s (interval {interval}s)")

    # Initial sleep to spread the requests
    time.sleep(offset)

    while True:
        start_time = time.time()
        try:
            logger.info(f"Calling {url}")
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            duration = time.time() - start_time
            if resp.status_code == 200:
                logger.info(f"OK   {url} -> status {resp.status_code} (%.2fs)" % duration)
            else:
                logger.warning(f"WARN {url} -> status {resp.status_code} (%.2fs)" % duration)
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"ERROR {url} -> {e} (%.2fs)" % duration)

        # Determine jitter: max 4 minutes, but no more than interval/2
        max_jitter = min(240, interval * 0.4)  # 240s = 4 min
        jitter = random.uniform(-max_jitter, max_jitter)
        sleep_time = max(1, interval + jitter)  # never negative
        logger.debug(f"Next run for {url} in {sleep_time:.1f}s")
        time.sleep(sleep_time)

# ---------- main ----------
def main():
    # Read config
    try:
        with open(CONFIG_PATH, "r") as f:
            sites = json.load(f)
    except Exception as e:
        logger.error(f"Cannot load config: {e}")
        return

    # Start healthcheck server in a separate thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    # Start a worker thread for each site
    threads = []
    for site in sites:
        url = site.get("url")
        interval = site.get("interval")
        if not url or not interval:
            logger.warning("Invalid site config (missing url or interval), skipped")
            continue
        t = threading.Thread(target=run_site_worker, args=(url, interval), daemon=True)
        t.start()
        threads.append(t)

    # Keep the main thread alive (workers are daemons, so we must wait)
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("Stopped by user")

if __name__ == "__main__":
    main()