"""Tools for the Neops AI agent to analyze code."""

import ast
from pathlib import Path
from typing import Any

import logfire
from pydantic import BaseModel, Field

from neops.logging_config import get_logger

logger = get_logger(__name__)


class ReadFileInput(BaseModel):
    """Input for reading a file."""

    file_path: str = Field(..., description="Path to the file to read")


class ReadFileOutput(BaseModel):
    """Output from reading a file."""

    content: str = Field(..., description="File contents")
    line_count: int = Field(..., description="Total number of lines in the file")
    file_path: str = Field(..., description="Path to the file that was read")


def read_file(file_path: str) -> ReadFileOutput:
    """Read the contents of a file with line numbers.

    Args:
        file_path: Path to the file to read

    Returns:
        ReadFileOutput with file contents (with line numbers) and line count
    """
    with logfire.span("read_file", file_path=file_path):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Format content with line numbers for accurate line number tracking
        numbered_lines = [f"{i}: {line}" for i, line in enumerate(lines, start=1)]
        numbered_content = "\n".join(numbered_lines)

        return ReadFileOutput(content=numbered_content, line_count=len(lines), file_path=str(path))


class ReadFilesInput(BaseModel):
    """Input for reading multiple files."""

    file_paths: list[str] = Field(..., description="List of paths to files to read")


class ReadFilesOutput(BaseModel):
    """Output from reading multiple files."""

    files: list[dict[str, Any]] = Field(
        ...,
        description="List of file contents, each with 'file_path', 'content', and 'line_count'",
    )


def read_files(file_paths: list[str]) -> ReadFilesOutput:
    """Read the contents of multiple files at once with line numbers.

    Args:
        file_paths: List of paths to files to read

    Returns:
        ReadFilesOutput with contents of all files (with line numbers)
    """
    with logfire.span("read_files", file_paths=file_paths, file_count=len(file_paths)):
        files = []
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                continue  # Skip non-existent files
            try:
                content = path.read_text(encoding="utf-8")
                lines = content.splitlines()

                # Format content with line numbers for accurate line number tracking
                numbered_lines = [f"{i}: {line}" for i, line in enumerate(lines, start=1)]
                numbered_content = "\n".join(numbered_lines)

                files.append(
                    {
                        "file_path": str(path),
                        "content": numbered_content,
                        "line_count": len(lines),
                    }
                )
            except Exception:
                continue  # Skip files that can't be read

        return ReadFilesOutput(files=files)


class ParseASTInput(BaseModel):
    """Input for parsing Python code to AST."""

    code: str = Field(..., description="Python code to parse")
    file_path: str = Field(default="<unknown>", description="Path to the file (for context)")


class ParseASTOutput(BaseModel):
    """Output from AST parsing."""

    file_path: str = Field(..., description="Path to the file that was parsed")
    ast_dump: str = Field(..., description="String representation of the AST")
    functions: list[str] = Field(..., description="List of function names found")
    classes: list[str] = Field(..., description="List of class names found")
    imports: list[str] = Field(..., description="List of import statements")


def parse_ast(code: str, file_path: str = "<unknown>") -> ParseASTOutput:
    """Parse Python code into an AST and extract key information.

    Args:
        code: Python code string to parse
        file_path: Path to the file (for context)

    Returns:
        ParseASTOutput with AST information
    """
    with logfire.span("parse_ast", file_path=file_path, code_length=len(code)):
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
                file_path=file_path,
                ast_dump=ast_dump,
                functions=list(set(functions)),
                classes=list(set(classes)),
                imports=list(set(imports)),
            )
        except SyntaxError as e:
            return ParseASTOutput(
                file_path=file_path,
                ast_dump=f"SyntaxError: {e}",
                functions=[],
                classes=[],
                imports=[],
            )


class ParseASTsInput(BaseModel):
    """Input for parsing multiple Python files to ASTs."""

    files: list[dict[str, str]] = Field(
        ...,
        description="List of dicts with 'file_path' and 'content' for each file to parse",
    )


