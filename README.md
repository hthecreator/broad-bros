# neops

**AI Safety code scanner**

`neops` is a security scanning tool that detects AI-related vulnerabilities in your codebase. It identifies unsafe handling of LLM outputs, deprecated model usage, risky provider configurations, and other AI security issues.

## The Idea

As AI models become integrated into applications, new security risks emerge. `neops` helps you catch these issues early by scanning your code for:

- **Improper Output Handling**: LLM outputs executed, rendered, or injected without sanitization
- **Deprecated Models**: Usage of models that have been deprecated or are scheduled for deprecation
- **Risky Providers**: Model providers flagged as concerning or dangerous
- **Missing Safety Practices**: Missing safety identifiers and other security best practices

**Trusted Sources**: Rules are based on guidelines from trusted AI safety organizations including **OWASP**, **OpenAI**, and **Anthropic**. We also maintain an up-to-date list of active, legacy, and deprecated models from major providers.

The tool uses AI Agents analysis to understand context and detect vulnerabilities that static analysis alone might miss.

## Installation

Install `neops` using pip:

```bash
pip install neops
```

Or install from source:

```bash
git clone https://github.com/your-org/neops.git
cd neops
pip install -e .
```

## Quick Start

### Basic Usage

Scan your entire codebase (automatically detects git-tracked files):

```bash
neops scan
```

Scan specific files or directories:

```bash
neops scan -f path/to/file -f path/to/directory/
```

View files that will be scanned:

```bash
neops list-files
```

### Example Output

After scanning, `neops` generates two report files:
- **JSON report**: Machine-readable results (`neops_scan_results_YYYYMMDD_HHMMSS.json`)
- **Markdown report**: Human-readable report with detailed findings (`neops_scan_results_YYYYMMDD_HHMMSS.md`)

Example scan output:

```
Scanning 15 file(s)...
Scan complete!
Summary: 3 errors, 3 warnings, 4 info
Results saved to:
  JSON: neops_scan_results_20251123_172405.json
  Markdown: neops_scan_results_20251123_172405.md
```

## What Errors Does neops Find?

`neops` detects several categories of AI security issues:

### 🔴 Errors (Critical Issues)

**OWASP-001: LLM output executed without sanitization**
- Detects direct execution of LLM outputs (exec, eval, system calls) without validation

**OWASP-003: LLM output used in DB/file path without parameterization**
- Detects SQL injection, file path injection, and command injection risks from unsanitized LLM outputs

**NEOps-002: Model provider is listed as Dangerous**
- Flags usage of model providers classified as dangerous

### 🟡 Warnings (Important Issues)

**OWASP-002: LLM output rendered to browser without encoding**
- Detects unsafe HTML rendering without proper encoding or escaping

**NEOps-001: Model provider is listed as Worrying**
- Flags usage of model providers classified as concerning

**NEOps-004: Legacy model used**
- Detects models scheduled for future deprecation (e.g., `claude-3-5-haiku-20241022`)

### ℹ️ Info (Best Practices)

**NEOps-003: Deprecated model used**
- Detects officially deprecated models from major providers (OpenAI, Anthropic, etc.)

**OpenAI-002: Safety identifier not provided in API requests**
- Detects missing safety identifiers in OpenAI API requests

### Example Findings

Here's what a finding looks like in the report:

```markdown
#### 🔴 OWASP-001 - LLM output executed without sanitization (ERROR)

**File:** `src/code_review.js`
**Line:** 145
**Message:** Direct execution of LLM output without any sanitization or validation.

**Reasoning:**
> The code directly executes LLM-generated content without sanitization.

**Remediation:**
> Avoid executing raw LLM output. Sanitize and validate any LLM-generated content.
```

## Configuration via pyproject.toml

You can customize rule behavior in your `pyproject.toml` file. Add a `[tool.neops.rules]` section to override severity levels or enable/disable specific rules.

### Disable a Rule

To disable a rule entirely:

```toml
[tool.neops.rules]
"OWASP-002" = { enabled = false }
```

### Change Rule Severity

To change the severity level of a rule:

```toml
[tool.neops.rules]
"OWASP-001" = { severity = "warning" }  # Change from error to warning
"NEOps-003" = { severity = "error" }    # Change from info to error
```

### Multiple Overrides

You can combine both options:

```toml
[tool.neops.rules]
"OWASP-001" = { severity = "warning", enabled = true }
"OWASP-002" = { enabled = false }
"NEOps-003" = { severity = "error" }
```

### Available Severity Levels

- `error` - Critical issues that should be fixed immediately
- `warning` - Important issues that should be addressed
- `info` - Best practice recommendations

### Rule IDs

Rule IDs follow the format `{ORGANIZATION}-{CODE}`:

- `OWASP-001`, `OWASP-002`, `OWASP-003` - OWASP AI security guidelines
- `NEOps-001`, `NEOps-002`, `NEOps-003`, `NEOps-004` - Neops rules (model provider and deprecation checks)
- `OpenAI-002` - OpenAI safety guidelines
- `Anthropic-*` - Anthropic safety guidelines (as available)

## Advanced Usage

### Custom pyproject.toml Location

Specify a custom path to `pyproject.toml`:

```bash
neops -p /path/to/pyproject.toml scan
neops -p /path/to/project/ scan  # Directory containing pyproject.toml
```

### Custom Output Directory

```bash
neops scan -o /path/to/results/
```

### Environment Variables

**Required**: `OPENAI_API_KEY` is always needed to run the code. Set your OpenAI API key for AI-powered analysis:

```bash
export OPENAI_API_KEY=your-api-key
```

**Model Support**: We currently use OpenAI o3 for analysis. We plan to support more OpenAI reasoning models and Anthropic in the future. We recommend o3 for value-for-money.

## Docker Usage

For consistent execution across different machines:

```bash
# Build the image
docker build -t neops:latest .

# Run scan
docker run --rm -v $(pwd):/workspace -w /workspace neops:latest scan

# With custom pyproject.toml
docker run --rm -v $(pwd):/workspace -w /workspace neops:latest -p /workspace/pyproject.toml scan
```

## Troubleshooting

If `neops` command is not found, try: `python -m neops scan`

If you get "No files to scan", specify files explicitly: `neops scan -f path/to/file`

If `pyproject.toml` overrides aren't being applied, ensure you're in the repository root where `pyproject.toml` is located.

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

This project uses `uv` for Python version and dependency management:

```bash
# Clone the repository
git clone https://github.com/your-org/neops.git
cd neops

# Create virtual environment and install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=neops
```

### Code Quality

```bash
# Run linting and formatting
uv run pre-commit run --all-files
```

### Adding New Rules

To add new security rules, edit the YAML configuration files in `neops/config/`:
- `rules.yaml` - Define new rules
- `rule_configuration.yaml` - Configure rule classes and organizations

See existing rules for examples of rule structure and patterns.

## License

See [LICENSE.txt](LICENSE.txt) for details.
