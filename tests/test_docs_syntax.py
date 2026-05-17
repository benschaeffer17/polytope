import os
import re
import subprocess
import pytest
from pathlib import Path

# Regex to find mermaid code blocks
MERMAID_REGEX = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)

def get_markdown_files():
    """Yields all markdown files in the repository (excluding node_modules)."""
    root_dir = Path(__file__).parent.parent
    for path in root_dir.rglob("*.md"):
        if "node_modules" not in path.parts and ".gemini" not in path.parts:
            yield path

def extract_diagrams(filepath):
    """Yields (diagram_code, line_number) for each mermaid block."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for match in MERMAID_REGEX.finditer(content):
        # Calculate line number by counting newlines before the match
        line_num = content.count('\n', 0, match.start()) + 1
        yield match.group(1), line_num

@pytest.mark.parametrize("md_file", get_markdown_files(), ids=lambda p: p.name)
def test_mermaid_syntax(md_file):
    """
    Parses the markdown file for Mermaid blocks and deterministically
    validates their syntax using the pure JS parser.
    """
    script_path = Path(__file__).parent / "validate_mermaid.js"
    assert script_path.exists(), f"Validation script missing: {script_path}"
    
    diagrams = list(extract_diagrams(md_file))
    if not diagrams:
        pytest.skip(f"No Mermaid diagrams found in {md_file.name}")
        
    for code, line_num in diagrams:
        # Pipe the diagram code into the Node.js validation script
        process = subprocess.run(
            ["node", str(script_path)],
            input=code,
            text=True,
            capture_output=True
        )
        
        # If it fails, print the exact error and fail the test
        assert process.returncode == 0, (
            f"Mermaid syntax error in {md_file.name} (Line {line_num}):\n"
            f"{process.stderr}\n\n"
            f"Diagram:\n{code}"
        )
