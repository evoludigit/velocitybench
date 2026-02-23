#!/usr/bin/env python3
"""
Master script to generate security tests for all frameworks.
Uses template-based approach with local AI model acceleration.

Usage:
    python scripts/generate_security_tests.py --framework fastapi-rest
    python scripts/generate_security_tests.py --language python
    python scripts/generate_security_tests.py --all
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Framework registry with metadata
FRAMEWORKS = {
    # Python Frameworks
    "fastapi-rest": {
        "language": "Python",
        "template": "SECURITY_TEST_TEMPLATE_PYTHON.py",
        "test_dir": "frameworks/fastapi-rest/tests",
        "factory_class": "TestFactory",
        "factory_methods": {
            "create_user": "create_user(username, email, full_name, bio)",
            "get_user_by_username": "get_user_by_username(username)",
            "get_auth_token": "get_auth_token(user_id)",
            "query_users": "query_users()",
        },
        "status": "ready",
    },
    "flask-rest": {
        "language": "Python",
        "template": "SECURITY_TEST_TEMPLATE_PYTHON.py",
        "test_dir": "frameworks/flask-rest/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "strawberry": {
        "language": "Python",
        "template": "SECURITY_TEST_TEMPLATE_PYTHON.py",
        "test_dir": "frameworks/strawberry/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "graphene": {
        "language": "Python",
        "template": "SECURITY_TEST_TEMPLATE_PYTHON.py",
        "test_dir": "frameworks/graphene/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "fraiseql": {
        "language": "Python",
        "template": "SECURITY_TEST_TEMPLATE_PYTHON.py",
        "test_dir": "frameworks/fraiseql/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "ariadne": {
        "language": "Python",
        "template": "SECURITY_TEST_TEMPLATE_PYTHON.py",
        "test_dir": "frameworks/ariadne/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "asgi-graphql": {
        "language": "Python",
        "template": "SECURITY_TEST_TEMPLATE_PYTHON.py",
        "test_dir": "frameworks/asgi-graphql/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    # Node.js Frameworks
    "express-rest": {
        "language": "TypeScript",
        "template": "SECURITY_TEST_TEMPLATE_TYPESCRIPT.ts",
        "test_dir": "frameworks/express-rest/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "apollo-server": {
        "language": "TypeScript",
        "template": "SECURITY_TEST_TEMPLATE_TYPESCRIPT.ts",
        "test_dir": "frameworks/apollo-server/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "graphql-yoga": {
        "language": "TypeScript",
        "template": "SECURITY_TEST_TEMPLATE_TYPESCRIPT.ts",
        "test_dir": "frameworks/graphql-yoga/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "apollo-orm": {
        "language": "TypeScript",
        "template": "SECURITY_TEST_TEMPLATE_TYPESCRIPT.ts",
        "test_dir": "frameworks/apollo-orm/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "express-orm": {
        "language": "TypeScript",
        "template": "SECURITY_TEST_TEMPLATE_TYPESCRIPT.ts",
        "test_dir": "frameworks/express-orm/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "express-graphql": {
        "language": "TypeScript",
        "template": "SECURITY_TEST_TEMPLATE_TYPESCRIPT.ts",
        "test_dir": "frameworks/express-graphql/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "mercurius": {
        "language": "TypeScript",
        "template": "SECURITY_TEST_TEMPLATE_TYPESCRIPT.ts",
        "test_dir": "frameworks/mercurius/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    # Go Frameworks
    "gin-rest": {
        "language": "Go",
        "template": "SECURITY_TEST_TEMPLATE_GO.go",
        "test_dir": "frameworks/gin-rest",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "go-gqlgen": {
        "language": "Go",
        "template": "SECURITY_TEST_TEMPLATE_GO.go",
        "test_dir": "frameworks/go-gqlgen",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "go-graphql-go": {
        "language": "Go",
        "template": "SECURITY_TEST_TEMPLATE_GO.go",
        "test_dir": "frameworks/go-graphql-go",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "graphql-go": {
        "language": "Go",
        "template": "SECURITY_TEST_TEMPLATE_GO.go",
        "test_dir": "frameworks/graphql-go/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    # Rust Frameworks
    "actix-web-rest": {
        "language": "Rust",
        "template": "SECURITY_TEST_TEMPLATE_RUST.rs",
        "test_dir": "frameworks/actix-web-rest/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "async-graphql": {
        "language": "Rust",
        "template": "SECURITY_TEST_TEMPLATE_RUST.rs",
        "test_dir": "frameworks/async-graphql/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "juniper": {
        "language": "Rust",
        "template": "SECURITY_TEST_TEMPLATE_RUST.rs",
        "test_dir": "frameworks/juniper/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    # Java Frameworks
    "java-spring-boot": {
        "language": "Java",
        "template": "SECURITY_TEST_TEMPLATE_JAVA.java",
        "test_dir": "frameworks/java-spring-boot/src/test/java",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "spring-boot-orm": {
        "language": "Java",
        "template": "SECURITY_TEST_TEMPLATE_JAVA.java",
        "test_dir": "frameworks/spring-boot-orm/src/test/java",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "spring-boot-orm-naive": {
        "language": "Java",
        "template": "SECURITY_TEST_TEMPLATE_JAVA.java",
        "test_dir": "frameworks/spring-boot-orm-naive/src/test/java",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "micronaut-graphql": {
        "language": "Java",
        "template": "SECURITY_TEST_TEMPLATE_JAVA.java",
        "test_dir": "frameworks/micronaut-graphql/src/test/java",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "play-graphql": {
        "language": "Scala",
        "template": "SECURITY_TEST_TEMPLATE_SCALA.scala",
        "test_dir": "frameworks/play-graphql/test",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "quarkus-graphql": {
        "language": "Java",
        "template": "SECURITY_TEST_TEMPLATE_JAVA.java",
        "test_dir": "frameworks/quarkus-graphql/src/test/java",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    # Ruby Frameworks
    "hanami": {
        "language": "Ruby",
        "template": "SECURITY_TEST_TEMPLATE_RUBY.rb",
        "test_dir": "frameworks/hanami/test",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "rails": {
        "language": "Ruby",
        "template": "SECURITY_TEST_TEMPLATE_RUBY.rb",
        "test_dir": "frameworks/rails/test",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "ruby-rails": {
        "language": "Ruby",
        "template": "SECURITY_TEST_TEMPLATE_RUBY.rb",
        "test_dir": "frameworks/ruby-rails/test",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    # PHP Frameworks
    "php-laravel": {
        "language": "PHP",
        "template": "SECURITY_TEST_TEMPLATE_PHP.php",
        "test_dir": "frameworks/php-laravel/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "webonyx-graphql-php": {
        "language": "PHP",
        "template": "SECURITY_TEST_TEMPLATE_PHP.php",
        "test_dir": "frameworks/webonyx-graphql-php/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    # Other Frameworks
    "postgraphile": {
        "language": "TypeScript",
        "template": "SECURITY_TEST_TEMPLATE_TYPESCRIPT.ts",
        "test_dir": "frameworks/postgraphile/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "hasura": {
        "language": "Python",
        "template": "SECURITY_TEST_TEMPLATE_PYTHON.py",
        "test_dir": "frameworks/hasura/tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
    "csharp-dotnet": {
        "language": "CSharp",
        "template": "SECURITY_TEST_TEMPLATE_CSHARP.cs",
        "test_dir": "frameworks/csharp-dotnet/FraiseQL.Benchmark.Tests",
        "factory_class": "TestFactory",
        "status": "ready",
    },
}


def list_frameworks(language: Optional[str] = None) -> None:
    """List all frameworks, optionally filtered by language."""
    if language:
        frameworks = {k: v for k, v in FRAMEWORKS.items() if v["language"] == language}
        print(f"\n=== {language} Frameworks ({len(frameworks)}) ===\n")
    else:
        frameworks = FRAMEWORKS
        print(f"\n=== All Frameworks ({len(frameworks)}) ===\n")

    by_language = {}
    for fw, meta in frameworks.items():
        lang = meta["language"]
        if lang not in by_language:
            by_language[lang] = []
        by_language[lang].append(fw)

    for lang in sorted(by_language.keys()):
        print(f"{lang}:")
        for fw in sorted(by_language[lang]):
            print(f"  - {fw}")
        print()


def generate_framework(framework: str, dry_run: bool = False) -> None:
    """Generate security tests for a single framework."""
    if framework not in FRAMEWORKS:
        print(f"Error: Framework '{framework}' not found")
        sys.exit(1)

    meta = FRAMEWORKS[framework]
    print(f"\n{'='*70}")
    print(f"Framework: {framework}")
    print(f"Language: {meta['language']}")
    print(f"Template: {meta['template']}")
    print(f"Test Dir: {meta['test_dir']}")
    print(f"{'='*70}\n")

    if dry_run:
        print("[DRY RUN] Would generate:")
        print(f"  - {meta['test_dir']}/test_security_injection.ext")
        print(f"  - {meta['test_dir']}/test_security_auth.ext")
        print(f"  - {meta['test_dir']}/test_security_rate_limit.ext")
    else:
        print(f"[SKIP] Generation not implemented for {framework}")


def generate_language(language: str, dry_run: bool = False) -> None:
    """Generate security tests for all frameworks of a given language."""
    frameworks = [fw for fw, meta in FRAMEWORKS.items() if meta["language"] == language]

    print(f"\nGenerating security tests for {language} ({len(frameworks)} frameworks)\n")

    for fw in sorted(frameworks):
        generate_framework(fw, dry_run=dry_run)


def generate_all(dry_run: bool = False) -> None:
    """Generate security tests for all frameworks."""
    print(f"\nGenerating security tests for ALL {len(FRAMEWORKS)} frameworks\n")

    by_language = {}
    for fw, meta in FRAMEWORKS.items():
        lang = meta["language"]
        if lang not in by_language:
            by_language[lang] = []
        by_language[lang].append(fw)

    for lang in sorted(by_language.keys()):
        generate_language(lang, dry_run=dry_run)

    print(f"\n{'='*70}")
    print(f"Total: {len(FRAMEWORKS)} frameworks")
    print(f"Total test files: {len(FRAMEWORKS) * 3} (3 per framework)")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Generate security tests for frameworks")
    parser.add_argument("--framework", help="Generate for specific framework")
    parser.add_argument("--language", help="Generate for all frameworks of a language")
    parser.add_argument("--all", action="store_true", help="Generate for all frameworks")
    parser.add_argument("--list", action="store_true", help="List all frameworks")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't generate)")

    args = parser.parse_args()

    if args.list:
        list_frameworks(args.language)
        return

    if args.framework:
        generate_framework(args.framework, dry_run=args.dry_run)
    elif args.language:
        generate_language(args.language, dry_run=args.dry_run)
    elif args.all:
        generate_all(dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
