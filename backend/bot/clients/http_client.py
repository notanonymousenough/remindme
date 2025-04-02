import aiohttp


class AsyncHttpClient:
    def __init__(self):
        self._session = aiohttp.ClientSession()

    async def _create_session(self, base_url="http://127.0.0.1:8000"):  # TODO() get from config
        self._session = aiohttp.ClientSession(base_url=base_url)

    async def _close_session(self):
        if self._session:
            await self._session.close()

    async def get(self, url, headers=None):
        if not self._session:
            await self._create_session()

        async with self._session.get(url, headers=headers) as response:
            return await response.text()

    async def post(self, url, data=None, headers=None):
        if not self._session:
            await self._create_session()

        async with self._session.post(url, data=data, headers=headers) as response:
            return await response.text()

    async def put(self, url, data=None, headers=None):
        if not self._session:
            await self._create_session()

        async with self._session.put(url, data=data, headers=headers) as response:
            return await response.text()

    async def delete(self, url, data=None, headers=None):
        if not self._session:
            await self._create_session()

        async with self._session.delete(url, data=data, headers=headers) as response:
            return await response.text()

    async def __aenter__(self):
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_session()
