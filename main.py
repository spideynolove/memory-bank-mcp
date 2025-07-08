import json
import uuid
import importlib
import inspect
import ast
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context
from datetime import datetime

# Import data models
from models import Memory, Collection, MemorySession, PackageAPI, CodebasePattern, CodingSession, ValidationCheck

# Import database components
from database import DatabaseAdapter
from migration import MigrationManager


class MemoryBankEngine:

    def __init__(self, project_path: Optional[str] = None):
        # Initialize database adapter with project isolation
        self.db_adapter = DatabaseAdapter(project_path)
        self.current_session: Optional[str] = None
        self.patterns: Dict[str, int] = {}
        
        # Auto-migrate if JSON data exists
        migrator = MigrationManager(project_path)
        migration_result = migrator.auto_migrate_if_needed()
        if migration_result:
            print(f"Auto-migration completed: {migration_result['message']}")
        
        # Load active session if exists
        active_session_id = self.db_adapter.get_active_session_id()
        if active_session_id:
            self.current_session = active_session_id

    def start_session(self, problem: str, criteria: str, constraints: List[str],
                      session_type: str = "general") -> str:
        session_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        session = MemorySession(id=session_id, problem_statement=problem,
            success_criteria=criteria, constraints=constraints, main_thread
            =[], collections={}, patterns=[], started=now, last_updated=now)
        
        # Save session to database
        self.db_adapter.create_session(session)
        self.db_adapter.set_active_session(session_id)
        self.current_session = session_id
        
        # Create coding session if it's a coding-specific session
        if session_type in ["coding_session", "debugging_session", "architecture_session"]:
            self.create_coding_session(session_id, session_type)
        
        return session_id

    def create_coding_session(self, session_id: str, session_type: str,
                             project_path: Optional[str] = None,
                             language: Optional[str] = None,
                             framework: Optional[str] = None) -> str:
        """Create a coding-specific session extension"""
        coding_session = CodingSession(
            session_id=session_id,
            session_type=session_type,
            project_path=project_path or os.getcwd(),
            language=language,
            framework=framework
        )
        
        # Save to database (implement in database adapter)
        self.db_adapter.create_coding_session(coding_session)
        return session_id

    def discover_packages(self, scan_imports: bool = True) -> List[PackageAPI]:
        """Discover available packages and their APIs"""
        if not self.current_session:
            raise ValueError("No active session")
        
        discovered_apis = []
        
        if scan_imports:
            # Scan current environment for installed packages
            for package_name in sys.modules.keys():
                if not package_name.startswith('_') and '.' not in package_name:
                    try:
                        module = importlib.import_module(package_name)
                        api_info = self._extract_api_info(module, package_name)
                        if api_info:
                            for api in api_info:
                                api_id = str(uuid.uuid4())[:8]
                                package_api = PackageAPI(
                                    id=api_id,
                                    session_id=self.current_session,
                                    package_name=package_name,
                                    api_signature=api['signature'],
                                    usage_example=api.get('example'),
                                    documentation=api.get('doc'),
                                    discovered_at=datetime.now().isoformat()
                                )
                                self.db_adapter.add_package_api(package_api)
                                discovered_apis.append(package_api)
                    except Exception:
                        continue
        
        return discovered_apis

    def _extract_api_info(self, module, package_name: str) -> List[Dict]:
        """Extract API information from a module"""
        api_info = []
        
        try:
            for name, obj in inspect.getmembers(module):
                if not name.startswith('_') and (inspect.isfunction(obj) or inspect.isclass(obj)):
                    try:
                        signature = str(inspect.signature(obj))
                        doc = inspect.getdoc(obj) or ""
                        api_info.append({
                            'name': name,
                            'signature': f"{package_name}.{name}{signature}",
                            'doc': doc[:200] if doc else "",
                            'example': f"import {package_name}\\n{package_name}.{name}()"
                        })
                    except Exception:
                        continue
        except Exception:
            pass
        
        return api_info[:10]  # Limit to prevent overwhelming

    def validate_package_usage(self, code_snippet: str) -> ValidationCheck:
        """Validate if code uses existing packages appropriately"""
        if not self.current_session:
            raise ValueError("No active session")
        
        check_id = str(uuid.uuid4())[:8]
        suggestions = []
        result = "passed"
        message = "Code validation passed"
        
        try:
            # Parse the code to find imports and function calls
            tree = ast.parse(code_snippet)
            imports = []
            function_calls = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        function_calls.append(node.func.id)
            
            # Check for potential reinvention
            existing_apis = self.db_adapter.get_package_apis(self.current_session)
            for api in existing_apis:
                if any(call in api.api_signature for call in function_calls):
                    suggestions.append(f"Consider using existing API: {api.api_signature}")
            
            # Check if common functionality is being reimplemented
            common_patterns = [
                ("def.*request.*http", "Consider using requests library"),
                ("def.*parse.*json", "Consider using json.loads()"),
                ("def.*format.*date", "Consider using datetime.strftime()"),
                ("class.*Exception", "Consider using built-in exceptions")
            ]
            
            import re
            for pattern, suggestion in common_patterns:
                if re.search(pattern, code_snippet, re.IGNORECASE):
                    suggestions.append(suggestion)
                    result = "warning"
                    message = "Potential reinvention detected"
        
        except Exception as e:
            result = "failed"
            message = f"Validation failed: {str(e)}"
        
        validation_check = ValidationCheck(
            id=check_id,
            session_id=self.current_session,
            check_type="package_usage",
            target_code=code_snippet,
            result=result,
            message=message,
            suggestions=suggestions,
            created_at=datetime.now().isoformat()
        )
        
        self.db_adapter.add_validation_check(validation_check)
        return validation_check

    def explore_existing_apis(self, functionality: str) -> List[PackageAPI]:
        """Explore existing APIs that might provide the needed functionality"""
        if not self.current_session:
            raise ValueError("No active session")
        
        matching_apis = []
        existing_apis = self.db_adapter.get_package_apis(self.current_session)
        
        # Simple keyword matching
        keywords = functionality.lower().split()
        for api in existing_apis:
            api_text = f"{api.api_signature} {api.documentation}".lower()
            if any(keyword in api_text for keyword in keywords):
                matching_apis.append(api)
        
        return matching_apis

    def store_codebase_pattern(self, pattern_type: str, code_snippet: str,
                              description: str = "", language: str = "",
                              file_path: str = "", tags: List[str] = None) -> str:
        """Store a codebase pattern for future reference"""
        if not self.current_session:
            raise ValueError("No active session")
        
        pattern_id = str(uuid.uuid4())[:8]
        pattern = CodebasePattern(
            id=pattern_id,
            session_id=self.current_session,
            pattern_type=pattern_type,
            code_snippet=code_snippet,
            description=description,
            language=language,
            file_path=file_path,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            tags=tags or []
        )
        
        self.db_adapter.add_codebase_pattern(pattern)
        return pattern_id

    def load_codebase_context(self, project_path: str = None) -> Dict[str, Any]:
        """Load existing codebase structure and patterns into memory"""
        if not self.current_session:
            raise ValueError("No active session")
        
        project_path = project_path or os.getcwd()
        context = {
            "project_path": project_path,
            "file_structure": [],
            "patterns": [],
            "imports": [],
            "functions": []
        }
        
        try:
            # Scan project files
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, project_path)
                        context["file_structure"].append(rel_path)
                        
                        # Extract patterns from Python files
                        if file.endswith('.py'):
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    # Store as pattern
                                    pattern_id = self.store_codebase_pattern(
                                        "structure",
                                        content[:1000],  # First 1000 chars
                                        f"Code structure from {rel_path}",
                                        "python",
                                        rel_path
                                    )
                                    context["patterns"].append(pattern_id)
                            except Exception:
                                continue
        
        except Exception as e:
            context["error"] = str(e)
        
        return context

    def add_memory(self, content: str, dependencies: List[str]=None,
        confidence: float=0.8, collection_id: Optional[str]=None) ->str:
        if not self.current_session:
            raise ValueError('No active session')
        
        memory_id = str(uuid.uuid4())[:8]
        session = self.db_adapter.get_session(self.current_session)
        
        if collection_id and collection_id not in session.collections:
            raise ValueError(f'Collection {collection_id} does not exist')
        
        memory_number = len(session.main_thread
            ) + 1 if not collection_id else len(session.collections[collection_id].
            memories) + 1
        
        contradictions = self._detect_contradictions(content, dependencies or [])
        
        memory = Memory(id=memory_id, content=content, number=
            memory_number, total_estimated=max(5, memory_number + 2),
            timestamp=datetime.now().isoformat(), dependencies=dependencies or
            [], contradictions=contradictions, confidence=confidence,
            collection_id=collection_id)
        
        # Save memory to database
        self.db_adapter.add_memory(memory)
        
        # Update session main_thread or collection
        if collection_id:
            collection = session.collections[collection_id]
            collection.memories.append(memory_id)
            self.db_adapter.update_collection(collection)
        else:
            session.main_thread.append(memory_id)
        
        self._update_patterns(content)
        return memory_id

    def revise_memory(self, original_id: str, new_content: str, confidence:
        float=0.8) ->str:
        original = self.db_adapter.get_memory(original_id)
        if not original:
            raise ValueError('Original memory not found')
        
        revised_id = str(uuid.uuid4())[:8]
        revised = Memory(id=revised_id, content=new_content, number=
            original.number, total_estimated=original.total_estimated,
            timestamp=datetime.now().isoformat(), dependencies=original.
            dependencies, contradictions=self._detect_contradictions(
            new_content, original.dependencies), confidence=confidence,
            collection_id=original.collection_id, revision_of=original_id)
        
        # Save revised memory to database
        self.db_adapter.add_memory(revised)
        
        # Update session or collection references
        session = self.db_adapter.get_session(self.current_session)
        if original.collection_id:
            collection = session.collections[original.collection_id]
            idx = collection.memories.index(original_id)
            collection.memories[idx] = revised_id
            self.db_adapter.update_collection(collection)
        else:
            idx = session.main_thread.index(original_id)
            session.main_thread[idx] = revised_id
        
        return revised_id

    def create_collection(self, name: str, from_memory: str, purpose: str) ->str:
        if not self.current_session:
            raise ValueError('No active session')
        
        collection_id = str(uuid.uuid4())[:8]
        collection = Collection(id=collection_id, name=name, created_from=from_memory,
            purpose=purpose, memories=[])
        
        # Save collection to database
        self.db_adapter.create_collection(collection)
        return collection_id

    def merge_collection(self, collection_id: str, target_memory: Optional[str]=None
        ) ->List[str]:
        if not self.current_session:
            raise ValueError('No active session')
        
        collection = self.db_adapter.get_collection(collection_id)
        if not collection:
            raise ValueError('Collection not found')
        
        merged_memories = []
        for memory_id in collection.memories:
            memory = self.db_adapter.get_memory(memory_id)
            if memory:
                memory.collection_id = None
                self.db_adapter.update_memory(memory)
                merged_memories.append(memory_id)
        
        # Update collection as merged
        collection.merged = True
        collection.merge_target = target_memory
        self.db_adapter.update_collection(collection)
        
        return merged_memories

    def _detect_contradictions(self, content: str, dependencies: List[str]
        ) ->List[str]:
        contradictions = []
        content_lower = content.lower()
        negative_indicators = ['not', 'false', 'incorrect', 'wrong',
            'impossible']
        positive_indicators = ['true', 'correct', 'right', 'possible', 'valid']
        for dep_id in dependencies:
            memory = self.db_adapter.get_memory(dep_id)
            if memory:
                dep_content = memory.content.lower()
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
        
        # Update patterns in database
        if self.current_session:
            self.db_adapter.update_patterns(self.patterns, self.current_session)

    def get_memory_tree(self) ->Dict[str, Any]:
        if not self.current_session:
            return {}
        session = self.db_adapter.get_session(self.current_session)

        def build_tree(memory_ids: List[str]) ->List[Dict]:
            tree = []
            for mid in memory_ids:
                memory = self.db_adapter.get_memory(mid)
                if memory:
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
        session = self.db_adapter.get_session(self.current_session)
        all_memories = []
        
        # Get all memories from main thread
        for mid in session.main_thread:
            memory = self.db_adapter.get_memory(mid)
            if memory:
                all_memories.append(memory)
        
        # Get all memories from collections
        for collection in session.collections.values():
            for mid in collection.memories:
                memory = self.db_adapter.get_memory(mid)
                if memory:
                    all_memories.append(memory)
        
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
        session = self.db_adapter.get_session(self.current_session)
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
    str='', session_type: str='general', ctx: Context=None) ->str:
    constraint_list = [c.strip() for c in constraints.split(',') if c.strip()
        ] if constraints else []
    session_id = engine.start_session(problem, success_criteria,
        constraint_list, session_type)
    return f'Started {session_type} session {session_id} for: {problem}'


