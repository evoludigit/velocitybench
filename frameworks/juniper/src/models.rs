use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// User model representing a user in the system
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct User {
    pub id: Uuid,
    pub pk_user: i32,
    pub username: String,
    pub full_name: Option<String>,
    pub bio: Option<String>,
    pub created_at: DateTime<Utc>,
}

/// Post model representing a blog post
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Post {
    pub id: Uuid,
    pub pk_post: i32,
    pub title: String,
    pub content: Option<String>,
    pub fk_author: i32,
    pub created_at: DateTime<Utc>,
}

/// Comment model representing a comment on a post
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Comment {
    pub id: Uuid,
    pub pk_comment: i32,
    pub content: String,
    pub fk_post: i32,
    pub fk_author: i32,
    pub created_at: DateTime<Utc>,
}

/// Input type for updating a user
#[derive(Clone, Debug)]
pub struct UpdateUserInput {
    pub full_name: Option<String>,
    pub bio: Option<String>,
}

/// Input type for updating a post
#[derive(Clone, Debug)]
pub struct UpdatePostInput {
    pub title: Option<String>,
    pub content: Option<String>,
}
