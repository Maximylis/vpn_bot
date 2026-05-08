from pydantic import BaseModel


class CreatePeerRequest(BaseModel):
    telegram_id: int
    device_name: str = "default"


class CreatePeerResponse(BaseModel):
    peer_id: str
    config: str


class DeletePeerResponse(BaseModel):
    success: bool
