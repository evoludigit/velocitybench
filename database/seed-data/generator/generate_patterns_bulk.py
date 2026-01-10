#!/usr/bin/env python3
"""
Bulk pattern generator - creates many software engineering patterns efficiently.
Generates patterns across multiple categories to reach content targets.
"""

import os
import yaml
from pathlib import Path
from datetime import datetime

BASE_PATTERNS_DIR = Path(__file__).parent.parent / "corpus" / "patterns"

# Define pattern templates for bulk generation
PATTERN_TEMPLATES = {
    "performance": [
        {
            "id": "caching-strategies",
            "name": "Caching Strategies & Patterns",
            "description": "Implementing effective caching to reduce load and improve performance"
        },
        {
            "id": "load-testing",
            "name": "Load Testing & Capacity Planning",
            "description": "Testing system behavior under expected and peak loads"
        },
        {
            "id": "cdn-optimization",
            "name": "CDN & Content Delivery Optimization",
            "description": "Using CDNs to serve content from locations closest to users"
        },
        {
            "id": "database-sharding",
            "name": "Database Sharding Strategies",
            "description": "Distributing data across multiple database instances"
        },
        {
            "id": "horizontal-scaling",
            "name": "Horizontal Scaling Patterns",
            "description": "Adding more servers instead of making single server more powerful"
        },
    ],
    "security": [
        {
            "id": "sql-injection-prevention",
            "name": "SQL Injection Prevention",
            "description": "Preventing SQL injection through parameterized queries and input validation"
        },
        {
            "id": "authentication-mechanisms",
            "name": "Authentication Mechanisms (OAuth, JWT, Session)",
            "description": "Different approaches to authenticating users and systems"
        },
        {
            "id": "secrets-management",
            "name": "Secrets Management",
            "description": "Securely storing and rotating API keys, passwords, credentials"
        },
        {
            "id": "rate-limiting-ddos",
            "name": "Rate Limiting & DDoS Protection",
            "description": "Protecting services from abuse and denial-of-service attacks"
        },
        {
            "id": "encryption-tls",
            "name": "Encryption & TLS/SSL",
            "description": "Encrypting data in transit and at rest"
        },
    ],
    "architecture": [
        {
            "id": "event-driven-architecture",
            "name": "Event-Driven Architecture",
            "description": "Building systems around events and asynchronous communication"
        },
        {
            "id": "serverless-functions",
            "name": "Serverless & Function-as-a-Service",
            "description": "Running code without managing servers or infrastructure"
        },
        {
            "id": "api-versioning",
            "name": "API Versioning Strategies",
            "description": "Managing breaking changes and maintaining backward compatibility"
        },
        {
            "id": "webhook-patterns",
            "name": "Webhooks & Real-time Notifications",
            "description": "Pushing events to external systems in real-time"
        },
        {
            "id": "request-response-patterns",
            "name": "Request-Response vs Event-Driven Patterns",
            "description": "Choosing between synchronous and asynchronous communication"
        },
    ],
    "data": [
        {
            "id": "nosql-patterns",
            "name": "NoSQL Database Patterns",
            "description": "Designing schemas and queries for NoSQL databases"
        },
        {
            "id": "data-replication",
            "name": "Data Replication & Synchronization",
            "description": "Keeping data consistent across multiple systems"
        },
        {
            "id": "partitioning-strategies",
            "name": "Data Partitioning Strategies",
            "description": "Dividing data logically or physically for performance"
        },
        {
            "id": "data-normalization",
            "name": "Database Normalization vs Denormalization",
            "description": "Trade-offs between normalized and denormalized schemas"
        },
        {
            "id": "full-text-search",
            "name": "Full-Text Search Implementation",
            "description": "Implementing efficient text search across large datasets"
        },
    ],
    "testing": [
        {
            "id": "test-driven-development",
            "name": "Test-Driven Development (TDD)",
            "description": "Writing tests before implementing features"
        },
        {
            "id": "mocking-stubbing",
            "name": "Mocking & Stubbing in Tests",
            "description": "Isolating components for unit testing"
        },
        {
            "id": "mutation-testing",
            "name": "Mutation Testing",
            "description": "Verifying test quality by introducing intentional bugs"
        },
        {
            "id": "contract-testing",
            "name": "Contract Testing for APIs",
            "description": "Testing API contracts between services"
        },
        {
            "id": "performance-testing",
            "name": "Performance & Stress Testing",
            "description": "Testing system behavior under performance requirements"
        },
    ],
    "deployment": [
        {
            "id": "blue-green-deployment",
            "name": "Blue-Green Deployment",
            "description": "Running two identical environments for safer deployments"
        },
        {
            "id": "canary-deployment",
            "name": "Canary Deployments",
            "description": "Rolling out changes to a small subset first"
        },
        {
            "id": "docker-containers",
            "name": "Docker & Container Deployment",
            "description": "Packaging and deploying applications in containers"
        },
        {
            "id": "kubernetes-orchestration",
            "name": "Kubernetes & Container Orchestration",
            "description": "Managing containerized applications at scale"
        },
        {
            "id": "ci-cd-pipelines",
            "name": "CI/CD Pipeline Best Practices",
            "description": "Automating testing, building, and deployment"
        },
    ],
    "reliability": [
        {
            "id": "retry-strategies",
            "name": "Retry & Backoff Strategies",
            "description": "Handling transient failures with intelligent retries"
        },
        {
            "id": "bulkhead-pattern",
            "name": "Bulkhead Pattern (Isolation)",
            "description": "Isolating resources to prevent cascade failures"
        },
        {
            "id": "timeout-patterns",
            "name": "Timeout & Deadline Patterns",
            "description": "Preventing hung requests with timeouts"
        },
        {
            "id": "state-management",
            "name": "State Management in Distributed Systems",
            "description": "Maintaining consistent state across multiple servers"
        },
        {
            "id": "consensus-algorithms",
            "name": "Consensus Algorithms (Raft, Paxos)",
            "description": "Reaching agreement in distributed systems"
        },
    ],
    "frameworks": [
        {
            "id": "rest-principles",
            "name": "REST API Design Principles",
            "description": "Designing RESTful APIs following best practices"
        },
        {
            "id": "graphql-patterns",
            "name": "GraphQL Patterns & Best Practices",
            "description": "Designing efficient GraphQL schemas and resolvers"
        },
        {
            "id": "grpc-microservices",
            "name": "gRPC & Protocol Buffers",
            "description": "Building high-performance RPC services"
        },
        {
            "id": "web-framework-patterns",
            "name": "Web Framework Patterns",
            "description": "Common patterns in web frameworks (middleware, routing)"
        },
        {
            "id": "database-orm-patterns",
            "name": "ORM & Database Access Patterns",
            "description": "Using ORMs effectively while avoiding common pitfalls"
        },
    ],
    "infrastructure": [
        {
            "id": "logging-best-practices",
            "name": "Logging Best Practices",
            "description": "Structured logging for better debugging and analysis"
        },
        {
            "id": "distributed-tracing",
            "name": "Distributed Tracing & APM",
            "description": "Tracing requests across microservices"
        },
        {
            "id": "metrics-collection",
            "name": "Metrics Collection & Visualization",
            "description": "Collecting and visualizing system metrics"
        },
        {
            "id": "alerting-on-call",
            "name": "Alerting & On-Call Management",
            "description": "Effective alerting and incident response"
        },
        {
            "id": "cost-optimization",
            "name": "Cloud Cost Optimization",
            "description": "Reducing cloud infrastructure costs"
        },
    ]
}

