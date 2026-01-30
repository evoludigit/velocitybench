# Docker Compose Guide

Complete guide for running VelocityBench services with Docker Compose.

## Quick Start

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f postgres

# Stop all services
docker-compose down
```

## Services Overview

### PostgreSQL Database

- **Image**: `postgres:15-alpine`
- **Port**: 5434 (remapped to 5432 inside container)
- **Health Check**: pg_isready every 30s
- **Volumes**:
  - `postgres_data` - persistent data
  - Schema initialization scripts

**Environment Variables**:
```env
POSTGRES_DB=velocitybench_benchmark
POSTGRES_USER=benchmark
POSTGRES_PASSWORD=benchmark123
DATA_VOLUME=small  # small, medium, large, xlarge
```

**Start PostgreSQL Only**:
```bash
docker-compose up postgres
```

### Framework Services

Each framework service is defined separately:

- **fraiseql** - Custom GraphQL framework (port 4000)
- **strawberry** - Python GraphQL (port 8011)
- **graphene** - Python GraphQL (port 8002)
- **spring-boot** - Java REST (port 8010)
- **apollo** - Node.js GraphQL (port 4001-4002)
- **postgraphile** - PostgreSQL GraphQL (port 4000, profile)
- And 30+ more frameworks...

**Dependencies**: All frameworks depend on PostgreSQL with `condition: service_started`

**Health Checks**: Each service has health checks configured for readiness:
```bash
# Watch health status
docker-compose ps  # Shows (healthy), (unhealthy), (starting)
```

## Profiles

Profiles allow selective startup of services:

```bash
# Start all services
docker-compose up

# Start only Hasura
docker-compose --profile hasura up

# Multiple profiles
docker-compose --profile hasura --profile postgraphile up

# All services except those in profiles
docker-compose up --profile ""
```

**Available Profiles**:
- `hasura` - Hasura GraphQL Engine
- `postgraphile` - PostGraphile (PostgreSQL-based)
- And others...

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
# Edit .env as needed
docker-compose up -d
```

### PostgreSQL Tuning

Adjust memory settings based on your machine:

**Laptop (4GB RAM)**:
```env
DB_SHARED_BUFFERS=1GB
DB_EFFECTIVE_CACHE_SIZE=3GB
DB_WORK_MEM=32MB
```

**Server (64GB RAM)**:
```env
DB_SHARED_BUFFERS=16GB
DB_EFFECTIVE_CACHE_SIZE=48GB
DB_WORK_MEM=256MB
```

### Database Size

Set data volume size:

```env
DATA_VOLUME=small      # ~1GB (minimal dataset)
DATA_VOLUME=medium     # ~5GB (representative sample)
DATA_VOLUME=large      # ~20GB (comprehensive)
DATA_VOLUME=xlarge     # ~100GB (full scale)
```

**Note**: Large datasets take 30+ minutes to generate.

## Common Tasks

### Check Service Status

```bash
# All services
docker-compose ps

# Specific service
docker-compose ps postgres
docker-compose ps strawberry

# Detailed status with health
docker-compose ps --all
```

### View Logs

```bash
# Follow PostgreSQL logs
docker-compose logs -f postgres

# View framework logs
docker-compose logs strawberry

# Show last 100 lines
docker-compose logs --tail 100 fraiseql

# View with timestamps
docker-compose logs -f --timestamps express-rest
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U benchmark -d velocitybench_benchmark

# Or from host (port 5434):
psql -h localhost -U benchmark -d velocitybench_benchmark -p 5434

# Common psql commands:
# \dt              - list tables
# \d table_name    - describe table
# \l               - list databases
# SELECT * FROM v_users LIMIT 5;  - query data
```

### Framework Access

```bash
# FastAPI (port 8003)
curl http://localhost:8003/users

# Flask (port 8001)
curl http://localhost:8001/ping

# Express REST (port 3000)
curl http://localhost:3000/users

# GraphQL endpoint
curl -X POST http://localhost:8011/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users(limit: 5) { id name } }"}'
```

### Rebuild Services

```bash
# Rebuild specific service
docker-compose build fraiseql

# Rebuild all services
docker-compose build

# Build without cache
docker-compose build --no-cache

# Then restart
docker-compose up -d
```

### Clean Up

