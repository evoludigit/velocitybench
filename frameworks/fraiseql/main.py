#!/usr/bin/env python3
"""FraiseQL v2 Framework Server for VelocityBench

FraiseQL v2 is a compiled GraphQL execution engine written in pure Rust.
This script manages the FraiseQL server lifecycle and schema compilation.

Architecture:
1. Python: Schema definition, server management
2. Rust (fraiseql-cli): Schema compilation
3. Rust (fraiseql-server): GraphQL query execution

Usage:
    python main.py                          # Start FraiseQL server
    python main.py --schema schema.json     # Compile custom schema
    python main.py --port 8815              # Use custom port
    python main.py --config fraiseql.toml   # Use custom config
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default port for FraiseQL v2
DEFAULT_PORT = 8815


class FraiseQLServer:
    """Manages FraiseQL v2 server lifecycle and schema compilation."""

    def __init__(
        self,
        schema_file: Optional[str] = None,
        config_file: Optional[str] = None,
        database_url: Optional[str] = None,
        port: int = DEFAULT_PORT,
        fraiseql_root: Optional[str] = None,
    ):
        """Initialize FraiseQL v2 server manager.

        Args:
            schema_file: Path to schema.json (will auto-compile to .compiled.json)
            config_file: Path to fraiseql.toml config file
            database_url: PostgreSQL connection URL (overrides config)
            port: HTTP server port (default: 8815, overrides config)
            fraiseql_root: Path to fraiseql repository (for finding binaries)
        """
        self.schema_file = schema_file or "schema.json"
        self.schema_compiled = str(Path(self.schema_file).stem) + ".compiled.json"
        self.config_file = config_file or "fraiseql.toml"
        self.database_url = database_url
        self.port = port
        self.process: Optional[subprocess.Popen] = None

        # Locate fraiseql binaries - check multiple locations
        self.fraiseql_root = self._find_fraiseql_root(fraiseql_root)
        self.fraiseql_cli = self._find_binary("fraiseql-cli")
        self.fraiseql_server = self._find_binary("fraiseql-server")

    def _find_fraiseql_root(self, explicit_root: Optional[str]) -> Path:
        """Find the FraiseQL installation root."""
        # Check explicit path first
        if explicit_root:
            path = Path(explicit_root)
            if path.exists():
                return path

        # Check environment variable
        env_root = os.getenv("FRAISEQL_ROOT")
        if env_root:
            path = Path(env_root)
            if path.exists():
                return path

        # Check common locations
        common_paths = [
            Path("/home/lionel/code/fraiseql"),
            Path.home() / "code" / "fraiseql",
            Path.home() / ".fraiseql",
            Path("/usr/local"),
            Path("/opt/fraiseql"),
        ]

        for path in common_paths:
            if path.exists():
                return path

        # Default fallback
        return Path("/home/lionel/code/fraiseql")

    def _find_binary(self, name: str) -> Path:
        """Find a FraiseQL binary."""
        # Check in fraiseql root target directory (local build)
        local_path = self.fraiseql_root / "target" / "release" / name
        if local_path.exists():
            return local_path

        # Check if installed globally (cargo install)
        cargo_bin = Path.home() / ".cargo" / "bin" / name
        if cargo_bin.exists():
            return cargo_bin

        # Check system PATH
        import shutil
        system_path = shutil.which(name)
        if system_path:
            return Path(system_path)

        # Return expected path (will error on use if not found)
        return local_path

    def validate_binaries(self) -> bool:
        """Validate that required binaries exist."""
        if not self.fraiseql_cli.exists():
            logger.error(f"fraiseql-cli not found at {self.fraiseql_cli}")
            logger.info("Install with: cargo install fraiseql-cli --version 2.0.0-rc.3")
            logger.info("Or build locally: cd /home/lionel/code/fraiseql && cargo build --release")
            return False

        if not self.fraiseql_server.exists():
            logger.error(f"fraiseql-server not found at {self.fraiseql_server}")
            logger.info("Install with: cargo install fraiseql-server --version 2.0.0-rc.3")
            return False

        return True

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
                logger.info(f"Using existing compiled schema: {compiled_path}")
                return True

        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return False

        if not self.fraiseql_cli.exists():
            logger.error(f"fraiseql-cli not found at {self.fraiseql_cli}")
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
                logger.info("Schema compiled successfully")
                logger.debug(f"Compiled schema size: {compiled_path.stat().st_size} bytes")
                return True
            else:
                logger.error("Compilation failed:")
                logger.error(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            logger.error("Schema compilation timed out")
            return False
        except Exception as e:
            logger.error(f"Error compiling schema: {e}")
            return False

    def start(self, auto_compile: bool = True) -> bool:
        """Start FraiseQL v2 server.

        Args:
            auto_compile: Automatically compile schema if needed

        Returns:
            True if server started successfully
        """
        # Validate binaries
        if not self.validate_binaries():
            return False

        # Compile schema if needed
        if auto_compile:
            if not self.compile_schema():
                logger.error("Failed to compile schema, cannot start server")
                return False

        # Verify compiled schema exists
        if not Path(self.schema_compiled).exists():
            logger.error(f"Compiled schema not found: {self.schema_compiled}")
            return False

        # Build server command with v2 CLI flags
        cmd = [
            str(self.fraiseql_server),
            "--schema",
            str(self.schema_compiled),
        ]

        # Add config file if it exists
        config_path = Path(self.config_file)
        if config_path.exists():
            cmd.extend(["--config", str(config_path)])

        # Add port (overrides config)
        cmd.extend(["--port", str(self.port)])

        # Add database URL if provided (overrides config)
        if self.database_url:
            cmd.extend(["--database-url", self.database_url])

        logger.info(f"Starting FraiseQL v2 server on port {self.port}")
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            # Set environment variables for v2 server
            env = os.environ.copy()
            env.setdefault("RUST_LOG", "info")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

            # Wait for server to start
            time.sleep(2)

            # Check if process is still running
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                logger.error("Server failed to start")
                if stderr:
                    logger.error(f"Error output: {stderr}")
                return False

            logger.info(f"FraiseQL v2 server running on http://localhost:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False

    def stop(self) -> None:
        """Stop FraiseQL server."""
        if self.process and self.process.poll() is None:
            logger.info("Stopping FraiseQL server...")
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
                logger.info("Server stopped")
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
            logger.error(f"Query failed: {e}")
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
        description="FraiseQL v2 Server for VelocityBench",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                # Start with default config
  python main.py --config fraiseql.toml         # Use custom config
  python main.py --schema custom_schema.json    # Use custom schema
  python main.py --port 8815                    # Use custom port
  python main.py --database postgresql://...    # Connect to database
        """,
    )

    parser.add_argument(
        "--schema",
        default="schema.json",
        help="Path to schema.json file (default: schema.json)",
    )
    parser.add_argument(
        "--config",
        default="fraiseql.toml",
        help="Path to fraiseql.toml config file (default: fraiseql.toml)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--database",
        help="PostgreSQL connection URL (overrides config)",
    )
    parser.add_argument(
        "--fraiseql-root",
        help="Path to FraiseQL repository or installation",
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
        config_file=args.config,
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
