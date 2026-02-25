use crate::db::DbPool;
use crate::error::ApiError;
use crate::models::{Comment, Post, User};
use deadpool_postgres::Client;

#[derive(Clone)]
pub struct UserRepository {
    pool: DbPool,
}

impl UserRepository {
    pub fn new(pool: DbPool) -> Self {
        Self { pool }
    }

    pub async fn get_client(&self) -> Result<Client, ApiError> {
        self.pool
            .get()
            .await
            .map_err(|e| ApiError::DatabaseError(e.to_string()))
    }

    pub async fn find_by_id(&self, id: &str) -> Result<Option<User>, ApiError> {
        let client = self.get_client().await?;

        let row = client
            .query_one(
                "SELECT id::text, username, full_name, bio
                 FROM benchmark.tb_user WHERE id::text = $1",
                &[&id],
            )
            .await
            .map_err(|_| ApiError::NotFound)?;

        let user = User {
            id: row.get("id"),
            username: row.get("username"),
            full_name: row.get("full_name"),
            bio: row.get("bio"),
            posts: None,
        };

        Ok(Some(user))
    }

    pub async fn find_all(&self, limit: i64, offset: i64) -> Result<Vec<User>, ApiError> {
        let client = self.get_client().await?;

        let rows = client
            .query(
                "SELECT id::text, username, full_name, bio
                 FROM benchmark.tb_user
                 ORDER BY id
                 LIMIT $1 OFFSET $2",
                &[&limit, &offset],
            )
            .await
            .map_err(|e| ApiError::DatabaseError(e.to_string()))?;

        let mut users = Vec::new();
        for row in rows {
            let user = User {
                id: row.get("id"),
                username: row.get("username"),
                full_name: row.get("full_name"),
                bio: row.get("bio"),
                posts: None,
            };
            users.push(user);
        }

        Ok(users)
    }

    pub async fn update_bio(&self, id: &str, bio: &str) -> Result<User, ApiError> {
        let client = self.get_client().await?;

        let row = client
            .query_one(
                "UPDATE benchmark.tb_user SET bio = $1
                 WHERE id::text = $2
                 RETURNING id::text, username, full_name, bio",
                &[&bio, &id],
            )
            .await
            .map_err(|_| ApiError::NotFound)?;

        Ok(User {
            id: row.get("id"),
            username: row.get("username"),
            full_name: row.get("full_name"),
            bio: row.get("bio"),
            posts: None,
        })
    }

    pub async fn find_posts_by_user(&self, user_id: &str, limit: i64) -> Result<Vec<Post>, ApiError> {
        let client = self.get_client().await?;

        let rows = client
            .query(
                "SELECT p.id::text, p.title, p.content, p.created_at::text,
                        u.id::text as user_id, u.username, u.full_name, u.bio
                 FROM benchmark.tb_post p
                 JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
                 WHERE u.id = $1 AND p.published = true
                 ORDER BY p.created_at DESC
                 LIMIT $2",
                &[&user_id, &limit],
            )
            .await
            .map_err(|e| ApiError::DatabaseError(e.to_string()))?;

        let mut posts = Vec::new();
        for row in rows {
            let author = User {
                id: row.get("user_id"),
                username: row.get("username"),
                full_name: row.get("full_name"),
                bio: row.get("bio"),
                posts: None,
            };

            let created_at_str: String = row.get("created_at");
            let created_at = chrono::DateTime::parse_from_rfc3339(&created_at_str)
                .map(|dt| dt.with_timezone(&chrono::Utc))
                .unwrap_or_else(|_| chrono::Utc::now());

            let post = Post {
                id: row.get("id"),
                title: row.get("title"),
                content: row.get("content"),
                author_id: row.get("user_id"),
                author,
                created_at,
            };

            posts.push(post);
        }

        Ok(posts)
    }
}

#[derive(Clone)]
pub struct PostRepository {
    pool: DbPool,
}

impl PostRepository {
    pub fn new(pool: DbPool) -> Self {
        Self { pool }
    }

    pub async fn get_client(&self) -> Result<Client, ApiError> {
        self.pool
            .get()
            .await
            .map_err(|e| ApiError::DatabaseError(e.to_string()))
    }

    pub async fn find_by_id(&self, id: &str) -> Result<Option<Post>, ApiError> {
        let client = self.get_client().await?;

        let row = client
            .query_one(
                "SELECT p.id::text, p.title, p.content, p.fk_author, p.created_at::text,
                        u.id::text as user_id, u.username, u.full_name, u.bio
                 FROM benchmark.tb_post p
                 JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
                 WHERE p.id = $1",
                &[&id],
            )
            .await
            .map_err(|_| ApiError::NotFound)?;

            let author = User {
                id: row.get("user_id"),
                username: row.get("username"),
                full_name: row.get("full_name"),
                bio: row.get("bio"),
                posts: None,
            };

        let created_at_str: String = row.get("created_at");
        let created_at = chrono::DateTime::parse_from_rfc3339(&created_at_str)
            .map(|dt| dt.with_timezone(&chrono::Utc))
            .unwrap_or_else(|_| chrono::Utc::now());

        let post = Post {
            id: row.get("id"),
            title: row.get("title"),
            content: row.get("content"),
            author_id: row.get("user_id"),
            author,
            created_at,
        };

        Ok(Some(post))
    }

