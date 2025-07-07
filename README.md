# Memory Bank MCP

A Model Context Protocol (MCP) server that provides persistent memory storage and retrieval capabilities for Claude Code, enabling structured knowledge management with session-based thinking, collections, exports, and project organization.

## Features

### Core Memory Management
- **Session-Based Thinking**: Structured problem-solving with memory sessions
- **Persistent Memory Storage**: Store and retrieve memories across sessions
- **Collection Management**: Organize related memories into logical groups
- **Memory Revision**: Update and refine memories with new insights
- **Dependency Tracking**: Link memories with logical dependencies

### Export & Project Management
- **Session Export**: Export complete thinking sessions to markdown/JSON
- **Filtered Memory Export**: Export memories by tags and criteria
- **Project Structure**: Generate organized folder hierarchies for teams
- **Context Loading**: Load existing project knowledge seamlessly
- **Index Management**: Maintain project documentation automatically

### Search & Analytics
- **Tag-Based Search**: Find memories using tags and content search
- **Importance Scoring**: Prioritize memories by importance level (0.0-1.0)
- **Session Analysis**: Quality metrics and contradiction detection
- **Pattern Recognition**: Identify recurring themes and insights
- **Resource Access**: Visual memory bank structure and analytics

## Quick Start (Beginners)

### 1. Basic Session Workflow

```python
# Start a thinking session (REQUIRED FIRST STEP)
create_memory_session(
    problem="Learn the new authentication system",
    success_criteria="Understand implementation and security patterns",
    constraints="Focus on practical examples"
)

# Store key insights
store_memory(
    content="JWT tokens expire after 15 minutes, refresh needed",
    tags="auth,security,jwt",
    importance=0.8
)

# Analyze your thinking
analyze_memories()

# Export when done
export_session_to_file("learning_session.md")
```

### 2. What Happens Next?

After completing a session:
1. **Analyze**: Use `analyze_memories()` to check quality
2. **Export**: Use `export_session_to_file()` to save your work
3. **Organize**: Use `create_project_structure()` for team projects
4. **Share**: Export filtered memories with `export_memories_to_file()`

### 3. Key Concept: Session-First Approach

**⚠️ Important**: You must create a session before using other tools. This is different from the original memory bank approach.

```python
# ❌ This will fail
store_memory("Some insight")  # No active session

# ✅ This works
create_memory_session("My problem", "My goals")
store_memory("Some insight")  # Now it works
```

## Installation

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Quick Setup

```bash
git clone <your-repo-url>
cd memory-bank-mcp
uv sync
```

### Installation Options

#### Option 1: Direct UV Run
```bash
uv run main.py
```

#### Option 2: Global Installation
```bash
uv tool install .
memory-bank-mcp
```

#### Option 3: Development Mode
```bash
uv pip install -e .
```

## Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "memory-bank": {
      "command": "uv",
      "args": [
        "run",
        "/path/to/memory-bank-mcp/main.py"
      ]
    }
  }
}
```

## Advanced Workflows (Integration Patterns)

### 1. Complete Session-to-Project Pipeline

```python
# Phase 1: Thinking Session
create_memory_session(
    problem="Implement user authentication system",
    success_criteria="Secure, scalable auth with proper error handling",
    constraints="Must integrate with existing user database"
)

# Store insights and decisions
store_memory(
    content="Use JWT with refresh tokens for session management",
    tags="auth,jwt,security",
    importance=0.9
)

store_memory(
    content="Implement rate limiting on login attempts",
    tags="security,rate-limiting",
    importance=0.8,
    dependencies="previous_memory_id"
)

# Create collections for organization
create_collection(
    name="Auth Architecture",
    from_memory="jwt_memory_id",
    purpose="Group all authentication-related decisions"
)

# Phase 2: Quality Check & Export
analyze_memories()  # Check for contradictions and quality
export_session_to_file("auth_implementation_session.md")
export_memories_to_file("auth_decisions.json", "auth,security")

# Phase 3: Project Organization
create_project_structure("Authentication System")
update_project_index("Implementation Status", "JWT auth decided, rate limiting planned")
```

### 2. Multi-Session Project Workflow

```python
# Session 1: Requirements gathering
create_memory_session("Analyze auth requirements", "Clear requirements doc")
# ... store requirements memories ...
export_session_to_file("memory-bank/thinking_sessions/requirements_2024-01-15.md")

# Session 2: Architecture design
create_memory_session("Design auth architecture", "Scalable secure design")
load_project_context("memory-bank")  # Load previous work
# ... store architecture memories ...
export_session_to_file("memory-bank/thinking_sessions/architecture_2024-01-16.md")

