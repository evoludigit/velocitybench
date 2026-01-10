#!/usr/bin/env python3
"""
Extensive pattern generator - creates hundreds of patterns across all categories
to reach 5K+ blog posts.
"""

import os
import yaml
from pathlib import Path

BASE_PATTERNS_DIR = Path(__file__).parent.parent / "corpus" / "patterns"

# Extensive pattern definitions across many categories
EXTENSIVE_PATTERNS = {
    "architecture": [
        ("domain-driven-design", "Domain-Driven Design (DDD)", "Organizing code around business domains"),
        ("hexagonal-architecture", "Hexagonal Architecture", "Isolating business logic from external concerns"),
        ("n-tier-architecture", "N-Tier Architecture", "Organizing code into logical layers"),
        ("microservices-communication", "Microservices Communication Patterns", "How services communicate effectively"),
        ("asynchronous-messaging", "Asynchronous Messaging Patterns", "Decoupling services with messaging"),
        ("saga-orchestration", "Saga Orchestration vs Choreography", "Coordinating distributed transactions"),
        ("cqrs-pattern", "CQRS Pattern", "Separating read and write models"),
        ("api-gateway-pattern", "API Gateway Pattern", "Centralizing API access"),
        ("strangler-fig-pattern", "Strangler Fig Pattern", "Gradually migrating monoliths"),
        ("anti-corruption-layer", "Anti-Corruption Layer", "Protecting domain models from legacy systems"),
    ],
    "data": [
        ("denormalization-strategies", "Denormalization Strategies", "Optimizing query performance"),
        ("materialized-views", "Materialized Views", "Pre-computed query results"),
        ("graph-databases", "Graph Database Patterns", "Working with relationship-rich data"),
        ("time-series-data", "Time-Series Data Management", "Handling sequential measurements"),
        ("data-archival", "Data Archival & Cold Storage", "Managing historical data efficiently"),
        ("data-synchronization", "Data Synchronization Between Systems", "Keeping data consistent"),
        ("eventual-consistency", "Eventual Consistency", "Accepting temporary inconsistency"),
        ("consensus-data-stores", "Consensus in Data Stores", "Achieving agreement across replicas"),
        ("backup-storage-patterns", "Backup & Storage Patterns", "Protecting data durability"),
        ("data-format-evolution", "Data Format Evolution", "Managing schema changes over time"),
    ],
    "performance": [
        ("memory-optimization", "Memory Optimization Techniques", "Reducing memory footprint"),
        ("cpu-efficiency", "CPU Efficiency Patterns", "Making efficient use of processors"),
        ("io-optimization", "I/O Optimization", "Reducing disk/network overhead"),
        ("lazy-loading-caching", "Lazy Loading & Caching", "Deferring computation"),
        ("batch-processing", "Batch Processing Patterns", "Processing data in groups"),
        ("parallel-processing", "Parallel Processing", "Using multiple threads/processes"),
        ("stream-processing", "Stream Processing", "Processing unbounded data"),
        ("resource-pooling", "Resource Pooling", "Reusing expensive resources"),
        ("rate-shaping", "Rate Shaping & Flow Control", "Managing throughput"),
        ("circuit-breaker-caching", "Circuit Breaker with Caching", "Hybrid resilience patterns"),
    ],
    "security": [
        ("oauth2-patterns", "OAuth 2.0 Patterns", "Delegated authorization"),
        ("jwt-security", "JWT Security Best Practices", "Securing token-based auth"),
        ("saml-sso", "SAML & Single Sign-On", "Enterprise authentication"),
        ("zero-trust-security", "Zero Trust Security Model", "Never trust, always verify"),
        ("secret-rotation", "Secrets Rotation Patterns", "Regularly changing credentials"),
        ("api-key-management", "API Key Management", "Securing and rotating keys"),
        ("input-validation-sanitization", "Input Validation & Sanitization", "Preventing injection attacks"),
        ("output-encoding-escaping", "Output Encoding & Escaping", "Preventing injection to users"),
        ("security-headers", "Security Headers (CSP, HSTS, etc)", "HTTP security headers"),
        ("compliance-standards", "Compliance Standards (PCI, HIPAA, GDPR)", "Meeting regulatory requirements"),
    ],
    "reliability": [
        ("chaos-engineering", "Chaos Engineering", "Testing system resilience"),
        ("graceful-degradation", "Graceful Degradation", "Partial service during failures"),
        ("error-recovery", "Error Recovery Strategies", "Bouncing back from failures"),
        ("observability-driven-development", "Observability-Driven Development", "Building observable systems"),
        ("sla-slo-sli", "SLA, SLO, SLI Metrics", "Defining reliability goals"),
        ("incident-response", "Incident Response Planning", "Handling production incidents"),
        ("post-mortem-analysis", "Post-Mortem Analysis", "Learning from failures"),
        ("disaster-recovery-planning", "Disaster Recovery Planning", "Recovering from major failures"),
        ("bcp-continuity", "Business Continuity Planning", "Maintaining operations"),
        ("resilience-testing", "Resilience Testing", "Validating fault tolerance"),
    ],
    "testing": [
        ("property-based-testing", "Property-Based Testing", "Generating test cases automatically"),
        ("fuzzing-security-testing", "Fuzzing & Security Testing", "Finding vulnerabilities"),
        ("load-stress-testing", "Load & Stress Testing", "Testing under extreme conditions"),
        ("chaos-testing", "Chaos Testing", "Injecting failures intentionally"),
        ("smoke-testing", "Smoke Testing", "Quick sanity checks"),
        ("regression-testing", "Regression Testing", "Ensuring old functionality still works"),
        ("acceptance-testing", "Acceptance Testing", "Validating user requirements"),
        ("accessibility-testing", "Accessibility Testing", "Ensuring inclusivity"),
        ("localization-testing", "Localization Testing", "Testing for multiple languages"),
        ("ui-visual-regression", "UI Visual Regression Testing", "Catching design changes"),
    ],
    "deployment": [
        ("immutable-infrastructure", "Immutable Infrastructure", "Never updating servers"),
        ("infrastructure-as-code", "Infrastructure as Code", "Managing infrastructure with code"),
        ("configuration-management", "Configuration Management", "Managing server configs"),
        ("secrets-in-deployment", "Secrets in Deployment", "Handling credentials safely"),
        ("zero-downtime-deployment", "Zero-Downtime Deployment", "Deploying without interruption"),
        ("rollback-strategies", "Rollback Strategies", "Quickly reverting changes"),
        ("A-B-testing-deployment", "A/B Testing Deployment", "Testing variations"),
        ("environment-management", "Environment Management (dev, staging, prod)", "Managing multiple environments"),
        ("infrastructure-provisioning", "Infrastructure Provisioning", "Setting up servers"),
        ("monitoring-deployment", "Monitoring Deployments", "Tracking deployment health"),
    ],
    "infrastructure": [
        ("network-architecture", "Network Architecture", "Designing network topology"),
        ("load-balancing-advanced", "Advanced Load Balancing", "Sophisticated traffic management"),
        ("dns-failover", "DNS Failover", "Using DNS for redundancy"),
        ("vpn-security-infrastructure", "VPN & Secure Infrastructure", "Private network connections"),
        ("firewall-policies", "Firewall & Access Control", "Network security"),
        ("logging-aggregation", "Log Aggregation Systems", "Centralized logging"),
        ("distributed-tracing-systems", "Distributed Tracing Systems", "Cross-service debugging"),
        ("metrics-aggregation", "Metrics Aggregation", "Collecting system metrics"),
        ("alerting-notification", "Alerting & Notifications", "Notifying on issues"),
        ("infrastructure-monitoring", "Infrastructure Monitoring", "Monitoring servers and network"),
    ],
    "frameworks": [
        ("microframework-patterns", "Microframework Patterns (Flask, Express)", "Lightweight web frameworks"),
        ("fullstack-framework-patterns", "Full-Stack Framework Patterns (Rails, Django)", "Comprehensive frameworks"),
        ("async-framework-patterns", "Async Framework Patterns (FastAPI, Quart)", "Async web frameworks"),
        ("message-queue-patterns", "Message Queue Patterns (RabbitMQ, Kafka)", "Async communication"),
        ("job-queue-patterns", "Job Queue Patterns (Celery, Bull)", "Background job processing"),
        ("caching-framework-patterns", "Caching Framework Patterns (Redis, Memcached)", "In-memory caching"),
        ("search-indexing-patterns", "Search & Indexing Patterns (Elasticsearch)", "Full-text search"),
        ("api-client-patterns", "API Client Patterns", "Making requests to APIs"),
        ("websocket-realtime-patterns", "WebSocket & Real-time Patterns", "Real-time communication"),
        ("rpc-framework-patterns", "RPC Framework Patterns", "Remote procedure calls"),
    ],
    "patterns-specific": [
        ("factory-pattern", "Factory Pattern", "Creating objects without specifying classes"),
        ("singleton-pattern", "Singleton Pattern", "Ensuring single instance"),
        ("observer-pattern", "Observer Pattern", "Event notification"),
        ("strategy-pattern", "Strategy Pattern", "Encapsulating algorithms"),
        ("decorator-pattern", "Decorator Pattern", "Adding behavior dynamically"),
        ("facade-pattern", "Facade Pattern", "Simplifying complex subsystems"),
        ("adapter-pattern", "Adapter Pattern", "Making incompatible interfaces work"),
        ("builder-pattern", "Builder Pattern", "Constructing complex objects"),
        ("iterator-pattern", "Iterator Pattern", "Traversing collections"),
        ("template-method-pattern", "Template Method Pattern", "Defining algorithm skeleton"),
    ],
    "cloud": [
        ("aws-patterns", "AWS Architecture Patterns", "Designing on AWS"),
        ("gcp-patterns", "Google Cloud Patterns", "Designing on GCP"),
        ("azure-patterns", "Azure Architecture Patterns", "Designing on Azure"),
        ("kubernetes-patterns", "Kubernetes Deployment Patterns", "Container orchestration"),
        ("serverless-architecture", "Serverless Architecture Patterns", "Function-based computing"),
        ("multi-cloud-strategy", "Multi-Cloud Strategy", "Using multiple cloud providers"),
        ("cloud-cost-optimization", "Cloud Cost Optimization", "Reducing cloud spending"),
        ("cloud-security", "Cloud Security Patterns", "Securing cloud infrastructure"),
        ("edge-computing", "Edge Computing Patterns", "Computing near users"),
        ("hybrid-cloud", "Hybrid Cloud Patterns", "Mixing on-premises and cloud"),
    ],
    "devops": [
        ("gitops-patterns", "GitOps Patterns", "Git as source of truth"),
        ("infrastructure-automation", "Infrastructure Automation", "Automating infrastructure"),
        ("configuration-drift", "Configuration Drift Detection", "Finding infrastructure changes"),
        ("secrets-management-devops", "Secrets Management in DevOps", "Securing credentials"),
        ("continuous-integration", "Continuous Integration Practices", "Frequent code integration"),
        ("continuous-delivery", "Continuous Delivery Practices", "Always ready to deploy"),
        ("continuous-deployment", "Continuous Deployment Practices", "Auto-deploying to production"),
        ("observability-pipelines", "Observability & Monitoring Pipelines", "Tracking system health"),
        ("on-call-management", "On-Call Management", "Handling production incidents"),
        ("compliance-automation", "Compliance & Automation", "Automating compliance checks"),
    ],
}

