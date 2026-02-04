# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "run",
# ]
# ///
from app.core import config
from app.core.logging import setup_logging
from app.soundcloud.auth import SoundCloudAuth, get_app_version, get_client_id, headers
from app.soundcloud.playlist import get_playlists
import asyncio
import aiohttp

logger = setup_logging(__name__)


async def main():
    logger.info("headers: %s", headers)
    async with aiohttp.ClientSession(
        proxy=config.settings.http_proxy,
        headers=headers,
    ) as session:
        client_id = await get_client_id(session)
        app_version = await get_app_version(session)
        sc_auth = SoundCloudAuth(client_id, app_version)
        res = await get_playlists(session, sc_auth)
        with open("res.json", "w") as file:
            file.write(str(res))


asyncio.run(main())
