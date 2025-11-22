FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv for faster dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install the package
RUN uv pip install --system -e .

# Set the entrypoint to your CLI command
ENTRYPOINT ["neops"]

# Default command (can be overridden)
CMD ["--help"]