def generate_pattern_yaml(category: str, pattern_id: str, pattern_name: str, description: str) -> dict:
    """Generate a complete pattern YAML"""
    return {
        "id": pattern_id,
        "name": pattern_name,
        "category": category,
        "type": "standard",
        "tags": [category, pattern_id.replace("-", "_")],
        "summary": {
            "short": description,
            "long": f"{description}. This is a comprehensive pattern that provides guidance on implementation and best practices.",
        },
        "problem": {
            "description": f"Issues arise without proper {pattern_name.lower()}",
            "symptoms": [
                f"System lacks proper {pattern_name.lower()}",
                "Performance or reliability issues",
                "Difficulty scaling the system",
                "Maintenance challenges",
                "Integration problems"
            ],
            "impact": "System reliability and performance degradation"
        },
        "solution": {
            "description": f"Implement {pattern_name.lower()} effectively"
        },
        "key_concepts": {
            "concept_1": f"Understanding {pattern_name.lower()} fundamentals",
            "concept_2": f"Implementing {pattern_name.lower()} in your system",
            "concept_3": f"Best practices for {pattern_name.lower()}",
        },
        "implementation_considerations": {
            "consideration_1": "Understand your specific use case",
            "consideration_2": "Consider trade-offs and scalability",
            "consideration_3": "Plan for maintenance and evolution",
        },
        "best_practices": [
            {"name": f"Understand {pattern_id}", "description": "Learn the fundamentals before implementing"},
            {"name": "Plan carefully", "description": "Design for your specific requirements"},
            {"name": "Test thoroughly", "description": "Validate your implementation works"},
            {"name": "Monitor continuously", "description": "Track performance and issues"},
        ],
        "anti_patterns": [
            {"name": "Ignoring the pattern", "consequence": "Systems become unreliable"},
            {"name": "Misapplication", "consequence": "Wasted effort and poor results"},
        ],
        "blog_hooks": {
            "beginner": {"focus": f"Introduction to {pattern_name}"},
            "intermediate": {"focus": f"Implementing {pattern_name}"},
            "advanced": {"focus": f"Advanced {pattern_name} techniques"},
        }
    }