# Session 3: Implementation planning
create_memory_session("Plan implementation steps", "Clear development roadmap")
# ... reference previous sessions ...
```

### 3. Team Collaboration Patterns

```python
# Developer A: Initial research
create_memory_session("Research auth libraries", "Evaluate options")
# ... research and store findings ...
export_session_to_file("memory-bank/thinking_sessions/auth_research_alice.md")
create_project_structure("Auth System Research")

# Developer B: Load context and continue
load_project_context("memory-bank")  # See Alice's work
create_memory_session("Design auth flow", "Detailed implementation plan")
# ... build on Alice's research ...
export_memories_to_file("memory-bank/domain_knowledge/auth_decisions.json")
update_project_index("Team Progress", "Research complete, design in progress")
```

### 4. Error Handling & Recovery

```python
# Check session state
analyze_memories()  # Look for contradictions or quality issues

# Revise memories when new information emerges
revise_memory(
    memory_id="old_jwt_decision",
    new_content="Use OAuth 2.0 instead of custom JWT implementation",
    confidence=0.9
)

# Merge collections when organizing
merge_collection("security_collection", "main_auth_collection")

# Export with error handling
try:
    export_session_to_file("backup_session.md")
except Exception as e:
    print(f"Export failed: {e}")
    # Fallback to JSON export
    export_session_to_file("backup_session.json", "json")
```

## Tool Hierarchy & Workflow

### Foundation Layer (Start Here)

| Tool | Description | Required First? |
|------|-------------|----------------|
| `create_memory_session` | Start a structured thinking session | ✅ **YES** |

### Core Memory Operations (Session Required)

| Tool | Description | Dependencies |
|------|-------------|-------------|
| `store_memory` | Store insights with tags and confidence | Active session |
| `revise_memory` | Update existing memories with new insights | Active session |
| `create_collection` | Group related memories for organization | Active session, existing memory |
| `merge_collection` | Integrate collections into main thread | Active session, existing collection |

### Analysis & Quality Control

| Tool | Description | When to Use |
|------|-------------|------------|
| `analyze_memories` | Get session quality metrics and contradictions | Before export |

### Export & Sharing

| Tool | Description | Typical Workflow |
|------|-------------|----------------|
| `export_session_to_file` | Export complete session to markdown/JSON | After analysis |
| `export_memories_to_file` | Export filtered memories by tags | For sharing specific insights |

### Project Management

| Tool | Description | Team Usage |
|------|-------------|----------|
| `create_project_structure` | Generate organized folder hierarchy | Project initialization |
| `load_project_context` | Load existing project knowledge | Team member onboarding |
| `update_project_index` | Maintain project documentation | Regular updates |

### Legacy Tools (Original Memory Bank)

| Tool | Description | Status |
|------|-------------|-------|
| `create_memory_bank` | Initialize memory bank | ⚠️ Superseded by sessions |
| `search_memories` | Search by content/tags | ⚠️ Limited without sessions |
| `get_memory_stats` | Basic statistics | ⚠️ Use `analyze_memories` instead |

## Session Management (New Paradigm)

### Why Sessions?

The session-based approach provides:
- **Structured thinking**: Problem → insights → solution
- **Quality control**: Contradiction detection and confidence tracking
- **Exportability**: Complete thinking sessions for sharing
- **Project continuity**: Multiple related sessions for complex projects

### Session Lifecycle

```python
# 1. Start session
create_memory_session(
    problem="Clear problem statement",
    success_criteria="Measurable success criteria",
    constraints="Limitations and boundaries"
)

# 2. Build knowledge
store_memory("Key insight 1", tags="tag1,tag2", importance=0.8)
store_memory("Key insight 2", dependencies="previous_memory_id")

# 3. Organize insights
create_collection("Related Insights", from_memory="insight_id", purpose="Group similar thoughts")

# 4. Refine understanding
revise_memory("old_insight_id", "Updated insight with new information")

# 5. Quality check
analyze_memories()  # Check for contradictions, quality assessment

