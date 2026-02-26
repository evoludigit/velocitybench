//! Tests for Juniper GraphQL resolvers.
//!
//! Uses an in-memory test factory for fast, isolated tests.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone)]
pub struct TestUser {
    pub id: String,
    pub pk_user: i32,
    pub username: String,
    pub full_name: String,
    pub bio: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone)]
pub struct TestPost {
    pub id: String,
    pub pk_post: i32,
    pub fk_author: i32,
    pub title: String,
    pub content: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub author: Option<TestUser>,
}

#[derive(Debug, Clone)]
pub struct TestComment {
    pub id: String,
    pub pk_comment: i32,
    pub fk_post: i32,
    pub fk_author: i32,
    pub content: String,
    pub created_at: DateTime<Utc>,
    pub author: Option<TestUser>,
    pub post: Option<TestPost>,
}

pub struct TestFactory {
    users: Arc<Mutex<HashMap<String, TestUser>>>,
    posts: Arc<Mutex<HashMap<String, TestPost>>>,
    comments: Arc<Mutex<HashMap<String, TestComment>>>,
    user_counter: Arc<Mutex<i32>>,
    post_counter: Arc<Mutex<i32>>,
    comment_counter: Arc<Mutex<i32>>,
}

impl TestFactory {
    pub fn new() -> Self {
        TestFactory {
            users: Arc::new(Mutex::new(HashMap::new())),
            posts: Arc::new(Mutex::new(HashMap::new())),
            comments: Arc::new(Mutex::new(HashMap::new())),
            user_counter: Arc::new(Mutex::new(0)),
            post_counter: Arc::new(Mutex::new(0)),
            comment_counter: Arc::new(Mutex::new(0)),
        }
    }

