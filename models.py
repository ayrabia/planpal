from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Literal

ISO_DATE_FMT = "%Y-%m-%d"          # e.g., 2025-11-14
ISO_TS_FMT  = "%Y-%m-%dT%H:%M:%S"  # e.g., 2025-11-14T12:34:56

def to_iso_date(d: Optional[date]) -> Optional[str]:
    """date -> 'YYYY-MM-DD'"""
    return d.strftime(ISO_DATE_FMT) if d else None

def from_iso_date(s: Optional[str]) -> Optional[date]:
    """'YYYY-MM-DD' -> date"""
    return datetime.strptime(s, ISO_DATE_FMT).date() if s else None

def now_iso_ts() -> str:
    """timestamp for created_at/updated_at"""
    return datetime.now().strftime(ISO_TS_FMT)




@dataclass
class User:
    """Minimal user model for a single-user local app"""
    id: int | None
    username: str
    password: str | None = None

@dataclass
class Category:
    """Simple category model for a single-user local app"""
    id: int | None
    user_id: int
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
    status: Status = "Todo"
    created_at: str = field(default_factory=now_iso_ts)
    updated_at: str = field(default_factory=now_iso_ts)
    completed_at: Optional[str] = None