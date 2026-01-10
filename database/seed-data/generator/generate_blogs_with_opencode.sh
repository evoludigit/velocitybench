#!/bin/bash
# Generate blog posts using opencode
#
# This script generates blog posts from the YAML corpus using opencode's free tier.
# It reads prompts from the generator and delegates writing to opencode.
#
# Usage:
#   ./generate_blogs_with_opencode.sh                    # Generate all blogs
#   ./generate_blogs_with_opencode.sh trinity-pattern    # Generate for specific pattern
#   ./generate_blogs_with_opencode.sh --model vllm/ministral-3-8b  # Use specific model

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/../output/blog"
CORPUS_DIR="$SCRIPT_DIR/../corpus"

# Default model (free tier)
MODEL="${MODEL:-opencode/glm-4.7-free}"

# Parse arguments
PATTERN=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--model MODEL] [PATTERN]"
            echo ""
            echo "Models available:"
            echo "  opencode/glm-4.7-free     (default, free)"
            echo "  opencode/gpt-5-nano       (free)"
            echo "  vllm/ministral-3-8b       (local)"
            echo ""
            echo "Patterns:"
            echo "  trinity-pattern"
            echo "  n-plus-one"
            exit 0
            ;;
        *)
            PATTERN="$1"
            shift
            ;;
    esac
done

# Create output directories
mkdir -p "$OUTPUT_DIR/tutorials"
mkdir -p "$OUTPUT_DIR/troubleshooting"
mkdir -p "$OUTPUT_DIR/reference"

echo "=============================================="
echo "Blog Generation with opencode"
echo "=============================================="
echo "Model: $MODEL"
echo "Output: $OUTPUT_DIR"
echo ""

# Function to generate a single blog post
generate_blog() {
    local pattern=$1
    local type=$2
    local depth=$3
    local output_file=$4

    echo "Generating: $output_file"

    # Generate the prompt
    local prompt
    prompt=$(python3 "$SCRIPT_DIR/generate_blog_prompt.py" \
        --pattern "$pattern" \
        --type "$type" \
        --depth "$depth" \
        --stdout 2>/dev/null)

    if [ -z "$prompt" ]; then
        echo "  ERROR: Failed to generate prompt"
        return 1
    fi

    # Add file writing instruction to prompt
    local full_prompt="$prompt

IMPORTANT: Write the complete blog post and save it to the file: $output_file

The file should be a complete, publishable markdown blog post."

    # Run opencode to generate the blog
    opencode run \
        --model "$MODEL" \
        --title "Generate blog: $(basename "$output_file")" \
        "$full_prompt" 2>&1 | tee -a "$OUTPUT_DIR/generation.log"

    if [ -f "$output_file" ]; then
        echo "  SUCCESS: Created $output_file"
        return 0
    else
        echo "  WARNING: File may not have been created"
        return 1
    fi
}

# Get list of patterns to process
if [ -n "$PATTERN" ]; then
    PATTERNS=("$PATTERN")
else
    PATTERNS=("trinity-pattern" "n-plus-one")
fi

# Blog types and depths to generate
TYPES=("tutorial" "troubleshooting" "reference")
DEPTHS=("beginner" "intermediate" "advanced")

# Generate blogs
for pattern in "${PATTERNS[@]}"; do
    echo ""
    echo "=== Pattern: $pattern ==="

    for type in "${TYPES[@]}"; do
        if [ "$type" = "reference" ]; then
            # Reference docs don't have depth variants
            output_file="$OUTPUT_DIR/reference/${pattern}-reference.md"
            generate_blog "$pattern" "$type" "all" "$output_file"
        else
            for depth in "${DEPTHS[@]}"; do
                output_file="$OUTPUT_DIR/${type}s/${pattern}-${type}-${depth}.md"
                generate_blog "$pattern" "$type" "$depth" "$output_file"
            done
        fi
    done
done

echo ""
echo "=============================================="
echo "Generation Complete"
echo "=============================================="
echo "Output directory: $OUTPUT_DIR"
echo "Log file: $OUTPUT_DIR/generation.log"
ls -la "$OUTPUT_DIR"/*/ 2>/dev/null || echo "No files generated yet"
