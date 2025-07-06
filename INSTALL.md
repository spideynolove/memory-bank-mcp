# Memory Bank MCP - Installation Guide

## Quick Setup

1. **Clone/Download the project:**
   ```bash
   git clone <your-repo> memory-bank-mcp
   cd memory-bank-mcp
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Add to Claude Code:**
   ```bash
   claude mcp add memory-bank uv run /full/path/to/memory-bank-mcp/main.py
   ```

4. **Verify installation:**
   ```bash
   claude mcp list
   ```

## Usage in Claude Code

### Create a Memory Bank
```
create_memory_bank(
    name="My Knowledge Base",
    description="Personal knowledge and insights",
    tags="work,personal,learning"
)
```

### Store Memories
```
store_memory(
    content="Always validate user input before processing",
    tags="security,best-practices",
    importance=0.9,
    metadata='{"context": "web development"}'
)
```

### Create Collections
```
create_collection(
    name="Security Guidelines",
    description="Security best practices and patterns",
    tags="security,guidelines"
)
```

### Search Memories
```
search_memories(
    query="validation",
    tags="security",
    collection_id="<collection-id>"
)
```

### Get Statistics
```
get_memory_stats()
```

## Available Tools

| Tool | Purpose |
|------|---------|
| `create_memory_bank` | Initialize a new memory bank |
| `store_memory` | Store memories with tags and metadata |
| `create_collection` | Create collections for organization |
| `search_memories` | Search by content, tags, or collection |
| `get_memory_stats` | Get memory bank statistics |

## MCP Resources

Access structured data with @ mentions:
- `@memory-bank:memory://bank` - Complete memory bank structure
- `@memory-bank:memory://search` - Search results and analytics
- `@memory-bank:memory://collections` - All collections overview

## Installation Scopes

### Local (Default)
```bash
claude mcp add memory-bank -s local uv run /path/to/main.py
```
- Private to you in current project only

### Project (Team Sharing)
```bash
claude mcp add memory-bank -s project uv run /path/to/main.py
```
- Shared with team via `.mcp.json` file
- Include in version control

### User (Global)
```bash
claude mcp add memory-bank -s user uv run /path/to/main.py
```
- Available across all your projects

## Troubleshooting

### Server Won't Start
```bash
# Test directly
uv run main.py

# Check dependencies
uv sync

# Verify path is absolute
claude mcp add memory-bank uv run $(pwd)/main.py
```

### Can't See Tools
- Restart Claude Code session
- Check server status: `claude mcp get memory-bank`
- Use `/mcp` command in Claude Code to check connection

### Permission Issues
```bash
# Make script executable
chmod +x main.py

# Or use uv explicitly
claude mcp add memory-bank uv run /absolute/path/to/main.py
```

## Example Workflow

1. **Create memory bank** with descriptive name and tags
2. **Store memories** with appropriate importance and tags
3. **Create collections** for organizing related memories
4. **Search memories** using content, tags, or collections
5. **Get statistics** to understand your memory bank
6. **Review and maintain** memories periodically

## Advanced Usage

### With Environment Variables
```bash
claude mcp add memory-bank -e DEBUG=1 -e STORAGE_PATH=/custom/path -- uv run /path/to/main.py
```

### Project Team Setup
```bash
# Add to project scope for team sharing
claude mcp add memory-bank -s project uv run ./main.py

# Team members can then use:
claude mcp list  # Shows shared servers
```

### Integration with Other Tools
The Memory Bank MCP works well with:
- Sequential Thinking MCP for structured reasoning
- File system MCPs for documentation integration
- Web search MCPs for research-backed knowledge storage

## Data Storage

- Memories are stored in `memory_storage.json` by default
- File is created automatically in the working directory
- Backup this file to preserve your memories
- File format is human-readable JSON

## Best Practices

1. **Use Descriptive Tags**: Add relevant tags for better categorization
2. **Set Importance Levels**: Use 0.8-1.0 for critical information
3. **Create Logical Collections**: Group related memories together
4. **Add Metadata**: Include context like source, date, or category
5. **Search Before Storing**: Avoid duplicates by searching first
6. **Regular Maintenance**: Review and update memories periodically

## Security Considerations

- Memory storage file contains your personal knowledge
- Ensure proper file permissions on the storage file
- Consider encryption for sensitive information
- Regular backups recommended for important memories