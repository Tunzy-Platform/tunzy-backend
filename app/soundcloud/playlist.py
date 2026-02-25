from fastapi import Request
from sqlmodel import select

from app.core.db import SessionDep
from app.core.logging import get_logger
from app.models.playlist import TrackModel
from app.soundcloud.auth import SoundCloudAuth
from aiohttp import ClientSession
import re
from datetime import datetime
from app.schemas.playlist import PlaylistSchema, TrackSchema

logger = get_logger(__name__)


async def get_playlists(
    session: ClientSession, sc_auth: SoundCloudAuth, limit: int = 100
) -> list[PlaylistSchema]:
    url = (
        "https://api-v2.soundcloud.com/me/library/all?"
        # "offset=2022-01-15T13%3A44%3A17.936Z"
        # "%2Csystem-playlist-like"
        # "%2C00000000000038985529"
        f"&limit={limit}"
        f"&client_id={sc_auth.client_id}"
        f"&app_version={sc_auth.app_version}"
        "&app_locale=en"
    )
    logger.info("Requesting url %s", url)
    playlists: list[PlaylistSchema] = []
    checked = set()
    async with session.get(url) as req:
        content = await req.text()
        logger.info("User playlists api status %d length %d", req.status, len(content))
        if req.status != 200:
            logger.error(
                "Non-200 response from url %s content[2000]: %s", url, content[:2000]
            )
            return []
        data: dict = await req.json()
        collections: list[dict] = data.get("collection", {})

        for collection in collections:
            collection: dict
            playlist: dict = collection.get(
                "playlist",
                # fallback
                collection.get("system_playlist", {}),
            )
            user = playlist.get("user", {}).get("full_name")

            is_system_playlist: bool = "system_playlist" in collection
            platform_id = str(playlist.get("id", -1))
            artwork = playlist.get("artwork_url") or playlist.get(
                "calculated_artwork_url"
            )

            # prevent duplicated from API
            if platform_id in checked:
                continue
            checked.add(platform_id)
            if artwork:
                obj = PlaylistSchema(
                    platform_id=platform_id,
                    duration=playlist.get("duration", 0),
                    is_synced=False,
                    last_modified=playlist.get("last_modified", datetime.now()),
                    name=playlist.get("title", "SoundCloud"),
                    owner=playlist.get("user", {}).get("full_name", None)
                    or user
                    or "SoundCloud",
                    track_count=playlist.get("track_count", 0)
                    or len(playlist.get("tracks", [])),
                    url=playlist.get("permalink_url", ""),
                    thumbnail=artwork,
                    service="soundcloud",
                )
                playlists.append(obj)
            else:
                if is_system_playlist:
                    platform_id = platform_id.split(":")[-1]

                obj = await get_playlist(platform_id, session, sc_auth)
                playlists.append(obj)  # type: ignore

    logger.info("Extracted playlists total %d", len(playlists))
    return playlists


async def get_playlist(
    id: int | str, session: ClientSession, sc_auth: SoundCloudAuth
) -> PlaylistSchema | None:
    url = (
        "https://api-v2.soundcloud.com/playlists/"
        f"{id}"
        "?representation=full"
        f"&client_id={sc_auth.client_id}"
        f"&app_version={sc_auth.app_version}"
        "&app_locale=en"
    )
    logger.info("requesting playlist %s url %s", id, url)

    async with session.get(url) as req:
        content = await req.text()
        logger.info("User playlist api status %d length %d", req.status, len(content))
        if req.status != 200:
            logger.error(
                "Non-200 response from url %s content[2000]: %s", url, content[:2000]
            )
            return None
        playlist: dict = await req.json()

        user = playlist.get("user", {}).get("full_name")
        tracks = playlist.get("tracks", [])
        first_track_thumbnail = None
        if tracks:
            first_track_thumbnail = tracks[0].get("artwork_url")

        obj = PlaylistSchema(
            platform_id=str(playlist.get("id", -1)),
            duration=playlist.get("duration", 0),
            is_synced=False,
            last_modified=playlist.get("last_modified", datetime.now()),
            name=playlist.get("title", "SoundCloud"),
            owner=playlist.get("user", {}).get("full_name", None)
            or user
            or "SoundCloud",
            track_count=playlist.get("track_count", 0) or len(tracks),
            url=playlist.get("permalink_url", ""),
            thumbnail=playlist.get("artwork_url") or first_track_thumbnail,
            service="soundcloud",
        )

    return obj

async def get_liked_playlist(
    request: Request, session: ClientSession, sc_auth: SoundCloudAuth, limit: int = 1000
) -> PlaylistSchema:
    tracks = await get_liked_tracks(session, sc_auth, limit)
    obj = PlaylistSchema(
        platform_id="soundcloud-likes",
        duration=0,
        is_synced=False,
        last_modified=datetime.now(),
        name="SoundCloud Likes",
        owner="SoundCloud",
        track_count=len(tracks),
        url="soundcloud-likes",
        thumbnail=str(request.url_for("static", path="/liked.png")),
        service="soundcloud",
    )
    logger.info("The Liked Playlist Schema %s", obj)
    return obj


