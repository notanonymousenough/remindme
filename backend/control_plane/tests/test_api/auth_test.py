from datetime import datetime, timedelta

import httpx
import pytest

from backend.control_plane.schemas.auth import UserTelegramDataSchema


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_auth_user(self, client: httpx.AsyncClient):
        new_user = UserTelegramDataSchema.model_validate({
            "id": "100100100",  # telegram id
            "first_name": "New",
            "last_name": "User",
            "username": "NewUserTEST",
            "auth_date": str((datetime.now() + timedelta(hours=10)).isoformat()),
            "hash": "huizxc"
        })
        response = await client.post("/v1/auth/telegram", data=new_user.model_dump_json())
        assert response.status_code == 200
