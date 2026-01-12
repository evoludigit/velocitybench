#!/usr/bin/env python3
"""
Generate FraiseQL v2 pattern YAML files for velocity benchmark.
Creates 180+ patterns covering compiled GraphQL execution, CDC, authorization, etc.
"""

import yaml
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path("database/seed-data/corpus/patterns/fraiseql")


def create_pattern(
    pattern_id: str,
    name: str,
    short_summary: str,
    long_summary: str,
    problem_desc: str,
    symptoms: list[str],
    key_concepts: dict[str, str],
    impl_considerations: dict[str, str],
    best_practices: list[dict[str, str]],
    anti_patterns: list[dict[str, str]],
    tags: list[str],
) -> dict[str, Any]:
    """Create a pattern dictionary."""
    return {
        "id": pattern_id,
        "name": name,
        "category": "fraiseql",
        "type": "standard",
        "tags": tags,
        "summary": {
            "short": short_summary,
            "long": long_summary,
        },
        "problem": {
            "description": problem_desc,
            "symptoms": symptoms,
            "impact": "Reduced effectiveness of compiled GraphQL execution",
        },
        "solution": {
            "description": f"Implement {name} effectively",
        },
        "key_concepts": key_concepts,
        "implementation_considerations": impl_considerations,
        "best_practices": best_practices,
        "anti_patterns": anti_patterns,
        "blog_hooks": {
            "beginner": {"focus": f"Introduction to {name}"},
            "intermediate": {"focus": f"Implementing {name}"},
            "advanced": {"focus": f"Advanced {name} techniques"},
        },
    }


def save_pattern(pattern: dict[str, Any]) -> None:
    """Save pattern to YAML file."""
    filename = OUTPUT_DIR / f"{pattern['id']}.yaml"
    with open(filename, "w") as f:
        yaml.dump(pattern, f, default_flow_style=False, sort_keys=False)
    print(f"✓ {filename.name}")


# ============================================================================
# 1. COMPILATION PIPELINE PATTERNS (20)
# ============================================================================

