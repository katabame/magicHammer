import os
import signal
import sys
import time
import queue
import threading
import asyncio
from flask import Flask, jsonify, render_template

from client import (
    CANARY,
    PTB,
    STABLE
)

app = Flask(__name__)
loop = asyncio.get_event_loop()


def join(co):
    return asyncio.run_coroutine_threadsafe(co, loop).result(10)


@app.route('/api/stable.json', methods=['GET'])
def fetch_stable():
    return join(STABLE.get())


@app.route('/api/ptb.json', methods=['GET'])
def fetch_ptb():
    return join(PTB.get())


@app.route('/api/canary.json', methods=['GET'])
def fetch_canary():
    return join(CANARY.get())


@app.route('/api/all.json', methods=['GET'])
def fetch_all():
    return jsonify([join(e.get()) for e in [STABLE, PTB, CANARY]])


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


if __name__ == "__main__":
    debug = bool(os.environ.get("DEBUG", "False"))
    host = str(os.environ.get("HOST", "0.0.0.0"))
    port = int(os.environ.get("PORT", "5000"))
    web_thread = threading.Thread(daemon=True,
                                  name="Web Handler Thread",
                                  target=lambda: app.run(debug=False, host=host, port=port))
    web_thread.start()

    print("Running asyncio event loop...")
    loop.set_debug(debug)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.stop()
