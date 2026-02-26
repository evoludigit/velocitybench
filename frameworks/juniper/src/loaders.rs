use crate::db::Database;
use crate::models::{Comment, Post, User};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;

/// DataLoader for batching user lookups by pk_user
pub struct UserLoader {
    db: Database,
    cache: Arc<Mutex<HashMap<i32, User>>>,
}

impl UserLoader {
    pub fn new(db: Database) -> Self {
        Self {
            db,
            cache: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub async fn load(&self, pk_user: i32) -> Result<Option<User>, String> {
        // Check cache first
        {
            let cache = self.cache.lock().await;
            if let Some(user) = cache.get(&pk_user) {
                return Ok(Some(user.clone()));
            }
        }

        // Load from database
        let client = self.db.pool().get().await
            .map_err(|e| format!("DB error: {}", e))?;

        let row = client
            .query_opt(
                "SELECT id, pk_user, username, full_name, bio, created_at
                 FROM benchmark.tb_user WHERE pk_user = $1",
                &[&pk_user],
            )
            .await
            .map_err(|e| format!("Query error: {}", e))?;

        let user = row.map(|r| User {
            id: r.get(0),
            pk_user: r.get(1),
            username: r.get(2),
            full_name: r.get(3),
            bio: r.get(4),
            created_at: r.get(5),
        });

        // Cache the result
        if let Some(ref u) = user {
            let mut cache = self.cache.lock().await;
            cache.insert(pk_user, u.clone());
        }

        Ok(user)
    }

    pub async fn load_many(&self, pk_users: &[i32]) -> Result<HashMap<i32, User>, String> {
        let client = self.db.pool().get().await
            .map_err(|e| format!("DB error: {}", e))?;

        let rows = client
            .query(
                "SELECT id, pk_user, username, full_name, bio, created_at
                 FROM benchmark.tb_user WHERE pk_user = ANY($1)",
                &[&pk_users],
            )
            .await
            .map_err(|e| format!("Query error: {}", e))?;

        let mut users = HashMap::new();
        for row in rows {
            let pk_user: i32 = row.get(1);
            let user = User {
                id: row.get(0),
                pk_user,
                username: row.get(2),
                full_name: row.get(3),
                bio: row.get(4),
                created_at: row.get(5),
            };
            users.insert(pk_user, user);
        }

        // Update cache
        {
            let mut cache = self.cache.lock().await;
            for (k, v) in users.iter() {
                cache.insert(*k, v.clone());
            }
        }

        Ok(users)
    }
}

/// DataLoader for batching post lookups
pub struct PostLoader {
    db: Database,
}

impl PostLoader {
    pub fn new(db: Database) -> Self {
        Self { db }
    }

    pub async fn load_by_uuid(&self, id: Uuid) -> Result<Option<Post>, String> {
        let client = self.db.pool().get().await
            .map_err(|e| format!("DB error: {}", e))?;

        let row = client
            .query_opt(
                "SELECT id, pk_post, title, content, fk_author, created_at
                 FROM benchmark.tb_post WHERE id = $1",
                &[&id],
            )
            .await
            .map_err(|e| format!("Query error: {}", e))?;

        Ok(row.map(|r| Post {
            id: r.get(0),
            pk_post: r.get(1),
            title: r.get(2),
            content: r.get(3),
            fk_author: r.get(4),
            created_at: r.get(5),
        }))
    }

    pub async fn load_by_pk(&self, pk_post: i32) -> Result<Option<Post>, String> {
        let client = self.db.pool().get().await
            .map_err(|e| format!("DB error: {}", e))?;

        let row = client
            .query_opt(
                "SELECT id, pk_post, title, content, fk_author, created_at
                 FROM benchmark.tb_post WHERE pk_post = $1",
                &[&pk_post],
            )
            .await
            .map_err(|e| format!("Query error: {}", e))?;

        Ok(row.map(|r| Post {
            id: r.get(0),
            pk_post: r.get(1),
            title: r.get(2),
            content: r.get(3),
            fk_author: r.get(4),
            created_at: r.get(5),
        }))
    }
}

/// DataLoader for loading posts by author
pub struct PostsByAuthorLoader {
    db: Database,
}

impl PostsByAuthorLoader {
    pub fn new(db: Database) -> Self {
        Self { db }
    }

    pub async fn load(&self, fk_author: i32, limit: i32) -> Result<Vec<Post>, String> {
        let client = self.db.pool().get().await
            .map_err(|e| format!("DB error: {}", e))?;

        let rows = client
            .query(
                "SELECT id, pk_post, title, content, fk_author, created_at
                 FROM benchmark.tb_post
                 WHERE fk_author = $1
                 ORDER BY created_at DESC
                 LIMIT $2",
                &[&fk_author, &(limit as i64)],
            )
            .await
            .map_err(|e| format!("Query error: {}", e))?;

        Ok(rows
            .iter()
            .map(|r| Post {
                id: r.get(0),
                pk_post: r.get(1),
                title: r.get(2),
                content: r.get(3),
                fk_author: r.get(4),
                created_at: r.get(5),
            })
            .collect())
    }
}

/// DataLoader for loading comments by post
pub struct CommentsByPostLoader {
    db: Database,
}

impl CommentsByPostLoader {
    pub fn new(db: Database) -> Self {
        Self { db }
    }

    pub async fn load(&self, fk_post: i32, limit: i32) -> Result<Vec<Comment>, String> {
        let client = self.db.pool().get().await
            .map_err(|e| format!("DB error: {}", e))?;

        let rows = client
            .query(
                "SELECT id, pk_comment, content, fk_post, fk_author, created_at
                 FROM benchmark.tb_comment
                 WHERE fk_post = $1
                 ORDER BY created_at DESC
                 LIMIT $2",
                &[&fk_post, &(limit as i64)],
            )
            .await
            .map_err(|e| format!("Query error: {}", e))?;

        Ok(rows
            .iter()
            .map(|r| Comment {
                id: r.get(0),
                pk_comment: r.get(1),
                content: r.get(2),
                fk_post: r.get(3),
                fk_author: r.get(4),
                created_at: r.get(5),
            })
            .collect())
    }
}

/// Container for all data loaders
#[derive(Clone)]
pub struct Loaders {
    pub user_loader: Arc<UserLoader>,
    pub post_loader: Arc<PostLoader>,
    pub posts_by_author_loader: Arc<PostsByAuthorLoader>,
    pub comments_by_post_loader: Arc<CommentsByPostLoader>,
}

impl Loaders {
    pub fn new(db: Database) -> Self {
        Self {
            user_loader: Arc::new(UserLoader::new(db.clone())),
            post_loader: Arc::new(PostLoader::new(db.clone())),
            posts_by_author_loader: Arc::new(PostsByAuthorLoader::new(db.clone())),
            comments_by_post_loader: Arc::new(CommentsByPostLoader::new(db)),
        }
    }
}
