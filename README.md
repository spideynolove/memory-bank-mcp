# Memory Bank MCP

A Model Context Protocol (MCP) server that provides persistent memory storage and retrieval capabilities for Claude Code, enabling structured knowledge management with collections, tags, and search functionality.

## Features

- **Persistent Memory Storage**: Store and retrieve memories across sessions
- **Collection Management**: Organize related memories into logical groups
- **Tag-Based Search**: Find memories using tags and content search
- **Importance Scoring**: Prioritize memories by importance level (0.0-1.0)
- **Metadata Support**: Store additional context with each memory
- **File Persistence**: Automatic JSON file storage for durability
- **Resource Access**: Visual memory bank structure and search analytics

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

## Usage

### 1. Create a Memory Bank

```python
create_memory_bank(
    name="My Knowledge Base",
    description="Personal knowledge and insights",
    tags="work,personal,learning"
)
```

### 2. Store Memories

```python
store_memory(
    content="Always validate user input before processing",
    tags="security,best-practices",
    importance=0.9,
    metadata='{"context": "web development", "source": "code review"}'
)
```

### 3. Create Collections

```python
create_collection(
    name="Security Guidelines",
    description="Security best practices and patterns",
    tags="security,guidelines"
)
```

### 4. Search Memories

```python
search_memories(
    query="validation",
    tags="security",
    collection_id="collection_id_here"
)
```

### 5. Get Statistics

```python
get_memory_stats()
```

## Available Tools

| Tool | Description |
|------|-------------|
| `create_memory_bank` | Initialize a new memory bank |
| `store_memory` | Store a memory with tags and metadata |
| `create_collection` | Create collections for organizing memories |
| `search_memories` | Search memories by content, tags, or collection |
| `get_memory_stats` | Get statistics about the memory bank |

## Resources

Access structured data through MCP resources:

- `memory://bank` - Complete memory bank structure
- `memory://search` - Search results and analytics
- `memory://collections` - All collections overview

## Advanced Features

### Persistent Storage
All memories are automatically saved to a JSON file and restored when the server restarts.

### Importance Scoring
Rate memories from 0.0 to 1.0 to prioritize important information in search results.

### Metadata Support
Store additional context with each memory using JSON metadata.

### Collection Organization
Group related memories into collections for better organization and focused searching.

### Tag-Based Search
Use tags to categorize and quickly find related memories.

## Best Practices

1. **Use Descriptive Tags**: Add relevant tags for better categorization
2. **Set Importance Levels**: Use 0.8-1.0 for critical information, 0.5-0.7 for useful info
3. **Create Logical Collections**: Group related memories for easier navigation
4. **Add Metadata**: Include context like source, date, or category
5. **Search Before Storing**: Avoid duplicates by searching first
6. **Regular Maintenance**: Review and update memories periodically

## Example Workflow

```python
# 1. Create memory bank
create_memory_bank(
    name="Development Knowledge",
    description="Programming insights and patterns",
    tags="development,learning"
)

# 2. Store important memories
memory1 = store_memory(
    content="Use dependency injection for better testability",
    tags="architecture,testing,best-practices",
    importance=0.8,
    metadata='{"language": "python", "pattern": "dependency-injection"}'
)

# 3. Create collection for organization
collection1 = create_collection(
    name="Architecture Patterns",
    description="Software architecture patterns and principles",
    tags="architecture,patterns"
)

# 4. Store memory in collection
store_memory(
    content="SOLID principles improve code maintainability",
    tags="architecture,principles",
    importance=0.9,
    collection_id=collection1
)

# 5. Search for specific knowledge
results = search_memories(
    query="testing",
    tags="best-practices"
)

# 6. Get statistics
stats = get_memory_stats()
```

## Testing Installation

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