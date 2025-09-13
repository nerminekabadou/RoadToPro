from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Team(BaseModel):
    id: int
    name: str
    slug: str
    acronym: Optional[str]


class Player(BaseModel):
    id: int
    name: str
    slug: str
    role: Optional[str] = None


class Tournament(BaseModel):
    id: int
    name: str
    slug: str
    league_id: int
    begin_at: Optional[datetime]
    end_at: Optional[datetime]


class Match(BaseModel):
    id: int
    slug: str
    name: Optional[str]
    status: str
    number_of_games: Optional[int]
    begin_at: Optional[datetime]
    scheduled_at: Optional[datetime]
    serie_id: Optional[int]
    tournament_id: Optional[int]
    opponents: List[Dict[str, Any]] = Field(default_factory=list)


class Event(BaseModel):
    """Normalized envelope passed on the bus."""

    type: str  # e.g. "lol.schedule.upsert", "lol.result.upsert"
    at: datetime
    key: str  # idempotency key like f"match:{id}"
    payload: Dict[str, Any]
    source: str = "pandascore"
    version: str = "1.0"
