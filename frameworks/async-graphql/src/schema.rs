use async_graphql::*;
use uuid::Uuid;

use crate::db::Database;
use crate::models::{User, Post, Comment};

pub struct QueryRoot {
    db: Database,
}

impl QueryRoot {
    pub fn new(db: Database) -> Self {
        Self { db }
    }
}

#[derive(InputObject)]
pub struct UpdateUserInput {
    #[graphql(validator(max_length = 255))]
    pub full_name: Option<String>,
    #[graphql(validator(max_length = 1000))]
    pub bio: Option<String>,
}

pub struct MutationRoot {
    db: Database,
}

impl MutationRoot {
    pub fn new(db: Database) -> Self {
        Self { db }
    }
}

#[Object]
impl MutationRoot {
    async fn update_user(&self, ctx: &Context<'_>, id: ID, input: UpdateUserInput) -> Result<User> {
        let db = ctx.data::<Database>()?;
        let user_id = Uuid::parse_str(&id)?;

        let client = db.pool().get().await?;

        // Build update query
        let mut query = "UPDATE benchmark.tb_user SET updated_at = NOW()".to_string();
        let mut params: Vec<&(dyn tokio_postgres::types::ToSql + Sync)> = vec![];
        let mut param_idx = 1;

        if let Some(ref full_name) = input.full_name {
            query.push_str(&format!(", full_name = ${}", param_idx));
            params.push(full_name);
            param_idx += 1;
        }

        if let Some(ref bio) = input.bio {
            query.push_str(&format!(", bio = ${}", param_idx));
            params.push(bio);
            param_idx += 1;
        }

        query.push_str(&format!(" WHERE id = ${}", param_idx));
        params.push(&user_id);

        if input.full_name.is_some() || input.bio.is_some() {
            let _ = client.execute(&query, &params[..]).await?;
        }

        // Return updated user
        let row = client
            .query_one(
                "SELECT id, username, full_name, bio, created_at, pk_user FROM benchmark.tb_user WHERE id = $1",
                &[&user_id],
            )
            .await?;

        Ok(User {
            id: row.get(0),
            pk_user: row.get(5),
            username: row.get(1),
            full_name: row.get(2),
            bio: row.get(3),
            created_at: row.get(4),
        })
    }
}

#[Object]
impl QueryRoot {
    async fn user(&self, ctx: &Context<'_>, id: ID) -> Result<Option<User>> {
        let db = ctx.data::<Database>()?;
        let user_id = Uuid::parse_str(&id)?;

        let client = db.pool().get().await?;
        let row = client
            .query_opt(
                "SELECT id, username, full_name, bio, created_at, pk_user FROM benchmark.tb_user WHERE id = $1",
                &[&user_id],
            )
            .await?;

        Ok(row.map(|r| User {
            id: r.get(0),
            pk_user: r.get(5),
            username: r.get(1),
            full_name: r.get(2),
            bio: r.get(3),
            created_at: r.get(4),
        }))
    }

    async fn users(&self, ctx: &Context<'_>, limit: Option<i32>, offset: Option<i32>) -> Result<Vec<User>> {
        let db = ctx.data::<Database>()?;
        let limit = limit.unwrap_or(10).min(100) as i64;
        let offset = offset.unwrap_or(0) as i64;

        let client = db.pool().get().await?;
        let rows = client
            .query(
                "SELECT id, pk_user, username, full_name, bio, created_at FROM benchmark.tb_user ORDER BY pk_user LIMIT $1 OFFSET $2",
                &[&limit, &offset],
            )
            .await?;

        let users = rows
            .iter()
            .map(|row| User {
                id: row.get(0),
                pk_user: row.get(1),
                username: row.get(2),
                full_name: row.get(3),
                bio: row.get(4),
                created_at: row.get(5),
            })
            .collect();

        Ok(users)
    }

    async fn post(&self, ctx: &Context<'_>, id: ID) -> Result<Option<Post>> {
        let db = ctx.data::<Database>()?;
        let post_id = Uuid::parse_str(&id)?;

        let client = db.pool().get().await?;
        let row = client
            .query_opt(
                "SELECT id, pk_post, title, content, fk_author, created_at FROM benchmark.tb_post WHERE id = $1",
                &[&post_id],
            )
            .await?;

        Ok(row.map(|r| Post {
            id: r.get(0),
            pk_post: r.get(1),
            title: r.get(2),
            content: r.get(3),
            fk_author: r.get(4),
            created_at: r.get(5),
        }))
    }

