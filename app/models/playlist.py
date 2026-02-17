import enum
from typing import Optional
from pathlib import Path
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint, Column, Enum
from app.schemas.playlist import PlaylistSchema, TrackSchema


class PlaylistTrackLinkModel(SQLModel, table=True):
    playlist_id: int | None = Field(
        default=None,
        foreign_key="playlistmodel.id",
        primary_key=True,
    )
    track_id: int | None = Field(
        default=None,
        foreign_key="trackmodel.id",
        primary_key=True,
    )


class PlaylistBaseModel(SQLModel):
    platform_id: str | None = Field(index=True)
    url: str | None = Field()
    name: str = Field()
    owner: str | None = Field()
    track_count: int = Field()
    duration: int = Field()
    thumbnail: str | None = Field()
    is_synced: bool = Field()
    last_modified: datetime = Field()
    service: str = Field()

    @classmethod
    def from_schema(cls, schema: PlaylistSchema) -> "PlaylistBaseModel":
        return cls(**schema.model_dump())

    def update_from_schema(self, schema: PlaylistSchema):
        self.sqlmodel_update(schema.model_dump())


class PlaylistModel(PlaylistBaseModel, table=True):
    __table_args__ = (
        UniqueConstraint("platform_id", "service", name="platform_id_service_unique"),
    )
    id: int | None = Field(primary_key=True)
    tracks: list["TrackModel"] = Relationship(
        back_populates="playlists", link_model=PlaylistTrackLinkModel
    )


class PlaylistPublicModel(PlaylistBaseModel):
    id: int | None


class PlaylistCreateModel(PlaylistBaseModel): ...


class TrackBaseModel(SQLModel):
    platform_id: str = Field(index=True)
    url: str | None = Field()
    name: str = Field()
    artist_name: str | None = Field()
    album: str | None = Field()
    duration: int = Field()
    is_synced: bool = Field()
    thumbnail: str | None = Field()

    @classmethod
    def from_schema(cls, schema: TrackSchema) -> "TrackBaseModel":
        return cls(**schema.model_dump())

    def update_from_schema(self, schema: TrackSchema) -> None:
        self.sqlmodel_update(
            schema.model_dump(),
        )


class TrackModel(TrackBaseModel, table=True):
    id: int | None = Field(primary_key=True, index=True)

    playlists: list["PlaylistModel"] = Relationship(
        back_populates="tracks", link_model=PlaylistTrackLinkModel
    )
    download: Optional["DownloadTrackModel"] = Relationship(back_populates="track")


class DownloadStatusEnum(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    FAILED = "failed"
    SUCCESSFUL = "successful"


class DownloadTrackBaseModel(SQLModel):
    status: DownloadStatusEnum = Field(sa_column=Column(Enum(DownloadStatusEnum)))
    file_path: Path | None = Field()


class DownloadTrackModel(DownloadTrackBaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key="trackmodel.id", unique=True)
    track: TrackModel = Relationship(back_populates="download")


class DownloadTrackPublicModel(DownloadTrackBaseModel):
    id: int
    track: TrackModel


class DownloadTrackDataModel(DownloadTrackBaseModel):
    id: int


class DownloadTrackPreviewModel(DownloadTrackBaseModel):
    id: int


class TrackPublicModel(TrackBaseModel):
    id: int
    file_path: str | None
    download: Optional["DownloadTrackPreviewModel"]
