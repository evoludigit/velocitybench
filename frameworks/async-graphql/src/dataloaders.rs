use async_graphql::dataloader::*;
use std::collections::HashMap;
use uuid::Uuid;
use crate::db::Database;
use crate::models::{User, Post, Comment};

pub struct UserLoader {
    db: Database,
}

impl UserLoader {
    pub fn new(db: Database) -> Self {
        Self { db }
    }
}

impl Loader<i32> for UserLoader {
    type Value = User;
    type Error = async_graphql::Error;

    async fn load(&self, keys: &[i32]) -> Result<HashMap<i32, Self::Value>, Self::Error> {
        let client = self.db.pool().get().await
            .map_err(|e| async_graphql::Error::new(format!("DB error: {}", e)))?;

        let query = "
            SELECT id, pk_user, username, full_name, bio, created_at
            FROM benchmark.tb_user
            WHERE pk_user = ANY($1)
        ";

        let rows = client.query(query, &[&keys]).await
            .map_err(|e| async_graphql::Error::new(format!("Query error: {}", e)))?;

        let mut users = HashMap::new();
        for row in rows {
            let pk_user: i32 = row.get("pk_user");
            let user = User {
                id: row.get("id"),
                pk_user,
                username: row.get("username"),
                full_name: row.get("full_name"),
                bio: row.get("bio"),
                created_at: row.get("created_at"),
            };
            users.insert(pk_user, user);
        }

        Ok(users)
    }
}

pub struct PostLoader {
    db: Database,
}

impl PostLoader {
    pub fn new(db: Database) -> Self {
        Self { db }
    }
}

impl Loader<i32> for PostLoader {
    type Value = Post;
    type Error = async_graphql::Error;

    async fn load(&self, keys: &[i32]) -> Result<HashMap<i32, Self::Value>, Self::Error> {
        let client = self.db.pool().get().await
            .map_err(|e| async_graphql::Error::new(format!("DB error: {}", e)))?;

        let query = "
            SELECT id, title, content, fk_author, created_at, pk_post
            FROM benchmark.tb_post
            WHERE pk_post = ANY($1)
        ";

        let rows = client.query(query, &[&keys]).await
            .map_err(|e| async_graphql::Error::new(format!("Query error: {}", e)))?;

        let mut posts = HashMap::new();
        for row in rows {
            let pk_post: i32 = row.get("pk_post");
            let post = Post {
                id: row.get("id"),
                pk_post,
                title: row.get("title"),
                content: row.get("content"),
                fk_author: row.get("fk_author"),
                created_at: row.get("created_at"),
            };
            posts.insert(pk_post, post);
        }

        Ok(posts)
    }
}

pub struct PostsByAuthorLoader {
    db: Database,
}

impl PostsByAuthorLoader {
    pub fn new(db: Database) -> Self {
        Self { db }
    }
}

impl Loader<Uuid> for PostsByAuthorLoader {
    type Value = Vec<Post>;
    type Error = async_graphql::Error;

    async fn load(&self, keys: &[Uuid]) -> Result<HashMap<Uuid, Self::Value>, Self::Error> {
        let client = self.db.pool().get().await
            .map_err(|e| async_graphql::Error::new(format!("DB error: {}", e)))?;

        let query = "
            SELECT p.id, p.pk_post, p.title, p.content, p.fk_author, p.created_at,
                   u.id as author_uuid
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE u.id = ANY($1)
            ORDER BY p.created_at DESC
        ";

        let rows = client.query(query, &[&keys]).await
            .map_err(|e| async_graphql::Error::new(format!("Query error: {}", e)))?;

        let mut posts_by_author: HashMap<Uuid, Vec<Post>> = HashMap::new();
        for &key in keys {
            posts_by_author.insert(key, Vec::new());
        }

        for row in rows {
            let author_uuid: Uuid = row.get("author_uuid");
            let post = Post {
                id: row.get("id"),
                pk_post: row.get("pk_post"),
                title: row.get("title"),
                content: row.get("content"),
                fk_author: row.get("fk_author"),
                created_at: row.get("created_at"),
            };
            if let Some(posts) = posts_by_author.get_mut(&author_uuid) {
                posts.push(post);
            }
        }

        Ok(posts_by_author)
    }
}

pub struct CommentsByPostLoader {
    db: Database,
}

impl CommentsByPostLoader {
    pub fn new(db: Database) -> Self {
        Self { db }
    }
}

impl Loader<Uuid> for CommentsByPostLoader {
    type Value = Vec<Comment>;
    type Error = async_graphql::Error;

    async fn load(&self, keys: &[Uuid]) -> Result<HashMap<Uuid, Self::Value>, Self::Error> {
        let client = self.db.pool().get().await
            .map_err(|e| async_graphql::Error::new(format!("DB error: {}", e)))?;

        let query = "
            SELECT c.id, c.pk_comment, c.content, c.fk_post, c.fk_author, c.created_at,
                   p.id as post_uuid
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
            WHERE p.id = ANY($1)
            ORDER BY c.created_at DESC
        ";

        let rows = client.query(query, &[&keys]).await
            .map_err(|e| async_graphql::Error::new(format!("Query error: {}", e)))?;

        let mut comments_by_post: HashMap<Uuid, Vec<Comment>> = HashMap::new();
        for &key in keys {
            comments_by_post.insert(key, Vec::new());
        }

        for row in rows {
            let post_uuid: Uuid = row.get("post_uuid");
            let comment = Comment {
                id: row.get("id"),
                pk_comment: row.get("pk_comment"),
                content: row.get("content"),
                fk_post: row.get("fk_post"),
                fk_author: row.get("fk_author"),
                created_at: row.get("created_at"),
            };
            if let Some(comments) = comments_by_post.get_mut(&post_uuid) {
                comments.push(comment);
            }
        }

        Ok(comments_by_post)
    }
}

pub struct CommentLoader {
    db: Database,
}

impl CommentLoader {
    pub fn new(db: Database) -> Self {
        Self { db }
    }
}

impl Loader<i32> for CommentLoader {
    type Value = Comment;
    type Error = async_graphql::Error;

    async fn load(&self, keys: &[i32]) -> Result<HashMap<i32, Self::Value>, Self::Error> {
        let client = self.db.pool().get().await
            .map_err(|e| async_graphql::Error::new(format!("DB error: {}", e)))?;

        let query = "
            SELECT id, content, fk_post, fk_author, created_at, pk_comment
            FROM benchmark.tb_comment
            WHERE pk_comment = ANY($1)
        ";

        let rows = client.query(query, &[&keys]).await
            .map_err(|e| async_graphql::Error::new(format!("Query error: {}", e)))?;

        let mut comments = HashMap::new();
        for row in rows {
            let pk_comment: i32 = row.get("pk_comment");
            let comment = Comment {
                id: row.get("id"),
                pk_comment,
                content: row.get("content"),
                fk_post: row.get("fk_post"),
                fk_author: row.get("fk_author"),
                created_at: row.get("created_at"),
            };
            comments.insert(pk_comment, comment);
        }

        Ok(comments)
    }
}
