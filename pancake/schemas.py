from pydantic import BaseModel


class Survey(BaseModel):
    claims: list[str]
    agrees: list[bool]


class ScoreIn(BaseModel):
    score: int
