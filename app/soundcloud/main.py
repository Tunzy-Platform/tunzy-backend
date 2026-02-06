from app.core import config
from app.core.logging import get_logger, setup_logging
from app.soundcloud.auth import SoundCloudAuth, get_app_version, get_client_id, headers
from app.soundcloud.playlist import get_playlists, get_liked_tracks, get_playlist_tracks
import asyncio
import aiohttp
from app.soundcloud.download import download_tracks

setup_logging(__name__)
logger = get_logger(__name__)


async def main():
    # logger.info("headers: %s", headers)
    async with aiohttp.ClientSession(
        proxy=config.settings.http_proxy,
        headers=headers,
    ) as session:
        client_id = await get_client_id(session)
        app_version = await get_app_version(session)
        sc_auth = SoundCloudAuth(client_id, app_version)
        res = await get_playlists(session, sc_auth)
        logger.info("selected playlist: %s", res[0])
        res = await get_playlist_tracks(res[0]["permalink_url"], session, sc_auth)

        permalink_urls = [track["permalink_url"] for track in res]
        # logger.info("Data: %s", res)
        await download_tracks(permalink_urls)

asyncio.run(main())