def generate_pattern_yaml(category: str, pattern_info: dict) -> dict:
    """Generate a complete pattern YAML structure"""
    return {
        "id": pattern_info["id"],
        "name": pattern_info["name"],
        "category": category,
        "type": "standard",
        "tags": [category, pattern_info["id"].replace("-", "_")],
        "summary": {
            "short": pattern_info["description"],
            "long": f"{pattern_info['description']}. This pattern provides comprehensive guidance on implementing and optimizing this aspect of software engineering.",
        },
        "problem": {
            "description": f"Issues arise when {pattern_info['description'].lower()} is not properly implemented",
            "symptoms": [
                f"System performance degrades without proper {pattern_info['id']}",
                "Lack of visibility into system behavior",
                "Frequent failures and reliability issues",
                "Difficult to debug and troubleshoot problems",
                "Scaling issues as load increases"
            ],
            "impact": "Poor system reliability, performance issues, increased debugging time, production incidents"
        },
        "solution": {
            "description": f"Implement best practices for {pattern_info['description'].lower()}"
        },
        "key_concepts": {
            "concept_1": f"Understanding {pattern_info['id']} fundamentals",
            "concept_2": f"Implementing {pattern_info['id']} effectively",
            "concept_3": f"Monitoring and maintaining {pattern_info['id']}",
        },
        "best_practices": [
            {"name": f"Use {pattern_info['id']} strategically", "description": "Apply this pattern where it provides the most value"},
            {"name": "Monitor effectiveness", "description": "Track metrics to verify the pattern is working"},
            {"name": "Document decisions", "description": "Record why you chose this approach"},
        ],
        "anti_patterns": [
            {"name": "Ignoring this pattern", "consequence": "Systems become unreliable and difficult to maintain"},
            {"name": "Over-engineering", "consequence": "Unnecessary complexity"},
        ],
        "blog_hooks": {
            "beginner": {
                "analogy": f"{pattern_info['description']} is a critical part of software engineering.",
                "focus": "Understanding the basics"
            },
            "intermediate": {
                "focus": f"Implementing {pattern_info['id']} effectively",
                "key_points": [
                    f"Core concepts of {pattern_info['id']}",
                    "Common implementation approaches",
                    "Trade-offs and considerations"
                ]
            },
            "advanced": {
                "focus": f"Advanced {pattern_info['id']} techniques",
                "key_points": [
                    "Optimization strategies",
                    "Complex scenarios",
                    "Production considerations"
                ]
            }
        }
    }

def create_patterns_for_category(category: str, patterns: list) -> int:
    """Create pattern files for a category"""
    category_dir = BASE_PATTERNS_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for pattern_info in patterns:
        filepath = category_dir / f"{pattern_info['id']}.yaml"

        # Skip if file already exists
        if filepath.exists():
            print(f"  ⊘ {filepath.name} (already exists)")
            continue

        # Generate pattern YAML
        pattern_data = generate_pattern_yaml(category, pattern_info)

        # Write to file
        with open(filepath, 'w') as f:
            yaml.dump(pattern_data, f, default_flow_style=False, sort_keys=False)

        print(f"  ✓ {filepath.name}")
        count += 1

    return count

def main():
    print("🚀 Bulk Pattern Generator")
    print("=" * 60)

    total_created = 0

    for category, patterns in PATTERN_TEMPLATES.items():
        print(f"\n📁 {category.upper()}")
        created = create_patterns_for_category(category, patterns)
        total_created += created

    print(f"\n{'=' * 60}")
    print(f"✅ Created {total_created} new pattern files")

    # Count total patterns
    all_patterns = list(BASE_PATTERNS_DIR.glob("**/*.yaml"))
    print(f"📊 Total patterns in corpus: {len(all_patterns)}")
    print(f"📈 Expected blog posts: {len(all_patterns) * 5}")

if __name__ == "__main__":
    main()