# 6. Export results
export_session_to_file("session_summary.md")
export_memories_to_file("key_insights.json", "important,decision")
```

### Session vs Memory Bank

| Aspect | Session-Based | Original Memory Bank |
|--------|---------------|---------------------|
| **Structure** | Problem-focused | General storage |
| **Quality** | Built-in analysis | Manual checking |
| **Export** | Rich session context | Basic memory lists |
| **Collaboration** | Project-oriented | Individual-focused |
| **Workflow** | Guided progression | Free-form |

## Export Workflows

### Complete Session Export

```python
# Export full session with all context
export_session_to_file(
    filename="project_analysis_session.md",
    format="markdown"  # or "json"
)
```

**Generated Output Includes:**
- Session details (problem, criteria, constraints)
- All memories with timestamps and confidence
- Collections and their relationships
- Detected patterns and contradictions
- Quality assessment summary

### Filtered Memory Export

```python
# Export specific memories by tags
export_memories_to_file(
    filename="security_decisions.json",
    tags="security,authentication,authorization"
)
```

**Use Cases:**
- Share domain-specific insights
- Create focused documentation
- Build knowledge bases by topic
- Generate reports for stakeholders

### Export Naming Conventions

- **Sessions**: `thinking_sessions/session_YYYY-MM-DD_feature-name.md`
- **Domain Knowledge**: `domain_knowledge/topic-name_YYYY-MM-DD.json`
- **Implementation Logs**: `implementation_log/feature-name_status.md`

## Project Structure Tools

### Team Knowledge Management

```python
# Initialize project structure
create_project_structure("Authentication System Redesign")
```

**Creates:**
```
memory-bank/
├── thinking_sessions/     # Session exports
├── domain_knowledge/      # Filtered memory exports
├── implementation_log/    # Progress tracking
├── exports/              # Raw session data
├── project_knowledge_index.md  # Main entry point
└── README.md             # Usage instructions
```

### Team Collaboration Workflow

```python
# Team member A: Initialize project
create_project_structure("Feature Development")
create_memory_session("Research phase", "Evaluate options")
# ... do research ...
export_session_to_file("memory-bank/thinking_sessions/research_alice.md")
update_project_index("Research Status", "Library evaluation complete")

# Team member B: Load context and continue
load_project_context("memory-bank")  # See Alice's work summary
create_memory_session("Design phase", "Create implementation plan")
# ... build on Alice's research ...
export_memories_to_file("memory-bank/domain_knowledge/design_decisions.json")
update_project_index("Design Status", "Architecture decisions finalized")
```

### Context Loading

```python
# Load existing project context
context_summary = load_project_context("memory-bank")
```

**Provides:**
- Project index overview
- Recent thinking sessions (last 5)
- Available domain knowledge files
- Implementation log summaries
- Recommended next steps

## Resources

Access structured data through MCP resources:

- `memory://tree` - Complete memory structure with dependencies
- `memory://analysis` - Session quality metrics and patterns
- `memory://patterns` - Detected patterns and learning insights

## Team Adoption Guide

### Role-Based Usage Patterns

#### Project Lead
- **Initialize**: `create_project_structure(project_name)`
- **Coordinate**: `load_project_context()` to monitor progress
- **Maintain**: `update_project_index()` with milestones
- **Review**: Regular `analyze_memories()` for quality control

#### Individual Developer
- **Start**: `create_memory_session()` for each feature/task
- **Document**: `store_memory()` for key decisions and insights
- **Organize**: `create_collection()` for related concepts
- **Share**: `export_session_to_file()` when complete

#### Team Member (Continuing Work)
- **Onboard**: `load_project_context()` to understand current state
- **Build**: `create_memory_session()` referencing previous work
- **Contribute**: `export_memories_to_file()` for domain knowledge
- **Update**: `update_project_index()` with progress

### Collaboration Workflows

#### Handoff Pattern
```python
# Developer A completes research
export_session_to_file("memory-bank/thinking_sessions/research_complete.md")
export_memories_to_file("memory-bank/domain_knowledge/tech_evaluation.json", "evaluation,technology")
update_project_index("Research Phase", "Technology evaluation complete - recommend FastAPI")

# Developer B takes over implementation
load_project_context("memory-bank")  # Get full context
create_memory_session("Implementation planning", "Detailed development roadmap")
# Reference A's research in new memories
```

#### Review & Refinement Pattern
```python
# Team reviews session quality
analyze_memories()  # Check for contradictions

# Refine insights based on team feedback
revise_memory(
    memory_id="initial_approach",
    new_content="Revised approach based on team review",
    confidence=0.9
)

# Re-export updated session
export_session_to_file("memory-bank/thinking_sessions/approach_v2.md")
```

### Error Handling Examples

#### Session Recovery
```python
# Check if session exists
try:
    analyze_memories()
except Exception:
    # No active session, create one
    create_memory_session("Recovery session", "Restore context")
```

#### Export Failures
```python
# Robust export with fallback
def safe_export(filename, format="markdown"):
    try:
        return export_session_to_file(filename, format)
    except Exception as e:
        print(f"Export failed: {e}")
        # Try JSON format as fallback
        if format != "json":
            return safe_export(filename.replace(".md", ".json"), "json")
        return f"Export failed: {e}"
```

#### Collection Management
```python
# Safe collection operations
try:
    merge_collection("temp_collection", "main_thread")
except Exception as e:
    print(f"Merge failed: {e}")
    # Keep collections separate for manual review
    export_memories_to_file("temp_collection_backup.json")
```

### Version Control Integration

```bash
# Include memory-bank in git
git add memory-bank/
git commit -m "Add thinking session: auth system research"

# .gitignore suggestions
echo "memory-bank/exports/*.json" >> .gitignore  # Exclude large exports
echo "!memory-bank/exports/README.md" >> .gitignore  # Keep documentation
```