async def get_unassigned_tracks_playlist(
    request: Request, orm: SessionDep
) -> PlaylistSchema:

    tracks_qs = select(TrackModel).where(~TrackModel.playlists.any())  # type: ignore
    tracks = orm.exec(tracks_qs).fetchall()

    obj = PlaylistSchema(
        platform_id="unassigned-tracks-playlist",
        duration=0,
        is_synced=False,
        last_modified=datetime.now(),
        name="Unassigned",
        owner="You",
        track_count=len(tracks),
        url="unassigned-tracks-playlist",
        thumbnail=str(request.url_for("static", path="/unassigned.png")),
        service="system",
    )
    logger.info("The Liked Playlist Schema %s", obj)
    return obj

async def get_liked_tracks(
    session: ClientSession, sc_auth: SoundCloudAuth, limit: int = 1000
) -> list[TrackSchema]:
    url = (
        f"https://api-v2.soundcloud.com/users/{sc_auth.user_id}/track_likes?"
        # "offset=2025-07-11T12%3A59%3A13.428Z%2Cuser-track-likes%2C000-00000000000751401199-00000000002038114156"
        f"&limit={limit}"
        f"&client_id={sc_auth.client_id}"
        f"&app_version={sc_auth.app_version}"
        "&app_locale=en"
    )
    logger.info("Requesting url %s ", url)
    liked_tracks: list[dict] = []
    while url:
        async with session.get(url) as req:
            content = await req.text()
            logger.info(
                "track likes Api response status %d length %d", req.status, len(content)
            )

            if req.status != 200:
                logger.error(
                    "Non-200 Response status %d content[2000]: %s",
                    req.status,
                    content[:2000],
                )
                return []

            data: dict = await req.json()
            tracks: list[dict] = data.get("collection", [])
            url: str | None = data.get("next_href")

            liked_tracks.extend(tracks)

            if url:
                logger.info("Paginate to next page %s", url)

    objects = []
    for data in liked_tracks:
        track = data.get("track", {})
        obj = TrackSchema(
            platform_id=str(track.get("id", 0)),
            url=track.get("permalink_url"),
            name=track.get("title", "SoundCloud"),
            artist_name=track.get("user", {}).get("full_name"),
            album=None,
            duration=track.get("duration", 0),
            is_synced=False,
            thumbnail=track.get("artwork_url"),
        )
        objects.append(obj)
    logger.info("Extracted liked tracks total %d", len(objects))

    return objects


async def get_playlist_tracks_ids(
    playlist_uri: str,
    session: ClientSession,
) -> list[str]:
    logger.info("request playlist page %s", playlist_uri)
    track_ids_regex = r'"id"\s*:\s*(\d+)\s*,\s*"kind"\s*:\s*"track"'

    async with session.get(playlist_uri) as req:
        content = await req.text()
        logger.info(
            "playlist page response status %d length %d", req.status, len(content)
        )
        if req.status != 200:
            logger.error(
                "Non-200 response status %d content[2000]: %s",
                req.status,
                content[:2000],
            )
            return []
        tracks_ids: list[str] = re.findall(track_ids_regex, content)
        logger.info("extracted playlist tracks IDs total %d", len(tracks_ids))
        logger.debug("extracted track ids : %s", tracks_ids)
    return tracks_ids


async def get_playlist_tracks(
    playlist_uri: str,
    session: ClientSession,
    sc_auth: SoundCloudAuth,
    batch_size_tracks_ids: int = 29,
) -> list[TrackSchema]:

    tracks_ids = await get_playlist_tracks_ids(playlist_uri, session)
    id_query_batch = []
    tracks_data: list[dict] = []

    for i in range(0, len(tracks_ids), batch_size_tracks_ids):
        ids_query = "%2C".join(tracks_ids[i : i + batch_size_tracks_ids])
        id_query_batch.append(ids_query)

    for ids_query in id_query_batch:
        url = (
            "https://api-v2.soundcloud.com/tracks?"
            f"ids={ids_query}"
            f"&client_id={sc_auth.client_id}"
            f"&app_version={sc_auth.app_version}"
            "&app_locale=en"
        )
        logger.info("requesting tracks api via url %s ", url)
        async with session.get(url) as req:
            content = await req.text()
            logger.info(
                "tracks api response status %d length %d", req.status, len(content)
            )
            if req.status != 200:
                logger.error(
                    "error on tracks api with status %d content[2000] %s",
                    req.status,
                    content[:2000],
                )
                return []

            tracks_data.extend(await req.json())

    objects = []
    for data in tracks_data:
        obj = TrackSchema(
            platform_id=str(data.get("id", 0)),
            url=data.get("permalink_url"),
            name=data.get("title", "SoundCloud"),
            artist_name=data.get("user", {}).get("full_name"),
            album=None,
            duration=data.get("duration", 0),
            is_synced=False,
            thumbnail=data.get("artwork_url"),
        )
        objects.append(obj)

    logger.info("extracted tracks data total %d", len(tracks_data))

    return objects