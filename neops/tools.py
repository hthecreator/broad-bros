"""Tools for the Neops AI agent to analyze code."""

import ast
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ReadFileInput(BaseModel):
    """Input for reading a file."""

    file_path: str = Field(..., description="Path to the file to read")


class ReadFileOutput(BaseModel):
    """Output from reading a file."""

    content: str = Field(..., description="File contents")
    line_count: int = Field(..., description="Total number of lines in the file")


def read_file(file_path: str) -> ReadFileOutput:
    """Read the contents of a file.

    Args:
        file_path: Path to the file to read

    Returns:
        ReadFileOutput with file contents and line count
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    return ReadFileOutput(content=content, line_count=len(lines))


class ParseASTInput(BaseModel):
    """Input for parsing Python code to AST."""

    code: str = Field(..., description="Python code to parse")


class ParseASTOutput(BaseModel):
    """Output from AST parsing."""

    ast_dump: str = Field(..., description="String representation of the AST")
    functions: list[str] = Field(..., description="List of function names found")
    classes: list[str] = Field(..., description="List of class names found")
    imports: list[str] = Field(..., description="List of import statements")


def parse_ast(code: str) -> ParseASTOutput:
    """Parse Python code into an AST and extract key information.

    Args:
        code: Python code string to parse

    Returns:
        ParseASTOutput with AST information
    """
    try:
        tree = ast.parse(code)
        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                else:
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")

        ast_dump = ast.dump(tree, indent=2)
        return ParseASTOutput(
            ast_dump=ast_dump,
            functions=list(set(functions)),
            classes=list(set(classes)),
            imports=list(set(imports)),
        )
    except SyntaxError as e:
        return ParseASTOutput(
            ast_dump=f"SyntaxError: {e}",
            functions=[],
            classes=[],
            imports=[],
        )


class SearchPatternInput(BaseModel):
    """Input for searching patterns in code."""

    code: str = Field(..., description="Code to search")
    pattern: str = Field(..., description="Pattern or keyword to search for")


class SearchPatternOutput(BaseModel):
    """Output from pattern search."""

    matches: list[dict[str, Any]] = Field(..., description="List of matches with line numbers and context")


def search_pattern(code: str, pattern: str) -> SearchPatternOutput:
    """Search for a pattern in code and return matches with line numbers.

    Args:
        code: Code to search
        pattern: Pattern or keyword to search for

    Returns:
        SearchPatternOutput with matches and their locations
    """
    lines = code.splitlines()
    matches = []

    for line_num, line in enumerate(lines, start=1):
        if pattern.lower() in line.lower():
            matches.append(
                {
                    "line": line_num,
                    "content": line.strip(),
                    "column": line.lower().find(pattern.lower()) + 1 if pattern.lower() in line.lower() else None,
                }
            )

    return SearchPatternOutput(matches=matches)