    async fn posts(&self, ctx: &Context<'_>, limit: Option<i32>, offset: Option<i32>) -> Result<Vec<Post>> {
        let db = ctx.data::<Database>()?;
        let limit = limit.unwrap_or(10).min(100) as i64;
        let offset = offset.unwrap_or(0) as i64;

        let client = db.pool().get().await?;
        let rows = client
            .query(
                "SELECT id, pk_post, title, content, fk_author, created_at FROM benchmark.tb_post LIMIT $1 OFFSET $2",
                &[&limit, &offset],
             )
            .await?;

        let posts = rows
            .iter()
            .map(|row| Post {
                id: row.get(0),
                pk_post: row.get(1),
                title: row.get(2),
                content: row.get(3),
                fk_author: row.get(4),
                created_at: row.get(5),
            })
            .collect();

        Ok(posts)
    }

    async fn posts_by_user(&self, ctx: &Context<'_>, user_id: ID, limit: Option<i32>) -> Result<Vec<Post>> {
        let db = ctx.data::<Database>()?;
        let user_uuid = Uuid::parse_str(&user_id)?;
        let limit = limit.unwrap_or(10).min(100) as i64;

        let client = db.pool().get().await?;
        let rows = client
            .query(
                "SELECT p.id, p.pk_post, p.title, p.content, p.fk_author, p.created_at FROM benchmark.tb_post p JOIN benchmark.tb_user u ON p.fk_author = u.pk_user WHERE u.id = $1 LIMIT $2",
                &[&user_uuid, &limit],
            )
            .await?;

        let posts = rows
            .iter()
            .map(|row| Post {
                id: row.get(0),
                pk_post: row.get(1),
                title: row.get(2),
                content: row.get(3),
                fk_author: row.get(4),
                created_at: row.get(5),
            })
            .collect();

        Ok(posts)
    }

    async fn comments_by_post(&self, ctx: &Context<'_>, post_id: ID, limit: Option<i32>) -> Result<Vec<Comment>> {
        let db = ctx.data::<Database>()?;
        let post_uuid = Uuid::parse_str(&post_id)?;
        let limit = limit.unwrap_or(50).min(200) as i64;

        let client = db.pool().get().await?;
        let rows = client
            .query(
                "SELECT c.id, c.pk_comment, c.content, c.fk_post, c.fk_author, c.created_at FROM benchmark.tb_comment c JOIN benchmark.tb_post p ON c.fk_post = p.pk_post WHERE p.id = $1 LIMIT $2",
                &[&post_uuid, &limit],
            )
            .await?;

        let comments = rows
            .iter()
            .map(|row| Comment {
                id: row.get(0),
                pk_comment: row.get(1),
                content: row.get(2),
                fk_post: row.get(3),
                fk_author: row.get(4),
                created_at: row.get(5),
            })
            .collect();

        Ok(comments)
    }

    async fn posts_with_comments(&self, ctx: &Context<'_>, limit: Option<i32>, offset: Option<i32>) -> Result<Vec<Post>> {
        let db = ctx.data::<Database>()?;
        let limit = limit.unwrap_or(10).min(100) as i64;
        let offset = offset.unwrap_or(0) as i64;

        let client = db.pool().get().await?;
        let rows = client
            .query(
                "SELECT id, title, content, fk_author, created_at, pk_post FROM benchmark.tb_post LIMIT $1 OFFSET $2",
                &[&limit, &offset],
            )
            .await?;

        let posts = rows
            .iter()
            .map(|row| Post {
                id: row.get(0),
                pk_post: row.get(5),
                title: row.get(1),
                content: row.get(2),
                fk_author: row.get(3),
                created_at: row.get(4),
            })
            .collect();

        Ok(posts)
    }

    async fn comments(&self, ctx: &Context<'_>, limit: Option<i32>) -> Result<Vec<Comment>> {
        let db = ctx.data::<Database>()?;
        let limit = limit.unwrap_or(20).min(100) as i64;

        let client = db.pool().get().await?;
        let rows = client
            .query(
                "SELECT c.id, c.pk_comment, c.content, c.fk_post, c.fk_author, c.created_at FROM benchmark.tb_comment c ORDER BY c.created_at DESC LIMIT $1",
                &[&limit],
            )
            .await?;

        let comments = rows
            .iter()
            .map(|row| Comment {
                id: row.get(0),
                pk_comment: row.get(1),
                content: row.get(2),
                fk_post: row.get(3),
                fk_author: row.get(4),
                created_at: row.get(5),
            })
            .collect();

        Ok(comments)
    }
}