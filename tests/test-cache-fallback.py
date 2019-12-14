import unittest
import asyncio

from datetime import timedelta

from client import (
    VersionFetcher,
    CachedVersionFetcher
)

import pyppeteer


class PseudoVersionFetcher(VersionFetcher):

    def __init__(self):
        self.initial_run = True

    async def get(self):
        if self.initial_run:
            self.initial_run = False
            return "hello"
        raise pyppeteer.errors.BrowserError()


class TestCacheFallback(unittest.TestCase):

    def test_raise(self):
        loop = asyncio.get_event_loop()
        target = PseudoVersionFetcher()
        loop.run_until_complete(target.get())
        self.assertRaises(pyppeteer.errors.BrowserError,
                          lambda: loop.run_until_complete(target.get()))

    def test_fallback(self):
        target = CachedVersionFetcher(
            PseudoVersionFetcher(),
            timedelta(0)  # instantly cache invalidation
        )

        loop = asyncio.get_event_loop()
        healthyResponse = loop.run_until_complete(target.get())
        fallbackedResponse = loop.run_until_complete(target.get())

        self.assertEquals(healthyResponse, fallbackedResponse)


if __name__ == "__main__":
    unittest.main()
