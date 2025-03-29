from datetime import date

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.control_plane.db.models import User, SexType
from backend.control_plane.schemas.requests.user import UserUpdateRequest
from backend.control_plane.schemas.user import UserSchema


@pytest.mark.usefixtures("TestUser")
class TestUserAPI:
    @pytest.mark.asyncio
    async def test_get_user(self, auth_user: dict, client: httpx.AsyncClient):
        response = await client.get("/v1/user/", headers=auth_user)
        assert response.status_code == 200
        assert UserSchema.model_validate(response.json())

    @pytest.mark.asyncio
    async def test_update_user(
            self,
            auth_user: dict,
            client: httpx.AsyncClient,
            session: AsyncSession,
            TestUser: UserSchema
    ):
        user = {
            "id": TestUser.id,
            "username": "test_user_123",
            "telegram_id": "987654321",
            "timezone": "Europe/Moscow",
            "email": "test@example.com",
            "sex": SexType.MALE,
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "birth_date": date(1990, 5, 15),
        }
        request = UserUpdateRequest.model_validate(user)

        response = await client.put("/v1/user/", headers=auth_user, data=request.model_dump_json())

        assert response.status_code == 200

        async with await session as session:
            user_from_db = UserSchema.model_validate(await session.get(User, request.id))
        assert user_from_db
        assert user_from_db.id == request.id
        assert user_from_db.username == request.username

    @pytest.mark.asyncio
    async def test_delete_user(
            self,
            auth_user: dict,
            client: httpx.AsyncClient,
            session: AsyncSession,
            TestUser: UserSchema
    ):
        response = await client.delete(f"/v1/user/", headers=auth_user)
        assert response.status_code == 200

        async with await session as session:
            deleted_model_from_db = await session.get(User, TestUser.id)
        assert deleted_model_from_db is None