```bash
# Stop all services (keep volumes)
docker-compose down

# Stop and remove volumes (careful - deletes data!)
docker-compose down -v

# Remove images too
docker-compose down --rmi all

# Remove unused Docker resources
docker system prune
```

### Resource Cleanup

```bash
# Remove specific volume
docker volume rm postgres_data

# Remove all dangling volumes
docker volume prune

# Check disk usage
docker system df
```

## Troubleshooting

### PostgreSQL Won't Start

```bash
# Check logs
docker-compose logs postgres

# Common issues:
# 1. Port 5434 already in use
#    Solution: Change POSTGRES_PORT in .env
# 2. Insufficient memory
#    Solution: Reduce DB_SHARED_BUFFERS in .env
# 3. Volume permission errors
#    Solution: Check docker or volume permissions
```

### Framework Connection Failure

```bash
# Check if PostgreSQL is healthy
docker-compose ps postgres  # Should show (healthy)

# Check framework logs
docker-compose logs strawberry

# Verify database connection
docker-compose exec strawberry \
  python -c "import psycopg2; print('OK')"
```

### Health Check Failures

```bash
# Some services fail health checks initially
# They may recover after startup

# Force restart unhealthy service
docker-compose restart fraiseql

# Increase timeout if needed
# Edit docker-compose.yml:
# healthcheck:
#   timeout: 30s
#   start_period: 60s
```

### Out of Disk Space

```bash
# Check disk usage
docker system df

# Clean up
docker system prune

# Remove unused images
docker image prune

# Remove large volumes (careful!)
docker volume rm postgres_data  # Deletes database!
```

## Advanced Topics

### Multi-Machine Setup

```bash
# Run Docker daemon on remote machine
export DOCKER_HOST=ssh://user@remote-server

# Now all docker-compose commands run remotely
docker-compose up -d  # Runs on remote-server
```

### Network Inspection

```bash
# List Docker networks
docker network ls

# Inspect velocitybench network
docker network inspect velocitybench-benchmark

# Services can reach each other by name:
# postgres:5432, strawberry:8000, etc.
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect postgres_data volume
docker volume inspect postgres_data

# Backup database
docker-compose exec postgres pg_dump -U benchmark velocitybench_benchmark > backup.sql

# Restore database
docker-compose exec -T postgres psql -U benchmark velocitybench_benchmark < backup.sql
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats

# Get detailed resource usage
docker stats --no-stream
docker stats postgres

# Monitor network
docker stats --no-stream | grep strawberry
```

## Docker Compose Reference

### Common Commands

| Command | Purpose |
|---------|---------|
| `docker-compose up` | Start services |
| `docker-compose up -d` | Start in background |
| `docker-compose down` | Stop and remove |
| `docker-compose ps` | List running services |
| `docker-compose logs` | View logs |
| `docker-compose exec` | Run command in container |
| `docker-compose build` | Build images |
| `docker-compose pull` | Pull images from registry |

### Health Check States

| State | Meaning |
|-------|---------|
| `(healthy)` | Service passed health check |
| `(unhealthy)` | Service failed health check |
| `(starting)` | Service running, health checking |
| N/A | Service has no health check |

## Performance Tips

1. **Use Volumes Efficiently**
   - Avoid mounting host directories for heavy I/O
   - Use named volumes for databases

2. **Configure Memory Limits**
   ```yaml
   postgres:
     deploy:
       resources:
         limits:
           memory: 8G
         reservations:
           memory: 4G
   ```

3. **Optimize Logging**
   ```bash
   # Reduce log verbosity
   docker-compose logs --tail 100  # Not 1000s of lines
   ```

4. **Use Resource Constraints**
   - Prevent runaway processes
   - Set CPU and memory limits per service

## Integration with GitHub Actions

For CI/CD, start services with:

```bash
docker-compose -f docker-compose.yml up -d

# Wait for health checks
sleep 10

# Run tests against services
pytest tests/

# Cleanup
docker-compose down
```

## Related Documentation

- [Development Guide](./DEVELOPMENT.md)
- [Docker Compose Spec](https://github.com/compose-spec/compose-spec)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## Need Help?

Check logs first:
```bash
docker-compose logs <service-name>
```

Then see troubleshooting section above.