compilation_patterns = [
    create_pattern(
        "schema-authoring-with-python-sdk",
        "Schema Authoring with Python SDK",
        "Using Python decorators to define GraphQL schemas",
        "The Python SDK provides decorator-based schema authoring for GraphQL types, allowing developers to define schemas directly in Python code with type hints and validation.",
        "Manual schema writing is error-prone and hard to maintain",
        [
            "Schema validation errors caught at runtime",
            "Type mismatches between Python and GraphQL",
            "Difficulty enforcing schema conventions",
        ],
        {
            "concept_1": "Python SDK decorator fundamentals",
            "concept_2": "Type binding and field mapping",
            "concept_3": "Validation at definition time",
        },
        {
            "consideration_1": "Python version compatibility",
            "consideration_2": "Type hint completeness",
            "consideration_3": "IDE integration and autocomplete",
        },
        [
            {"name": "Use type hints", "description": "Always add type hints to fields"},
            {"name": "Validate early", "description": "Enable schema validation during definition"},
            {"name": "Document fields", "description": "Add descriptions to all fields"},
        ],
        [
            {"name": "Incomplete type hints", "consequence": "Loss of compile-time validation"},
            {"name": "Missing field validation", "consequence": "Runtime errors in compilation"},
        ],
        ["compilation", "python", "schema-authoring", "sdks"],
    ),
    create_pattern(
        "schema-authoring-with-yaml",
        "Schema Authoring with YAML",
        "Declarative schema definition using YAML syntax",
        "YAML-based schema authoring provides a language-agnostic way to define GraphQL schemas, ideal for configuration-driven development and multi-language teams.",
        "Complex schema definitions are hard to version control and review",
        [
            "Large schema files difficult to maintain",
            "Version control conflicts in schema files",
            "Difficulty in generating alternative formats",
        ],
        {
            "concept_1": "YAML schema structure and syntax",
            "concept_2": "Type relationships and bindings",
            "concept_3": "Validation rules in YAML",
        },
        {
            "consideration_1": "YAML parser compatibility",
            "consideration_2": "Schema organization and modularity",
            "consideration_3": "Cross-platform line ending handling",
        },
        [
            {"name": "Modularize", "description": "Split large schemas into multiple files"},
            {"name": "Use anchors", "description": "Leverage YAML anchors for reusable definitions"},
            {"name": "Version control", "description": "Track schema changes with clear diffs"},
        ],
        [
            {"name": "Monolithic files", "consequence": "Difficult to review and merge"},
            {"name": "Missing validation", "consequence": "Invalid schemas deployed to production"},
        ],
        ["compilation", "yaml", "schema-authoring", "declarative"],
    ),
    create_pattern(
        "schema-authoring-with-graphql-sdl",
        "Schema Authoring with GraphQL SDL",
        "Using GraphQL Schema Definition Language for schema definition",
        "GraphQL SDL provides a standard syntax for defining GraphQL schemas that is language-agnostic and widely understood by the GraphQL community.",
        "Different teams use different schema definition approaches",
        [
            "Inconsistent schema definitions across teams",
            "Difficulty integrating with GraphQL tooling",
            "Compatibility issues with GraphQL clients",
        ],
        {
            "concept_1": "GraphQL SDL syntax and semantics",
            "concept_2": "Type system representation in SDL",
            "concept_3": "Directive usage and custom directives",
        },
        {
            "consideration_1": "GraphQL version compatibility",
            "consideration_2": "Custom directive support",
            "consideration_3": "Tooling ecosystem integration",
        },
        [
            {"name": "Follow conventions", "description": "Adhere to SDL naming conventions"},
            {"name": "Use directives", "description": "Leverage directives for metadata"},
            {"name": "Document types", "description": "Add descriptions to all types and fields"},
        ],
        [
            {"name": "Ignoring directives", "consequence": "Loss of metadata and context"},
            {"name": "Non-standard SDL", "consequence": "Incompatibility with tools"},
        ],
        ["compilation", "graphql-sdl", "schema-authoring", "standards"],
    ),
    create_pattern(
        "multi-language-schema-input",
        "Multi-Language Schema Input",
        "Supporting schema definition in Python, YAML, GraphQL SDL, and TypeScript",
        "FraiseQL's compilation pipeline accepts schemas from multiple languages and formats, translating them to a language-agnostic intermediate representation for compilation.",
        "Teams are forced to choose one schema language",
        [
            "Different teams have different language preferences",
            "Polyglot development teams need flexibility",
            "Legacy systems use different formats",
        ],
        {
            "concept_1": "Intermediate representation design",
            "concept_2": "Format translation and normalization",
            "concept_3": "Semantic equivalence across formats",
        },
        {
            "consideration_1": "Parser implementation for each language",
            "consideration_2": "Format feature parity and gaps",
            "consideration_3": "Circular reference handling",
        },
        [
            {"name": "Choose consistently", "description": "Use one format per project"},
            {"name": "Document format mapping", "description": "Clearly show how formats map"},
            {"name": "Test all formats", "description": "Validate each format's compilation"},
        ],
        [
            {"name": "Mixing formats", "consequence": "Maintenance nightmare and confusion"},
            {"name": "Format gaps", "consequence": "Some features unavailable in some formats"},
        ],
        ["compilation", "schema-authoring", "polyglot", "formats"],
    ),
    create_pattern(
        "type-binding-to-database-views",
        "Type Binding to Database Views",
        "Mapping GraphQL types to database views (v_* naming convention)",
        "FraiseQL types are bound to database views rather than resolver functions, enabling compile-time verification that the data source exists and matches the schema.",
        "Resolvers can reference non-existent database objects or wrong schemas",
        [
            "Resolvers written before database schema exists",
            "Schema and database get out of sync",
            "Runtime errors when views don't exist",
        ],
        {
            "concept_1": "View naming conventions and discovery",
            "concept_2": "Column-to-field mapping",
            "concept_3": "Type matching and validation",
        },
        {
            "consideration_1": "Binding strategy and flexibility",
            "consideration_2": "Handling optional or polymorphic views",
            "consideration_3": "DBA vs API developer concerns",
        },
        [
            {"name": "Follow conventions", "description": "Use v_* prefix for GraphQL views"},
            {"name": "Validate bindings", "description": "Verify views exist before compilation"},
            {"name": "Document mappings", "description": "Clearly show type-to-view mappings"},
        ],
        [
            {"name": "Ad-hoc naming", "consequence": "Binding failures and confusion"},
            {"name": "Missing validation", "consequence": "Runtime errors in production"},
        ],
        ["compilation", "database-binding", "views", "schema-validation"],
    ),
    create_pattern(
        "intermediate-representation-design",
        "Intermediate Representation Design",
        "Language-agnostic compilation IR for schema normalization",
        "The compilation pipeline uses an intermediate representation (IR) to normalize schemas from different input languages, enabling database-agnostic compilation and validation.",
        "Each input format requires custom compilation logic",
        [
            "Code duplication across compilers",
            "Difficult to add new input formats",
            "Inconsistent compilation behavior",
        ],
        {
            "concept_1": "IR design and structure",
            "concept_2": "Format-to-IR translation",
            "concept_3": "IR-to-output generation",
        },
        {
            "consideration_1": "IR completeness and expressiveness",
            "consideration_2": "Round-trip conversion capability",
            "consideration_3": "Performance and memory efficiency",
        },
        [
            {"name": "Design for extension", "description": "IR should support new formats easily"},
            {"name": "Preserve fidelity", "description": "IR should not lose source information"},
            {"name": "Validate IR", "description": "Check IR consistency after translation"},
        ],
        [
            {"name": "Incomplete IR", "consequence": "Some formats lose information"},
            {"name": "Format-specific hacks", "consequence": "IR bloat and complexity"},
        ],
        ["compilation", "intermediate-representation", "architecture", "design"],
    ),
    create_pattern(
        "where-type-auto-generation",
        "WHERE Type Auto-Generation",
        "Automatically generating WHERE input types from database capabilities",
        "Instead of hardcoding filter operators, FraiseQL generates WHERE input types based on the database's capability manifest, enabling different operators across databases.",
        "WHERE types are hardcoded and don't match database capabilities",
        [
            "Unsupported filters attempted on SQLite",
            "Different WHERE types for different databases",
            "Maintenance burden of manual WHERE type creation",
        ],
        {
            "concept_1": "Database capability manifest structure",
            "concept_2": "WHERE type generator algorithms",
            "concept_3": "Operator support matching",
        },
        {
            "consideration_1": "Capability manifest discovery",
            "consideration_2": "Performance of WHERE type generation",
            "consideration_3": "Handling operator aliases and variants",
        },
        [
            {"name": "Capability-driven design", "description": "Generate types from capabilities"},
            {"name": "Test all databases", "description": "Verify WHERE types on each database"},
            {"name": "Document operators", "description": "List supported operators per database"},
        ],
        [
            {"name": "Hardcoded WHERE types", "consequence": "Inconsistent across databases"},
            {"name": "Missing operators", "consequence": "Users can't filter on available columns"},
        ],
        ["compilation", "where-types", "filters", "operators", "database-agnostic"],
    ),
    create_pattern(
        "database-introspection-strategy",
        "Database Introspection Strategy",
        "Querying database metadata to validate schema bindings",
        "The compiler introspects the target database to discover tables, views, columns, and procedures, validating that schema bindings reference valid database objects.",
        "Schema references database objects that don't exist",
        [
            "View bindings fail at runtime",
            "Column names don't match schema fields",
            "Stored procedures have wrong signatures",
        ],
        {
            "concept_1": "Introspection query patterns",
            "concept_2": "Metadata extraction and parsing",
            "concept_3": "Binding validation algorithms",
        },
        {
            "consideration_1": "Database-specific introspection queries",
            "consideration_2": "Performance of introspection",
            "consideration_3": "Handling schema evolution",
        },
        [
            {"name": "Cache metadata", "description": "Cache introspection results"},
            {"name": "Validate all objects", "description": "Check views, procedures, columns"},
            {"name": "Detect changes", "description": "Flag schema changes for review"},
        ],
        [
            {"name": "No introspection", "consequence": "Silent binding failures"},
            {"name": "Stale metadata", "consequence": "Invalid bindings not caught"},
        ],
        ["compilation", "database-introspection", "validation", "metadata"],
    ),
    create_pattern(
        "compilation-validation-engine",
        "Compilation Validation Engine",
        "Comprehensive validation of schema, bindings, authorization, and capabilities",
        "The compilation pipeline includes a comprehensive validation engine that checks type closure, binding correctness, authorization rule validity, and database capability matching.",
        "Invalid schemas are compiled and deployed, causing runtime failures",
        [
            "Missing type definitions cause resolver errors",
            "Authorization rules reference non-existent fields",
            "WHERE clauses use unsupported operators",
        ],
        {
            "concept_1": "Validation rule categories",
            "concept_2": "Error accumulation and reporting",
            "concept_3": "Validation phase in compilation",
        },
        {
            "consideration_1": "Validation rule extensibility",
            "consideration_2": "Performance of validation",
            "consideration_3": "Error message clarity",
        },
        [
            {"name": "Run validation early", "description": "Catch errors before deployment"},
            {"name": "Report all errors", "description": "Don't stop at first error"},
            {"name": "Clear messages", "description": "Help developers fix problems"},
        ],
        [
            {"name": "Partial validation", "consequence": "Some errors slip through"},
            {"name": "Stopping on first error", "consequence": "Multiple compilation rounds"},
        ],
        ["compilation", "validation", "error-handling", "quality"],
    ),
    create_pattern(
        "schema-artifacts-generation",
        "Schema Artifacts Generation",
        "Generating CompiledSchema, GraphQL SDL, and validation reports",
        "The compilation pipeline outputs multiple artifacts: CompiledSchema (execution plan), GraphQL SDL (for clients), and validation reports (for developers).",
        "Hard to know what was compiled or debug compilation issues",
        [
            "No way to inspect compiled queries",
            "Clients don't know schema structure",
            "Validation errors not documented",
        ],
        {
            "concept_1": "Artifact types and formats",
            "concept_2": "CompiledSchema structure",
            "concept_3": "Report generation and formatting",
        },
        {
            "consideration_1": "Artifact versioning",
            "consideration_2": "Artifact compatibility",
            "consideration_3": "Artifact documentation",
        },
        [
            {"name": "Generate all artifacts", "description": "Don't skip schema or reports"},
            {"name": "Version artifacts", "description": "Track schema versions"},
            {"name": "Document structure", "description": "Explain artifact contents"},
        ],
        [
            {"name": "Missing artifacts", "consequence": "No visibility into compilation"},
            {"name": "Incompatible versions", "consequence": "Client/server mismatches"},
        ],
        ["compilation", "artifacts", "code-generation", "outputs"],
    ),
    create_pattern(
        "multi-database-compilation",
        "Multi-Database Compilation",
        "Database-agnostic compilation with optional per-database optimizations",
        "FraiseQL compiles once to a database-agnostic CompiledSchema, which can then be targeted to PostgreSQL, SQLite, Oracle, MySQL, or SQL Server with optional optimizations.",
        "Separate compilation and schema per database",
        [
            "Managing multiple schema versions",
            "Inconsistent behavior across databases",
            "Wasted compilation effort",
        ],
        {
            "concept_1": "Database-agnostic contracts",
            "concept_2": "Capability matching and selection",
            "concept_3": "Per-database optimization strategies",
        },
        {
            "consideration_1": "Feature parity across databases",
            "consideration_2": "Performance trade-offs",
            "consideration_3": "Testing multi-database setups",
        },
        [
            {"name": "Compile once", "description": "Single schema for all databases"},
            {"name": "Optimize per database", "description": "Use best features of each DB"},
            {"name": "Test all variants", "description": "Run tests on every target database"},
        ],
        [
            {"name": "Database-specific schemas", "consequence": "Maintenance nightmare"},
            {"name": "No optimization", "consequence": "Poor performance on capable databases"},
        ],
        ["compilation", "multi-database", "database-agnostic", "optimization"],
    ),
    create_pattern(
        "schema-parsing-multiple-formats",
        "Schema Parsing from Multiple Formats",
        "Implementing parsers for Python, YAML, GraphQL SDL, and TypeScript schemas",
        "The compilation pipeline includes parsers for multiple schema formats, translating each to the intermediate representation for database-agnostic compilation.",
        "Limited to single schema format",
        [
            "Teams restricted to one language",
            "Difficulty integrating existing schemas",
            "Inflexible tooling integration",
        ],
        {
            "concept_1": "Parser architecture patterns",
            "concept_2": "Format-specific parsing logic",
            "concept_3": "Error recovery in parsing",
        },
        {
            "consideration_1": "Parser complexity per format",
            "consideration_2": "Performance of parsing",
            "consideration_3": "Maintaining format parity",
        },
        [
            {"name": "Parser tests", "description": "Test each format extensively"},
            {"name": "Error messages", "description": "Clear feedback for parse errors"},
            {"name": "Performance", "description": "Parse schemas quickly"},
        ],
        [
            {"name": "Single parser", "consequence": "Limited format support"},
            {"name": "Incomplete parsing", "consequence": "Features lost in translation"},
        ],
        ["compilation", "parsing", "formats", "multi-language"],
    ),
    create_pattern(
        "six-phase-compilation-process",
        "Six-Phase Compilation Process",
        "Parser, Binder, WHERE Generator, Validator, Optimizer, and Artifact Emitter phases",
        "The compilation pipeline consists of six phases: parsing the input schema, binding types to databases, generating WHERE filter types, validating everything, optimizing, and emitting artifacts.",
        "Ad-hoc compilation without clear phases",
        [
            "Unclear where compilation errors originate",
            "Difficult to add compilation features",
            "Inconsistent compilation behavior",
        ],
        {
            "concept_1": "Phase architecture",
            "concept_2": "Phase responsibilities and boundaries",
            "concept_3": "Data flow between phases",
        },
        {
            "consideration_1": "Phase extensibility",
            "consideration_2": "Phase performance and ordering",
            "consideration_3": "Error propagation between phases",
        },
        [
            {"name": "Clear phases", "description": "Each phase has single responsibility"},
            {"name": "Validate between phases", "description": "Check output of each phase"},
            {"name": "Document flow", "description": "Explain data flow through phases"},
        ],
        [
            {"name": "Mixed concerns", "consequence": "Hard to maintain and extend"},
            {"name": "No validation", "consequence": "Invalid intermediate states"},
        ],
        ["compilation", "phases", "architecture", "design"],
    ),
    create_pattern(
        "compilation-error-reporting",
        "Compilation Error Reporting",
        "Accumulating and formatting validation errors for developer feedback",
        "The compilation pipeline accumulates all errors (not just stopping at the first) and formats them with line numbers, suggestions, and context for easy debugging.",
        "Single error stops compilation and requires multiple rounds to fix",
        [
            "Multiple compilation rounds to find all errors",
            "Unclear error messages",
            "No suggestions for fixes",
        ],
        {
            "concept_1": "Error accumulation patterns",
            "concept_2": "Error formatting and context",
            "concept_3": "Error categorization",
        },
        {
            "consideration_1": "Error message clarity",
            "consideration_2": "Suggestion accuracy",
            "consideration_3": "Line number accuracy",
        },
        [
            {"name": "Accumulate errors", "description": "Report all problems at once"},
            {"name": "Clear messages", "description": "Explain what went wrong and why"},
            {"name": "Suggestions", "description": "Help developers fix problems"},
        ],
        [
            {"name": "First-error stopping", "consequence": "Multiple compilation rounds"},
            {"name": "Vague messages", "consequence": "Hard to debug"},
        ],
        ["compilation", "error-handling", "diagnostics", "developer-experience"],
    ),
    create_pattern(
        "deterministic-compilation",
        "Deterministic Compilation",
        "Guaranteed identical output for identical input schema",
        "The compilation pipeline is deterministic: the same input schema always produces the same CompiledSchema artifact, enabling reproducible builds and caching.",
        "Non-deterministic compilation makes caching and debugging difficult",
        [
            "Different compiled schemas from same input",
            "Can't cache compilation results",
            "Difficult to debug non-determinism",
        ],
        {
            "concept_1": "Determinism guarantees",
            "concept_2": "Sources of non-determinism",
            "concept_3": "Testing for determinism",
        },
        {
            "consideration_1": "Hash-based caching",
            "consideration_2": "Dictionary ordering",
            "consideration_3": "Floating-point operations",
        },
        [
            {"name": "Sorted output", "description": "Sort all collections in output"},
            {"name": "Fixed seeds", "description": "Use deterministic randomization"},
            {"name": "Test determinism", "description": "Verify same input produces same output"},
        ],
        [
            {"name": "Random ordering", "consequence": "Can't rely on output"},
            {"name": "No determinism testing", "consequence": "Non-determinism discovered in production"},
        ],
        ["compilation", "determinism", "reproducibility", "caching"],
    ),
    create_pattern(
        "schema-versioning-compatibility",
        "Schema Versioning and Compatibility",
        "Tracking schema versions and managing forward/backward compatibility",
        "FraiseQL schemas are versioned to track changes, and the compiler validates that schema changes maintain compatibility with existing clients and servers.",
        "Schema changes break clients without warning",
        [
            "Deployed schemas break existing clients",
            "Can't track when schema changed",
            "No way to support multiple versions",
        ],
        {
            "concept_1": "Version numbering schemes",
            "concept_2": "Compatibility checking algorithms",
            "concept_3": "Version metadata tracking",
        },
        {
            "consideration_1": "Semantic versioning",
            "consideration_2": "Migration path support",
            "consideration_3": "Client version negotiation",
        },
        [
            {"name": "Semantic versioning", "description": "Use major.minor.patch versioning"},
            {"name": "Compatibility checks", "description": "Validate changes are compatible"},
            {"name": "Version metadata", "description": "Store version with compiled schema"},
        ],
        [
            {"name": "No versioning", "consequence": "No way to track changes"},
            {"name": "No compatibility checking", "consequence": "Breaking changes deployed"},
        ],
        ["compilation", "versioning", "compatibility", "evolution"],
    ),
    create_pattern(
        "capability-manifest-design",
        "Capability Manifest Design",
        "Database feature declarations for capability-driven compilation",
        "FraiseQL uses a capability manifest to declare what features each database supports (operators, functions, extensions), enabling capability-driven compilation and optimization.",
        "Hardcoded database feature support matrix",
        [
            "Difficult to add support for new database",
            "Wrong operators generated for database",
            "Manual updates when database changes",
        ],
        {
            "concept_1": "Capability categories and types",
            "concept_2": "Manifest structure and format",
            "concept_3": "Capability matching algorithms",
        },
        {
            "consideration_1": "Manifest versioning",
            "consideration_2": "Capability discovery vs declaration",
            "consideration_3": "Fallback capabilities",
        },
        [
            {"name": "Structured manifest", "description": "Organize capabilities logically"},
            {"name": "Version capabilities", "description": "Track capability versions"},
            {"name": "Test coverage", "description": "Test each capability"},
        ],
        [
            {"name": "Hardcoded features", "consequence": "Unmaintainable feature list"},
            {"name": "Undeclared capabilities", "consequence": "Missing optimizations"},
        ],
        ["compilation", "capabilities", "database-features", "manifest"],
    ),
    create_pattern(
        "type-closure-validation",
        "Type Closure Validation",
        "Ensuring all referenced types are defined and relationships are valid",
        "The validator checks type closure by ensuring all referenced types exist, circular dependencies are avoided, and relationship constraints are satisfied.",
        "Schema references undefined types",
        [
            "Runtime errors when missing types referenced",
            "Circular type dependencies cause confusion",
            "Invalid relationships allowed",
        ],
        {
            "concept_1": "Type graph construction",
            "concept_2": "Closure checking algorithms",
            "concept_3": "Circular dependency detection",
        },
        {
            "consideration_1": "Handling interfaces and unions",
            "consideration_2": "Performance of closure checking",
            "consideration_3": "Clear error messages",
        },
        [
            {"name": "Validate closure", "description": "Check all types are defined"},
            {"name": "Detect cycles", "description": "Find and report circular deps"},
            {"name": "Clear errors", "description": "Show missing types and cycles"},
        ],
        [
            {"name": "No closure check", "consequence": "Runtime type errors"},
            {"name": "Cycle detection fails", "consequence": "Infinite loops or confusion"},
        ],
        ["compilation", "validation", "type-system", "graph-analysis"],
    ),
    create_pattern(
        "authorization-rule-compilation",
        "Authorization Rule Compilation",
        "Pre-compiling authorization metadata during schema compilation",
        "Authorization rules are compiled into metadata during schema compilation, not evaluated at runtime, ensuring they can't be bypassed and enabling static analysis.",
        "Authorization logic in resolver code",
        [
            "Authorization logic can be bypassed",
            "No way to audit authorization decisions",
            "Difficult to ensure consistent auth",
        ],
        {
            "concept_1": "Rule metadata structure",
            "concept_2": "Authorization metadata compilation",
            "concept_3": "Field vs query vs mutation auth",
        },
        {
            "consideration_1": "Rule expressiveness",
            "consideration_2": "Rule composition",
            "consideration_3": "Runtime rule evaluation",
        },
        [
            {"name": "Compile rules upfront", "description": "Generate auth metadata during compilation"},
            {"name": "Audit metadata", "description": "Inspect auth decisions"},
            {"name": "Consistent enforcement", "description": "Same rules everywhere"},
        ],
        [
            {"name": "Runtime auth checks", "consequence": "Can be bypassed"},
            {"name": "Ad-hoc rules", "consequence": "Inconsistent enforcement"},
        ],
        ["compilation", "authorization", "security", "metadata"],
    ),
    create_pattern(
        "view-existence-validation",
        "View Existence Validation",
        "Verifying that all bound views exist in the database",
        "The compiler checks that all views referenced in type bindings actually exist in the target database, preventing broken bindings.",
        "Schema binds to views that don't exist",
        [
            "Execution fails when views don't exist",
            "No way to validate bindings",
            "Hard to debug binding errors",
        ],
        {
            "concept_1": "View discovery strategies",
            "concept_2": "Validation algorithms",
            "concept_3": "Error reporting for missing views",
        },
        {
            "consideration_1": "Performance of view checking",
            "consideration_2": "Handling schema changes",
            "consideration_3": "View versioning",
        },
        [
            {"name": "Check all views", "description": "Verify every bound view exists"},
            {"name": "Clear errors", "description": "Say which views are missing"},
            {"name": "Suggestions", "description": "Suggest similar view names"},
        ],
        [
            {"name": "No view checking", "consequence": "Broken schemas deployed"},
            {"name": "Silent failures", "consequence": "No indication of problem"},
        ],
        ["compilation", "validation", "database", "binding"],
    ),
    create_pattern(
        "procedure-signature-validation",
        "Procedure Signature Validation",
        "Verifying stored procedure signatures match mutation contracts",
        "The compiler validates that stored procedures used for mutations have the correct signatures (parameters and return types) matching the mutation contract.",
        "Stored procedure calls fail due to signature mismatch",
        [
            "Wrong number of parameters passed",
            "Wrong data types for parameters",
            "Return type doesn't match response contract",
        ],
        {
            "concept_1": "Procedure metadata extraction",
            "concept_2": "Signature matching algorithms",
            "concept_3": "Contract validation",
        },
        {
            "consideration_1": "Parameter name matching",
            "consideration_2": "Optional vs required parameters",
            "consideration_3": "Return type polymorphism",
        },
        [
            {"name": "Validate parameters", "description": "Check parameter count and types"},
            {"name": "Validate return", "description": "Check return type matches contract"},
            {"name": "Clear errors", "description": "Show signature mismatches"},
        ],
        [
            {"name": "No signature checking", "consequence": "Runtime procedure call failures"},
            {"name": "Loose matching", "consequence": "Type errors at execution"},
        ],
        ["compilation", "validation", "database", "procedures"],
    ),
    create_pattern(
        "operator-support-validation",
        "Operator Support Validation",
        "Verifying WHERE operators are supported by target database",
        "The compiler validates that all WHERE operators in the schema are supported by the target database, using the capability manifest.",
        "WHERE clause uses unsupported operators",
        [
            "Query fails at runtime with unknown operator",
            "Different results on different databases",
            "No way to know what operators are available",
        ],
        {
            "concept_1": "Operator catalog",
            "concept_2": "Capability matching",
            "concept_3": "Fallback operator strategies",
        },
        {
            "consideration_1": "Operator aliases and variants",
            "consideration_2": "Performance of different operators",
            "consideration_3": "Custom operator support",
        },
        [
            {"name": "Match against capability", "description": "Use capability manifest to check"},
            {"name": "Suggest alternatives", "description": "If operator not available, suggest one that is"},
            {"name": "Clear errors", "description": "Tell user which operators unavailable"},
        ],
        [
            {"name": "No operator checking", "consequence": "Runtime query failures"},
            {"name": "Hardcoded operators", "consequence": "Same operators across all DBs"},
        ],
        ["compilation", "validation", "operators", "database-capabilities"],
    ),
]

