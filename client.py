import asyncio
import os
import threading
import unittest
import traceback
from datetime import datetime, timedelta
from typing import Dict, List

import pyppeteer


class VersionFetcher:
    """
    VersionFetcher class represents an interface of version fetcher.
    """

    async def get(self):
        raise NotImplementedError()


class CachedVersionFetcher(VersionFetcher):
    DEFAULT_TIMEOUT = timedelta(minutes=1)

    def __init__(self, delegation: VersionFetcher, timeout: timedelta = DEFAULT_TIMEOUT):
        self.delegation = delegation
        self.timeout = timeout
        self.last = datetime.now() - timeout
        self.cache = None

    async def get(self):
        currentTime = datetime.now()
        if (currentTime - self.last) >= self.timeout:
            try:
                self.cache = await self.delegation.get()
                self.last = currentTime
            except pyppeteer.errors.BrowserError:
                traceback.print_exc()
        return self.cache


class VersionFetcherImpl(VersionFetcher):
    """
    VersionFetcherImpl class implements VersionFetcher interface.
    Method "get" fetches version data from discordapp.com every time.
    For performance, use CachedVersionFetcher.
    """

    def __init__(self, url: str):
        self.url = url

    async def get(self):
        print(f"Fetching from {self.url}...")
        future = asyncio.get_event_loop().create_future()

        async def launch():
            if "DYNO" in os.environ:
                return await pyppeteer.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
            else:
                return await pyppeteer.launch(headless=True)

        browser = await launch()
        page = await browser.newPage()

        def handle_console(msg):
            if future.done():
                return
            text = msg.text
            if not ("Release Channel" in text
                    and "Build Number" in text
                    and "Version Hash" in text):
                return

            ks = ['release_channel', 'build_number', 'version_hash']
            vs = [line[line.rfind(' ') + 1:]
                  for line in text.split(',')]
            future.set_result({k: v for k, v in zip(ks, vs)})

        page.on('console', handle_console)
        await page.goto(self.url)
        await browser.close()
        return await future


STABLE_NOCACHE = VersionFetcherImpl('https://discordapp.com/login')
PTB_NOCACHE = VersionFetcherImpl('https://ptb.discordapp.com/login')
CANARY_NOCACHE = VersionFetcherImpl('https://canary.discordapp.com/login')
STABLE = CachedVersionFetcher(STABLE_NOCACHE)
PTB = CachedVersionFetcher(PTB_NOCACHE)
CANARY = CachedVersionFetcher(CANARY_NOCACHE)


class TestImpl(unittest.TestCase):

    def testGet(self):
        loop: asyncio.BaseEventLoop = asyncio.get_event_loop()
        fetcher = VersionFetcherImpl('https://discordapp.com/login')
        result = loop.run_until_complete(fetcher.get())
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn("release_channel", result)
        self.assertIn("build_number", result)
        self.assertIn("version_hash", result)
        print(result)


if __name__ == "__main__":
    unittest.main()
