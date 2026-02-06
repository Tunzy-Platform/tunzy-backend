from pydantic import BaseModel, ConfigDict


class PlaylistSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    name: str
    owner: str
    track_counts: int
    duration: int
    thumbnail: str
    is_synced: bool


class TrackSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str | None
    name: str
    artist_name: str | None
    album: str | None
    duration: int
    is_synced: bool
    thumbnail: str | None


class PlaylistTrackSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    track: TrackSchema
    playlist: PlaylistSchema
