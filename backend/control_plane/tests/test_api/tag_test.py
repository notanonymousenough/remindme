import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.control_plane.db.models import Tag
from backend.control_plane.schemas.requests.tag import TagRequestSchema
from backend.control_plane.schemas.tag import TagSchema


class TestTag:
    @pytest.mark.asyncio
    async def test_post(self, auth_user: dict, session: AsyncSession, client: httpx.AsyncClient):
        tag = {
            "name": "test_tag",
            "color": "#FFAABB",
            "emoji": "🧩",
        }
        tag_schema = TagRequestSchema.model_validate(tag)
        response = await client.post("/v1/tag/", data=tag_schema.model_dump_json(), headers=auth_user)
        assert response.status_code == 200

        tag_response = TagSchema.model_validate(response.json())

        async with await session as session:
            tag_from_db = await session.get(Tag, tag_response.id)
            tag_schema_from_db = TagSchema.model_validate(tag_from_db)

        assert tag_response == tag_schema_from_db

    @pytest.mark.asyncio
    async def test_tags_get(self, auth_user: dict, session: AsyncSession, client: httpx.AsyncClient):
        response = await client.get("/v1/tag/", headers=auth_user)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_tag_delete(self, auth_user: dict, session: AsyncSession, client: httpx.AsyncClient):
        response_tags = await client.get("/v1/tag/", headers=auth_user)
        first_tag = [TagSchema.model_validate(response_tag) for response_tag in response_tags.json()][0]

        response_delete = await client.delete(f"/v1/tag/{first_tag.id}", headers=auth_user)
        assert response_delete.status_code == 200