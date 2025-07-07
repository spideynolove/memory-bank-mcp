"""
Data models for Memory Bank MCP
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Memory:
    id: str
    content: str
    number: int
    total_estimated: int
    timestamp: str
    dependencies: List[str]
    contradictions: List[str]
    confidence: float
    collection_id: Optional[str] = None
    revision_of: Optional[str] = None
    is_checkpoint: bool = False
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class Collection:
    id: str
    name: str
    created_from: str
    purpose: str
    memories: List[str]
    merged: bool = False
    merge_target: Optional[str] = None


@dataclass
class MemorySession:
    id: str
    problem_statement: str
    success_criteria: str
    constraints: List[str]
    main_thread: List[str]
    collections: Dict[str, Collection]
    patterns: List[str]
    started: str
    last_updated: str