from fastapi import HTTPException, status
from fastapi.routing import APIRouter
from sqlmodel import select
from app.core.db import SessionDep

from app.models.playlist import (
    DownloadTrackDataModel,
    DownloadTrackModel,
    DownloadTrackPublicModel,
    DownloadStatusEnum,
)
from app.models.playlist import TrackModel

router = APIRouter(prefix="/downloads")


@router.get("/", response_model=list[DownloadTrackPublicModel])
async def downloads_list(orm: SessionDep):
    query = select(DownloadTrackModel)
    items = orm.exec(query).fetchall()
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Items Not Found"
        )
    return items


@router.post("/{id}/stop")
async def stop_download(orm: SessionDep): ...


@router.post("/{id}/start")
async def start_download(orm: SessionDep): ...


@router.post(
    "/playlists/tracks/{track_id}",
    response_model=DownloadTrackDataModel,
)
async def download_track(track_id: int, orm: SessionDep):
    track_query = select(TrackModel).where(TrackModel.id == track_id)
    track_obj = orm.exec(track_query).one_or_none()
    if not track_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Track Not Found"
        )
    download_track_query = select(DownloadTrackModel).where(
        DownloadTrackModel.track_id == track_id
    )
    download_track_obj = orm.exec(download_track_query).one_or_none()
    if download_track_obj:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This Track Already Is Exists"
        )

    download_item = DownloadTrackModel(
        status=DownloadStatusEnum.PENDING,
        track_id=track_id,
        file_path=None,
    )
    orm.add(download_item)
    orm.commit()

    return download_item


@router.post("/playlists/{id}/tracks")
async def download_playlist(orm: SessionDep): ...
