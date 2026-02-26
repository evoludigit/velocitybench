use juniper::{graphql_object, EmptySubscription, FieldResult, GraphQLInputObject, RootNode, ID};
use uuid::Uuid;

use crate::db::Database;
use crate::loaders::Loaders;
use crate::models::{Comment, Post, User};

/// GraphQL context containing database and loaders
pub struct Context {
    pub db: Database,
    pub loaders: Loaders,
}

impl juniper::Context for Context {}

// GraphQL object implementations

#[graphql_object(context = Context)]
impl User {
    fn id(&self) -> ID {
        ID::new(self.id.to_string())
    }

    fn username(&self) -> &str {
        &self.username
    }

    fn full_name(&self) -> Option<&str> {
        self.full_name.as_deref()
    }

    fn bio(&self) -> Option<&str> {
        self.bio.as_deref()
    }

    fn created_at(&self) -> String {
        self.created_at.to_rfc3339()
    }

    async fn posts(&self, context: &Context, limit: Option<i32>) -> FieldResult<Vec<Post>> {
        let limit = limit.unwrap_or(50).min(50);
        let posts = context
            .loaders
            .posts_by_author_loader
            .load(self.pk_user, limit)
            .await
            .map_err(|e| juniper::FieldError::new(e, juniper::Value::null()))?;
        Ok(posts)
    }

    async fn followers(&self, _context: &Context, _limit: Option<i32>) -> FieldResult<Vec<User>> {
        // Followers relationship not implemented in benchmark schema
        Ok(vec![])
    }

    async fn following(&self, _context: &Context, _limit: Option<i32>) -> FieldResult<Vec<User>> {
        // Following relationship not implemented in benchmark schema
        Ok(vec![])
    }
}

#[graphql_object(context = Context)]
impl Post {
    fn id(&self) -> ID {
        ID::new(self.id.to_string())
    }

    fn title(&self) -> &str {
        &self.title
    }

    fn content(&self) -> Option<&str> {
        self.content.as_deref()
    }

    fn created_at(&self) -> String {
        self.created_at.to_rfc3339()
    }

    async fn author(&self, context: &Context) -> FieldResult<User> {
        context
            .loaders
            .user_loader
            .load(self.fk_author)
            .await
            .map_err(|e| juniper::FieldError::new(e, juniper::Value::null()))?
            .ok_or_else(|| juniper::FieldError::new("Author not found", juniper::Value::null()))
    }

    async fn comments(&self, context: &Context, limit: Option<i32>) -> FieldResult<Vec<Comment>> {
        let limit = limit.unwrap_or(50).min(50);
        let comments = context
            .loaders
            .comments_by_post_loader
            .load(self.pk_post, limit)
            .await
            .map_err(|e| juniper::FieldError::new(e, juniper::Value::null()))?;
        Ok(comments)
    }
}

#[graphql_object(context = Context)]
impl Comment {
    fn id(&self) -> ID {
        ID::new(self.id.to_string())
    }

    fn content(&self) -> &str {
        &self.content
    }

    fn created_at(&self) -> String {
        self.created_at.to_rfc3339()
    }

    async fn author(&self, context: &Context) -> FieldResult<User> {
        context
            .loaders
            .user_loader
            .load(self.fk_author)
            .await
            .map_err(|e| juniper::FieldError::new(e, juniper::Value::null()))?
            .ok_or_else(|| juniper::FieldError::new("Author not found", juniper::Value::null()))
    }

    async fn post(&self, context: &Context) -> FieldResult<Post> {
        context
            .loaders
            .post_loader
            .load_by_pk(self.fk_post)
            .await
            .map_err(|e| juniper::FieldError::new(e, juniper::Value::null()))?
            .ok_or_else(|| juniper::FieldError::new("Post not found", juniper::Value::null()))
    }
}

// Query root

pub struct QueryRoot;

