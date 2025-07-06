import json
import uuid
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context


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


class MemoryBankEngine:

    def __init__(self):
        self.memories: Dict[str, Memory] = {}
        self.sessions: Dict[str, MemorySession] = {}
        self.current_session: Optional[str] = None
        self.patterns: Dict[str, int] = {}

    def start_session(self, problem: str, criteria: str, constraints: List[str]
        ) ->str:
        session_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        session = MemorySession(id=session_id, problem_statement=problem,
            success_criteria=criteria, constraints=constraints, main_thread
            =[], collections={}, patterns=[], started=now, last_updated=now)
        self.sessions[session_id] = session
        self.current_session = session_id
        return session_id

    def add_memory(self, content: str, dependencies: List[str]=None,
        confidence: float=0.8, collection_id: Optional[str]=None) ->str:
        if not self.current_session:
            raise ValueError('No active session')
        memory_id = str(uuid.uuid4())[:8]
        session = self.sessions[self.current_session]
        if collection_id and collection_id not in session.collections:
            raise ValueError(f'Collection {collection_id} does not exist')
        memory_number = len(session.main_thread
            ) + 1 if not collection_id else len(session.collections[collection_id].
            memories) + 1
        contradictions = self._detect_contradictions(content, dependencies or
            [])
        memory = Memory(id=memory_id, content=content, number=
            memory_number, total_estimated=max(5, memory_number + 2),
            timestamp=datetime.now().isoformat(), dependencies=dependencies or
            [], contradictions=contradictions, confidence=confidence,
            collection_id=collection_id)
        self.memories[memory_id] = memory
        if collection_id:
            session.collections[collection_id].memories.append(memory_id)
        else:
            session.main_thread.append(memory_id)
        session.last_updated = datetime.now().isoformat()
        self._update_patterns(content)
        return memory_id

    def revise_memory(self, original_id: str, new_content: str, confidence:
        float=0.8) ->str:
        if original_id not in self.memories:
            raise ValueError('Original memory not found')
        original = self.memories[original_id]
        revised_id = str(uuid.uuid4())[:8]
        revised = Memory(id=revised_id, content=new_content, number=
            original.number, total_estimated=original.total_estimated,
            timestamp=datetime.now().isoformat(), dependencies=original.
            dependencies, contradictions=self._detect_contradictions(
            new_content, original.dependencies), confidence=confidence,
            collection_id=original.collection_id, revision_of=original_id)
        self.memories[revised_id] = revised
        session = self.sessions[self.current_session]
        if original.collection_id:
            collection_memories = session.collections[original.collection_id].memories
            idx = collection_memories.index(original_id)
            collection_memories[idx] = revised_id
        else:
            idx = session.main_thread.index(original_id)
            session.main_thread[idx] = revised_id
        return revised_id

    def create_collection(self, name: str, from_memory: str, purpose: str) ->str:
        if not self.current_session:
            raise ValueError('No active session')
        collection_id = str(uuid.uuid4())[:8]
        session = self.sessions[self.current_session]
        collection = Collection(id=collection_id, name=name, created_from=from_memory,
            purpose=purpose, memories=[])
        session.collections[collection_id] = collection
        return collection_id

    def merge_collection(self, collection_id: str, target_memory: Optional[str]=None
        ) ->List[str]:
        if not self.current_session:
            raise ValueError('No active session')
        session = self.sessions[self.current_session]
        if collection_id not in session.collections:
            raise ValueError('Collection not found')
        collection = session.collections[collection_id]
        merged_memories = []
        for memory_id in collection.memories:
            memory = self.memories[memory_id]
            memory.collection_id = None
            session.main_thread.append(memory_id)
            merged_memories.append(memory_id)
        collection.merged = True
        collection.merge_target = target_memory
        return merged_memories

    def _detect_contradictions(self, content: str, dependencies: List[str]
        ) ->List[str]:
        contradictions = []
        content_lower = content.lower()
        negative_indicators = ['not', 'false', 'incorrect', 'wrong',
            'impossible']
        positive_indicators = ['true', 'correct', 'right', 'possible', 'valid']
        for dep_id in dependencies:
            if dep_id in self.memories:
                dep_content = self.memories[dep_id].content.lower()
                content_negative = any(word in content_lower for word in
                    negative_indicators)
                dep_positive = any(word in dep_content for word in
                    positive_indicators)
                if content_negative and dep_positive:
                    contradictions.append(dep_id)
        return contradictions

    def _update_patterns(self, content: str):
        words = content.lower().split()
        key_phrases = ['first principles', 'breaking down', 'assumption',
            'because', 'therefore', 'however', 'alternatively',
            'given that', 'it follows', 'contradiction']
        for phrase in key_phrases:
            if phrase in content.lower():
                self.patterns[phrase] = self.patterns.get(phrase, 0) + 1

    def get_memory_tree(self) ->Dict[str, Any]:
        if not self.current_session:
            return {}
        session = self.sessions[self.current_session]

        def build_tree(memory_ids: List[str]) ->List[Dict]:
            tree = []
            for mid in memory_ids:
                memory = self.memories[mid]
                node = {'id': mid, 'content': memory.content, 'number':
                    memory.number, 'confidence': memory.confidence,
                    'contradictions': len(memory.contradictions) > 0,
                    'revision_of': memory.revision_of, 'dependencies':
                    memory.dependencies}
                tree.append(node)
            return tree
        result = {'problem': session.problem_statement, 'main_thread':
            build_tree(session.main_thread), 'collections': {}}
        for collection_id, collection in session.collections.items():
            result['collections'][collection_id] = {'name': collection.name, 'purpose':
                collection.purpose, 'memories': build_tree(collection.memories),
                'merged': collection.merged}
        return result

    def get_analysis(self) ->Dict[str, Any]:
        if not self.current_session:
            return {}
        session = self.sessions[self.current_session]
        all_memories = [self.memories[mid] for mid in session.main_thread]
        for collection in session.collections.values():
            all_memories.extend([self.memories[mid] for mid in collection.memories]
                )
        contradictions = sum(1 for m in all_memories if m.contradictions)
        avg_confidence = sum(m.confidence for m in all_memories) / len(
            all_memories) if all_memories else 0
        revisions = sum(1 for m in all_memories if m.revision_of)
        return {'total_memories': len(all_memories), 'contradictions_found':
            contradictions, 'average_confidence': round(avg_confidence, 2),
            'revisions_made': revisions, 'collections_created': len(session.
            collections), 'patterns_detected': dict(self.patterns),
            'memory_quality': self._assess_quality()}

    def _assess_quality(self) ->str:
        if not self.current_session:
            return 'unknown'
        session = self.sessions[self.current_session]
        total_memories = len(session.main_thread)
        if total_memories < 3:
            return 'insufficient'
        elif total_memories < 7:
            return 'basic'
        elif len(session.collections) > 0:
            return 'advanced'
        else:
            return 'good'


