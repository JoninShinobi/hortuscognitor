#!/bin/bash

# Memory Search Hook for Claude Code
# Searches through CLAUDE.md, business_plan.md, and related files
# to find relevant context for the user's message

USER_MESSAGE="$1"
PROJECT_ROOT="/Users/aarondudfield/Desktop/Folder/Projects/Hortus Cognitor"

# Function to search and display results
search_memory() {
    local query="$1"
    local file="$2"

    if [ -f "$file" ]; then
        # Search case-insensitively for the query
        results=$(grep -i -C 2 "$query" "$file" 2>/dev/null)

        if [ ! -z "$results" ]; then
            echo "📝 Found in $file:"
            echo "$results"
            echo ""
        fi
    fi
}

# Function to extract key topics from user message
extract_topics() {
    echo "$USER_MESSAGE" | tr '[:upper:]' '[:lower:]' | grep -oE '\w{4,}' | sort -u
}

echo "🔍 Searching memory for relevant context..."
echo ""

# Primary memory files
MEMORY_FILES=(
    "$PROJECT_ROOT/CLAUDE.md"
    "$PROJECT_ROOT/business_plan.md"
    "$PROJECT_ROOT/README.md"
)

# Extract topics from user message
TOPICS=$(extract_topics)

# Search through primary memory files
for file in "${MEMORY_FILES[@]}"; do
    if [ -f "$file" ]; then
        for topic in $TOPICS; do
            search_memory "$topic" "$file"
        done
    fi
done

# Search for connected files mentioned in CLAUDE.md
if [ -f "$PROJECT_ROOT/CLAUDE.md" ]; then
    # Look for file references (paths with @, /, or extensions)
    REFERENCED_FILES=$(grep -oE '@[a-zA-Z0-9_/.-]+|[a-zA-Z0-9_/-]+\.(md|py|html|js|css)' "$PROJECT_ROOT/CLAUDE.md" | sort -u)

    for ref_file in $REFERENCED_FILES; do
        # Remove @ prefix if present
        ref_file=${ref_file#@}

        # Try to find the file
        full_path="$PROJECT_ROOT/$ref_file"

        if [ -f "$full_path" ]; then
            for topic in $TOPICS; do
                search_memory "$topic" "$full_path"
            done
        fi
    done
fi

# Search through recent git commit messages for context
echo "📚 Recent relevant commits:"
cd "$PROJECT_ROOT"
for topic in $TOPICS; do
    git log --all --grep="$topic" --oneline -n 3 2>/dev/null
done

echo ""
echo "✅ Memory search complete"
