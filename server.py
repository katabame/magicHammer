import os
import signal
import sys
import time
import queue
import threading
import asyncio
from flask import Flask, jsonify, render_template
from client import DiscordVersionClient, DefaultDiscordVersionClients, SimpleDiscordVersionClient, CachedDiscordVersionClient

app = Flask(__name__)
taskQueue = queue.Queue()

def fetch(endpoint: DiscordVersionClient):
	assert isinstance(endpoint, DiscordVersionClient)
	return jsonify(endpoint.get(taskQueue))

@app.route('/api/stable.json', methods=['GET'])
def fetchStable():
	return fetch(DefaultDiscordVersionClients.STABLE)
	
@app.route('/api/ptb.json', methods=['GET'])
def fetchPTB():
	return fetch(DefaultDiscordVersionClients.PTB)

@app.route('/api/canary.json', methods=['GET'])
def fetchCanary():
	return fetch(DefaultDiscordVersionClients.CANARY)

@app.route('/api/all.json', methods=['GET'])
def fetchAll():
	return jsonify([DefaultDiscordVersionClients.STABLE.get(taskQueue), DefaultDiscordVersionClients.PTB.get(taskQueue), DefaultDiscordVersionClients.CANARY.get(taskQueue)])

@app.route('/', methods=['GET'])
def index():
	return render_template('index.html')

if __name__ == "__main__":
	port = int(os.environ.get("PORT", "5000"))
	connectionHandler = threading.Thread(target = app.run(debug=False, host='0.0.0.0', port=port), daemon = True)
	connectionHandler.start()
	while True:
		try:
			task = taskQueue.get(block = False)
			if task:
				loop = asyncio.new_event_loop()
				loop.run_until_complete(task)
				loop.close()
		except queue.Empty:
			time.sleep(1)

