import enum
from typing import Union

import aiohttp

from backend.control_plane.config import get_settings


class REQUEST_METHODS(str, enum.Enum):
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    DELETE = "DELETE"


class AsyncHttpClient:
    def __init__(self):
        self._session = aiohttp.ClientSession(base_url=get_settings().FULL_ADDRESS)

    async def create_request(self, endpoint: str, method: REQUEST_METHODS, access_token: str=None, request_body=None) -> \
            Union[dict, bool, None]:
        await self._create_session()

        SESSION_REQUEST_METHODS = {
            key: getattr(self._session, key.lower()) for key in REQUEST_METHODS
        }

        if access_token:
            headers = {
                "Authorization": f"Bearer {access_token}",
                'accept': "application/json",
                "Content-Type": "application/json"
            }
        else:
            headers = {
                'accept': "application/json",
                "Content-Type": "application/json"
            }

        request_kwargs = {
            "url": endpoint,
            "headers": headers
        }
        if request_body:
            request_kwargs.update(data=request_body.model_dump_json())

        http_method = SESSION_REQUEST_METHODS[method]
        try:
            response = await http_method(
                **request_kwargs
            )

        except Exception as ex:
            print(f"api response error: {ex}")
            await self._close_session()
            raise ex
        if response.status != 200:
            print("api response status ERROR:", response.status)
            await self._close_session()
            return None

        response_json = await response.json()
        await self._close_session()

        return response_json

    async def _create_session(self):
        self._session = aiohttp.ClientSession(base_url=get_settings().FULL_ADDRESS)

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