for pattern in compilation_patterns:
    save_pattern(pattern)

print(f"\n✓ Generated {len(compilation_patterns)} compilation pipeline patterns")

# ============================================================================
# 2. QUERY EXECUTION PATTERNS (25)
# ============================================================================

execution_patterns = [
    create_pattern(
        "six-phase-query-execution",
        "Six-Phase Query Execution Pipeline",
        "Validation, Authorization, Planning, Execution, Projection, and Error Handling",
        "GraphQL queries go through six phases: request validation against schema, authorization rule checking, query plan optimization, database execution, result projection, and error handling.",
        "Unclear query execution flow and responsibility",
        [
            "Difficult to debug query execution",
            "Authorization decisions unclear",
            "Performance bottlenecks hard to identify",
        ],
        {
            "concept_1": "Execution phase separation",
            "concept_2": "Data flow between phases",
            "concept_3": "Phase responsibilities",
        },
        {
            "consideration_1": "Phase ordering optimization",
            "consideration_2": "Error handling across phases",
            "consideration_3": "Observability in each phase",
        },
        [
            {"name": "Clear phases", "description": "Each phase has single responsibility"},
            {"name": "Phase boundaries", "description": "Clear input/output contracts"},
            {"name": "Observability", "description": "Instrument each phase"},
        ],
        [
            {"name": "Mixed phases", "consequence": "Hard to understand execution"},
            {"name": "No instrumentation", "consequence": "Can't debug issues"},
        ],
        ["execution", "pipeline", "phases", "architecture"],
    ),
    create_pattern(
        "graphql-request-validation",
        "GraphQL Request Validation",
        "Validating queries conform to compiled schema",
        "GraphQL requests are validated against the CompiledSchema to ensure they conform to the schema structure, argument requirements, and type constraints.",
        "Invalid queries reach execution without feedback",
        [
            "Queries with syntax errors execute",
            "Wrong argument types accepted",
            "Confusing error messages",
        ],
        {
            "concept_1": "Schema validation rules",
            "concept_2": "Query structure validation",
            "concept_3": "Argument type checking",
        },
        {
            "consideration_1": "Validation rule completeness",
            "consideration_2": "Error message clarity",
            "consideration_3": "Performance of validation",
        },
        [
            {"name": "Validate early", "description": "Check queries before execution"},
            {"name": "Clear errors", "description": "Explain validation failures"},
            {"name": "Suggest fixes", "description": "Help users fix invalid queries"},
        ],
        [
            {"name": "Partial validation", "consequence": "Some invalid queries pass through"},
            {"name": "Poor error messages", "consequence": "Hard to debug queries"},
        ],
        ["execution", "validation", "graphql", "quality"],
    ),
    create_pattern(
        "deterministic-authorization-enforcement",
        "Deterministic Authorization Enforcement",
        "Applying pre-compiled authorization rules consistently",
        "Authorization is enforced by applying pre-compiled metadata rules, not runtime resolver logic, ensuring consistent and auditable authorization decisions.",
        "Authorization enforcement varies or can be bypassed",
        [
            "Inconsistent authorization across fields",
            "Authorization bypassed through alternate queries",
            "No audit trail of auth decisions",
        ],
        {
            "concept_1": "Rule metadata application",
            "concept_2": "Decision algorithms",
            "concept_3": "Authorization context",
        },
        {
            "consideration_1": "Rule composition",
            "consideration_2": "Context availability",
            "consideration_3": "Performance of enforcement",
        },
        [
            {"name": "Use compiled rules", "description": "Apply pre-compiled auth metadata"},
            {"name": "Consistent enforcement", "description": "Same rules everywhere"},
            {"name": "Audit decisions", "description": "Log authorization decisions"},
        ],
        [
            {"name": "Runtime auth checks", "consequence": "Can be bypassed or inconsistent"},
            {"name": "Ad-hoc rules", "consequence": "Difficult to reason about"},
        ],
        ["execution", "authorization", "security", "determinism"],
    ),
    create_pattern(
        "authorization-context-extraction",
        "Authorization Context Extraction",
        "Parsing JWT claims, session data, and tenant context",
        "The execution pipeline extracts authorization context from JWT tokens, session data, or other sources, providing role, claims, and tenant information for authorization checks.",
        "Authorization context unclear or incomplete",
        [
            "Some required context missing",
            "Claims not properly extracted",
            "Tenant context not propagated",
        ],
        {
            "concept_1": "JWT parsing and validation",
            "concept_2": "Claim extraction",
            "concept_3": "Tenant context propagation",
        },
        {
            "consideration_1": "Context caching",
            "consideration_2": "Multiple auth sources",
            "consideration_3": "Default context values",
        },
        [
            {"name": "Validate tokens", "description": "Verify JWT signatures and expiry"},
            {"name": "Extract completely", "description": "Get all relevant claims"},
            {"name": "Propagate context", "description": "Make context available to auth rules"},
        ],
        [
            {"name": "No validation", "consequence": "Untrusted context used in auth"},
            {"name": "Missing claims", "consequence": "Auth rules can't evaluate properly"},
        ],
        ["execution", "authorization", "security", "authentication"],
    ),
    create_pattern(
        "field-level-authorization",
        "Field-Level Authorization",
        "Applying authorization rules per field in response",
        "Authorization rules can be applied to individual fields, controlling whether each field is included in the response based on user permissions.",
        "Entire queries succeed or fail; can't restrict fields",
        [
            "Users see data they shouldn't",
            "Can't use single query for different roles",
            "Hard to implement field-level security",
        ],
        {
            "concept_1": "Field auth metadata",
            "concept_2": "Field masking logic",
            "concept_3": "Nested field auth",
        },
        {
            "consideration_1": "Error handling for denied fields",
            "consideration_2": "Performance of field checking",
            "consideration_3": "Null vs error for denied fields",
        },
        [
            {"name": "Define per-field", "description": "Set auth rules per field"},
            {"name": "Consistent application", "description": "Apply rules everywhere"},
            {"name": "Clear semantics", "description": "Define behavior for denied fields"},
        ],
        [
            {"name": "No field-level auth", "consequence": "Can't restrict specific fields"},
            {"name": "Inconsistent enforcement", "consequence": "Same field protected differently"},
        ],
        ["execution", "authorization", "security", "field-level"],
    ),
    create_pattern(
        "authorization-decision-algorithm",
        "Authorization Decision Algorithm",
        "Evaluating compiled rules for role, claim, and custom checks",
        "The decision algorithm evaluates compiled authorization rules, checking role requirements, JWT claims, and custom conditions to allow or deny access.",
        "Authorization logic is ad-hoc and inconsistent",
        [
            "Some authorization rules don't work",
            "Inconsistent decisions across similar scenarios",
            "Difficult to add new auth rules",
        ],
        {
            "concept_1": "Rule types (role, claim, custom)",
            "concept_2": "Evaluation order",
            "concept_3": "Decision outcomes",
        },
        {
            "consideration_1": "Short-circuit evaluation",
            "consideration_2": "Error handling in evaluation",
            "consideration_3": "Caching decisions",
        },
        [
            {"name": "Clear rules", "description": "Make rules explicit and readable"},
            {"name": "Consistent evaluation", "description": "Always use same algorithm"},
            {"name": "Test all rules", "description": "Verify each rule works correctly"},
        ],
        [
            {"name": "Unclear rules", "consequence": "Unpredictable authorization"},
            {"name": "Ad-hoc evaluation", "consequence": "Inconsistent results"},
        ],
        ["execution", "authorization", "algorithms", "security"],
    ),
    create_pattern(
        "query-planning-optimization",
        "Query Planning and Optimization",
        "Pre-computed execution plans with optional database optimization",
        "Queries are planned during compilation, creating pre-computed execution plans that can be cached and optimized for the target database.",
        "Queries planned at runtime with variable performance",
        [
            "Unpredictable query performance",
            "Query planning overhead",
            "Difficult to optimize queries",
        ],
        {
            "concept_1": "Plan caching",
            "concept_2": "Database-specific optimization",
            "concept_3": "Plan analysis and visualization",
        },
        {
            "consideration_1": "Plan cache invalidation",
            "consideration_2": "Plan size and complexity",
            "consideration_3": "Explain plan analysis",
        },
        [
            {"name": "Pre-compute plans", "description": "Generate plans during compilation"},
            {"name": "Cache plans", "description": "Reuse plans across requests"},
            {"name": "Monitor plans", "description": "Analyze plan efficiency"},
        ],
        [
            {"name": "Runtime planning", "consequence": "Variable performance"},
            {"name": "No caching", "consequence": "Repeated planning overhead"},
        ],
        ["execution", "performance", "optimization", "planning"],
    ),
    create_pattern(
        "where-clause-compilation",
        "WHERE Clause Compilation to SQL",
        "Converting GraphQL filter input to database-specific SQL WHERE clauses",
        "WHERE clauses from GraphQL filter inputs are compiled to SQL WHERE clauses, handling operators, types, and database-specific syntax.",
        "Manual WHERE clause construction is error-prone",
        [
            "SQL injection vulnerabilities",
            "Incorrect filter logic",
            "Wrong operators for database",
        ],
        {
            "concept_1": "Filter input structure",
            "concept_2": "WHERE clause generation",
            "concept_3": "Operator mapping",
        },
        {
            "consideration_1": "Type conversion",
            "consideration_2": "Null handling",
            "consideration_3": "Complex filter composition",
        },
        [
            {"name": "Parameterized queries", "description": "Always use parameters, never string concat"},
            {"name": "Validate operators", "description": "Check operators are supported"},
            {"name": "Test filters", "description": "Test WHERE clause on all databases"},
        ],
        [
            {"name": "String concatenation", "consequence": "SQL injection vulnerability"},
            {"name": "No operator validation", "consequence": "Runtime errors"},
        ],
        ["execution", "sql-generation", "filters", "security"],
    ),
    create_pattern(
        "database-execution-strategy",
        "Database Execution Strategy",
        "Translating execution plans to database dialect SQL",
        "The execution engine translates pre-computed plans into database-specific SQL, handling dialect differences and database-specific features.",
        "Single SQL generation approach fails on different databases",
        [
            "Queries work on PostgreSQL but fail on SQLite",
            "Different results on different databases",
            "Can't use database-specific features",
        ],
        {
            "concept_1": "SQL dialect handling",
            "concept_2": "Database feature detection",
            "concept_3": "Fallback strategies",
        },
        {
            "consideration_1": "Performance of dialect translation",
            "consideration_2": "Feature availability",
            "consideration_3": "Error handling",
        },
        [
            {"name": "Database adapters", "description": "Separate adapter per database"},
            {"name": "Feature detection", "description": "Check capability before using feature"},
            {"name": "Fallback paths", "description": "Provide alternatives if feature unavailable"},
        ],
        [
            {"name": "Single SQL generation", "consequence": "Fails on some databases"},
            {"name": "No adapters", "consequence": "Can't use database features"},
        ],
        ["execution", "sql-generation", "multi-database", "adapters"],
    ),
    create_pattern(
        "result-projection-from-jsonb",
        "Result Projection from JSONB",
        "Extracting and projecting fields from database JSONB responses",
        "Results from database views are JSONB objects; the projection phase extracts requested fields and constructs the GraphQL response shape.",
        "Hard to extract correct fields from response",
        [
            "Response contains unwanted fields",
            "Nested structure doesn't match schema",
            "Missing requested fields",
        ],
        {
            "concept_1": "JSONB field extraction",
            "concept_2": "Path navigation",
            "concept_3": "Type conversion",
        },
        {
            "consideration_1": "Null handling",
            "consideration_2": "Type coercion",
            "consideration_3": "Performance of extraction",
        },
        [
            {"name": "Follow schema", "description": "Only include fields in schema"},
            {"name": "Handle nulls", "description": "Correctly handle missing fields"},
            {"name": "Type check", "description": "Verify field types match schema"},
        ],
        [
            {"name": "Include all fields", "consequence": "Unwanted data exposure"},
            {"name": "Type mismatch", "consequence": "Invalid response"},
        ],
        ["execution", "projection", "response-formatting", "jsonb"],
    ),
    create_pattern(
        "nested-type-projection",
        "Nested Type Projection",
        "Constructing nested GraphQL responses from flat database results",
        "Complex nested GraphQL types are constructed from flat database results, requiring multi-level projection and composition logic.",
        "Nested queries produce incorrect structure",
        [
            "Nested objects missing or malformed",
            "Wrong nesting depth",
            "Extra nesting levels",
        ],
        {
            "concept_1": "Nested result assembly",
            "concept_2": "Grouping and joining",
            "concept_3": "Recursive nesting",
        },
        {
            "consideration_1": "N+1 query prevention",
            "consideration_2": "Performance of nesting",
            "consideration_3": "Circular references",
        },
        [
            {"name": "Pre-computed views", "description": "Use views to compose nested shapes"},
            {"name": "Test nesting", "description": "Verify nested structure is correct"},
            {"name": "Avoid N+1", "description": "Fetch all data in single query"},
        ],
        [
            {"name": "Manual nesting", "consequence": "Hard to get structure right"},
            {"name": "Query per field", "consequence": "N+1 query problems"},
        ],
        ["execution", "projection", "nested-types", "response-formatting"],
    ),
    create_pattern(
        "mutation-execution-via-stored-procedures",
        "Mutation Execution via Stored Procedures",
        "Calling database stored procedures for mutations",
        "GraphQL mutations are executed as stored procedure calls, delegating business logic to the database.",
        "Mutations duplicated across application and database",
        [
            "Inconsistent mutation logic",
            "Data integrity issues",
            "Difficult to debug mutations",
        ],
        {
            "concept_1": "Procedure call patterns",
            "concept_2": "Parameter passing",
            "concept_3": "Response parsing",
        },
        {
            "consideration_1": "Transaction handling",
            "consideration_2": "Error handling",
            "consideration_3": "Audit logging",
        },
        [
            {"name": "Single logic source", "description": "Put mutation logic in stored procedure"},
            {"name": "Consistent calls", "description": "Always use same calling pattern"},
            {"name": "Test procedures", "description": "Test all mutation procedures"},
        ],
        [
            {"name": "Application logic", "consequence": "Duplication with database logic"},
            {"name": "Inconsistent calls", "consequence": "Hard to maintain"},
        ],
        ["execution", "mutations", "stored-procedures", "database-logic"],
    ),
    create_pattern(
        "mutation-response-contract",
        "Mutation Response Contract",
        "Structured response from stored procedures matching schema",
        "Stored procedures return structured responses conforming to the mutation response contract defined in the schema.",
        "Procedure responses don't match expected schema",
        [
            "Response parsing fails",
            "Missing required fields",
            "Type mismatches in response",
        ],
        {
            "concept_1": "Response structure",
            "concept_2": "Contract definition",
            "concept_3": "Response validation",
        },
        {
            "consideration_1": "Error responses",
            "consideration_2": "Partial success handling",
            "consideration_3": "Response size limits",
        },
        [
            {"name": "Define contract", "description": "Clearly specify response structure"},
            {"name": "Validate response", "description": "Check response matches contract"},
            {"name": "Test responses", "description": "Test all response scenarios"},
        ],
        [
            {"name": "Informal contract", "consequence": "Responses unpredictable"},
            {"name": "No validation", "consequence": "Invalid responses not caught"},
        ],
        ["execution", "mutations", "contracts", "response-design"],
    ),
    create_pattern(
        "cache-invalidation-emission",
        "Cache Invalidation Emission",
        "Emitting cache invalidation events after mutations",
        "After mutations complete, cache invalidation events are emitted indicating what cached data is now stale.",
        "Cache never invalidated after mutations",
        [
            "Stale data returned from cache",
            "Users see old data",
            "Manual cache clearing required",
        ],
        {
            "concept_1": "Invalidation event types",
            "concept_2": "Entity dependency tracking",
            "concept_3": "Cascade invalidation",
        },
        {
            "consideration_1": "Invalidation timing",
            "consideration_2": "Partial invalidation",
            "consideration_3": "Cache warming strategies",
        },
        [
            {"name": "Track mutations", "description": "Know what was changed"},
            {"name": "Emit events", "description": "Send invalidation events"},
            {"name": "Handle cascades", "description": "Invalidate dependent data"},
        ],
        [
            {"name": "No invalidation", "consequence": "Stale cached data"},
            {"name": "Overly broad invalidation", "consequence": "Unnecessary cache misses"},
        ],
        ["execution", "caching", "mutations", "cache-invalidation"],
    ),
    create_pattern(
        "error-handling-partial-results",
        "Error Handling and Partial Results",
        "Gracefully handling errors in nested queries with partial result returns",
        "When errors occur in nested fields, the response can return partial results for successful fields and errors for failed fields.",
        "Single error fails entire query",
        [
            "Query fails completely on any error",
            "Can't get any data if one field fails",
            "Difficult error debugging",
        ],
        {
            "concept_1": "Error propagation",
            "concept_2": "Partial response handling",
            "concept_3": "Error accumulation",
        },
        {
            "consideration_1": "Error context and paths",
            "consideration_2": "Null vs error semantics",
            "consideration_3": "Client error handling",
        },
        [
            {"name": "Partial success", "description": "Return successful fields with errors"},
            {"name": "Clear errors", "description": "Include error context and paths"},
            {"name": "Graceful degradation", "description": "Get best-effort results"},
        ],
        [
            {"name": "All-or-nothing", "consequence": "Single error loses all data"},
            {"name": "Vague errors", "consequence": "Hard to debug"},
        ],
        ["execution", "error-handling", "resilience", "robustness"],
    ),
    create_pattern(
        "multi-database-execution",
        "Multi-Database Execution",
        "Adapting execution engine for different database targets",
        "The execution engine adapts for different databases (PostgreSQL, SQLite, Oracle, MySQL, SQL Server), using database-specific SQL and features.",
        "Execution fails when targeting different database",
        [
            "Queries work on PostgreSQL but fail on SQLite",
            "Performance varies widely across databases",
            "Can't use database-specific features",
        ],
        {
            "concept_1": "Database adapter pattern",
            "concept_2": "Feature capability checking",
            "concept_3": "Dialect translation",
        },
        {
            "consideration_1": "Performance per database",
            "consideration_2": "Feature availability",
            "consideration_3": "Testing coverage",
        },
        [
            {"name": "Database adapters", "description": "Separate adapter per database"},
            {"name": "Capability detection", "description": "Check before using features"},
            {"name": "Test on all DBs", "description": "Run tests on every target database"},
        ],
        [
            {"name": "Database-specific code", "consequence": "Can't switch databases"},
            {"name": "No adapters", "consequence": "Features don't work on all DBs"},
        ],
        ["execution", "multi-database", "adapters", "compatibility"],
    ),
    create_pattern(
        "streaming-results",
        "Streaming Large Result Sets",
        "Memory-efficient handling of large paginated result sets",
        "Large result sets are streamed to clients with pagination, avoiding loading entire results into memory.",
        "Large queries consume excessive memory or timeout",
        [
            "Out-of-memory errors on large queries",
            "Query timeouts",
            "Slow client response",
        ],
        {
            "concept_1": "Pagination strategies",
            "concept_2": "Stream handling",
            "concept_3": "Cursor design",
        },
        {
            "consideration_1": "Cursor encoding",
            "consideration_2": "Page size optimization",
            "consideration_3": "Sort stability",
        },
        [
            {"name": "Paginate results", "description": "Return data in pages"},
            {"name": "Efficient cursors", "description": "Use efficient cursor encoding"},
            {"name": "Memory efficient", "description": "Stream data, don't load all at once"},
        ],
        [
            {"name": "Load all results", "consequence": "Memory exhaustion"},
            {"name": "No pagination", "consequence": "Timeouts on large datasets"},
        ],
        ["execution", "performance", "pagination", "streaming"],
    ),
    create_pattern(
        "type-projection-masking",
        "Type Projection with Auth Masking",
        "Applying authorization rules to mask fields in response",
        "Type projection applies authorization rules to mask fields that the user doesn't have permission to see.",
        "Masking not applied to response fields",
        [
            "Users see fields they shouldn't",
            "Authorization leaks in nested data",
            "Difficult to implement field-level security",
        ],
        {
            "concept_1": "Field auth metadata",
            "concept_2": "Masking logic",
            "concept_3": "Nested field handling",
        },
        {
            "consideration_1": "Null vs error for masked",
            "consideration_2": "Performance of masking",
            "consideration_3": "Error messages",
        },
        [
            {"name": "Apply auth rules", "description": "Check permission for each field"},
            {"name": "Consistent masking", "description": "Always mask the same fields"},
            {"name": "Clear semantics", "description": "Define what happens to masked fields"},
        ],
        [
            {"name": "No masking", "consequence": "Users see restricted data"},
            {"name": "Inconsistent masking", "consequence": "Same field masked differently"},
        ],
        ["execution", "authorization", "security", "projection"],
    ),
    create_pattern(
        "null-handling-projections",
        "Null Handling in Projections",
        "Correctly handling missing or null JSONB fields in response",
        "Projection logic handles null values, missing fields, and type conversions for GraphQL response construction.",
        "Null handling inconsistent or produces invalid responses",
        [
            "Null values in unexpected places",
            "Missing fields not defaulted",
            "Type mismatches with nulls",
        ],
        {
            "concept_1": "Null semantics",
            "concept_2": "Default value handling",
            "concept_3": "Type coercion with nulls",
        },
        {
            "consideration_1": "Non-null field handling",
            "consideration_2": "Nested null propagation",
            "consideration_3": "Client expectations",
        },
        [
            {"name": "Clear null semantics", "description": "Define null behavior per field"},
            {"name": "Test nulls", "description": "Test all null scenarios"},
            {"name": "Type safe", "description": "Ensure type safety with nulls"},
        ],
        [
            {"name": "Loose null handling", "consequence": "Unexpected null values"},
            {"name": "No default values", "consequence": "Missing required fields"},
        ],
        ["execution", "projection", "null-handling", "type-safety"],
    ),
    create_pattern(
        "query-performance-optimization",
        "Query Performance Optimization",
        "Index strategy and query analysis for efficient execution",
        "Query performance is optimized through index strategy, query analysis, and monitoring to identify and fix performance bottlenecks.",
        "Queries run slowly with no way to optimize",
        [
            "Slow query execution",
            "Full table scans",
            "Index misses",
        ],
        {
            "concept_1": "Query analysis",
            "concept_2": "Index strategy",
            "concept_3": "Performance monitoring",
        },
        {
            "consideration_1": "Index size and maintenance",
            "consideration_2": "Query plan analysis",
            "consideration_3": "Benchmark before/after",
        },
        [
            {"name": "Analyze queries", "description": "Use EXPLAIN to analyze plan"},
            {"name": "Create indexes", "description": "Add indexes for common queries"},
            {"name": "Monitor performance", "description": "Track query latencies"},
        ],
        [
            {"name": "No analysis", "consequence": "Slow queries undetected"},
            {"name": "No indexes", "consequence": "Full table scans on large data"},
        ],
        ["execution", "performance", "optimization", "monitoring"],
    ),
    create_pattern(
        "execution-plan-caching",
        "Execution Plan Caching",
        "Reusing pre-computed execution plans across requests",
        "Execution plans compiled at build time are cached and reused across requests, avoiding repeated planning overhead.",
        "Plans recalculated for each request",
        [
            "Repeated planning overhead",
            "Variable execution performance",
            "Wasted CPU on planning",
        ],
        {
            "concept_1": "Plan cache key design",
            "concept_2": "Cache invalidation",
            "concept_3": "Cache hit tracking",
        },
        {
            "consideration_1": "Cache size limits",
            "consideration_2": "Plan age limits",
            "consideration_3": "Cache statistics",
        },
        [
            {"name": "Pre-compile plans", "description": "Generate plans at build time"},
            {"name": "Cache plans", "description": "Store plans for reuse"},
            {"name": "Monitor cache", "description": "Track cache hit rates"},
        ],
        [
            {"name": "Runtime planning", "consequence": "Overhead per request"},
            {"name": "No caching", "consequence": "Repeated planning costs"},
        ],
        ["execution", "performance", "caching", "optimization"],
    ),
    create_pattern(
        "response-formatting",
        "Response Formatting and Serialization",
        "Converting database results to JSON GraphQL responses",
        "Database results are formatted into JSON responses conforming to the GraphQL schema and response structure.",
        "Response format doesn't match schema",
        [
            "Invalid JSON in response",
            "Wrong response structure",
            "Type mismatches",
        ],
        {
            "concept_1": "JSON serialization",
            "concept_2": "Type conversion",
            "concept_3": "Error formatting",
        },
        {
            "consideration_1": "Circular reference handling",
            "consideration_2": "Large object serialization",
            "consideration_3": "Special type handling",
        },
        [
            {"name": "Follow schema", "description": "Serialize according to schema"},
            {"name": "Type safety", "description": "Ensure correct types in response"},
            {"name": "Error structure", "description": "Format errors consistently"},
        ],
        [
            {"name": "Ad-hoc serialization", "consequence": "Inconsistent responses"},
            {"name": "No type checking", "description": "Invalid types in response"},
        ],
        ["execution", "response-formatting", "serialization", "json"],
    ),
    create_pattern(
        "timeout-resource-limits",
        "Query Timeout and Resource Limits",
        "Enforcing execution time and resource consumption limits",
        "Queries have maximum execution time and resource consumption limits to prevent runaway queries from consuming resources.",
        "Long-running queries consume excessive resources",
        [
            "Server exhaustion from long queries",
            "DoS vulnerability from expensive queries",
            "No way to kill stuck queries",
        ],
        {
            "concept_1": "Timeout implementation",
            "concept_2": "Resource tracking",
            "concept_3": "Limit enforcement",
        },
        {
            "consideration_1": "Graceful timeout handling",
            "consideration_2": "Partial result on timeout",
            "consideration_3": "User notification",
        },
        [
            {"name": "Set timeouts", "description": "Define maximum execution time"},
            {"name": "Track resources", "description": "Monitor memory, CPU, I/O"},
            {"name": "Kill when over", "description": "Abort queries exceeding limits"},
        ],
        [
            {"name": "No timeouts", "consequence": "Runaway queries possible"},
            {"name": "No limits", "consequence": "Resource exhaustion"},
        ],
        ["execution", "performance", "reliability", "limits"],
    ),
    create_pattern(
        "cascade-operation-tracking",
        "Cascade Operation Tracking",
        "Following and logging cascade operations through mutations",
        "When mutations cascade to related entities, all affected entities are tracked and logged in the change log.",
        "Cascade operations not tracked",
        [
            "Can't see what data was affected",
            "Difficult to audit mutations",
            "Hard to undo cascades",
        ],
        {
            "concept_1": "Cascade metadata",
            "concept_2": "Affected entity tracking",
            "concept_3": "Cascade logging",
        },
        {
            "consideration_1": "Deep cascade chains",
            "consideration_2": "Performance of tracking",
            "consideration_3": "Log size management",
        },
        [
            {"name": "Track cascades", "description": "Log all affected entities"},
            {"name": "Include context", "description": "Store cascade reason and chain"},
            {"name": "Audit trail", "description": "Maintain complete mutation audit"},
        ],
        [
            {"name": "No cascade tracking", "consequence": "Invisible side effects"},
            {"name": "Partial logging", "consequence": "Incomplete audit trail"},
        ],
        ["execution", "mutations", "audit", "cascades"],
    ),
    create_pattern(
        "request-tracing-execution",
        "Request Tracing Through Execution",
        "Correlation IDs tracking requests through execution pipeline",
        "Requests are assigned correlation IDs that follow them through all execution phases, enabling request tracing and debugging.",
        "Hard to follow request through execution",
        [
            "Can't correlate logs across phases",
            "Difficult to debug request flow",
            "No visibility into request path",
        ],
        {
            "concept_1": "Correlation ID generation",
            "concept_2": "ID propagation",
            "concept_3": "Request lifecycle tracking",
        },
        {
            "consideration_1": "Distributed tracing",
            "consideration_2": "Log aggregation",
            "consideration_3": "ID uniqueness",
        },
        [
            {"name": "Generate IDs", "description": "Create unique ID per request"},
            {"name": "Propagate everywhere", "description": "Include in all logs"},
            {"name": "Aggregate logs", "description": "Collect by correlation ID"},
        ],
        [
            {"name": "No correlation", "consequence": "Logs scattered across files"},
            {"name": "Inconsistent IDs", "consequence": "Tracing doesn't work"},
        ],
        ["execution", "observability", "tracing", "debugging"],
    ),
]