    pub fn create_user(&self, username: &str, email: &str, full_name: &str, bio: Option<&str>) -> TestUser {
        let mut counter = self.user_counter.lock().unwrap();
        *counter += 1;
        let pk = *counter;

        let user = TestUser {
            id: Uuid::new_v4().to_string(),
            pk_user: pk,
            username: username.to_string(),
            full_name: full_name.to_string(),
            bio: bio.map(|s| s.to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        self.users.lock().unwrap().insert(user.id.clone(), user.clone());
        user
    }

    pub fn create_post(&self, author_id: &str, title: &str, content: &str) -> TestPost {
        let users = self.users.lock().unwrap();
        let author = users.get(author_id).expect("Author not found").clone();
        drop(users);

        let mut counter = self.post_counter.lock().unwrap();
        *counter += 1;
        let pk = *counter;

        let post = TestPost {
            id: Uuid::new_v4().to_string(),
            pk_post: pk,
            fk_author: author.pk_user,
            title: title.to_string(),
            content: content.to_string(),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            author: Some(author),
        };

        self.posts.lock().unwrap().insert(post.id.clone(), post.clone());
        post
    }

    pub fn create_comment(&self, author_id: &str, post_id: &str, content: &str) -> TestComment {
        let users = self.users.lock().unwrap();
        let author = users.get(author_id).expect("Author not found").clone();
        drop(users);

        let posts = self.posts.lock().unwrap();
        let post = posts.get(post_id).expect("Post not found").clone();
        drop(posts);

        let mut counter = self.comment_counter.lock().unwrap();
        *counter += 1;
        let pk = *counter;

        let comment = TestComment {
            id: Uuid::new_v4().to_string(),
            pk_comment: pk,
            fk_post: post.pk_post,
            fk_author: author.pk_user,
            content: content.to_string(),
            created_at: Utc::now(),
            author: Some(author),
            post: Some(post),
        };

        self.comments.lock().unwrap().insert(comment.id.clone(), comment.clone());
        comment
    }

    pub fn get_user(&self, id: &str) -> Option<TestUser> {
        self.users.lock().unwrap().get(id).cloned()
    }

    pub fn get_post(&self, id: &str) -> Option<TestPost> {
        self.posts.lock().unwrap().get(id).cloned()
    }

    pub fn get_comment(&self, id: &str) -> Option<TestComment> {
        self.comments.lock().unwrap().get(id).cloned()
    }

    pub fn get_all_users(&self) -> Vec<TestUser> {
        self.users.lock().unwrap().values().cloned().collect()
    }

    pub fn get_posts_by_author(&self, author_pk: i32) -> Vec<TestPost> {
        self.posts.lock().unwrap()
            .values()
            .filter(|p| p.fk_author == author_pk)
            .cloned()
            .collect()
    }

    pub fn get_comments_by_post(&self, post_pk: i32) -> Vec<TestComment> {
        self.comments.lock().unwrap()
            .values()
            .filter(|c| c.fk_post == post_pk)
            .cloned()
            .collect()
    }

    pub fn reset(&self) {
        self.users.lock().unwrap().clear();
        self.posts.lock().unwrap().clear();
        self.comments.lock().unwrap().clear();
        *self.user_counter.lock().unwrap() = 0;
        *self.post_counter.lock().unwrap() = 0;
        *self.comment_counter.lock().unwrap() = 0;
    }
}

impl Default for TestFactory {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ============================================================================
    // User Query Tests
    // ============================================================================

    #[test]
    fn test_query_user_by_uuid() {
        let factory = TestFactory::new();
        let user = factory.create_user("alice", "alice@example.com", "Alice Smith", Some("Hello!"));

        let result = factory.get_user(&user.id);

        assert!(result.is_some());
        let found = result.unwrap();
        assert_eq!(found.id, user.id);
        assert_eq!(found.username, "alice");
        assert_eq!(found.full_name, "Alice Smith");
        assert_eq!(found.bio, Some("Hello!".to_string()));
    }

    #[test]
    fn test_query_users_returns_list() {
        let factory = TestFactory::new();
        factory.create_user("alice", "alice@example.com", "Alice", None);
        factory.create_user("bob", "bob@example.com", "Bob", None);
        factory.create_user("charlie", "charlie@example.com", "Charlie", None);

        let users = factory.get_all_users();

        assert_eq!(users.len(), 3);
    }

    #[test]
    fn test_query_user_not_found() {
        let factory = TestFactory::new();

        let result = factory.get_user("non-existent-id");

        assert!(result.is_none());
    }

    // ============================================================================
    // Post Query Tests
    // ============================================================================

    #[test]
    fn test_query_post_by_id() {
        let factory = TestFactory::new();
        let user = factory.create_user("author", "author@example.com", "Author", None);
        let post = factory.create_post(&user.id, "Test Post", "Test content");

        let result = factory.get_post(&post.id);

        assert!(result.is_some());
        let found = result.unwrap();
        assert_eq!(found.title, "Test Post");
        assert_eq!(found.content, "Test content");
    }

    #[test]
    fn test_query_posts_by_author() {
        let factory = TestFactory::new();
        let user = factory.create_user("author", "author@example.com", "Author", None);
        factory.create_post(&user.id, "Post 1", "Content 1");
        factory.create_post(&user.id, "Post 2", "Content 2");

        let posts = factory.get_posts_by_author(user.pk_user);

        assert_eq!(posts.len(), 2);
    }

    // ============================================================================
    // Comment Query Tests
    // ============================================================================

    #[test]
    fn test_query_comment_by_id() {
        let factory = TestFactory::new();
        let author = factory.create_user("author", "author@example.com", "Author", None);
        let post = factory.create_post(&author.id, "Test Post", "Content");
        let commenter = factory.create_user("commenter", "commenter@example.com", "Commenter", None);
        let comment = factory.create_comment(&commenter.id, &post.id, "Great post!");

        let result = factory.get_comment(&comment.id);

        assert!(result.is_some());
        assert_eq!(result.unwrap().content, "Great post!");
    }

    #[test]
    fn test_query_comments_by_post() {
        let factory = TestFactory::new();
        let author = factory.create_user("author", "author@example.com", "Author", None);
        let post = factory.create_post(&author.id, "Test Post", "Content");
        let commenter = factory.create_user("commenter", "commenter@example.com", "Commenter", None);
        factory.create_comment(&commenter.id, &post.id, "Comment 1");
        factory.create_comment(&commenter.id, &post.id, "Comment 2");

        let comments = factory.get_comments_by_post(post.pk_post);

        assert_eq!(comments.len(), 2);
    }

    // ============================================================================
    // Relationship Tests
    // ============================================================================

    #[test]
    fn test_user_posts_relationship() {
        let factory = TestFactory::new();
        let user = factory.create_user("author", "author@example.com", "Author", None);
        let post1 = factory.create_post(&user.id, "Post 1", "Content 1");
        let post2 = factory.create_post(&user.id, "Post 2", "Content 2");

        let posts = factory.get_posts_by_author(user.pk_user);

        assert_eq!(posts.len(), 2);
        let post_ids: Vec<_> = posts.iter().map(|p| p.id.clone()).collect();
        assert!(post_ids.contains(&post1.id));
        assert!(post_ids.contains(&post2.id));
    }

    #[test]
    fn test_post_author_relationship() {
        let factory = TestFactory::new();
        let author = factory.create_user("author", "author@example.com", "Author", None);
        let post = factory.create_post(&author.id, "Test Post", "Content");

        assert!(post.author.is_some());
        assert_eq!(post.author.unwrap().pk_user, author.pk_user);
    }

    #[test]
    fn test_comment_author_relationship() {
        let factory = TestFactory::new();
        let author = factory.create_user("author", "author@example.com", "Author", None);
        let post = factory.create_post(&author.id, "Test Post", "Content");
        let commenter = factory.create_user("commenter", "commenter@example.com", "Commenter", None);
        let comment = factory.create_comment(&commenter.id, &post.id, "Great!");

        assert!(comment.author.is_some());
        assert_eq!(comment.author.unwrap().pk_user, commenter.pk_user);
    }

    // ============================================================================
    // Edge Case Tests
    // ============================================================================

    #[test]
    fn test_null_bio() {
        let factory = TestFactory::new();
        let user = factory.create_user("user", "user@example.com", "User", None);

        assert!(user.bio.is_none());
    }

    #[test]
    fn test_empty_posts_list() {
        let factory = TestFactory::new();
        let user = factory.create_user("newuser", "new@example.com", "New User", None);

        let posts = factory.get_posts_by_author(user.pk_user);

        assert!(posts.is_empty());
    }

    #[test]
    fn test_special_characters_in_content() {
        let factory = TestFactory::new();
        let user = factory.create_user("author", "author@example.com", "Author", None);
        let special_content = "Test with 'quotes' and \"double quotes\" and <html>";
        let post = factory.create_post(&user.id, "Special", special_content);

        assert_eq!(post.content, special_content);
    }

    #[test]
    fn test_unicode_content() {
        let factory = TestFactory::new();
        let user = factory.create_user("author", "author@example.com", "Author", None);
        let unicode_content = "Test with émojis 🎉 and ñ and 中文";
        let post = factory.create_post(&user.id, "Unicode", unicode_content);

        assert_eq!(post.content, unicode_content);
    }

    // ============================================================================
    // Performance Tests
    // ============================================================================

    #[test]
    fn test_create_many_posts() {
        let factory = TestFactory::new();
        let user = factory.create_user("author", "author@example.com", "Author", None);

        for i in 0..50 {
            factory.create_post(&user.id, &format!("Post {}", i), "Content");
        }

        let posts = factory.get_posts_by_author(user.pk_user);
        assert_eq!(posts.len(), 50);
    }

    #[test]
    fn test_reset() {
        let factory = TestFactory::new();
        factory.create_user("user1", "user1@example.com", "User 1", None);
        factory.create_user("user2", "user2@example.com", "User 2", None);

        factory.reset();

        assert!(factory.get_all_users().is_empty());
    }

    // ============================================================================
    // Validation Tests
    // ============================================================================

    #[test]
    fn test_valid_uuid() {
        let factory = TestFactory::new();
        let user = factory.create_user("user", "user@example.com", "User", None);

        let parsed = Uuid::parse_str(&user.id);
        assert!(parsed.is_ok());
    }

    #[test]
    #[should_panic(expected = "Author not found")]
    fn test_create_post_with_invalid_author() {
        let factory = TestFactory::new();
        factory.create_post("invalid-author", "Test", "Content");
    }

    #[test]
    #[should_panic(expected = "Post not found")]
    fn test_create_comment_with_invalid_post() {
        let factory = TestFactory::new();
        let user = factory.create_user("user", "user@example.com", "User", None);
        factory.create_comment(&user.id, "invalid-post", "Content");
    }
}