def create_patterns_bulk(category: str, patterns: list) -> int:
    """Create patterns for a category"""
    category_dir = BASE_PATTERNS_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for pattern_id, pattern_name, description in patterns:
        filepath = category_dir / f"{pattern_id}.yaml"

        if filepath.exists():
            continue

        pattern_data = generate_pattern_yaml(category, pattern_id, pattern_name, description)
        with open(filepath, 'w') as f:
            yaml.dump(pattern_data, f, default_flow_style=False, sort_keys=False)

        count += 1

    return count

def main():
    print("🚀 Extensive Pattern Generator")
    print("=" * 70)

    total_created = 0

    for category, patterns in EXTENSIVE_PATTERNS.items():
        created = create_patterns_bulk(category, patterns)
        total_created += created
        status = f"✓ {created} new" if created > 0 else "⊘ All exist"
        print(f"  {category:20s} {status}")

    # Count totals
    all_patterns = list(BASE_PATTERNS_DIR.glob("**/*.yaml"))
    expected_posts = len(all_patterns) * 5

    print(f"\n{'=' * 70}")
    print(f"✅ Created {total_created} new patterns")
    print(f"📊 Total patterns: {len(all_patterns)}")
    print(f"📈 Expected blog posts: {expected_posts:,}")

    if expected_posts >= 5000:
        print(f"🎉 TARGET REACHED: {expected_posts:,} ≥ 5000 blog posts!")

if __name__ == "__main__":
    main()
