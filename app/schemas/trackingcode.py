from pydantic import BaseModel

class ShowTrackCode(BaseModel):
    tracking_code : str