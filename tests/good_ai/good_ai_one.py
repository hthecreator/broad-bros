import html
import os
import subprocess
from pathlib import Path
from urllib.parse import quote

llm_output = "some content from LLM"


def good_exec_llm_output():
    sanitized = sanitize_output(llm_output)
    if is_safe_to_execute(sanitized):
        exec(sanitized)
    safe_command = ["ls", "-la"]
    subprocess.run(safe_command, check=True)


def good_render_llm_output():
    escaped_output = html.escape(llm_output)
    html_content = f"<div>{escaped_output}</div>"  # noqa: F841
    url_encoded = quote(llm_output)  # noqa: F841
    template = f"<html><body>{escaped_output}</body></html>"  # noqa: F841


def good_sql_file_path():
    query = "SELECT * FROM users WHERE name = ?"  # noqa: F841
    safe_path = sanitize_file_path(llm_output)
    file_path = Path("/tmp") / safe_path
    with open(file_path, "w") as f:
        f.write("data")
    safe_command = ["ls", sanitize_file_path(llm_output)]
    subprocess.run(safe_command, check=True)


def good_model_provider():
    model_provider = "OpenAI"
    return model_provider


def good_model_version():
    model = "gpt-4o"
    return model


def sanitize_output(output: str) -> str:
    import re

    sanitized = re.sub(r"[^a-zA-Z0-9\s\-_]", "", output)
    return sanitized


def is_safe_to_execute(code: str) -> bool:
    dangerous_keywords = ["import", "exec", "eval", "__"]
    return not any(keyword in code for keyword in dangerous_keywords)


def sanitize_file_path(path: str) -> str:
    safe_path = os.path.basename(path)
    safe_path = "".join(c for c in safe_path if c.isalnum() or c in "._-")
    return safe_path
