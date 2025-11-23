# neops

A CLI tool for network operations and analysis.

## Description

`neops` is a command-line interface tool designed for network operations. The tool can be run locally using `uv` or deployed via Docker for consistent cross-machine execution.

## Getting started
This project makes use of `uv` for python version management and for virtual environment/ dependency management.

```bash
#Clone the repository using your preferred method(SSH vs HTTPS)
git clone <repo_url>
cd <repo>
```
```bash
#Create the uv virtual environment (if you don't have a compatible version of python on your system
#you might have to install it !!Danger platform user see uv notes in Notion above!!)
uv sync
```
```bash
#you can now run all packages installed such as pre-commit, ruff and pytest using
uv run <package>

# Make sure to install the pre-commit hooks
uv run pre-commit install
```

## Running the CLI

### Available Commands

- **`hello`**: Greet someone (sample command)
- **`show-config`**: Display the loaded project configuration from pyproject.toml

### Local Development Usage

Once you've set up the environment with `uv sync`, you can run the CLI tool using:

```bash
# Get help
uv run neops --help

# Example: Run the hello command
uv run neops hello World

# With verbose output (INFO level)
uv run neops -v hello World

# With debug output (DEBUG level - shows timestamps and function names)
uv run neops -vv hello World

# With all debug output (includes third-party library logs)
uv run neops -vvv hello World
```

#### Verbosity Levels

The CLI supports incremental verbosity flags following Unix conventions:

- **No flag (default)**: Only shows WARNING and ERROR messages
- **`-v` (INFO)**: Shows informational messages about what the tool is doing
- **`-vv` (DEBUG)**: Shows detailed debug information with timestamps and function names
- **`-vvv` (TRACE)**: Shows all debug information including from third-party libraries

#### Configuration File

The CLI automatically loads your `pyproject.toml` file. You can specify a custom path:

```bash
# Use default (searches for pyproject.toml at repository root)
uv run neops show-config

# Specify a custom path to pyproject.toml file
uv run neops -p /path/to/pyproject.toml show-config

# Specify a directory containing pyproject.toml
uv run neops -p /path/to/project/ show-config

# View what was loaded with verbose output
uv run neops -vv -p /custom/path show-config
```

### Docker Usage

For consistent execution across different machines, use Docker:

#### Building the Docker Image

```bash
# Build the image
docker build -t neops:latest .
```

#### Running with Docker

```bash
# Show help
docker run --rm neops:latest --help

# Run the hello command
docker run --rm neops:latest hello World

# Run with verbose output
docker run --rm neops:latest -v hello World

# Run with debug output
docker run --rm neops:latest -vv hello World

# Mount local files if needed (e.g., for data processing)
docker run --rm -v $(pwd)/data:/data neops:latest hello World

# Interactive mode (if needed)
docker run --rm -it neops:latest hello World
```

#### Docker Compose (Optional)

For more complex setups, you can use docker-compose:

```yaml
# docker-compose.yml
version: '3.8'

services:
  neops:
    build: .
    volumes:
      - ./data:/data
    command: --help  # Override with actual command
```

Then run:
```bash
# Basic usage
docker-compose run --rm neops hello World

# With verbose output
docker-compose run --rm neops -v hello World
```

## Local development
Relying on the remote CI pipeline to check your code leads to slow development iteration. Locally, you can trigger:

- linting & formatting checks: `uv run pre-commit run --all-files`
- tests: `uv run pytest tests/`

## Adding New Commands

To add new commands to the CLI, edit `src/neops/main.py`:

```python
@app.command()
def your_command(arg: str):
    """Description of your command"""
    logger.debug(f"Starting your_command with arg: {arg}")
    logger.info("Processing data...")

    # Your implementation here
    # Use print() for actual output
    # Use logger for informational/debug messages
    print(f"Result: {arg}")

    logger.debug("Command completed successfully")
```

**Logging Best Practices:**
- Use `logger.debug()` for detailed debugging information
- Use `logger.info()` for general informational messages
- Use `logger.warning()` for warnings that don't stop execution
- Use `logger.error()` for errors
- Use `print()` for actual command output (not logs)

After adding commands, rebuild the Docker image to include the changes:
```bash
docker build -t neops:latest .
```

## Distribution

### Sharing the Docker Image

To share the tool with others:

```bash
# Save image to a tar file
docker save neops:latest -o neops-latest.tar

# Load image on another machine
docker load -i neops-latest.tar
```

Or push to a registry:
```bash
# Tag for registry
docker tag neops:latest your-registry/neops:latest

# Push to registry
docker push your-registry/neops:latest
```

## Troubleshooting

### Command not found (local)
If you get `command not found: neops` when trying to run locally:
- Always use `uv run neops <args>` instead of `neops <args>`
- The `neops` command is only available within the uv-managed environment

### Docker build fails
- Ensure you're in the project root directory
- Check that all required files (README.md, pyproject.toml, etc.) are present
- Make sure `.dockerignore` doesn't exclude necessary files
