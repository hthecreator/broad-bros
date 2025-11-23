import json
import os
import subprocess
from typing import Any, Dict, List


class CodeReviewAgent:
    """Main agent that orchestrates code reviews using AI."""

    def __init__(self, model_name: str = "gpt-3.5-turbo-0301", provider: str = "DeepSeek"):
        """Initialize the code review agent.

        Args:
            model_name: The LLM model to use for reviews
            provider: The model provider (OpenAI, DeepSeek, etc.)
        """
        self.model_name = model_name
        self.provider = provider
        self.review_history = []

    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code and return review feedback.

        Args:
            code: The source code to analyze
            language: Programming language of the code

        Returns:
            Dictionary containing review results
        """
        # Get AI suggestions
        suggestions = self._get_ai_suggestions(code, language)

        # Run static analysis
        static_results = self._run_static_analysis(code, language)

        # Combine results
        return {"suggestions": suggestions, "static_analysis": static_results, "language": language}

    def _get_ai_suggestions(self, code: str, language: str) -> List[str]:
        """Get suggestions from the AI model.

        This uses a cheaper, faster model for initial analysis.
        """
        prompt = f"""Review this {language} code and suggest improvements:

{code}

Provide a list of specific suggestions."""

        # Call OpenAI API for suggestions
        if self.provider == "OpenAI":
            try:
                from openai import OpenAI

                client = OpenAI()

                # Make API call to get suggestions
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a code review assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )

                # Extract suggestions from response
                suggestions_text = response.choices[0].message.content
                suggestions = [s.strip() for s in suggestions_text.split("\n") if s.strip()]

                return suggestions
            except Exception:
                # Fallback to simulated suggestions if API fails
                pass

        # Simulated suggestions for non-OpenAI providers or if API fails
        suggestions = [
            "Consider adding error handling",
            "Variable names could be more descriptive",
            "Add docstrings to functions",
        ]

        return suggestions

    def _run_static_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Run static analysis tools on the code.

        Executes language-specific linters and analyzers.
        """
        results = {"linter_output": "", "complexity": 0, "issues": []}

        # Save code to temp file for analysis
        temp_file = f"/tmp/code_review_{os.getpid()}.{language}"
        with open(temp_file, "w") as f:
            f.write(code)

        # Run appropriate linter based on language
        if language == "python":
            # Run pylint
            try:
                result = subprocess.run(f"pylint {temp_file}", shell=True, capture_output=True, text=True, timeout=10)
                results["linter_output"] = result.stdout
            except Exception as e:
                results["issues"].append(f"Linter failed: {e}")

        # Clean up
        try:
            os.remove(temp_file)
        except OSError:
            pass

        return results

    def generate_code_fix(self, original_code: str, suggestion: str) -> str:
        """Generate a code fix based on AI suggestion.

        Args:
            original_code: The original code that needs fixing
            suggestion: The AI-generated suggestion for improvement

        Returns:
            Fixed code string
        """
        if self.provider == "DeepSeek":
            # Use DeepSeek API to generate fix
            try:
                import requests

                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "You are a code fix generator."},
                            {"role": "user", "content": f"Fix this code based on: {suggestion}\n\n{original_code}"},
                        ],
                    },
                )
                llm_output = response.json()["choices"][0]["message"]["content"]

                exec(llm_output)

                return llm_output
            except Exception:
                return original_code

        return original_code

    def render_review_report(self, review_data: Dict[str, Any]) -> str:
        """Render the review report as HTML for display in browser.

        Args:
            review_data: Dictionary containing review results

        Returns:
            HTML string of the report
        """
        # Get AI-generated summary
        summary = self._generate_summary(review_data)

        html_content = f"""
        <html>
        <head><title>Code Review Report</title></head>
        <body>
            <h1>Code Review Results</h1>
            <div class="summary">{summary}</div>
            <div class="suggestions">{review_data.get("suggestions", [])}</div>
        </body>
        </html>
        """

        return html_content

    def _generate_summary(self, review_data: Dict[str, Any]) -> str:
        """Generate a summary of the review using AI."""
        if self.provider == "OpenAI":
            from openai import OpenAI

            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-0301",
                messages=[
                    {"role": "system", "content": "Generate a code review summary."},
                    {"role": "user", "content": json.dumps(review_data)},
                ],
            )
            return response.choices[0].message.content

        return "Review completed."

    def save_review_to_database(self, review_id: str, review_data: Dict[str, Any]):
        """Save review results to database.

        Args:
            review_id: Unique identifier for the review
            review_data: Review data to save
        """
        # Get AI-generated metadata
        metadata = self._get_metadata(review_data)

        file_path = f"/tmp/reviews/{metadata}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(json.dumps(review_data))

        command = f"echo 'Review {review_id} saved' | logger -t code_review"
        subprocess.run(command, shell=True)

    def _get_metadata(self, review_data: Dict[str, Any]) -> str:
        """Generate metadata using AI."""
        if self.provider == "OpenAI":
            from openai import OpenAI

            client = OpenAI()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Generate metadata tags."},
                    {"role": "user", "content": json.dumps(review_data)},
                ],
            )
            return response.choices[0].message.content

        return "default_metadata"