    pub async fn find_all(&self, limit: i64, offset: i64) -> Result<Vec<Post>, ApiError> {
        let client = self.get_client().await?;

        let rows = client
            .query(
                "SELECT p.id::text, p.title, p.content, p.fk_author, p.created_at::text,
                        u.id::text as user_id, u.username, u.full_name, u.bio
                 FROM benchmark.tb_post p
                 JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
                 WHERE p.published = true
                 ORDER BY p.created_at DESC
                 LIMIT $1 OFFSET $2",
                &[&limit, &offset],
            )
            .await
            .map_err(|e| ApiError::DatabaseError(e.to_string()))?;

        let mut posts = Vec::new();
        for row in rows {
            let author = User {
                id: row.get("user_id"),
                username: row.get("username"),
                full_name: row.get("full_name"),
                bio: row.get("bio"),
                posts: None,
            };

            let created_at_str: String = row.get("created_at");
            let created_at = chrono::DateTime::parse_from_rfc3339(&created_at_str)
                .map(|dt| dt.with_timezone(&chrono::Utc))
                .unwrap_or_else(|_| chrono::Utc::now());

            let post = Post {
                id: row.get("id"),
                title: row.get("title"),
                content: row.get("content"),
                author_id: row.get("user_id"),
                author,
                created_at,
            };

            posts.push(post);
        }

        Ok(posts)
    }

    pub async fn find_by_author(&self, author_id: &str, limit: i64, offset: i64) -> Result<Vec<Post>, ApiError> {
        let client = self.get_client().await?;

        let rows = client
            .query(
                "SELECT p.id::text, p.title, p.content, p.fk_author, p.created_at::text,
                        u.id::text as user_id, u.username, u.full_name, u.bio
                 FROM benchmark.tb_post p
                 JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
                 WHERE u.id = $1 AND p.published = true
                 ORDER BY p.created_at DESC
                 LIMIT $2 OFFSET $3",
                &[&author_id, &limit, &offset],
            )
            .await
            .map_err(|e| ApiError::DatabaseError(e.to_string()))?;

        let mut posts = Vec::new();
        for row in rows {
            let author = User {
                id: row.get("user_id"),
                username: row.get("username"),
                full_name: row.get("full_name"),
                bio: row.get("bio"),
                posts: None,
            };

            let created_at_str: String = row.get("created_at");
            let created_at = chrono::DateTime::parse_from_rfc3339(&created_at_str)
                .map(|dt| dt.with_timezone(&chrono::Utc))
                .unwrap_or_else(|_| chrono::Utc::now());

            let post = Post {
                id: row.get("id"),
                title: row.get("title"),
                content: row.get("content"),
                author_id: row.get("user_id"),
                author,
                created_at,
            };

            posts.push(post);
        }

        Ok(posts)
    }
}

#[derive(Clone)]
pub struct CommentRepository {
    pool: DbPool,
}

impl CommentRepository {
    pub fn new(pool: DbPool) -> Self {
        Self { pool }
    }

    pub async fn get_client(&self) -> Result<Client, ApiError> {
        self.pool
            .get()
            .await
            .map_err(|e| ApiError::DatabaseError(e.to_string()))
    }

    pub async fn find_by_post(&self, post_id: &str, limit: i64, offset: i64) -> Result<Vec<Comment>, ApiError> {
        let client = self.get_client().await?;

        let rows = client
            .query(
                "SELECT c.id::text, c.content, c.created_at::text,
                        u.id::text as user_id, u.username, u.full_name, u.bio
                 FROM benchmark.tb_comment c
                 JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
                 WHERE c.fk_post = (SELECT pk_post FROM benchmark.tb_post WHERE id::text = $1)
                 AND c.is_approved = true
                 ORDER BY c.created_at DESC
                 LIMIT $2 OFFSET $3",
                &[&post_id, &limit, &offset],
            )
            .await
            .map_err(|e| ApiError::DatabaseError(e.to_string()))?;

        let mut comments = Vec::new();
        for row in rows {
            let author = User {
                id: row.get("user_id"),
                username: row.get("username"),
                full_name: row.get("full_name"),
                bio: row.get("bio"),
                posts: None,
            };

            let created_at_str: String = row.get("created_at");
            let created_at = chrono::DateTime::parse_from_rfc3339(&created_at_str)
                .map(|dt| dt.with_timezone(&chrono::Utc))
                .unwrap_or_else(|_| chrono::Utc::now());

            let comment = Comment {
                id: row.get("id"),
                content: row.get("content"),
                post_id: post_id.to_string(),
                author_id: row.get("user_id"),
                author,
                created_at,
            };

            comments.push(comment);
        }

        Ok(comments)
    }
}