# neops

A CLI tool for network operations and analysis.

## Description

`neops` is a command-line interface tool designed for network operations. The tool can be run locally using `uv` or deployed via Docker for consistent cross-machine execution.

## Getting started
This project makes use of `uv` for python version management and for virtual environment/ dependency management. To get started with these tools, you can refer to [Python dev](https://www.notion.so/facultyai/uv-25c296bcfe388052821be36e24c8297e?source=copy_link) in Notion.

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

### Local Development Usage

Once you've set up the environment with `uv sync`, you can run the CLI tool using:

```bash
# Get help
uv run neops --help

# Example: Say hello (currently the only command, so it's the default)
uv run neops World

# Note: Once you add more commands, the structure will be:
# uv run neops <command> [arguments]
# uv run neops hello World
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

# Run with arguments
docker run --rm neops:latest World

# Mount local files if needed (e.g., for data processing)
docker run --rm -v $(pwd)/data:/data neops:latest <arguments>

# Interactive mode (if needed)
docker run --rm -it neops:latest <arguments>

# Note: Once you add more commands, use: docker run --rm neops:latest <command> [arguments]
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
docker-compose run --rm neops World
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
    # Your implementation here
    pass
```

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

## Note

This project has been setup using Faculty's [consultancy-cookie](https://gitlab.com/facultyai/faculty-tools/consultancy-cookie).
