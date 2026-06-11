from pydantic import BaseModel, Field


class CreatePlaylistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)


class UpdatePlaylistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)


class AddSongRequest(BaseModel):
    netease_song_id: int
    song_name: str = Field(min_length=1, max_length=255)
    artist_name: str = Field(min_length=1, max_length=255)
    cover_url: str = Field(default="", max_length=512)