@mcp.tool()
def store_memory(content: str, dependencies: str='', confidence: float=0.8,
    collection_id: str='', code_snippet: str='', language: str='',
    pattern_type: str='', ctx: Context=None) ->str:
    dep_list = [d.strip() for d in dependencies.split(',') if d.strip()
        ] if dependencies else []
    collection = collection_id if collection_id else None
    
    # Store the memory
    memory_id = engine.add_memory(content, dep_list, confidence, collection)
    memory = engine.db_adapter.get_memory(memory_id)
    
    # If code snippet is provided, also store it as a codebase pattern
    if code_snippet and engine.current_session:
        try:
            pattern_id = engine.store_codebase_pattern(
                pattern_type or "memory_code",
                code_snippet,
                f"Code associated with memory {memory_id}: {content[:50]}...",
                language,
                "",
                [f"memory_{memory_id}"]
            )
            result = f'Added memory {memory_id} with code pattern {pattern_id}: {content[:50]}...'
        except Exception:
            result = f'Added memory {memory_id}: {content[:50]}...'
    else:
        result = f'Added memory {memory_id}: {content[:50]}...'
    
    if memory and memory.contradictions:
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


@mcp.tool()
def export_session_to_file(filename: str, format: str = "markdown", ctx: Context = None) -> str:
    if not engine.current_session:
        return "Error: No active session to export"
    
    session = engine.sessions[engine.current_session]
    
    if format.lower() == "markdown":
        content = f"""# Memory Session Export: {session.problem_statement}

    ## Session Details
    - **Session ID**: {session.id}
    - **Started**: {session.started}
    - **Last Updated**: {session.last_updated}
    - **Problem**: {session.problem_statement}
    - **Success Criteria**: {session.success_criteria}
    - **Constraints**: {', '.join(session.constraints)}

    ## Main Thread Memories

    """
        for i, memory_id in enumerate(session.main_thread, 1):
            memory = engine.memories[memory_id]
            content += f"""### {i}. Memory {memory_id}
- **Content**: {memory.content}
- **Confidence**: {memory.confidence}
- **Timestamp**: {memory.timestamp}
- **Dependencies**: {', '.join(memory.dependencies) if memory.dependencies else 'None'}
- **Tags**: {', '.join(memory.tags) if memory.tags else 'None'}
- **Contradictions**: {', '.join(memory.contradictions) if memory.contradictions else 'None'}

"""

        if session.collections:
            content += "## Collections\n\n"
            for collection_id, collection in session.collections.items():
                content += f"""### Collection: {collection.name}
- **ID**: {collection_id}
- **Purpose**: {collection.purpose}
- **Created From**: {collection.created_from}
- **Merged**: {collection.merged}

#### Collection Memories:
"""
                for memory_id in collection.memories:
                    memory = engine.memories[memory_id]
                    content += f"""- **{memory_id}**: {memory.content} (Confidence: {memory.confidence})
"""
                content += "\n"

        if engine.patterns:
            content += "## Detected Patterns\n\n"
            for pattern, count in engine.patterns.items():
                content += f"- **{pattern}**: {count} occurrences\n"

        content += f"""
## Session Summary
- **Total Memories**: {len(session.main_thread)}
- **Collections Created**: {len(session.collections)}
- **Quality Assessment**: {engine._assess_quality()}
"""

    elif format.lower() == "json":
        session_data = {
            "session_id": session.id,
            "problem_statement": session.problem_statement,
            "success_criteria": session.success_criteria,
            "constraints": session.constraints,
            "started": session.started,
            "last_updated": session.last_updated,
            "memories": {},
            "collections": {},
            "patterns": engine.patterns
        }
        for memory_id in session.main_thread:
            memory = engine.memories[memory_id]
            session_data["memories"][memory_id] = asdict(memory)
        for collection_id, collection in session.collections.items():
            session_data["collections"][collection_id] = asdict(collection)
            for memory_id in collection.memories:
                if memory_id not in session_data["memories"]:
                    memory = engine.memories[memory_id]
                    session_data["memories"][memory_id] = asdict(memory)

        content = json.dumps(session_data, indent=2, default=str)

    else:
        return f"Error: Unsupported format '{format}'. Use 'markdown' or 'json'"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Session exported successfully to {filename} ({format} format)"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def export_memories_to_file(filename: str, tags: str = "", ctx: Context = None) -> str:
    if not engine.current_session:
        return "Error: No active session"
    
    session = engine.sessions[engine.current_session]
    tag_filter = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []

    all_memory_ids = session.main_thread.copy()
    for collection in session.collections.values():
        all_memory_ids.extend(collection.memories)

    filtered_memories = {}
    for memory_id in all_memory_ids:
        memory = engine.memories[memory_id]
        if tag_filter and not any(tag in memory.tags for tag in tag_filter):
            continue
        filtered_memories[memory_id] = {
            "id": memory.id,
            "content": memory.content,
            "timestamp": memory.timestamp,
            "confidence": memory.confidence,
            "tags": memory.tags,
            "dependencies": memory.dependencies,
            "contradictions": memory.contradictions,
            "collection_id": memory.collection_id,
            "revision_of": memory.revision_of,
            "is_checkpoint": memory.is_checkpoint
        }

    export_data = {
        "session_id": session.id,
        "export_timestamp": datetime.now().isoformat(),
        "tag_filter": tag_filter,
        "total_memories": len(filtered_memories),
        "memories": filtered_memories
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        return f"Exported {len(filtered_memories)} memories to {filename}" + \
               (f" (filtered by tags: {', '.join(tag_filter)})" if tag_filter else "")
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def create_project_structure(project_name: str, ctx: Context = None) -> str:
    base_path = Path("memory-bank")
    folders = [
        base_path,
        base_path / "thinking_sessions",
        base_path / "domain_knowledge", 
        base_path / "implementation_log",
        base_path / "exports"
    ]
    created_folders = []
    for folder in folders:
        try:
            folder.mkdir(parents=True, exist_ok=True)
            created_folders.append(str(folder))
        except Exception as e:
            return f"Error creating folder {folder}: {str(e)}"
    
    index_content = f"""# {project_name} - Project Knowledge Index

## Project Overview
- **Project Name**: {project_name}
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Knowledge Base Structure**: Memory Bank MCP + Sequential Thinking Framework

## Folder Structure
- `thinking_sessions/` - Sequential thinking session exports
- `domain_knowledge/` - Exported memories organized by domain
- `implementation_log/` - Implementation progress and decisions
- `exports/` - Raw session and memory exports

## Active Sessions
<!-- Link to current thinking sessions -->

## Key Memories by Domain
<!-- Memory collections organized by topic -->

## Implementation Status
<!-- Track what's been built vs planned -->

## Next Actions
<!-- Action items and pending tasks -->

## Usage Notes
- Export thinking sessions regularly with `export_session_to_file()`
- Store domain knowledge with `export_memories_to_file()`
- Update this index when major decisions are made
- Use tags for memory organization and retrieval

---
*Generated by Memory Bank MCP - {datetime.now().isoformat()}*
"""
    index_file = base_path / "project_knowledge_index.md"
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
    except Exception as e:
        return f"Error creating index file: {str(e)}"
    
    readme_content = f"""# Memory Bank for {project_name}

This folder contains the knowledge management system for the {project_name} project.

## Quick Start

1. **Export Current Session**: 
```

export_session_to_file("memory-bank/thinking_sessions/session_YYYY-MM-DD.md")

```

2. **Export Domain Memories**:
```

export_memories_to_file("memory-bank/domain_knowledge/domain_name.json", "tag1,tag2")

```

3. **Update Project Index**:
- Edit `project_knowledge_index.md` with new sessions and key decisions

## File Naming Conventions

- **Thinking Sessions**: `thinking_sessions/session_YYYY-MM-DD_feature-name.md`
- **Domain Knowledge**: `domain_knowledge/domain-name_YYYY-MM-DD.json`  
- **Implementation Logs**: `implementation_log/feature-name_status.md`

## Backup and Sharing

- Commit this folder to version control for team knowledge sharing
- Regular exports ensure no knowledge is lost between sessions
- Use the project index as the main entry point for new team members

---
*Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    readme_file = base_path / "README.md"
    try:
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    except Exception as e:
        return f"Error creating README: {str(e)}"
    
    return f"""Created project structure for '{project_name}':
    {chr(10).join(f'  ✓ {folder}' for folder in created_folders)}
    ✓ project_knowledge_index.md
    ✓ README.md

Usage:
1. export_session_to_file("memory-bank/thinking_sessions/session_{datetime.now().strftime('%Y-%m-%d')}.md")
2. export_memories_to_file("memory-bank/domain_knowledge/{project_name.lower().replace(' ', '_')}.json")
3. Update memory-bank/project_knowledge_index.md with your progress
"""


@mcp.tool()
def load_project_context(project_path: str = "memory-bank", ctx: Context = None) -> str:
 base_path = Path(project_path)
 if not base_path.exists():
     return f"Error: Project path '{project_path}' does not exist. Create it first with create_project_structure()"
 
 context_summary = f"# Project Context from {project_path}\n\n"

 index_file = base_path / "project_knowledge_index.md"
 if index_file.exists():
     try:
         with open(index_file, 'r', encoding='utf-8') as f:
             context_summary += "## Project Index\n"
             context_summary += f.read()[:500] + "...\n\n"
     except Exception as e:
         context_summary += f"Error reading index: {str(e)}\n\n"

 sessions_dir = base_path / "thinking_sessions"
 if sessions_dir.exists():
     sessions = list(sessions_dir.glob("*.md"))
     if sessions:
         context_summary += f"## Recent Thinking Sessions ({len(sessions)} found)\n"
         for session in sorted(sessions)[-5:]:
             context_summary += f"- {session.name}\n"
         context_summary += "\n"

 knowledge_dir = base_path / "domain_knowledge"
 if knowledge_dir.exists():
     knowledge_files = list(knowledge_dir.glob("*.json"))
     if knowledge_files:
         context_summary += f"## Domain Knowledge Files ({len(knowledge_files)} found)\n"
         for kfile in knowledge_files:
             context_summary += f"- {kfile.name}\n"
         context_summary += "\n"

 impl_dir = base_path / "implementation_log"
 if impl_dir.exists():
     impl_files = list(impl_dir.glob("*.md"))
     if impl_files:
         context_summary += f"## Implementation Logs ({len(impl_files)} found)\n"
         for impl_file in impl_files:
             context_summary += f"- {impl_file.name}\n"
         context_summary += "\n"

 context_summary += f"""
## Recommendations
1. Review project_knowledge_index.md for current project status
2. Load latest thinking session to understand recent decisions
3. Check implementation_log/ for what's been completed
4. Start new session building on previous work

Use the files above to understand project history before continuing development.
"""
 
 return context_summary


@mcp.tool()
def update_project_index(section: str, content: str, ctx: Context = None) -> str:
    """Update specific section in project_knowledge_index.md"""
    index_file = Path("memory-bank/project_knowledge_index.md")
    
    if not index_file.exists():
        return "Error: project_knowledge_index.md not found. Create project structure first."
    
    try:
        # Read current content
        with open(index_file, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # Add timestamp to content
        timestamped_content = f"{content}\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        # Simple append to section (could be made more sophisticated)
        section_header = f"## {section}"
        if section_header in current_content:
            # Find section and append
            lines = current_content.split('\n')
            new_lines = []
            in_section = False
            
            for line in lines:
                new_lines.append(line)
                if line.strip() == section_header:
                    in_section = True
                elif line.startswith('## ') and in_section:
                    # Found next section, insert content before it
                    new_lines.insert(-1, f"\n{timestamped_content}")
                    in_section = False
            
            # If section was last, append at end
            if in_section:
                new_lines.append(f"\n{timestamped_content}")
            
            updated_content = '\n'.join(new_lines)
        else:
            # Section doesn't exist, append at end
            updated_content = current_content + f"\n\n{section_header}\n{timestamped_content}"
        
        # Write back
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return f"Updated section '{section}' in project index"
        
    except Exception as e:
        return f"Error updating project index: {str(e)}"


# Coding Integration Tools

@mcp.tool()
def discover_packages(scan_imports: bool = True, ctx: Context = None) -> str:
    """Discover available packages and their APIs"""
    try:
        apis = engine.discover_packages(scan_imports)
        return f"Discovered {len(apis)} package APIs and stored them in the current session"
    except Exception as e:
        return f"Error discovering packages: {str(e)}"


@mcp.tool()
def validate_package_usage(code_snippet: str, ctx: Context = None) -> str:
    """Validate if code uses existing packages appropriately"""
    try:
        check = engine.validate_package_usage(code_snippet)
        result = f"Validation {check.result}: {check.message}"
        if check.suggestions:
            result += f"\nSuggestions:\n" + "\n".join(f"- {s}" for s in check.suggestions)
        return result
    except Exception as e:
        return f"Error validating package usage: {str(e)}"


@mcp.tool()
def explore_existing_apis(functionality: str, ctx: Context = None) -> str:
    """Explore existing APIs that might provide the needed functionality"""
    try:
        apis = engine.explore_existing_apis(functionality)
        if not apis:
            return f"No existing APIs found for '{functionality}'"
        
        result = f"Found {len(apis)} existing APIs for '{functionality}':\n"
        for api in apis:
            result += f"- {api.api_signature}\n"
            if api.usage_example:
                result += f"  Example: {api.usage_example}\n"
        return result
    except Exception as e:
        return f"Error exploring APIs: {str(e)}"


@mcp.tool()
def store_codebase_pattern(pattern_type: str, code_snippet: str, description: str = "",
                          language: str = "", file_path: str = "", tags: str = "",
                          ctx: Context = None) -> str:
    """Store a codebase pattern for future reference"""
    try:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []
        pattern_id = engine.store_codebase_pattern(
            pattern_type, code_snippet, description, language, file_path, tag_list
        )
        return f"Stored codebase pattern {pattern_id} (type: {pattern_type})"
    except Exception as e:
        return f"Error storing pattern: {str(e)}"


@mcp.tool()
def load_codebase_context(project_path: str = "", ctx: Context = None) -> str:
    """Load existing codebase structure and patterns into memory"""
    try:
        context = engine.load_codebase_context(project_path or None)
        result = f"Loaded codebase context from {context['project_path']}\n"
        result += f"Files scanned: {len(context['file_structure'])}\n"
        result += f"Patterns stored: {len(context['patterns'])}\n"
        if context.get('error'):
            result += f"Warning: {context['error']}\n"
        return result
    except Exception as e:
        return f"Error loading codebase context: {str(e)}"


@mcp.tool()
def prevent_reinvention_check(functionality_description: str, ctx: Context = None) -> str:
    """Check if functionality might already exist in known packages"""
    try:
        # This is a comprehensive check that combines API exploration and validation
        apis = engine.explore_existing_apis(functionality_description)
        
        if not apis:
            return f"No existing APIs found for '{functionality_description}'. Safe to implement."
        
        result = f"⚠️ POTENTIAL REINVENTION DETECTED ⚠️\n"
        result += f"Found {len(apis)} existing APIs for '{functionality_description}':\n"
        
        for api in apis:
            result += f"\n📦 {api.package_name}\n"
            result += f"  API: {api.api_signature}\n"
            if api.usage_example:
                result += f"  Example: {api.usage_example}\n"
            if api.documentation:
                result += f"  Docs: {api.documentation[:100]}...\n"
        
        result += f"\n💡 Recommendation: Consider using these existing APIs instead of implementing from scratch."
        return result
    except Exception as e:
        return f"Error checking for reinvention: {str(e)}"


@mcp.resource('codebase://packages')
def get_discovered_packages() -> str:
    """Get discovered packages in the current session"""
    try:
        if not engine.current_session:
            return "No active session"
        
        apis = engine.db_adapter.get_package_apis(engine.current_session)
        packages = {}
        
        for api in apis:
            if api.package_name not in packages:
                packages[api.package_name] = []
            packages[api.package_name].append({
                'signature': api.api_signature,
                'usage_example': api.usage_example,
                'documentation': api.documentation
            })
        
        return json.dumps(packages, indent=2)
    except Exception as e:
        return f"Error getting packages: {str(e)}"


@mcp.resource('codebase://patterns')
def get_codebase_patterns() -> str:
    """Get stored codebase patterns"""
    try:
        if not engine.current_session:
            return "No active session"
        
        patterns = engine.db_adapter.get_codebase_patterns(engine.current_session)
        pattern_data = []
        
        for pattern in patterns:
            pattern_data.append({
                'id': pattern.id,
                'type': pattern.pattern_type,
                'description': pattern.description,
                'language': pattern.language,
                'file_path': pattern.file_path,
                'tags': pattern.tags,
                'code_snippet': pattern.code_snippet[:200] + "..." if len(pattern.code_snippet) > 200 else pattern.code_snippet
            })
        
        return json.dumps(pattern_data, indent=2)
    except Exception as e:
        return f"Error getting patterns: {str(e)}"


@mcp.resource('codebase://validation-checks')
def get_validation_checks() -> str:
    """Get validation checks for the current session"""
    try:
        if not engine.current_session:
            return "No active session"
        
        checks = engine.db_adapter.get_validation_checks(engine.current_session)
        check_data = []
        
        for check in checks:
            check_data.append({
                'id': check.id,
                'type': check.check_type,
                'result': check.result,
                'message': check.message,
                'suggestions': check.suggestions,
                'created_at': check.created_at
            })
        
        return json.dumps(check_data, indent=2)
    except Exception as e:
        return f"Error getting validation checks: {str(e)}"


def main():
    mcp.run()


if __name__ == '__main__':
    main()