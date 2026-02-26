#!/bin/bash
#
# Generate CI Test Summary
# Helper script to automatically calculate framework counts from CI matrix
# Run this when adding new frameworks to update the CI summary
#
# Usage: ./scripts/generate-ci-summary.sh
#

set -e

WORKFLOW_FILE=".github/workflows/unit-tests.yml"

if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "Error: $WORKFLOW_FILE not found"
    exit 1
fi

echo "📊 Generating CI Test Summary..."
echo ""

# Extract matrices and count frameworks
python3 << 'PYTHON'
import yaml
import sys

# Read workflow file
with open('.github/workflows/unit-tests.yml', 'r') as f:
    workflow = yaml.safe_load(f)

# Extract framework counts from each job
jobs = workflow['jobs']
language_counts = {}
total_count = 0

# Process each job that has framework matrices or is a special single-framework job
for job_name, job_config in jobs.items():
    if 'strategy' not in job_config:
        # Special cases: jobs without matrix (e.g., hasura-tests)
        if job_name == 'hasura-tests':
            language_counts['HASURA'] = 1
            total_count += 1
        continue

    matrix = job_config['strategy'].get('matrix', {})

    # Handle simple framework list
    if 'framework' in matrix:
        frameworks = matrix['framework']
        if isinstance(frameworks, list):
            count = len(frameworks)
            language_key = job_name.replace('-tests', '').upper()
            language_counts[language_key] = count
            total_count += count

    # Handle include-based matrix (for JVM and special cases)
    elif 'include' in matrix:
        count = len(matrix['include'])
        language_key = job_name.replace('-tests', '').upper()
        language_counts[language_key] = count
        total_count += count

# Generate summary table
print("| Language | Frameworks |")
print("|----------|------------|")

language_mapping = {
    'PYTHON': 'Python',
    'TYPESCRIPT': 'TypeScript',
    'GO': 'Go',
    'JAVA': 'Java (Maven)',
    'JVM': 'JVM (Multi-tool)',
    'RUST': 'Rust',
    'PHP': 'PHP',
    'RUBY': 'Ruby',
    'CSHARP': 'C#',
    'HASURA': 'Hasura'
}

for lang_code in sorted(language_counts.keys()):
    lang_name = language_mapping.get(lang_code, lang_code.title())
    count = language_counts[lang_code]
    print(f"| {lang_name} | {count} |")

print("|----------|------------|")
print(f"| **TOTAL** | **{total_count}** |")
print()
print(f"✅ Total frameworks in CI: {total_count}")
PYTHON
