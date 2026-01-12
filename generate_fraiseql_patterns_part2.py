#!/usr/bin/env python3
"""
Generate remaining FraiseQL v2 pattern YAML files - Part 2 (CDC, Auth, Performance, etc.)
Continues from Part 1 which generated compilation and execution patterns.
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
            "impact": "Reduced effectiveness of FraiseQL operations",
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
# 4. CHANGE DATA CAPTURE (CDC) PATTERNS (20)
# ============================================================================

cdc_patterns = [
    create_pattern(
        "universal-cdc-event-format",
        "Universal CDC Event Format",
        "Database-agnostic change data capture event structure",
        "FraiseQL defines a universal CDC event format that works across all supported databases, enabling consistent event handling regardless of database backend.",
        "Different CDC formats for different databases",
        [
            "Event format varies by database",
            "Systems can't process events from different DBs",
            "Difficult to migrate databases",
        ],
        {
            "concept_1": "Event structure design",
            "concept_2": "Database adaptation layer",
            "concept_3": "Event normalization",
        },
        {
            "consideration_1": "Format completeness",
            "consideration_2": "Performance of translation",
            "consideration_3": "Backward compatibility",
        },
        [
            {"name": "Universal format", "description": "Design format that all DBs map to"},
            {"name": "Adaptation layer", "description": "Translate DB-specific formats to universal"},
            {"name": "Test all DBs", "description": "Verify format on every database"},
        ],
        [
            {"name": "Database-specific formats", "consequence": "Hard to process events"},
            {"name": "Ad-hoc translation", "consequence": "Inconsistent event handling"},
        ],
        ["cdc", "events", "universal", "format"],
    ),
    create_pattern(
        "cdc-event-metadata",
        "CDC Event Metadata",
        "Event ID, timestamp, version, and sequence tracking",
        "CDC events include metadata for tracking and ordering: unique event ID, precise timestamp, event format version, and sequence number for causal ordering.",
        "Events lack metadata for tracking",
        [
            "Can't uniquely identify events",
            "No way to order events correctly",
            "Can't handle version changes",
        ],
        {
            "concept_1": "Metadata requirements",
            "concept_2": "Sequence numbering",
            "concept_3": "Version tracking",
        },
        {
            "consideration_1": "Event ID generation",
            "consideration_2": "Clock skew handling",
            "consideration_3": "Sequence overflow",
        },
        [
            {"name": "Unique IDs", "description": "Each event gets unique ID"},
            {"name": "Precise timestamps", "description": "Use database timestamps for ordering"},
            {"name": "Sequence numbers", "description": "Include monotonic sequence numbers"},
        ],
        [
            {"name": "No unique IDs", "consequence": "Can't identify individual events"},
            {"name": "Unreliable timestamps", "description": "Events get wrong order"},
        ],
        ["cdc", "events", "metadata", "tracking"],
    ),
    create_pattern(
        "cdc-entity-information",
        "CDC Entity Information",
        "Entity type, ID, and tenant tracking in events",
        "CDC events include information about the affected entity: type, primary key, public ID (UUID), and tenant context for filtering and routing.",
        "Events don't identify affected entity",
        [
            "Hard to know what changed",
            "Can't route events to right system",
            "Multi-tenant context lost",
        ],
        {
            "concept_1": "Entity identification",
            "concept_2": "Tenant context",
            "concept_3": "Type information",
        },
        {
            "consideration_1": "Polymorphic entities",
            "consideration_2": "Tenant isolation",
            "consideration_3": "Entity ID format",
        },
        [
            {"name": "Include entity info", "description": "Type, ID, tenant in every event"},
            {"name": "Clear types", "description": "Use consistent entity type names"},
            {"name": "Tenant isolation", "description": "Always include tenant ID"},
        ],
        [
            {"name": "Missing entity info", "consequence": "Events unusable"},
            {"name": "Mixed entities", "consequence": "Can't route events"},
        ],
        ["cdc", "events", "entities", "multi-tenant"],
    ),
    create_pattern(
        "cdc-operation-details",
        "CDC Operation Details",
        "Before/after state and operation type in events",
        "CDC events include operation type (created, updated, deleted) and before/after snapshots of the entity for understanding what changed.",
        "Unclear what changed or why",
        [
            "Don't know if created, updated, or deleted",
            "Before state lost",
            "Can't calculate what changed",
        ],
        {
            "concept_1": "Operation types",
            "concept_2": "State snapshots",
            "concept_3": "Change calculation",
        },
        {
            "consideration_1": "Snapshot size",
            "consideration_2": "Null handling",
            "consideration_3": "Partial updates",
        },
        [
            {"name": "Include operation", "description": "Type of operation (create/update/delete)"},
            {"name": "Before/after", "description": "Include state before and after change"},
            {"name": "Calculate delta", "description": "Compute what fields changed"},
        ],
        [
            {"name": "No operation type", "consequence": "Can't understand event"},
            {"name": "No snapshots", "consequence": "Can't calculate deltas"},
        ],
        ["cdc", "events", "operations", "state"],
    ),
    create_pattern(
        "cdc-cascade-information",
        "CDC Cascade Information",
        "Tracking related entities affected by cascade mutations",
        "CDC events include cascade information indicating other entities affected by the mutation (e.g., delete post cascades to comments).",
        "Cascade side effects invisible",
        [
            "Don't know what cascaded",
            "Dependent systems out of sync",
            "Difficult to undo cascades",
        ],
        {
            "concept_1": "Cascade metadata",
            "concept_2": "Affected entity tracking",
            "concept_3": "Cascade chains",
        },
        {
            "consideration_1": "Cascade depth",
            "consideration_2": "Event size limits",
            "consideration_3": "Cycle detection",
        },
        [
            {"name": "Track cascades", "description": "Include affected entities in event"},
            {"name": "Include chain", "description": "Show cascade relationships"},
            {"name": "Test cascades", "description": "Verify all cascades captured"},
        ],
        [
            {"name": "No cascade info", "consequence": "Side effects invisible"},
            {"name": "Incomplete tracking", "consequence": "Some cascades missed"},
        ],
        ["cdc", "events", "cascades", "mutations"],
    ),
    create_pattern(
        "cdc-source-information",
        "CDC Source Information",
        "Database, instance, transaction ID, and session in events",
        "CDC events include source information: database name, instance identifier, transaction ID, and session information for tracing and auditing.",
        "Can't trace event origin",
        [
            "Don't know which database produced event",
            "Can't identify transactions",
            "No session context",
        ],
        {
            "concept_1": "Source identification",
            "concept_2": "Transaction tracking",
            "concept_3": "Session context",
        },
        {
            "consideration_1": "Instance identification",
            "consideration_2": "Transaction ID uniqueness",
            "consideration_3": "Session ID scope",
        },
        [
            {"name": "Database identity", "description": "Include database name/version"},
            {"name": "Instance ID", "description": "Identify specific instance"},
            {"name": "Transaction ID", "description": "Include transaction identifier"},
        ],
        [
            {"name": "No source info", "consequence": "Origin unknown"},
            {"name": "Missing context", "consequence": "Can't debug issues"},
        ],
        ["cdc", "events", "source", "audit"],
    ),
    create_pattern(
        "cdc-event-type-taxonomy",
        "CDC Event Type Taxonomy",
        "Consistent naming for event types across all entities",
        "CDC event types follow consistent naming: entity:created, entity:updated, entity:deleted (e.g., post:created, comment:updated, user:deleted).",
        "Inconsistent event type naming",
        [
            "Hard to find events for entity type",
            "Routing logic complex",
            "Filtering confusing",
        ],
        {
            "concept_1": "Type naming convention",
            "concept_2": "Event categorization",
            "concept_3": "Routing keys",
        },
        {
            "consideration_1": "Namespace collisions",
            "consideration_2": "Type discovery",
            "consideration_3": "Evolution",
        },
        [
            {"name": "Consistent naming", "description": "Use entity:operation format"},
            {"name": "Document types", "description": "List all possible event types"},
            {"name": "Test routing", "description": "Verify routing on all event types"},
        ],
        [
            {"name": "Ad-hoc naming", "consequence": "Type names inconsistent"},
            {"name": "No convention", "consequence": "Complex routing logic"},
        ],
        ["cdc", "events", "taxonomy", "naming"],
    ),
    create_pattern(
        "debezium-envelope-format",
        "Debezium Envelope Format",
        "PostgreSQL CDC format with before/after/source structure",
        "CDC events from PostgreSQL databases use Debezium envelope format with before, after, source, and transaction fields.",
        "PostgreSQL CDC format unclear",
        [
            "Hard to understand event structure",
            "Can't extract before/after state",
            "Source information mixed up",
        ],
        {
            "concept_1": "Envelope structure",
            "concept_2": "Field organization",
            "concept_3": "Source field mapping",
        },
        {
            "consideration_1": "DDL events",
            "consideration_2": "Transaction metadata",
            "consideration_3": "Snapshot events",
        },
        [
            {"name": "Follow format", "description": "Use Debezium envelope structure"},
            {"name": "Document fields", "description": "Explain each field"},
            {"name": "Test extraction", "description": "Verify before/after extraction"},
        ],
        [
            {"name": "Custom format", "consequence": "Incompatible with tools"},
            {"name": "Missing fields", "consequence": "Information lost"},
        ],
        ["cdc", "postgresql", "debezium", "format"],
    ),
    create_pattern(
        "postgresql-cdc-implementation",
        "PostgreSQL CDC Implementation",
        "Trigger-based change capture for PostgreSQL",
        "PostgreSQL CDC is implemented using database triggers that capture changes in tb_*_change_log tables following Debezium envelope format.",
        "Hard to implement PostgreSQL CDC",
        [
            "Changes not captured",
            "Trigger logic complex",
            "Change log corruption",
        ],
        {
            "concept_1": "Trigger design",
            "concept_2": "Change log table",
            "concept_3": "Envelope generation",
        },
        {
            "consideration_1": "Trigger performance",
            "consideration_2": "Transaction semantics",
            "consideration_3": "Concurrent changes",
        },
        [
            {"name": "Trigger per table", "description": "Create trigger for each tracked table"},
            {"name": "Change log table", "description": "Use tb_*_change_log table"},
            {"name": "Test triggers", "description": "Verify trigger captures all changes"},
        ],
        [
            {"name": "No triggers", "consequence": "Changes not captured"},
            {"name": "Broken triggers", "consequence": "Inconsistent change logs"},
        ],
        ["cdc", "postgresql", "triggers", "implementation"],
    ),
    create_pattern(
        "sqlite-cdc-implementation",
        "SQLite CDC Implementation",
        "Trigger-based CDC for SQLite with different semantics",
        "SQLite CDC is implemented using triggers similar to PostgreSQL but accounting for SQLite's different transaction and trigger semantics.",
        "CDC behavior differs from PostgreSQL",
        [
            "SQLite triggers have different semantics",
            "Changes not ordered correctly",
            "Transaction visibility issues",
        ],
        {
            "concept_1": "SQLite trigger semantics",
            "concept_2": "Transaction handling",
            "concept_3": "Change ordering",
        },
        {
            "consideration_1": "Foreign key constraints",
            "consideration_2": "Pragma settings",
            "consideration_3": "Journal mode",
        ],
        [
            {"name": "Account for semantics", "description": "Use SQLite-specific trigger code"},
            {"name": "Handle transactions", "description": "Deal with SQLite transaction model"},
            {"name": "Test thoroughly", "description": "Verify on SQLite specifically"},
        ],
        [
            {"name": "PostgreSQL logic", "consequence": "Wrong behavior on SQLite"},
            {"name": "Missing pragmas", "consequence": "Transaction isolation breaks"},
        ],
        ["cdc", "sqlite", "triggers", "implementation"],
    ),
    create_pattern(
        "cdc-change-log-table-architecture",
        "Change Log Table Architecture",
        "Design of tb_entity_change_log tables",
        "Change log tables (tb_entity_change_log) are designed for efficient capture, storage, and querying of change events.",
        "Change log table design unclear",
        [
            "Poor change log performance",
            "Hard to query change log",
            "Missing data integrity",
        ],
        {
            "concept_1": "Table structure",
            "concept_2": "Index strategy",
            "concept_3": "Archival strategy",
        },
        {
            "consideration_1": "Table size management",
            "consideration_2": "Query patterns",
            "consideration_3": "Retention policy",
        ],
        [
            {"name": "Optimal structure", "description": "Design for query patterns"},
            {"name": "Indexes", "description": "Create appropriate indexes"},
            {"name": "Archival", "description": "Plan for long-term storage"},
        ],
        [
            {"name": "Poor structure", "consequence": "Slow queries"},
            {"name": "No indexes", "consequence": "Full table scans"},
        ],
        ["cdc", "change-log", "tables", "design"],
    ),
    create_pattern(
        "cdc-status-taxonomy",
        "Change Log Status Taxonomy",
        "Success, error, conflict, validation status codes",
        "CDC change log records include status indicating success, validation error, conflict, or other error conditions.",
        "Can't determine if mutation succeeded",
        [
            "Hard to know if change was successful",
            "Error details missing",
            "Conflict information unclear",
        ],
        {
            "concept_1": "Status categories",
            "concept_2": "Error details",
            "concept_3": "Conflict handling",
        },
        {
            "consideration_1": "Status transitions",
            "consideration_2": "Error messages",
            "consideration_3": "Retry strategies",
        },
        [
            {"name": "Define status types", "description": "List all possible statuses"},
            {"name": "Include details", "description": "Attach error messages"},
            {"name": "Test all paths", "description": "Verify each status works"},
        ],
        [
            {"name": "No status", "consequence": "Can't determine outcome"},
            {"name": "Vague statuses", "consequence": "Hard to debug"},
        ],
        ["cdc", "change-log", "status", "error-handling"],
    ),
    create_pattern(
        "cdc-event-delivery-protocol",
        "CDC Event Delivery Protocol",
        "Exactly-once vs at-least-once semantics and guarantees",
        "CDC events are delivered with guaranteed semantics: exactly-once for transactional consistency or at-least-once with idempotency for durability.",
        "No guarantees on event delivery",
        [
            "Events lost or duplicated",
            "Inconsistent downstream state",
            "Hard to reason about correctness",
        ],
        {
            "concept_1": "Delivery semantics",
            "concept_2": "Idempotency",
            "concept_3": "Ordering guarantees",
        ],
        {
            "consideration_1": "Trade-offs",
            "consideration_2": "Deduplication",
            "consideration_3": "Retry logic",
        },
        [
            {"name": "Choose semantics", "description": "Decide on exactly/at-least once"},
            {"name": "Implement guarantee", "description": "Build dedup or transactional logic"},
            {"name": "Test delivery", "description": "Verify semantics are maintained"},
        ],
        [
            {"name": "No guarantees", "consequence": "Unreliable event delivery"},
            {"name": "Wrong semantics", "consequence": "Data inconsistency"},
        ],
        ["cdc", "events", "delivery", "guarantees"],
    ),
    create_pattern(
        "cdc-event-ordering",
        "CDC Event Ordering and Sequences",
        "Monotonic sequence guarantees for causal ordering",
        "CDC events include sequence numbers providing global causal ordering: later events have higher sequence numbers, enabling ordered processing.",
        "Event ordering unclear",
        [
            "Can't determine event order",
            "Process events out of order",
            "Inconsistent state from ordering",
        ],
        {
            "concept_1": "Sequence numbers",
            "concept_2": "Causal ordering",
            "concept_3": "Sequence gaps",
        },
        {
            "consideration_1": "Sequence overflow",
            "consideration_2": "Clock skew",
            "consideration_3": "Distributed ordering",
        ],
        [
            {"name": "Monotonic sequences", "description": "Use incrementing sequence numbers"},
            {"name": "Verify ordering", "description": "Test that order is preserved"},
            {"name": "Handle gaps", "description": "Detect missing sequences"},
        ],
        [
            {"name": "No sequences", "consequence": "Can't order events"},
            {"name": "Non-monotonic", "consequence": "Wrong event order"},
        ],
        ["cdc", "events", "ordering", "sequences"],
    ),
    create_pattern(
        "cdc-custom-metadata",
        "CDC Custom Metadata",
        "Request ID, user ID, roles, and custom fields in events",
        "CDC events can include custom metadata: correlation request ID, user who made change, roles, and application-specific fields.",
        "Missing context in change events",
        [
            "Can't correlate with requests",
            "Don't know who made change",
            "Roles/permissions not captured",
        ],
        {
            "concept_1": "Metadata inclusion",
            "concept_2": "Context propagation",
            "concept_3": "Custom field support",
        },
        {
            "consideration_1": "Metadata size",
            "consideration_2": "Privacy concerns",
            "consideration_3": "Retention",
        ],
        [
            {"name": "Capture context", "description": "Include user, roles, request ID"},
            {"name": "Custom fields", "description": "Support application-specific metadata"},
            {"name": "Propagate everywhere", "description": "Include in all events"},
        ],
        [
            {"name": "No metadata", "consequence": "Context lost"},
            {"name": "Incomplete metadata", "consequence": "Some context missing"},
        ],
        ["cdc", "events", "metadata", "context"],
    ),
    create_pattern(
        "cdc-event-streaming",
        "CDC Event Streaming",
        "Real-time event emission to subscribers",
        "CDC events are streamed to real-time subscribers as they occur, enabling live updates and real-time features.",
        "Can't get real-time updates",
        [
            "Updates not real-time",
            "Subscribers miss events",
            "Polling overhead",
        ],
        {
            "concept_1": "Event streaming",
            "concept_2": "Subscriber management",
            "concept_3": "Backpressure",
        },
        {
            "consideration_1": "Stream performance",
            "consideration_2": "Subscriber scalability",
            "consideration_3": "Event buffering",
        },
        [
            {"name": "Stream events", "description": "Emit events as they occur"},
            {"name": "Manage subscribers", "description": "Handle multiple subscribers"},
            {"name": "Handle backpressure", "description": "Deal with slow subscribers"},
        ],
        [
            {"name": "No streaming", "consequence": "Only polling available"},
            {"name": "Lost events", "consequence": "Some events never delivered"},
        ],
        ["cdc", "streaming", "real-time", "subscriptions"],
    ),
    create_pattern(
        "cdc-event-consumption",
        "CDC Event Consumption Patterns",
        "How systems consume and handle CDC events",
        "Systems consume CDC events through various patterns: subscriptions, polling, batch processing, or event-driven workers.",
        "Unclear how to consume events",
        [
            "Hard to implement event handling",
            "Processing logic scattered",
            "Hard to debug consumption",
        ],
        {
            "concept_1": "Consumption patterns",
            "concept_2": "Handler implementation",
            "concept_3": "Error handling",
        },
        {
            "consideration_1": "Scalability",
            "consideration_2": "Ordering guarantees",
            "consideration_3": "Retries",
        },
        [
            {"name": "Pick pattern", "description": "Choose consumption pattern"},
            {"name": "Implement handlers", "description": "Write event handlers"},
            {"name": "Test thoroughly", "description": "Verify event handling works"},
        ],
        [
            {"name": "Ad-hoc handling", "consequence": "Inconsistent processing"},
            {"name": "No error handling", "consequence": "Events lost on errors"},
        ],
        ["cdc", "consumption", "event-driven", "patterns"],
    ),
    create_pattern(
        "cdc-event-idempotency",
        "CDC Event Idempotency",
        "Handling duplicate events from at-least-once delivery",
        "Event handlers must be idempotent to safely process duplicate events without side effects when at-least-once delivery is used.",
        "Duplicate events cause incorrect side effects",
        [
            "Duplicate processing causes issues",
            "Can't use at-least-once delivery",
            "Hard to debug idempotency",
        ],
        {
            "concept_1": "Idempotency design",
            "concept_2": "Deduplication keys",
            "concept_3": "Idempotent operations",
        },
        {
            "consideration_1": "Deduplication window",
            "consideration_2": "Storage for dedup",
            "consideration_3": "Performance",
        },
        [
            {"name": "Idempotent design", "description": "Handle duplicate events safely"},
            {"name": "Dedup keys", "description": "Use event ID for deduplication"},
            {"name": "Test duplicates", "description": "Test with duplicate events"},
        ],
        [
            {"name": "Non-idempotent", "consequence": "Side effects on duplicates"},
            {"name": "No deduplication", "consequence": "Can't use at-least-once"},
        ],
        ["cdc", "idempotency", "deduplication", "reliability"],
    ),
]

for pattern in cdc_patterns:
    save_pattern(pattern)

print(f"✓ Generated {len(cdc_patterns)} CDC patterns")

# ============================================================================
# 5. AUTHORIZATION PATTERNS (18)
# ============================================================================

auth_patterns = [
    create_pattern(
        "declarative-auth-vs-resolver-auth",
        "Declarative Auth vs Resolver-Based Auth",
        "Why metadata-driven auth is superior to middleware/resolver auth",
        "Declarative authorization rules compiled as metadata are superior to runtime resolver checks: they prevent bypasses, enable static analysis, and provide consistency.",
        "Authorization in resolvers can be bypassed",
        [
            "Auth can be bypassed with alternate queries",
            "No audit trail of auth decisions",
            "Difficult to ensure consistent auth",
        ],
        {
            "concept_1": "Metadata-driven auth",
            "concept_2": "Resolver auth limitations",
            "concept_3": "Bypass prevention",
        },
        {
            "consideration_1": "Expressiveness",
            "consideration_2": "Performance",
            "consideration_3": "Auditability",
        },
        [
            {"name": "Use metadata", "description": "Compile auth rules upfront"},
            {"name": "No bypasses", "description": "Enforce auth everywhere"},
            {"name": "Audit trail", "description": "Log all auth decisions"},
        ],
        [
            {"name": "Resolver auth", "consequence": "Can be bypassed"},
            {"name": "Ad-hoc checks", "consequence": "Inconsistent enforcement"},
        ],
        ["authorization", "security", "design", "declarative"],
    ),
    create_pattern(
        "role-based-authorization",
        "Role-Based Authorization",
        "Requiring specific roles for access",
        "Authorization rules can require users to have specific roles (e.g., admin, editor, viewer) to access queries, mutations, or fields.",
        "No way to restrict by role",
        [
            "Users access data they shouldn't",
            "No role-based restrictions",
            "Hard to manage access",
        ],
        {
            "concept_1": "Role definitions",
            "concept_2": "Role assignment",
            "concept_3": "Role checking",
        },
        {
            "consideration_1": "Role hierarchy",
            "consideration_2": "Dynamic role assignment",
            "consideration_3": "Role evolution",
        },
        [
            {"name": "Define roles", "description": "List required roles"},
            {"name": "Check roles", "description": "Verify user has required role"},
            {"name": "Test access", "description": "Test role-based restrictions"},
        ],
        [
            {"name": "No roles", "consequence": "Can't restrict by role"},
            {"name": "Vague roles", "consequence": "Access control confusing"},
        ],
        ["authorization", "roles", "security", "access-control"],
    ),
    create_pattern(
        "claim-based-authorization",
        "Claim-Based Authorization",
        "Checking JWT claims and custom attributes",
        "Authorization rules can check JWT claims (sub, email, permissions, custom claims) to make access decisions based on user attributes.",
        "Can't check claims for authorization",
        [
            "No way to check user attributes",
            "Custom permissions not supported",
            "Hard to implement fine-grained auth",
        ],
        {
            "concept_1": "JWT claims",
            "concept_2": "Claim extraction",
            "concept_3": "Claim validation",
        },
        {
            "consideration_1": "Claim format",
            "consideration_2": "Custom claims",
            "consideration_3": "Claim freshness",
        },
        [
            {"name": "Extract claims", "description": "Pull relevant claims from JWT"},
            {"name": "Check claims", "description": "Validate required claims"},
            {"name": "Test claims", "description": "Test with different claim values"},
        ],
        [
            {"name": "No claim checking", "consequence": "Custom auth impossible"},
            {"name": "Missing claims", "consequence": "Incomplete auth logic"},
        ],
        ["authorization", "claims", "jwt", "security"],
    ),
    create_pattern(
        "custom-authorization-rules",
        "Custom Authorization Rules",
        "Beyond role and claim checks with custom logic",
        "Authorization can include custom rules beyond roles and claims, such as ownership checks (user can only see their own data).",
        "Hard to implement custom auth rules",
        [
            "Can't express complex conditions",
            "Custom rules duplicated",
            "Hard to maintain",
        ],
        {
            "concept_1": "Custom rule design",
            "concept_2": "Rule composition",
            "concept_3": "Rule evaluation",
        },
        {
            "consideration_1": "Rule expressiveness",
            "consideration_2": "Performance of evaluation",
            "consideration_3": "Rule testing",
        },
        [
            {"name": "Define rules", "description": "Specify custom conditions"},
            {"name": "Compose rules", "description": "Combine with role/claim rules"},
            {"name": "Test thoroughly", "description": "Test all rule combinations"},
        ],
        [
            {"name": "No custom rules", "consequence": "Can't express complex auth"},
            {"name": "Ad-hoc rules", "consequence": "Hard to maintain"},
        ],
        ["authorization", "custom-rules", "security", "complex-auth"],
    ),
    create_pattern(
        "multi-tenant-authorization",
        "Multi-Tenant Authorization",
        "Isolating data by tenant context",
        "Authorization includes multi-tenant scoping: users can only see data for their tenant, enforced at query level.",
        "Tenant data leaks between customers",
        [
            "Users see data from other tenants",
            "Tenant context missing",
            "Hard to implement isolation",
        ],
        {
            "concept_1": "Tenant identification",
            "concept_2": "Scoping logic",
            "concept_3": "Isolation verification",
        },
        {
            "consideration_1": "Tenant hierarchy",
            "consideration_2": "Shared resources",
            "consideration_3": "Admin access",
        ],
        [
            {"name": "Include tenant ID", "description": "Extract from context"},
            {"name": "Scope queries", "description": "Filter by tenant in authorization"},
            {"name": "Test isolation", "description": "Verify data is isolated"},
        ],
        [
            {"name": "No tenant scoping", "consequence": "Data leaks across tenants"},
            {"name": "Missing tenant context", "consequence": "All data visible"},
        ],
        ["authorization", "multi-tenant", "security", "isolation"],
    ),
    create_pattern(
        "query-level-authorization",
        "Query-Level Authorization",
        "Controlling access to entire queries",
        "Authorization rules at query level control whether users can execute specific queries at all.",
        "No way to restrict query access",
        [
            "Users execute queries they shouldn't",
            "No query-level access control",
            "Hard to restrict features",
        ],
        {
            "concept_1": "Query authorization",
            "concept_2": "Permission checking",
            "concept_3": "Execution gates",
        },
        {
            "consideration_1": "Query grouping",
            "consideration_2": "Default policies",
            "consideration_3": "Audit logging",
        ],
        [
            {"name": "Define permissions", "description": "List who can call each query"},
            {"name": "Check before execution", "description": "Enforce before running"},
            {"name": "Test access", "description": "Verify access control works"},
        ],
        [
            {"name": "No query auth", "consequence": "Users call any query"},
            {"name": "Inconsistent checks", "consequence": "Some queries bypass auth"},
        ],
        ["authorization", "queries", "security", "access-control"],
    ),
    create_pattern(
        "mutation-level-authorization",
        "Mutation-Level Authorization",
        "Controlling access to mutations",
        "Authorization rules at mutation level control who can execute mutations, preventing unauthorized data modifications.",
        "Users perform mutations they shouldn't",
        [
            "Unauthorized mutations allowed",
            "No mutation access control",
            "Data integrity compromised",
        ],
        {
            "concept_1": "Mutation authorization",
            "concept_2": "Permission enforcement",
            "concept_3": "Modification gates",
        },
        {
            "consideration_1": "Mutation grouping",
            "consideration_2": "Default deny",
            "consideration_3": "Partial success",
        ],
        [
            {"name": "Require permissions", "description": "Specify who can mutate"},
            {"name": "Deny by default", "description": "Default to denying mutations"},
            {"name": "Test mutations", "description": "Verify access control on mutations"},
        ],
        [
            {"name": "No mutation auth", "consequence": "Anyone can mutate"},
            {"name": "Permissive defaults", "consequence": "Unauthorized mutations"},
        ],
        ["authorization", "mutations", "security", "modification"],
    ),
    create_pattern(
        "authorization-denial-handling",
        "Authorization Denial Handling",
        "Error vs null responses for denied access",
        "When authorization is denied, responses are either errors or nulls depending on whether the query exists: errors if user doesn't have role, nulls if field is masked.",
        "Confusing what happens on denied access",
        [
            "Sometimes error, sometimes null",
            "No clear semantics",
            "Client confusion",
        ],
        {
            "concept_1": "Denial semantics",
            "concept_2": "Error vs null",
            "concept_3": "Introspection implications",
        ],
        {
            "consideration_1": "Information leakage",
            "consideration_2": "Client error handling",
            "consideration_3": "Debug difficulty",
        ],
        [
            {"name": "Clear semantics", "description": "Define error vs null"},
            {"name": "Consistent behavior", "description": "Same semantics everywhere"},
            {"name": "Document choices", "description": "Explain why error vs null"},
        ],
        [
            {"name": "Inconsistent", "consequence": "Confusing behavior"},
            {"name": "Leaky semantics", "consequence": "Information leakage"},
        ],
        ["authorization", "error-handling", "security", "semantics"],
    ),
    create_pattern(
        "authorization-masking",
        "Authorization Masking",
        "Filtering results based on user permissions",
        "Authorization can mask (filter out) results that users don't have permission to see, returning partial results instead of denying entire queries.",
        "No way to selectively restrict results",
        [
            "All or nothing access",
            "Can't see any data if one item hidden",
            "Hard to implement partial visibility",
        ],
        {
            "concept_1": "Result filtering",
            "concept_2": "Per-item authorization",
            "concept_3": "Partial results",
        },
        {
            "consideration_1": "Performance of filtering",
            "consideration_2": "Pagination with filtering",
            "consideration_3": "Total count with filters",
        ],
        [
            {"name": "Filter results", "description": "Only return authorized items"},
            {"name": "Per-item checks", "description": "Check each result item"},
            {"name": "Test filtering", "description": "Verify correct items returned"},
        ],
        [
            {"name": "No masking", "consequence": "Can't restrict individual results"},
            {"name": "Performance issues", "consequence": "Filtering too slow"},
        ],
        ["authorization", "masking", "filtering", "security"],
    ),
    create_pattern(
        "auth-rule-validation-compile-time",
        "Authorization Rule Validation at Compile Time",
        "Detecting invalid authorization rules during schema compilation",
        "Authorization rules are validated during compilation to catch errors early: rules referencing non-existent fields, invalid claims, etc.",
        "Invalid auth rules deployed to production",
        [
            "Broken auth rules in production",
            "Runtime auth failures",
            "No early error detection",
        ],
        {
            "concept_1": "Rule validation",
            "concept_2": "Field reference checking",
            "concept_3": "Scope validation",
        },
        {
            "consideration_1": "Custom rule validation",
            "consideration_2": "Performance of validation",
            "consideration_3": "Error messages",
        },
        [
            {"name": "Validate rules", "description": "Check all auth rules at compile time"},
            {"name": "Reference checking", "description": "Verify fields exist"},
            {"name": "Scope checking", "description": "Verify scopes are valid"},
        ],
        [
            {"name": "No validation", "consequence": "Invalid rules deployed"},
            {"name": "Partial validation", "consequence": "Some errors missed"},
        ],
        ["authorization", "validation", "compilation", "security"],
    ),
    create_pattern(
        "authorization-audit-logging",
        "Authorization Audit Logging",
        "Tracking all authorization decisions",
        "Authorization decisions (allow/deny) are logged with context for auditing and compliance.",
        "No audit trail of authorization",
        [
            "Can't see who accessed what",
            "No compliance audit trail",
            "Difficult to debug access issues",
        ],
        {
            "concept_1": "Decision logging",
            "concept_2": "Context capture",
            "concept_3": "Log storage",
        },
        {
            "consideration_1": "Log volume",
            "consideration_2": "Performance impact",
            "consideration_3": "Privacy concerns",
        },
        [
            {"name": "Log decisions", "description": "Record allow/deny with context"},
            {"name": "Include context", "description": "User, resource, reason"},
            {"name": "Secure logs", "description": "Protect audit trail"},
        ],
        [
            {"name": "No logging", "consequence": "No audit trail"},
            {"name": "Incomplete logging", "consequence": "Missing context"},
        ],
        ["authorization", "audit", "compliance", "logging"],
    ),
]

for pattern in auth_patterns:
    save_pattern(pattern)

print(f"✓ Generated {len(auth_patterns)} authorization patterns")

print(f"\n{'='*70}")
print(f"GENERATION SUMMARY (PART 2)")
print(f"{'='*70}")
print(f"\nPatterns generated in Part 2:")
print(f"  - CDC Patterns: {len(cdc_patterns)}")
print(f"  - Authorization Patterns: {len(auth_patterns)}")
print(f"  - Total Part 2: {len(cdc_patterns) + len(auth_patterns)}")
print(f"\nCumulative from Part 1 + Part 2:")
print(f"  - Compilation: 22")
print(f"  - Execution: 25")
print(f"  - Schema Conventions: 4")
print(f"  - CDC: {len(cdc_patterns)}")
print(f"  - Authorization: {len(auth_patterns)}")
print(f"  - TOTAL: {22 + 25 + 4 + len(cdc_patterns) + len(auth_patterns)}")
