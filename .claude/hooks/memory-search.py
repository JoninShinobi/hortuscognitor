#!/usr/bin/env python3
"""
Memory Search Hook for Claude Code
Searches through CLAUDE.md, business_plan.md, and connected files
to inject relevant context into Claude's knowledge.
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Set

def extract_topics(text: str, min_length: int = 4) -> Set[str]:
    """Extract meaningful words from text as search topics."""
    # Common words to ignore (stop words + meta/system words)
    stop_words = {
        'will', 'when', 'what', 'where', 'which', 'that', 'this', 'these', 'those',
        'have', 'with', 'from', 'they', 'been', 'were', 'their', 'there', 'then',
        'than', 'into', 'only', 'also', 'some', 'such', 'make', 'them', 'about',
        'would', 'could', 'should', 'does', 'memory', 'access', 'hook', 'accessed',
        'show', 'print', 'code', 'thing', 'something', 'anything', 'everything',
        'user', 'users', 'file', 'files', 'work', 'works', 'working', 'actually',
        'really', 'just', 'like', 'want', 'need', 'make', 'good', 'better', 'best'
    }

    words = re.findall(r'\b\w+\b', text.lower())
    return {w for w in words if len(w) >= min_length and w not in stop_words}

def search_file(file_path: Path, topics: Set[str]) -> List[str]:
    """Search a file for topics and return matching context."""
    if not file_path.exists():
        return []

    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        results = []

        for topic in topics:
            for i, line in enumerate(lines):
                if topic in line.lower():
                    # Get context: 2 lines before and after
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context = '\n'.join(lines[start:end])
                    results.append(f"Found '{topic}' in {file_path.name}:\n{context}\n")

        return results
    except Exception as e:
        return [f"Error reading {file_path}: {e}"]

def find_referenced_files(claude_md_path: Path, project_root: Path) -> List[Path]:
    """Find files referenced in CLAUDE.md using @ syntax or paths."""
    if not claude_md_path.exists():
        return []

    content = claude_md_path.read_text(encoding='utf-8')

    # Find references like @filename, @path/to/file, or explicit paths
    patterns = [
        r'@([a-zA-Z0-9_/.-]+)',  # @file references
        r'([a-zA-Z0-9_/-]+\.(md|py|html|js|css|txt))',  # File paths
    ]

    referenced = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            # Handle tuple results from regex groups
            file_ref = match[0] if isinstance(match, tuple) else match
            file_ref = file_ref.lstrip('@')
            referenced.add(file_ref)

    # Convert to full paths and filter existing files
    files = []
    for ref in referenced:
        full_path = project_root / ref
        if full_path.exists() and full_path.is_file():
            files.append(full_path)

    return files

def main():
    # Read input from stdin
    input_data = json.loads(sys.stdin.read())
    user_prompt = input_data.get('prompt', '')
    cwd = Path(input_data.get('cwd', '.'))

    # Extract topics from user's message
    topics = extract_topics(user_prompt)

    if not topics:
        # No meaningful topics, return empty context
        sys.exit(0)

    # Memory files to search
    memory_files = [
        cwd / 'CLAUDE.md',
        cwd / 'business_plan.md',
        cwd / 'README.md',
    ]

    context_parts = []

    # Search primary memory files
    for file_path in memory_files:
        results = search_file(file_path, topics)
        context_parts.extend(results)

    # Search connected files referenced in CLAUDE.md
    claude_md = cwd / 'CLAUDE.md'
    referenced_files = find_referenced_files(claude_md, cwd)

    if referenced_files:
        for file_path in referenced_files[:5]:  # Limit to 5 files to avoid spam
            results = search_file(file_path, topics)
            context_parts.extend(results)

    # Output context for Claude - with instruction to acknowledge
    context_content = '\n'.join(context_parts) if context_parts else ""

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"""IMPORTANT: You must begin your response with the exact phrase: "✓ Memory Accessed"

Memory search results:
{context_content}"""
        }
    }

    print(json.dumps(output))
    sys.exit(0)

if __name__ == '__main__':
    main()