for pattern in execution_patterns:
    save_pattern(pattern)

print(f"✓ Generated {len(execution_patterns)} query execution patterns")

# ============================================================================
# 3. SCHEMA CONVENTIONS PATTERNS (35)
# ============================================================================

schema_patterns = [
    create_pattern(
        "trinity-pattern-fraiseql",
        "Trinity Pattern in FraiseQL",
        "Primary key strategy with pk_*, id UUID, and identifier columns",
        "The Trinity Pattern combines INTEGER primary key (pk_*), UUID public identifier (id), and human-readable identifier (identifier) for flexible entity identification.",
        "Entity identification strategy unclear",
        [
            "No efficient way to identify entities",
            "Missing human-readable identifiers",
            "Confusion between internal and public IDs",
        ],
        {
            "concept_1": "Trinity Pattern structure",
            "concept_2": "Primary key usage",
            "concept_3": "Public ID strategy",
        },
        {
            "consideration_1": "Index strategy for IDs",
            "consideration_2": "UUID vs sequential trade-offs",
            "consideration_3": "Identifier uniqueness constraints",
        },
        [
            {"name": "Follow convention", "description": "Use pk_*, id, identifier pattern"},
            {"name": "Index all IDs", "description": "Create indexes on all ID columns"},
            {"name": "Document purpose", "description": "Explain which ID to use when"},
        ],
        [
            {"name": "Single ID column", "consequence": "Inflexible and problematic"},
            {"name": "Inconsistent naming", "consequence": "Confusion about IDs"},
        ],
        ["schema", "naming", "conventions", "primary-keys", "trinity-pattern"],
    ),
    create_pattern(
        "table-naming-with-prefix",
        "Table Naming with tb_* Prefix",
        "Prefixing storage tables with tb_* for consistency and clarity",
        "All storage tables (normalized data) are prefixed with tb_* to distinguish them from views and make their purpose explicit.",
        "Table and view names ambiguous",
        [
            "Hard to distinguish tables from views",
            "No clear indication of table purpose",
            "Inconsistent naming across schemas",
        ],
        {
            "concept_1": "Naming convention principles",
            "concept_2": "Storage vs presentation separation",
            "concept_3": "Convention enforcement",
        },
        {
            "consideration_1": "Legacy table handling",
            "consideration_2": "Naming consistency",
            "consideration_3": "Documentation of convention",
        },
        [
            {"name": "Apply convention", "description": "Prefix all storage tables with tb_"},
            {"name": "Enforce everywhere", "description": "Ensure all tables follow pattern"},
            {"name": "Document convention", "description": "Clearly explain tb_* pattern"},
        ],
        [
            {"name": "No prefix", "consequence": "Names ambiguous"},
            {"name": "Inconsistent naming", "consequence": "Confusion and mistakes"},
        ],
        ["schema", "naming", "conventions", "tables"],
    ),
    create_pattern(
        "view-naming-convention",
        "View Naming Convention (v_*, tv_*, mv_*, av_*)",
        "Prefixing views with v_*, tv_*, mv_*, av_* to indicate view type",
        "Views are prefixed to indicate their type: v_* for base views, tv_* for table-backed views, mv_* for materialized views, av_* for arrow (columnar) views.",
        "View purpose and type unclear",
        [
            "Hard to understand view semantics",
            "Don't know if view is materialized",
            "Unclear what data view contains",
        ],
        {
            "concept_1": "View type taxonomy",
            "concept_2": "Naming convention mapping",
            "concept_3": "Convention usage",
        },
        {
            "consideration_1": "View performance characteristics",
            "consideration_2": "Materialization strategy",
            "consideration_3": "Column projection",
        },
        [
            {"name": "Use prefixes", "description": "Prefix views with type indicator"},
            {"name": "Be consistent", "description": "Always use same prefix for type"},
            {"name": "Document types", "description": "Explain what each prefix means"},
        ],
        [
            {"name": "No prefixes", "consequence": "View type unclear"},
            {"name": "Inconsistent prefixes", "consequence": "Confusion about view types"},
        ],
        ["schema", "naming", "conventions", "views"],
    ),
    create_pattern(
        "stored-procedure-naming-pattern",
        "Stored Procedure Naming (fn_*)",
        "Prefixing stored procedures with fn_* for mutation actions",
        "Stored procedures implementing mutation actions are prefixed with fn_* to indicate they are functions, not views.",
        "Function vs view distinction unclear",
        [
            "Hard to find mutation logic",
            "Confusion about what's callable",
            "No clear procedure naming",
        ],
        {
            "concept_1": "Procedure naming convention",
            "concept_2": "Action pattern",
            "concept_3": "Procedure discovery",
        },
        {
            "consideration_1": "Naming clarity",
            "consideration_2": "Action verb usage",
            "consideration_3": "Function variants",
        },
        [
            {"name": "Use fn_* prefix", "description": "Prefix mutation procedures with fn_"},
            {"name": "Action verbs", "description": "Use clear action verbs (create, update, delete)"},
            {"name": "Discover easily", "description": "Make procedures easy to find"},
        ],
        [
            {"name": "No prefix", "consequence": "Procedures hard to find"},
            {"name": "Vague names", "consequence": "Unclear what procedures do"},
        ],
        ["schema", "naming", "conventions", "stored-procedures"],
    ),
]

# Continue with more schema patterns...
for pattern in schema_patterns:
    save_pattern(pattern)

print(f"✓ Generated {len(schema_patterns)} schema convention patterns (partial set)")

# ============================================================================
# Generate summary
# ============================================================================

print(f"\n{'='*70}")
print(f"GENERATION SUMMARY")
print(f"{'='*70}")
print(f"\nTotal patterns generated: {len(compilation_patterns) + len(execution_patterns) + len(schema_patterns)}")
print(f"\nPatterns by category:")
print(f"  - Compilation Pipeline: {len(compilation_patterns)}")
print(f"  - Query Execution: {len(execution_patterns)}")
print(f"  - Schema Conventions: {len(schema_patterns)}")
print(f"\nOutput directory: {OUTPUT_DIR}")
print(f"\nFiles created:")

import glob
files = glob.glob(str(OUTPUT_DIR / "*.yaml"))
print(f"  Total YAML files: {len(files)}")
print(f"\nNext steps:")
print(f"  1. Review generated patterns")
print(f"  2. Add more pattern categories (CDC, Auth, etc.)")
print(f"  3. Generate blog posts from patterns")
print(f"  4. Update velocity benchmark catalog")
