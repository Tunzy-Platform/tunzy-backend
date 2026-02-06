from app.core.logging import get_logger
from app.core import config
import asyncio
import yt_dlp

logger = get_logger(__name__)


def sync_download_ytdl(links: list[str]):
    with yt_dlp.YoutubeDL(config.ydl_opts) as ydl:
        ydl.download(links)


async def download_tracks(
    track_urls: list[str],
) -> None:

    track_urls = list(set(track_urls))

    download_buckets: list[list[str]] = []
    bucket_size: int = (
        len(track_urls) + config.settings.concurrent_downloads
    ) // config.settings.concurrent_downloads
    for i in range(0, len(track_urls), bucket_size):
        bucket = track_urls[i : i + bucket_size]
        download_buckets.append(bucket)

    logger.info(
        "Start downloading %s",
        track_urls,
    )
    tasks = []
    for i, _bucket in enumerate(download_buckets):
        logger.debug("Bucket %d data: %s", i, _bucket)
        task = asyncio.create_task(asyncio.to_thread(sync_download_ytdl, _bucket))

        tasks.append(task)
    await asyncio.gather(*tasks)
    logger.info("Finish downloading %s", track_urls)