### Quality Assurance

```python
# Regular quality checks
analysis = analyze_memories()
if analysis['contradictions_found'] > 0:
    print("⚠️  Contradictions detected - review needed")
if analysis['average_confidence'] < 0.7:
    print("⚠️  Low confidence - consider revision")
if analysis['memory_quality'] == 'insufficient':
    print("⚠️  Need more detailed memories")
```

## Best Practices

### Session Management
1. **Clear Problem Statements**: Define specific, actionable problems
2. **Measurable Success Criteria**: Set concrete goals for session completion
3. **Meaningful Constraints**: Document limitations and boundaries
4. **Regular Analysis**: Use `analyze_memories()` to check quality

### Memory Storage
1. **Descriptive Content**: Write clear, actionable insights
2. **Relevant Tags**: Use consistent tagging for discoverability
3. **Appropriate Confidence**: 0.8-1.0 for decisions, 0.5-0.7 for hypotheses
4. **Logical Dependencies**: Link related memories for context

### Export Strategy
1. **Session Documentation**: Export complete sessions for sharing
2. **Filtered Exports**: Create domain-specific knowledge files
3. **Consistent Naming**: Follow project naming conventions
4. **Regular Backups**: Export sessions before major changes

### Team Collaboration
1. **Project Structure**: Initialize structure before team work
2. **Context Loading**: Always load context before starting new sessions
3. **Index Updates**: Keep project index current with progress
4. **Quality Reviews**: Team review of session quality and insights

### Error Prevention
1. **Session-First**: Always create session before other operations
2. **Quality Checks**: Analyze before export
3. **Backup Strategy**: Multiple export formats for safety
4. **Version Control**: Track memory-bank folder in git

## Complete Example Workflow

### Individual Developer Session

```python
# 1. Start thinking session
create_memory_session(
    problem="Implement caching strategy for API responses",
    success_criteria="Efficient caching with proper invalidation",
    constraints="Must work with existing Redis infrastructure"
)

# 2. Store research and decisions
store_memory(
    content="Redis TTL of 300 seconds works well for user data",
    tags="caching,redis,performance",
    importance=0.8
)

store_memory(
    content="Cache invalidation needed on user profile updates",
    tags="caching,invalidation,user-data",
    importance=0.9,
    dependencies="previous_memory_id"
)

# 3. Organize related insights
create_collection(
    name="Caching Strategy",
    from_memory="redis_ttl_memory_id",
    purpose="Group all caching-related decisions"
)

# 4. Quality check
analysis = analyze_memories()
print(f"Quality: {analysis['memory_quality']}, Confidence: {analysis['average_confidence']}")

# 5. Export session
export_session_to_file("caching_implementation_session.md")
export_memories_to_file("caching_decisions.json", "caching,decision")
```

### Team Project Workflow

```python
# Project initialization
create_project_structure("API Performance Optimization")

# Developer A: Research phase
create_memory_session("Cache strategy research", "Evaluate caching options")
# ... research memories ...
export_session_to_file("memory-bank/thinking_sessions/cache_research_2024-01-15.md")
update_project_index("Research Status", "Cache strategy options evaluated")

# Developer B: Implementation phase
load_project_context("memory-bank")  # Load A's research
create_memory_session("Cache implementation", "Working cache system")
# ... implementation memories ...
export_memories_to_file("memory-bank/domain_knowledge/cache_implementation.json")
update_project_index("Implementation Status", "Redis caching implemented")

# Team review
analyze_memories()  # Check quality
# ... revise memories based on review ...
export_session_to_file("memory-bank/thinking_sessions/cache_final_2024-01-16.md")
```

### Multi-Session Project

```python
# Session 1: Problem analysis
create_memory_session("Analyze performance issues", "Identify bottlenecks")
# ... analysis memories ...
export_session_to_file("memory-bank/thinking_sessions/performance_analysis.md")

# Session 2: Solution design
create_memory_session("Design optimization strategy", "Comprehensive solution")
load_project_context("memory-bank")  # Reference previous analysis
# ... solution memories ...
export_session_to_file("memory-bank/thinking_sessions/optimization_design.md")

# Session 3: Implementation planning
create_memory_session("Plan implementation steps", "Detailed roadmap")
# ... planning memories ...
export_session_to_file("memory-bank/thinking_sessions/implementation_plan.md")

# Final project export
export_memories_to_file("memory-bank/domain_knowledge/performance_optimization.json", "performance,optimization,decision")
```

## Installation

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Quick Setup

```bash
git clone <your-repo-url>
cd memory-bank-mcp
uv sync
```

### Testing Installation

```bash
uv run -c "import main; print('Installation successful')"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review usage examples above