mcp = FastMCP('Memory Bank')
engine = MemoryBankEngine()


@mcp.tool()
def create_memory_session(problem: str, success_criteria: str, constraints:
    str='', ctx: Context=None) ->str:
    constraint_list = [c.strip() for c in constraints.split(',') if c.strip()
        ] if constraints else []
    session_id = engine.start_session(problem, success_criteria,
        constraint_list)
    return f'Started memory session {session_id} for: {problem}'


@mcp.tool()
def store_memory(content: str, dependencies: str='', confidence: float=0.8,
    collection_id: str='', ctx: Context=None) ->str:
    dep_list = [d.strip() for d in dependencies.split(',') if d.strip()
        ] if dependencies else []
    collection = collection_id if collection_id else None
    memory_id = engine.add_memory(content, dep_list, confidence, collection)
    memory = engine.memories[memory_id]
    result = f'Added memory {memory_id}: {content[:50]}...'
    if memory.contradictions:
        result += f" WARNING: Contradicts: {', '.join(memory.contradictions)}"
    return result


@mcp.tool()
def revise_memory(memory_id: str, new_content: str, confidence: float=0.8,
    ctx: Context=None) ->str:
    revised_id = engine.revise_memory(memory_id, new_content, confidence)
    return f'Revised {memory_id} -> {revised_id}: {new_content[:50]}...'


@mcp.tool()
def create_collection(name: str, from_memory: str, purpose: str, ctx: Context=None
    ) ->str:
    collection_id = engine.create_collection(name, from_memory, purpose)
    return (
        f"Created collection {collection_id} '{name}' from {from_memory}: {purpose}")


@mcp.tool()
def merge_collection(collection_id: str, target_memory: str='', ctx: Context=None
    ) ->str:
    target = target_memory if target_memory else None
    merged = engine.merge_collection(collection_id, target)
    return f'Merged collection {collection_id}: {len(merged)} memories integrated'


@mcp.tool()
def analyze_memories(ctx: Context=None) ->str:
    analysis = engine.get_analysis()
    return json.dumps(analysis, indent=2)


@mcp.resource('memory://tree')
def get_memory_tree() ->str:
    tree = engine.get_memory_tree()
    return json.dumps(tree, indent=2)


@mcp.resource('memory://analysis')
def get_analysis() ->str:
    analysis = engine.get_analysis()
    return json.dumps(analysis, indent=2)


@mcp.resource('memory://patterns')
def get_patterns() ->str:
    return json.dumps(engine.patterns, indent=2)


@mcp.prompt()
def memory_guide() ->str:
    return """Memory Bank Process:

1. create_memory_session(problem, success_criteria, constraints)
2. store_memory(content, dependencies, confidence, collection_id)
3. revise_memory(memory_id, new_content, confidence) 
4. create_collection(name, from_memory, purpose)
5. merge_collection(collection_id, target_memory)
6. analyze_memories()

Resources:
- memory://tree - Complete memory structure
- memory://analysis - Quality metrics  
- memory://patterns - Learning insights

Best Practices:
- Start with problem decomposition
- Build logical dependencies
- Create collections for alternatives
- Revise when new insights emerge
- Analyze before concluding"""


def main():
    mcp.run()


if __name__ == '__main__':
    main()