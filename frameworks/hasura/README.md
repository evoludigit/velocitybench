# Hasura GraphQL Engine

Hasura is an instant GraphQL API generator that creates a GraphQL API from your PostgreSQL database automatically.

## Features

- **Auto-generated GraphQL**: Instantly creates queries, mutations, and subscriptions from database schema
- **Relationships**: Automatically detects foreign keys and creates object/array relationships
- **Permissions**: Role-based access control at the row and column level
- **Real-time**: Built-in subscriptions via WebSockets
- **N+1 prevention**: Uses SQL JOINs rather than multiple queries

## Port

- **GraphQL**: `4000` (mapped from Hasura's internal port 8080)

## Quick Start

### Standalone (Development)

```bash
cd frameworks/hasura
docker-compose up -d
```

Access GraphQL console at: http://localhost:4000/console

### With VelocityBench (Benchmarking)

```bash
# From repository root
docker-compose --profile hasura up -d
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | See .env.example | PostgreSQL connection string |
| `HASURA_ADMIN_SECRET` | `benchmark-admin` | Admin secret for console access |

### Tracked Tables

Hasura is configured to track these tables from the `benchmark` schema:

**Command Side (Normalized)**:
- `tb_user` - Users with posts relationship
- `tb_post` - Posts with author and comments relationships
- `tb_comment` - Comments with author and post relationships

**Query Side (Denormalized JSONB)**:
- `tv_user` - User data with pre-computed aggregations
- `tv_post` - Post data with embedded author info
- `tv_comment` - Comment data with embedded author and post info

## GraphQL Endpoints

- **GraphQL**: `POST http://localhost:4000/v1/graphql`
- **Health Check**: `GET http://localhost:4000/healthz`
- **Console**: `GET http://localhost:4000/console` (when enabled)

## Example Queries

```graphql
# Get all users with their posts
query GetUsers {
  benchmark_tb_user {
    id
    username
    full_name
    posts {
      id
      title
      published
    }
  }
}

# Get a post with author and comments
query GetPost($id: uuid!) {
  benchmark_tb_post_by_pk(id: $id) {
    id
    title
    content
    author {
      username
      full_name
    }
    comments {
      content
      author {
        username
      }
    }
  }
}

# Using JSONB query side (faster for reads)
query GetPostFromView($id: uuid!) {
  benchmark_tv_post_by_pk(id: $id) {
    id
    data
  }
}
```

## Metadata Management

The `metadata/` directory contains Hasura's configuration:

```
metadata/
├── version.yaml           # Metadata format version
├── actions.yaml           # Custom actions (empty for benchmark)
└── databases/
    ├── databases.yaml     # Database connection config
    └── default/
        └── tables/
            └── tables.yaml  # Table tracking and permissions
```

To apply metadata changes:

```bash
# Using Hasura CLI
hasura metadata apply --endpoint http://localhost:4000 --admin-secret benchmark-admin

# Or restart the container (metadata is auto-applied from volume)
docker-compose restart hasura
```

## Performance Notes

- Hasura uses PostgreSQL's query planner for optimal JOINs
- Connection pooling is configured (max 50 connections)
- Query batching is supported via the `/v1/graphql` endpoint
- For benchmarks, disable console (`HASURA_GRAPHQL_ENABLE_CONSOLE=false`)
