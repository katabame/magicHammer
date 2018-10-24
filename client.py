import asyncio
import unittest
import weakref
import time
import queue

from typing import Dict, List
from datetime import datetime, timedelta
from concurrent.futures import Future, TimeoutError
from pyppeteer import launch
from enum import Enum

"""
DiscordVersionClient クラスはDiscordのバージョンを拾ってくるクライアントを定義する
このクラスは "機能" として扱われる
"""
class DiscordVersionClient:
	def get(self, taskQueue: queue.Queue):
		pass

"""
CachedDiscordVersionClient クラスはバージョンが情報がキャッシュされた DiscordVersionClient を実装する
このクラスは別のDiscordVersionClient を呼び出し、その結果を指定された時間キャッシュする
"""
class CachedDiscordVersionClient(DiscordVersionClient):
	DEFAULT_TIMEOUT = timedelta(minutes = 1)

	def __init__(self, delegation: DiscordVersionClient, timeout: timedelta = DEFAULT_TIMEOUT):
		self.delegation = delegation
		self.timeout = timeout
		self.lastUpdated = datetime.now() - timeout
		self.cached = None

	def get(self, taskQueue: queue.Queue):
		currentTime = datetime.now()
		if (currentTime - self.lastUpdated) > self.timeout:
			self.lastUpdated = currentTime
			self.cached = self.delegation.get(taskQueue)
		return self.cached

"""
SimpleDiscordVersionClient クラスはDiscordVersionClient を実装する
このクラスは確実に discordapp.com からバージョン情報を抜き出してくる
キャッシュ機能を付ける場合はDiscordVersionClientの別の実装を使用する
"""
class SimpleDiscordVersionClient(DiscordVersionClient):

	def __init__(self, url: str):
		self.url = url

	def get(self, taskQueue: queue.Queue):
		return self.request(taskQueue)

	def onConsoleMessage(self, msg: str):
		log = [line[line.rfind(' ') + 1:] for line in msg.text.split(',')]
		return { 'release_channel': log[0], 'build_number': log[1], 'version_hash': log[2] }

	def request(self, taskQueue: queue.Queue):
		future = Future()
		async def requestAsync(self, future):
			browser = await launch(headless=True)
			page = await browser.newPage()

			page.once('console', lambda msg: future.set_result(self.onConsoleMessage(msg))) 
			
			await page.goto(self.url)
			await browser.close()
		while True:
			try:
				taskQueue.put(requestAsync(self, future), block = False)
				break
			except queue.Full:
				time.sleep(1)
		while True:
			try:
				return future.result(timeout = 1)
			except TimeoutError:
				time.sleep(1)


class DefaultDiscordVersionClients:
	STABLE_NOCACHE	= SimpleDiscordVersionClient('https://discordapp.com/login')
	PTB_NOCACHE		= SimpleDiscordVersionClient('https://ptb.discordapp.com/login')
	CANARY_NOCACHE	= SimpleDiscordVersionClient('https://canary.discordapp.com/login')
	STABLE	= CachedDiscordVersionClient(STABLE_NOCACHE)
	PTB		= CachedDiscordVersionClient(PTB_NOCACHE)
	CANARY	= CachedDiscordVersionClient(CANARY_NOCACHE)

def testTemplate(self, target):
	self.assertNotEqual(isinstance(target.value, DefaultDiscordVersionClients))
	self.assertEqual(isinstance(target.value, DiscordVersionClient))

class DefaultDiscordVersionClientsTest(unittest.TestCase):
	def testStable(self):
		testTemplate(self, DefaultDiscordVersionClients.STABLE)
	def testPTB(self):
		testTemplate(self, DefaultDiscordVersionClients.PTB)
	def testCanary(self):
		testTemplate(self, DefaultDiscordVersionClients.CANARY)

if __name__ == "__main__":
	unittest.main()
