use async_graphql::*;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct User {
    pub id: Uuid,
    pub pk_user: i32,  // Primary key for foreign key relationships
    pub username: String,
    pub full_name: String,
    pub bio: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[Object]
impl User {
    async fn id(&self) -> ID {
        ID::from(self.id.to_string())
    }

    async fn username(&self) -> &str {
        &self.username
    }

    async fn full_name(&self) -> &str {
        &self.full_name
    }

    async fn bio(&self) -> Option<&str> {
        self.bio.as_deref()
    }

    async fn created_at(&self) -> String {
        self.created_at.to_rfc3339()
    }

    async fn posts(&self, ctx: &Context<'_>, limit: Option<i32>) -> Result<Vec<Post>> {
        use async_graphql::dataloader::DataLoader;
        use crate::dataloaders::PostsByAuthorLoader;

        let loader = ctx.data::<DataLoader<PostsByAuthorLoader>>()?;
        let posts = loader.load_one(self.id).await?;
        let mut posts = posts.unwrap_or_default();

        // Apply limit
        if let Some(limit) = limit {
            let limit = limit.min(50) as usize;
            if posts.len() > limit {
                posts.truncate(limit);
            }
        }

        Ok(posts)
    }

    async fn comments(&self, _ctx: &Context<'_>) -> Result<Vec<Comment>> {
        // TODO: Implement comment loading for users
        Ok(vec![])
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Post {
    pub id: Uuid,
    pub pk_post: i32,  // Primary key for foreign key relationships
    pub title: String,
    pub content: String,
    pub fk_author: i32,
    pub created_at: DateTime<Utc>,
}

#[Object]
impl Post {
    async fn id(&self) -> ID {
        ID::from(self.id.to_string())
    }

    async fn title(&self) -> &str {
        &self.title
    }

    async fn content(&self) -> &str {
        &self.content
    }

    async fn created_at(&self) -> String {
        self.created_at.to_rfc3339()
    }

    async fn author(&self, ctx: &Context<'_>) -> Result<User> {
        use async_graphql::dataloader::DataLoader;
        use crate::dataloaders::UserLoader;

        let loader = ctx.data::<DataLoader<UserLoader>>()?;
        let user = loader.load_one(self.fk_author).await?;
        user.ok_or_else(|| async_graphql::Error::new("Author not found"))
    }

    async fn comments(&self, ctx: &Context<'_>, limit: Option<i32>) -> Result<Vec<Comment>> {
        use async_graphql::dataloader::DataLoader;
        use crate::dataloaders::CommentsByPostLoader;

        let loader = ctx.data::<DataLoader<CommentsByPostLoader>>()?;
        let comments = loader.load_one(self.id).await?;
        let mut comments = comments.unwrap_or_default();

        // Apply limit
        if let Some(limit) = limit {
            let limit = limit.min(50) as usize;
            if comments.len() > limit {
                comments.truncate(limit);
            }
        }

        Ok(comments)
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Comment {
    pub id: Uuid,
    pub pk_comment: i32,  // Primary key for foreign key relationships
    pub content: String,
    pub fk_post: i32,
    pub fk_author: i32,
    pub created_at: DateTime<Utc>,
}

#[Object]
impl Comment {
    async fn id(&self) -> ID {
        ID::from(self.id.to_string())
    }

    async fn content(&self) -> &str {
        &self.content
    }

    async fn created_at(&self) -> String {
        self.created_at.to_rfc3339()
    }

    async fn post(&self, ctx: &Context<'_>) -> Result<Post> {
        use async_graphql::dataloader::DataLoader;
        use crate::dataloaders::PostLoader;

        let loader = ctx.data::<DataLoader<PostLoader>>()?;
        let post = loader.load_one(self.fk_post).await?;
        post.ok_or_else(|| async_graphql::Error::new("Post not found"))
    }

    async fn author(&self, ctx: &Context<'_>) -> Result<User> {
        use async_graphql::dataloader::DataLoader;
        use crate::dataloaders::UserLoader;

        let loader = ctx.data::<DataLoader<UserLoader>>()?;
        let user = loader.load_one(self.fk_author).await?;
        user.ok_or_else(|| async_graphql::Error::new("Author not found"))
    }
}