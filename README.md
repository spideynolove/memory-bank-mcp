# 🧠 Memory Bank MCP

A Model Context Protocol (MCP) server for Claude Code that enables persistent memory, structured thinking, team collaboration, and project-based knowledge management — with full export, revision, and analysis capabilities.

---

## 🚀 Features

### 🧠 Core Memory Management
- **Session-Based Thinking**: Start with a problem and track related insights
- **Persistent Storage**: Store and retrieve memories across sessions
- **Collections**: Group related memories with clear purposes
- **Revision & Dependencies**: Refine ideas, track changes and links

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

> ⚠️ Must start with `create_memory_session()` before storing anything.

---

## 🧩 Session Tools

| Tool                        | Description                            |
| --------------------------- | -------------------------------------- |
| `create_memory_session()`   | Start a new thinking session           |
| `store_memory()`            | Save insights with tags and confidence |
| `revise_memory()`           | Update previous memories               |
| `create_collection()`       | Group insights                         |
| `merge_collection()`        | Combine collections                    |
| `analyze_memories()`        | Run quality checks                     |
| `export_session_to_file()`  | Export full sessions                   |
| `export_memories_to_file()` | Export filtered memories               |
| `load_project_context()`    | Resume prior sessions                  |
| `update_project_index()`    | Document team progress                 |

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

### Developer A

```python
create_memory_session("Research auth libs", "Evaluate options")
store_memory("Use FastAPI JWT plugin")
export_session_to_file("thinking_sessions/research_alice.md")
```

### Developer B

```python
load_project_context("memory-bank")
create_memory_session("Design auth flow", "Complete plan")
export_memories_to_file("domain_knowledge/auth_decisions.json")
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
| Lead         | `create_project_structure()`, `update_project_index()`                  |
| Developer    | `create_memory_session()`, `store_memory()`, `export_session_to_file()` |
| New Teammate | `load_project_context()`                                                |

---

## 📘 Best Practices

* Always start with `create_memory_session()`
* Use specific tags for search/export
* Run `analyze_memories()` before final export
* Use collections for structure
* Track everything under version control

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