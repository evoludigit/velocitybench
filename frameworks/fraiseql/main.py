#!/usr/bin/env python3
"""FraiseQL Framework Server for VelocityBench

FraiseQL is a compiled GraphQL execution engine written in pure Rust.
This script manages the FraiseQL server lifecycle and schema compilation.

Architecture:
1. Python: Schema definition, server management
2. Rust (fraiseql-cli): Schema compilation
3. Rust (fraiseql-server): GraphQL query execution

Usage:
    python main.py                      # Start FraiseQL server
    python main.py --schema schema.py   # Compile custom schema
    python main.py --port 3000          # Use custom port
"""

import os
import sys
import subprocess
import json
import time
import signal
from pathlib import Path
from typing import Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FraiseQLServer:
    """Manages FraiseQL server lifecycle and schema compilation."""

    def __init__(
        self,
        schema_file: Optional[str] = None,
        database_url: Optional[str] = None,
        port: int = 3000,
        fraiseql_root: Optional[str] = None,
    ):
        """Initialize FraiseQL server manager.

        Args:
            schema_file: Path to schema.json (will auto-compile to .compiled.json)
            database_url: PostgreSQL connection URL
            port: HTTP server port (default: 3000)
            fraiseql_root: Path to fraiseql repository (for finding binaries)
        """
        self.schema_file = schema_file or "schema.json"
        self.schema_compiled = str(Path(self.schema_file).stem) + ".compiled.json"
        self.database_url = database_url
        self.port = port
        self.process: Optional[subprocess.Popen] = None

        # Locate fraiseql binaries
        self.fraiseql_root = Path(fraiseql_root or "/home/lionel/code/fraiseql")
        self.fraiseql_cli = self.fraiseql_root / "target" / "release" / "fraiseql-cli"
        self.fraiseql_server = (
            self.fraiseql_root / "target" / "release" / "fraiseql-server"
        )

        if not self.fraiseql_cli.exists():
            logger.error(f"fraiseql-cli not found at {self.fraiseql_cli}")
            logger.info("Build FraiseQL with: cd /home/lionel/code/fraiseql && cargo build --release")
            sys.exit(1)

        if not self.fraiseql_server.exists():
            logger.error(f"fraiseql-server not found at {self.fraiseql_server}")
            sys.exit(1)

    def compile_schema(self, force: bool = False) -> bool:
        """Compile schema.json to schema.compiled.json using fraiseql-cli.

        Args:
            force: Recompile even if .compiled.json exists

        Returns:
            True if compilation succeeded, False otherwise
        """
        schema_path = Path(self.schema_file)
        compiled_path = Path(self.schema_compiled)

        # Check if compilation is needed
        if compiled_path.exists() and not force:
            if schema_path.stat().st_mtime < compiled_path.stat().st_mtime:
                logger.info(f"✓ Using existing compiled schema: {compiled_path}")
                return True

        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return False

        logger.info(f"Compiling schema: {schema_path} -> {compiled_path}")

        try:
            result = subprocess.run(
                [
                    str(self.fraiseql_cli),
                    "compile",
                    str(schema_path),
                    "-o",
                    str(compiled_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"✓ Schema compiled successfully")
                logger.debug(f"Compiled schema size: {compiled_path.stat().st_size} bytes")
                return True
            else:
                logger.error(f"❌ Compilation failed:")
                logger.error(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ Schema compilation timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Error compiling schema: {e}")
            return False

    def start(self, auto_compile: bool = True) -> bool:
        """Start FraiseQL server.

        Args:
            auto_compile: Automatically compile schema if needed

        Returns:
            True if server started successfully
        """
        # Compile schema if needed
        if auto_compile:
            if not self.compile_schema():
                logger.error("Failed to compile schema, cannot start server")
                return False

        # Verify compiled schema exists
        if not Path(self.schema_compiled).exists():
            logger.error(f"Compiled schema not found: {self.schema_compiled}")
            return False

        # Build server command
        cmd = [
            str(self.fraiseql_server),
            "--schema",
            str(self.schema_compiled),
            "--port",
            str(self.port),
        ]

        # Add database URL if provided
        if self.database_url:
            cmd.extend(["--database", self.database_url])

        logger.info(f"Starting FraiseQL server on port {self.port}")
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait a moment for server to start
            time.sleep(2)

            # Check if process is still running
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                logger.error("❌ Server failed to start")
                if stderr:
                    logger.error(f"Error output: {stderr}")
                return False

            logger.info(f"✓ FraiseQL server running on http://localhost:{self.port}")
            return True

        except Exception as e:
            logger.error(f"❌ Error starting server: {e}")
            return False

    def stop(self) -> None:
        """Stop FraiseQL server."""
        if self.process and self.process.poll() is None:
            logger.info("Stopping FraiseQL server...")
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
                logger.info("✓ Server stopped")
            except subprocess.TimeoutExpired:
                logger.warning("Server did not stop gracefully, killing...")
                self.process.kill()

    def query(self, query: str, variables: Optional[dict] = None) -> Optional[dict]:
        """Send GraphQL query to server.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Parsed JSON response or None on error
        """
        import requests

        url = f"http://localhost:{self.port}/graphql"
        payload = {"query": query}

        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return None

    def health_check(self) -> bool:
        """Check if server is running and responsive.

        Returns:
            True if server is healthy
        """
        import requests

        try:
            response = requests.get(
                f"http://localhost:{self.port}/health",
                timeout=2,
            )
            return response.status_code == 200
        except Exception:
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="FraiseQL Server for VelocityBench",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Start with default schema.json
  python main.py --schema custom_schema.json  # Use custom schema
  python main.py --port 4000                  # Use custom port
  python main.py --database postgresql://...  # Connect to database
        """,
    )

    parser.add_argument(
        "--schema",
        default="schema.json",
        help="Path to schema.json file (default: schema.json)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Server port (default: 3000)",
    )
    parser.add_argument(
        "--database",
        help="PostgreSQL connection URL (optional)",
    )
    parser.add_argument(
        "--fraiseql-root",
        default="/home/lionel/code/fraiseql",
        help="Path to FraiseQL repository (default: /home/lionel/code/fraiseql)",
    )
    parser.add_argument(
        "--no-auto-compile",
        action="store_true",
        help="Don't automatically compile schema",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and start server
    server = FraiseQLServer(
        schema_file=args.schema,
        database_url=args.database,
        port=args.port,
        fraiseql_root=args.fraiseql_root,
    )

    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info("\nReceived interrupt signal, shutting down...")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start server
    if not server.start(auto_compile=not args.no_auto_compile):
        logger.error("Failed to start server")
        sys.exit(1)

    # Keep server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
