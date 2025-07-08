# 🧠 Memory Bank MCP

A Model Context Protocol (MCP) server for Claude Code that enables persistent memory, structured thinking, team collaboration, and project-based knowledge management — with full export, revision, and analysis capabilities. **Now featuring comprehensive coding integration to prevent package reinvention and enforce existing API usage.**

---

## 🚀 Features

### 🧠 Core Memory Management
- **Session-Based Thinking**: Start with a problem and track related insights
- **Persistent Storage**: Store and retrieve memories across sessions
- **Collections**: Group related memories with clear purposes
- **Revision & Dependencies**: Refine ideas, track changes and links

### 💻 Coding Integration (NEW)
- **Package Discovery**: Auto-scan installed packages and extract API signatures
- **Reinvention Prevention**: Validate code against existing libraries before implementation
- **Code Pattern Storage**: Store and retrieve proven code templates and examples
- **Coding Sessions**: Specialized session types for development workflows
- **Validation Gates**: Catch potential issues and suggest existing solutions

### 📦 Project & Export System
- **Export to Markdown/JSON**: Full or filtered memory exports
- **Project Structure Generation**: Standardized folders for teams
- **Project Indexing**: Maintain status updates and documentation
- **Context Loading**: Load ongoing work for seamless continuation

### 📊 Search & Analytics
- **Tag-Based Search**: Find insights by topics or keywords
- **Importance Scores**: Prioritize content using confidence metrics
- **Session Analysis**: Detect contradictions, gaps, and themes

---

## ⚡ Quick Start

```bash
git clone https://github.com/spideynolove/memory-bank-mcp
cd memory-bank-mcp
uv sync
uv run main.py
````

> Requires Python 3.10+ and [uv](https://github.com/astral-sh/uv)

---

## 🛠 Installation Options

* **Direct run**: `uv run main.py`
* **Global install**: `uv tool install .`
* **Development mode**: `uv pip install -e .`

---

## 🧪 Test

```bash
uv run -c "import main; print('Installation successful')"
```

---

## 🔧 Session Workflow (API Example)

### Basic Memory Session
```python
create_memory_session(
    problem="Implement user auth",
    success_criteria="Secure + scalable",
    constraints="Use existing DB"
)

store_memory(
    content="Use JWT with refresh",
    tags="auth,jwt",
    importance=0.9
)

analyze_memories()
export_session_to_file("auth_session.md")
```

### Coding Session with Validation
```python
# Start a coding-specific session
create_memory_session(
    problem="Build HTTP client for API integration",
    success_criteria="Efficient, maintainable, using existing libraries",
    constraints="Must handle auth, retries, rate limiting",
    session_type="coding_session"
)

# Discover what packages are already available
discover_packages()

# Check if functionality already exists before coding
prevent_reinvention_check("HTTP client for REST APIs")
# Returns: Found existing APIs: requests.get(), urllib3.request(), etc.

# Validate code before implementation
validate_package_usage("""
def make_request(url):
    import urllib.request
    return urllib.request.urlopen(url).read()
""")
# Returns: Warning - Consider using requests library

# Store proven patterns for reuse
store_codebase_pattern(
    pattern_type="api_usage",
    code_snippet="import requests\nresponse = requests.get(url, headers=headers)",
    description="Standard HTTP GET with auth headers",
    language="python"
)
```

> ⚠️ Must start with `create_memory_session()` before storing anything.

---

## 🧩 Session Tools

### Core Memory Tools
| Tool                        | Description                            |
| --------------------------- | -------------------------------------- |
| `create_memory_session()`   | Start a new thinking session (now supports `session_type`) |
| `store_memory()`            | Save insights with tags and confidence (now supports `code_snippet`) |
| `revise_memory()`           | Update previous memories               |
| `create_collection()`       | Group insights                         |
| `merge_collection()`        | Combine collections                    |
| `analyze_memories()`        | Run quality checks                     |
| `export_session_to_file()`  | Export full sessions                   |
| `export_memories_to_file()` | Export filtered memories               |
| `load_project_context()`    | Resume prior sessions                  |
| `update_project_index()`    | Document team progress                 |

### 💻 Coding Integration Tools (NEW)
| Tool                         | Description                                    |
| ---------------------------- | ---------------------------------------------- |
| `discover_packages()`        | Auto-scan installed packages and extract APIs |
| `validate_package_usage()`   | Validate code against existing packages       |
| `explore_existing_apis()`    | Find existing APIs for needed functionality   |
| `prevent_reinvention_check()`| Comprehensive reinvention prevention warning  |
| `store_codebase_pattern()`   | Store code patterns with metadata             |
| `load_codebase_context()`    | Load project structure into memory            |

### Enhanced Tools
- **`create_memory_session()`**: Now accepts `session_type` parameter for `coding_session`, `debugging_session`, `architecture_session`
- **`store_memory()`**: Now accepts `code_snippet`, `language`, `pattern_type` parameters for code integration

---

## 💻 Coding Session Types & Workflows

### Session Types
- **`coding_session`**: General development work with package discovery and validation
- **`debugging_session`**: Problem-solving focused with enhanced error pattern storage  
- **`architecture_session`**: System design with emphasis on integration patterns

### Validation Workflow
```python
# 1. Start coding session
create_memory_session("Build user service", "Efficient API", session_type="coding_session")

# 2. Discover available packages
discover_packages()
# Scans environment and stores: requests, fastapi, pydantic, etc.

# 3. Check for existing solutions before coding
prevent_reinvention_check("HTTP server framework")
# ⚠️ POTENTIAL REINVENTION DETECTED ⚠️
# Found existing APIs: fastapi.FastAPI(), flask.Flask(), etc.

# 4. Validate specific code patterns
validate_package_usage("""
class CustomHTTPServer:
    def __init__(self, port):
        self.port = port
    def start(self):
        # custom server implementation
        pass
""")
# Warning: Consider using FastAPI or Flask instead

# 5. Store proven patterns for team reuse
store_codebase_pattern(
    pattern_type="api_endpoint",
    code_snippet="""
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}
""",
    description="Standard FastAPI endpoint pattern",
    language="python",
    tags="api,fastapi,endpoint"
)
```

### 🔍 MCP Resources for Coding

Access coding data through these resources:

| Resource                     | Description                           |
| ---------------------------- | ------------------------------------- |
| `codebase://packages`        | View discovered packages in session   |
| `codebase://patterns`        | View stored code patterns             |
| `codebase://validation-checks` | View validation check history        |

#### Example Usage
```python
# View discovered packages
# Resource: codebase://packages
{
  "requests": [
    {"signature": "requests.get(url, **kwargs)", "usage_example": "requests.get('https://api.example.com')"},
    {"signature": "requests.post(url, data=None, json=None, **kwargs)", "usage_example": "requests.post(url, json={'key': 'value'})"}
  ],
  "fastapi": [
    {"signature": "fastapi.FastAPI()", "usage_example": "app = FastAPI()"}
  ]
}

# View code patterns  
# Resource: codebase://patterns
[
  {
    "id": "abc123",
    "type": "api_endpoint", 
    "description": "Standard FastAPI endpoint",
    "language": "python",
    "tags": ["api", "fastapi"],
    "code_snippet": "@app.get('/users/{user_id}')\nasync def get_user(user_id: int)..."
  }
]
```

---

## 🏗 Project Structure

```text
memory-bank/
├── thinking_sessions/
├── domain_knowledge/
├── implementation_log/
├── exports/
├── project_knowledge_index.md
└── README.md
```

Initialize with:

```python
create_project_structure("My Project")
```

---

## 🧑‍🤝‍🧑 Collaboration Patterns

### Developer A - Research Phase
```python
create_memory_session("Research auth libs", "Evaluate options", session_type="coding_session")
discover_packages()  # Find available auth libraries
prevent_reinvention_check("JWT authentication")
store_memory("Use FastAPI JWT plugin", code_snippet="from fastapi_jwt import JWT", language="python")
export_session_to_file("thinking_sessions/research_alice.md")
```

### Developer B - Implementation Phase
```python
load_project_context("memory-bank")
create_memory_session("Design auth flow", "Complete plan", session_type="architecture_session")

# Load existing patterns from team
# Resource: codebase://patterns shows Alice's JWT pattern

validate_package_usage("""
def custom_jwt_encode(payload):
    import base64
    return base64.b64encode(json.dumps(payload).encode())
""")
# Warning: Consider using existing JWT libraries

export_memories_to_file("domain_knowledge/auth_decisions.json")
```

### Developer C - Debugging Phase
```python
create_memory_session("Fix auth token expiry", "Resolve production issue", session_type="debugging_session")
explore_existing_apis("JWT token refresh")
store_codebase_pattern("debugging", "Token expiry logs", "Check exp claim in JWT payload")
```

---

## 💥 Error Recovery

```python
try:
    analyze_memories()
except:
    create_memory_session("Recovery", "Rebuild context")
```

Safe export:

```python
def safe_export(path):
    try:
        export_session_to_file(path)
    except:
        export_session_to_file(path.replace(".md", ".json"))
```

---

## 🧑‍💼 Role-Based Usage

| Role         | Actions                                                                 |
| ------------ | ----------------------------------------------------------------------- |
| Lead         | `create_project_structure()`, `update_project_index()`, `discover_packages()` |
| Developer    | `create_memory_session()`, `validate_package_usage()`, `store_codebase_pattern()` |
| New Teammate | `load_project_context()`, `explore_existing_apis()`, `prevent_reinvention_check()` |

## 🗄️ Database Schema Extensions

The coding integration adds 4 new tables to the SQLite database:

### New Tables
```sql
-- Package APIs discovered in sessions
CREATE TABLE package_apis (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    package_name TEXT NOT NULL,        -- e.g., "requests"
    api_signature TEXT NOT NULL,       -- e.g., "requests.get(url, **kwargs)"
    usage_example TEXT,                -- e.g., "requests.get('https://api.com')"
    documentation TEXT,                -- API documentation excerpt
    discovered_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- Code patterns stored for reuse
CREATE TABLE codebase_patterns (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,        -- 'api_usage', 'integration', 'structure'
    code_snippet TEXT NOT NULL,       -- Actual code
    description TEXT,                  -- Human description
    language TEXT,                     -- 'python', 'javascript', etc.
    file_path TEXT,                    -- Original file path if applicable
    tags_json TEXT DEFAULT '[]',       -- JSON array of tags
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Coding session metadata
CREATE TABLE coding_sessions (
    session_id TEXT PRIMARY KEY,
    session_type TEXT NOT NULL,       -- 'coding_session', 'debugging_session', 'architecture_session'
    project_path TEXT,               -- Project directory
    language TEXT,                   -- Primary language
    framework TEXT,                  -- Primary framework
    packages_discovered INTEGER,     -- Count of packages found
    patterns_stored INTEGER,         -- Count of patterns stored
    validation_checks INTEGER        -- Count of validations run
);

-- Validation check results  
CREATE TABLE validation_checks (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    check_type TEXT NOT NULL,         -- 'package_usage', 'reinvention_prevention'
    target_code TEXT NOT NULL,       -- Code that was validated
    result TEXT NOT NULL,            -- 'passed', 'failed', 'warning'
    message TEXT,                    -- Human-readable result
    suggestions_json TEXT,           -- JSON array of suggestions
    created_at TIMESTAMP
);
```

### Migration & Compatibility
- **Automatic Migration**: New tables created automatically when first used
- **Backwards Compatible**: Existing sessions continue to work unchanged
- **Schema Evolution**: Database adapts seamlessly to new features
- **Data Isolation**: Coding features are project-specific via session isolation

---

## 📘 Best Practices

### General Memory Management
* Always start with `create_memory_session()`
* Use specific tags for search/export
* Run `analyze_memories()` before final export
* Use collections for structure
* Track everything under version control

### Coding Integration Best Practices
* **Start coding sessions with package discovery**: `discover_packages()` first
* **Check for reinvention before coding**: Use `prevent_reinvention_check()` early
* **Validate code patterns**: Run `validate_package_usage()` before implementation
* **Store proven patterns**: Use `store_codebase_pattern()` for team knowledge sharing
* **Load project context**: Always `load_codebase_context()` when joining existing projects
* **Use appropriate session types**: 
  - `coding_session` for general development
  - `debugging_session` for problem-solving
  - `architecture_session` for system design

### Team Workflow
```python
# 1. Project Lead: Set up discovery
create_memory_session("Project kickoff", "Team alignment", session_type="architecture_session")
discover_packages()  # Establish baseline
load_codebase_context()  # Scan existing code

# 2. Developers: Check before coding
prevent_reinvention_check("user authentication")  # Before starting work
validate_package_usage(proposed_code)  # Before committing

# 3. Knowledge Sharing: Store patterns
store_codebase_pattern("error_handling", error_code, "Team standard error pattern")
export_session_to_file("team_standards.md")
```

---

## 🧩 Claude Desktop Integration

```json
{
  "mcpServers": {
    "memory-bank": {
      "command": "uv",
      "args": ["run", "/path/to/memory-bank-mcp/main.py"]
    }
  }
}
```

---

## 📄 License

MIT License

---

## 🆘 Support

* Open an issue on GitHub
* Read the usage examples above