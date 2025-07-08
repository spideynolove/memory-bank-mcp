"""
Data models for Memory Bank MCP
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


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


@dataclass
class PackageAPI:
    id: str
    session_id: str
    package_name: str
    api_signature: str
    usage_example: Optional[str] = None
    documentation: Optional[str] = None
    discovered_at: Optional[str] = None
    last_used: Optional[str] = None
    usage_count: int = 0


@dataclass
class CodebasePattern:
    id: str
    session_id: str
    pattern_type: str  # 'api_usage', 'integration', 'structure', 'template'
    code_snippet: str
    description: Optional[str] = None
    language: Optional[str] = None
    file_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class CodingSession:
    session_id: str
    session_type: str  # 'coding_session', 'debugging_session', 'architecture_session'
    project_path: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    packages_discovered: int = 0
    patterns_stored: int = 0
    validation_checks: int = 0


@dataclass
class ValidationCheck:
    id: str
    session_id: str
    check_type: str  # 'package_usage', 'api_existence', 'reinvention_prevention'
    target_code: str
    result: str  # 'passed', 'failed', 'warning'
    message: Optional[str] = None
    suggestions: List[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []