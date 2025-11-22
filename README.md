# broad_bros

A short description of your project goes here...

## Description

A longer description of your project goes here...

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

## Local development
 Relying on the remote CI pipeline to check your code leads to slow development  iteration. Locally, you can trigger:

 - linting & formatting checks : `uv run pre-commit run --all-files`
 - tests: `uv run pytest tests/`


## Note

This project has been setup using Faculty's [consultancy-cookie](https://gitlab.com/facultyai/faculty-tools/consultancy-cookie).
