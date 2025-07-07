FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including uv
RUN apt-get update && apt-get install -y \
    sqlite3 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml .
COPY uv.lock* .

# Install Python dependencies using uv
RUN uv sync --frozen

# Copy MCP source code
COPY . /app/mcp

# Create project directory
RUN mkdir -p /app/project

# Set environment variables
ENV PYTHONPATH=/app/mcp
ENV PROJECT_PATH=/app/project

# Expose MCP port (if needed)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; sqlite3.connect('/app/project/memory.db').close()" || exit 1

# Run migration check and start MCP server
CMD ["uv", "run", "python", "/app/mcp/main.py"]