#[graphql_object(context = Context)]
impl QueryRoot {
    fn ping() -> &'static str {
        "pong"
    }

    async fn user(context: &Context, id: ID) -> FieldResult<Option<User>> {
        let user_id = Uuid::parse_str(&id.to_string())
            .map_err(|e| juniper::FieldError::new(format!("Invalid UUID: {}", e), juniper::Value::null()))?;

        let client = context.db.pool().get().await
            .map_err(|e| juniper::FieldError::new(format!("DB error: {}", e), juniper::Value::null()))?;

        let row = client
            .query_opt(
                "SELECT id, pk_user, username, full_name, bio, created_at
                 FROM benchmark.tb_user WHERE id = $1",
                &[&user_id],
            )
            .await
            .map_err(|e| juniper::FieldError::new(format!("Query error: {}", e), juniper::Value::null()))?;

        Ok(row.map(|r| User {
            id: r.get(0),
            pk_user: r.get(1),
            username: r.get(2),
            full_name: r.get(3),
            bio: r.get(4),
            created_at: r.get(5),
        }))
    }

    async fn users(context: &Context, limit: Option<i32>) -> FieldResult<Vec<User>> {
        let limit = limit.unwrap_or(10).min(100) as i64;

        let client = context.db.pool().get().await
            .map_err(|e| juniper::FieldError::new(format!("DB error: {}", e), juniper::Value::null()))?;

        let rows = client
            .query(
                "SELECT id, pk_user, username, full_name, bio, created_at
                 FROM benchmark.tb_user
                 ORDER BY created_at DESC
                 LIMIT $1",
                &[&limit],
            )
            .await
            .map_err(|e| juniper::FieldError::new(format!("Query error: {}", e), juniper::Value::null()))?;

        Ok(rows
            .iter()
            .map(|r| User {
                id: r.get(0),
                pk_user: r.get(1),
                username: r.get(2),
                full_name: r.get(3),
                bio: r.get(4),
                created_at: r.get(5),
            })
            .collect())
    }

    async fn post(context: &Context, id: ID) -> FieldResult<Option<Post>> {
        let post_id = Uuid::parse_str(&id.to_string())
            .map_err(|e| juniper::FieldError::new(format!("Invalid UUID: {}", e), juniper::Value::null()))?;

        context
            .loaders
            .post_loader
            .load_by_uuid(post_id)
            .await
            .map_err(|e| juniper::FieldError::new(e, juniper::Value::null()))
    }

    async fn posts(context: &Context, limit: Option<i32>) -> FieldResult<Vec<Post>> {
        let limit = limit.unwrap_or(10).min(100) as i64;

        let client = context.db.pool().get().await
            .map_err(|e| juniper::FieldError::new(format!("DB error: {}", e), juniper::Value::null()))?;

        let rows = client
            .query(
                "SELECT id, pk_post, title, content, fk_author, created_at
                 FROM benchmark.tb_post
                 ORDER BY created_at DESC
                 LIMIT $1",
                &[&limit],
            )
            .await
            .map_err(|e| juniper::FieldError::new(format!("Query error: {}", e), juniper::Value::null()))?;

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

    async fn comments(context: &Context, limit: Option<i32>) -> FieldResult<Vec<Comment>> {
        let limit = limit.unwrap_or(20).min(100) as i64;

        let client = context.db.pool().get().await
            .map_err(|e| juniper::FieldError::new(format!("DB error: {}", e), juniper::Value::null()))?;

        let rows = client
            .query(
                "SELECT id, pk_comment, content, fk_post, fk_author, created_at
                 FROM benchmark.tb_comment
                 ORDER BY created_at DESC
                 LIMIT $1",
                &[&limit],
            )
            .await
            .map_err(|e| juniper::FieldError::new(format!("Query error: {}", e), juniper::Value::null()))?;

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

// Mutation root

#[derive(GraphQLInputObject)]
pub struct UpdateUserInput {
    pub full_name: Option<String>,
    pub bio: Option<String>,
}

#[derive(GraphQLInputObject)]
pub struct UpdatePostInput {
    pub title: Option<String>,
    pub content: Option<String>,
}

pub struct MutationRoot;

#[graphql_object(context = Context)]
impl MutationRoot {
    async fn update_user(context: &Context, id: ID, input: UpdateUserInput) -> FieldResult<User> {
        let user_id = Uuid::parse_str(&id.to_string())
            .map_err(|e| juniper::FieldError::new(format!("Invalid UUID: {}", e), juniper::Value::null()))?;

        let client = context.db.pool().get().await
            .map_err(|e| juniper::FieldError::new(format!("DB error: {}", e), juniper::Value::null()))?;

        // Build update query dynamically
        let mut query = String::from("UPDATE benchmark.tb_user SET updated_at = NOW()");
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
            client
                .execute(&query, &params[..])
                .await
                .map_err(|e| juniper::FieldError::new(format!("Update error: {}", e), juniper::Value::null()))?;
        }

        // Return updated user
        let row = client
            .query_one(
                "SELECT id, pk_user, username, full_name, bio, created_at
                 FROM benchmark.tb_user WHERE id = $1",
                &[&user_id],
            )
            .await
            .map_err(|e| juniper::FieldError::new(format!("Query error: {}", e), juniper::Value::null()))?;

        Ok(User {
            id: row.get(0),
            pk_user: row.get(1),
            username: row.get(2),
            full_name: row.get(3),
            bio: row.get(4),
            created_at: row.get(5),
        })
    }

    async fn update_post(context: &Context, id: ID, input: UpdatePostInput) -> FieldResult<Post> {
        let post_id = Uuid::parse_str(&id.to_string())
            .map_err(|e| juniper::FieldError::new(format!("Invalid UUID: {}", e), juniper::Value::null()))?;

        let client = context.db.pool().get().await
            .map_err(|e| juniper::FieldError::new(format!("DB error: {}", e), juniper::Value::null()))?;

        // Build update query dynamically
        let mut query = String::from("UPDATE benchmark.tb_post SET updated_at = NOW()");
        let mut params: Vec<&(dyn tokio_postgres::types::ToSql + Sync)> = vec![];
        let mut param_idx = 1;

        if let Some(ref title) = input.title {
            query.push_str(&format!(", title = ${}", param_idx));
            params.push(title);
            param_idx += 1;
        }

        if let Some(ref content) = input.content {
            query.push_str(&format!(", content = ${}", param_idx));
            params.push(content);
            param_idx += 1;
        }

        query.push_str(&format!(" WHERE id = ${}", param_idx));
        params.push(&post_id);

        if input.title.is_some() || input.content.is_some() {
            client
                .execute(&query, &params[..])
                .await
                .map_err(|e| juniper::FieldError::new(format!("Update error: {}", e), juniper::Value::null()))?;
        }

        // Return updated post
        let row = client
            .query_one(
                "SELECT id, pk_post, title, content, fk_author, created_at
                 FROM benchmark.tb_post WHERE id = $1",
                &[&post_id],
            )
            .await
            .map_err(|e| juniper::FieldError::new(format!("Query error: {}", e), juniper::Value::null()))?;

        Ok(Post {
            id: row.get(0),
            pk_post: row.get(1),
            title: row.get(2),
            content: row.get(3),
            fk_author: row.get(4),
            created_at: row.get(5),
        })
    }
}

// Schema type alias
pub type Schema = RootNode<'static, QueryRoot, MutationRoot, EmptySubscription<Context>>;

pub fn create_schema() -> Schema {
    Schema::new(QueryRoot, MutationRoot, EmptySubscription::new())
}
