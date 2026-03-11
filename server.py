"""Lightweight HTTP server for the Major System memorization trainer.

Run:  python server.py
"""

import json
import logging
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generator import load_or_generate_wordlist
from validator import DIGIT_TO_SOUNDS

logger = logging.getLogger(__name__)

HOST = 'localhost'
PORT = 8080

# Populated at startup
wordlist = {}


class MajorSystemHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            directory=str(Path(__file__).parent / 'static'),
            **kwargs,
        )

    def do_GET(self):
        if self.path == '/api/wordlist':
            self._json_response(wordlist)
        elif self.path == '/api/mapping':
            self._json_response(DIGIT_TO_SOUNDS)
        elif self.path == '/':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()

    def _json_response(self, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        logger.debug(fmt, *args)


def main():
    global wordlist

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  %(levelname)-7s  %(message)s',
    )

    logger.info("Loading wordlist...")
    wordlist = load_or_generate_wordlist()

    filled = sum(1 for v in wordlist.values() if v is not None)
    logger.info("Loaded %d/100 associations", filled)

    if filled < 100:
        missing = [k for k, v in wordlist.items() if v is None]
        logger.warning("Missing associations: %s", ', '.join(missing))

    server = HTTPServer((HOST, PORT), MajorSystemHandler)
    logger.info("Server running at http://%s:%d", HOST, PORT)
    logger.info("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
