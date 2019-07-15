import asyncio
import unittest
import pyppeteer

from concurrent.futures import Future
from datetime import datetime, timedelta
from typing import Dict, List


class VersionFetcher:
    """
    VersionFetcher class represents an interface of version fetcher.
    """

    def get(self):
        pass


class CachedVersionFetcher(VersionFetcher):
    DEFAULT_TIMEOUT = timedelta(minutes=1)

    def __init__(self, delegation: VersionFetcher, timeout: timedelta = DEFAULT_TIMEOUT):
        self.delegation = delegation
        self.timeout = timeout
        self.last = datetime.now() - timeout
        self.cache = None

    def get(self):
        currentTime = datetime.now()
        if (currentTime - self.last) >= self.timeout:
            self.cache = self.delegation.get()
            self.last = currentTime
        return self.cache


class VersionFetcherImpl(VersionFetcher):
    """
    VersionFetcherImpl class implements VersionFetcher interface.
    Method "get" fetches version data from discordapp.com every time.
    For performance, use CachedVersionFetcher.
    """

    def __init__(self, url: str):
        self.url = url
        self.loop = asyncio.new_event_loop()

    def get(self):
        async def get_async(url):
            browser = await pyppeteer.launch(headless=True)
            page = await browser.newPage()
            result = Future()

            def handle_console(msg):
                text = msg.text
                if not ("Release Channel" in text
                        and "Build Number" in text
                        and "Version Hash" in text):
                    return

                ks = ['release_channel', 'build_number', 'version_hash']
                vs = [line[line.rfind(' ') + 1:]
                      for line in text.split(',')]
                result.set_result({k: v for k, v in zip(ks, vs)})

            page.on('console', handle_console)
            await page.goto(url)
            await browser.close()
            return result

        return self.loop.run_until_complete(get_async(self.url)).result(10)


STABLE_NOCACHE = VersionFetcherImpl('https://discordapp.com/login')
PTB_NOCACHE = VersionFetcherImpl('https://ptb.discordapp.com/login')
CANARY_NOCACHE = VersionFetcherImpl('https://canary.discordapp.com/login')
STABLE = CachedVersionFetcher(STABLE_NOCACHE)
PTB = CachedVersionFetcher(PTB_NOCACHE)
CANARY = CachedVersionFetcher(CANARY_NOCACHE)


class TestImpl(unittest.TestCase):

    def testGet(self):
        fetcher = VersionFetcherImpl('https://discordapp.com/login')
        result = fetcher.get()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn("release_channel", result)
        self.assertIn("build_number", result)
        self.assertIn("version_hash", result)
        print(result)


if __name__ == "__main__":
    unittest.main()
