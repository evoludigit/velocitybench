# VelocityBench Development Container

This directory contains configuration for **GitHub Codespaces** and **VS Code Remote Containers**.

## Quick Start

### Option 1: GitHub Codespaces (Recommended)
1. Click **Code** → **Codespaces** → **Create codespace on main**
2. Wait for environment to initialize (~2 minutes)
3. Terminal opens automatically with full environment

### Option 2: VS Code Remote Containers
1. Install [Remote Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open project folder in VS Code
3. Click **Remote Container** icon in bottom-left corner
4. Select **Reopen in Container**
5. Wait for setup to complete (~1-2 minutes)

## What's Included

### Languages & Toolchains
- **Python 3.12** with uv package manager
- **Node.js 18** with npm/yarn
- **Go 1.21** with full tools
- **Rust** with clippy and rustfmt
- **Java 17** with Maven
- **Docker** (Docker-in-Docker for container builds)

### Development Tools
- **Pre-commit hooks** configured (linting, formatting)
- **Code formatters**: Black (Python), Prettier (JS/TS/YAML)
- **Linters**: Ruff (Python), ESLint (JavaScript)
- **Git** with LFS support
- **Make** for build automation
- **PostgreSQL/MySQL clients** for database operations

### VS Code Extensions
- Python development (Pylance, Black formatter, Ruff)
- TypeScript/JavaScript (Prettier, ESLint)
- Go (gopls)
- Rust (rust-analyzer)
- Java
- Docker
- GitHub Copilot
- Makefile tools

### Environment Setup
- Root Python environment created with dependencies
- Database environment (uv)
- Pre-commit hooks installed
- All ports forwarded for local testing

## Ports Available

| Port | Service | Notes |
|------|---------|-------|
| 3000 | Node.js Dev | Various Node frameworks |
| 4000+ | GraphQL | GraphQL endpoints |
| 8000-8016 | REST APIs | REST framework endpoints |
| 5433 | PostgreSQL | Database |

## Using the Container

### Open Terminal
- VS Code: `Ctrl+`` ` or **Terminal** → **New Terminal**
- Codespaces: Terminal opens by default

### Run Commands
```bash
# View available commands
make help

# Start database
make db-up

# Run tests
./tests/integration/smoke-test.sh

# Check virtual environments
make venv-check

# Set up individual framework
cd frameworks/fastapi-rest
python -m pytest tests/
```

### Set Up Framework Environments (Optional)
The post-create script sets up the root environment by default. To set up framework-specific environments:

```bash
# Manual setup for a framework
cd frameworks/fastapi-rest
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Uncomment the framework setup loop in `post-create.sh` if you want automatic setup for all frameworks.

## Customization

### Adjust Python Version
Edit `devcontainer.json`:
```json
"ghcr.io/devcontainers/features/python:1": {
  "version": "3.11"
}
```

### Add More Extensions
Edit the `customizations.vscode.extensions` array:
```json
"extensions": [
  "existing-extensions",
  "new.extension"
]
```

### Change Node/Go/Rust Versions
Edit corresponding feature versions in `devcontainer.json`.

## Environment Variables

Pre-configured for database connectivity:
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`
- `POSTGRES_DB=velocitybench`

Override in `.env` file for custom values.

## Tips & Tricks

### Faster Startup
- Comment out framework venv setup in `post-create.sh` if you don't need all frameworks
- Framework environments are created on-demand when you cd into a framework directory

### SSH Keys
SSH keys from host are automatically mounted (read-only):
```bash
git clone git@github.com:your-repo.git  # Works!
```

### Docker Build inside Container
Docker-in-Docker is enabled:
```bash
docker build -t my-image .
docker run my-image
```

### Persistent Shell History
Shell history is saved between container sessions.

## Troubleshooting

### Container fails to start
- Check Docker is running
- Delete container and rebuild: **VS Code** → **Remote** → **Rebuild Container**

### Command not found
- Restart VS Code
- Check environment: `which python` should return `/usr/local/bin/python`

### Port already in use
- Edit `forwardPorts` in `devcontainer.json`
- Or use `docker ps` to see what's running

### Out of disk space in Codespaces
- Delete large dependencies: `rm -rf node_modules`
- Rebuild container

## Resources

- [Dev Containers Documentation](https://containers.dev/)
- [GitHub Codespaces Docs](https://docs.github.com/en/codespaces)
- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)

---

**Happy coding!** 🚀

For issues, see [CONTRIBUTING.md](../CONTRIBUTING.md)