class ParseASTsOutput(BaseModel):
    """Output from parsing multiple ASTs."""

    asts: list[dict[str, Any]] = Field(
        ...,
        description="List of AST results, each with 'file_path', 'ast_dump', 'functions', 'classes', 'imports'",
    )


def parse_asts(files: list[dict[str, str]]) -> ParseASTsOutput:
    """Parse multiple Python files into ASTs and extract key information.

    Args:
        files: List of dicts with 'file_path' and 'content' for each file

    Returns:
        ParseASTsOutput with AST information for all files
    """
    file_paths = [f.get("file_path", "<unknown>") for f in files]
    with logfire.span("parse_asts", file_paths=file_paths, file_count=len(files)):
        asts = []
        for file_info in files:
            file_path = file_info.get("file_path", "")
            content = file_info.get("content", "")
            try:
                tree = ast.parse(content)
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
                asts.append(
                    {
                        "file_path": file_path,
                        "ast_dump": ast_dump,
                        "functions": list(set(functions)),
                        "classes": list(set(classes)),
                        "imports": list(set(imports)),
                    }
                )
            except SyntaxError as e:
                asts.append(
                    {
                        "file_path": file_path,
                        "ast_dump": f"SyntaxError: {e}",
                        "functions": [],
                        "classes": [],
                        "imports": [],
                    }
                )
            except Exception:
                continue  # Skip files that can't be parsed

        return ParseASTsOutput(asts=asts)


class SearchPatternInput(BaseModel):
    """Input for searching patterns in code."""

    code: str = Field(..., description="Code to search")
    pattern: str = Field(..., description="Pattern or keyword to search for")
    file_path: str = Field(default="<unknown>", description="Path to the file (for context)")


class SearchPatternOutput(BaseModel):
    """Output from pattern search."""

    file_path: str = Field(..., description="Path to the file that was searched")
    matches: list[dict[str, Any]] = Field(..., description="List of matches with line numbers and context")


def search_pattern(code: str, pattern: str, file_path: str = "<unknown>") -> SearchPatternOutput:
    """Search for a pattern in code and return matches with line numbers.

    Args:
        code: Code to search
        pattern: Pattern or keyword to search for
        file_path: Path to the file (for context)

    Returns:
        SearchPatternOutput with matches and their locations
    """
    with logfire.span("search_pattern", file_path=file_path, pattern=pattern, code_length=len(code)):
        lines = code.splitlines()
        matches = []

        for line_num, line in enumerate(lines, start=1):
            if pattern.lower() in line.lower():
                matches.append(
                    {
                        "line": line_num,
                        "content": line.strip(),
                    }
                )

        return SearchPatternOutput(file_path=file_path, matches=matches)


class SearchPatternsInput(BaseModel):
    """Input for searching patterns across multiple files."""

    files: list[dict[str, str]] = Field(
        ...,
        description="List of dicts with 'file_path' and 'content' for each file to search",
    )
    pattern: str = Field(..., description="Pattern or keyword to search for")


class SearchPatternsOutput(BaseModel):
    """Output from searching patterns across multiple files."""

    results: list[dict[str, Any]] = Field(
        ...,
        description="List of search results, each with 'file_path' and 'matches' (list of matches with line numbers)",
    )


def search_patterns(files: list[dict[str, str]], pattern: str) -> SearchPatternsOutput:
    """Search for a pattern across multiple files and return matches with line numbers.

    Args:
        files: List of dicts with 'file_path' and 'content' for each file
        pattern: Pattern or keyword to search for

    Returns:
        SearchPatternsOutput with matches from all files
    """
    file_paths = [f.get("file_path", "<unknown>") for f in files]
    with logfire.span("search_patterns", pattern=pattern, file_paths=file_paths, file_count=len(files)):
        results = []
        for file_info in files:
            file_path = file_info.get("file_path", "")
            content = file_info.get("content", "")
            lines = content.splitlines()
            matches = []

            for line_num, line in enumerate(lines, start=1):
                if pattern.lower() in line.lower():
                    matches.append(
                        {
                            "line": line_num,
                            "content": line.strip(),
                        }
                    )

            if matches:  # Only include files with matches
                results.append({"file_path": file_path, "matches": matches})

        return SearchPatternsOutput(results=results)
