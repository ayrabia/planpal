from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Literal

ISO_TS_FMT = "%Y-%m-%dT%H:%M:%SZ"
ISO_DATE_FMT = "%Y-%m-%d"

def to_iso_date(d: Optional[date]) -> Optional[str]:
    """Convert a Python date to an ISO string for DB storage."""
    return d.strftime(ISO_DATE_FMT) if d else None

def from_iso_date(s: Optional[date]) -> Optional[str]:
    """Convert a ISO string from DB back to Python date """
    return datetime.strptime(s, ISO_TS_FMT) if s else None

def now_iso_ts() -> str:
    """Returns current local timestamp in ISO-like format"""
    return datetime.now().strftime(ISO_TS_FMT)



@dataclass
class User:
    """Minimal user model for a single-user local app"""
    id: int | None
    username: str

@dataclass
class Category:
    """Simple category model for a single-user local app"""
    id: int | None
    name: str
    color: str | None = None



#Task class
Priority = Literal["Low", "Medium", "High"]
Status = Literal["Todo", "Done"]

@dataclass
class Task:
    """"
    Represents a single to-do task
    """
    id: Optional[int]
    user_id: int
    category_id: Optional[int]
    title: str
    description: str = ""
    due_date: Optional[date] = None
    priority: Priority = "Medium"
    stats: Status = "Todo"
    created_at: str = field(default_factory=now_iso_ts)
    updated_at: str = field(default_factory=now_iso_ts)
    completed_at: Optional[str] = None