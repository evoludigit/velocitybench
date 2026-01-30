use uuid::Uuid;
use chrono::Utc;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

/// TestFactory provides helper methods for creating test data
pub struct TestFactory {
    users: Arc<Mutex<HashMap<String, TestUser>>>,
    posts: Arc<Mutex<HashMap<String, TestPost>>>,
}

#[derive(Clone, Debug)]
pub struct TestUser {
    pub id: String,
    pub pk_user: i32,
    pub username: String,
    pub full_name: String,
    pub bio: Option<String>,
    pub created_at: String,
}

#[derive(Clone, Debug)]
pub struct TestPost {
    pub id: String,
    pub pk_post: i32,
    pub title: String,
    pub content: String,
    pub fk_author: i32,
    pub created_at: String,
}

#[derive(Clone, Debug)]
pub struct TestComment {
    pub id: String,
    pub pk_comment: i32,
    pub content: String,
    pub fk_post: i32,
    pub fk_author: i32,
    pub created_at: String,
}

impl TestFactory {
    /// Create a new test factory instance
    pub fn new() -> Self {
        TestFactory {
            users: Arc::new(Mutex::new(HashMap::new())),
            posts: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// Create a test user
    pub fn create_test_user(
        &self,
        username: &str,
        _email: &str,
        full_name: &str,
        bio: &str,
    ) -> TestUser {
        let id = Uuid::new_v4().to_string();
        let pk_user = self.users.lock().unwrap().len() as i32 + 1;
        let bio = if bio.is_empty() { None } else { Some(bio.to_string()) };

        let user = TestUser {
            id: id.clone(),
            pk_user,
            username: username.to_string(),
            full_name: full_name.to_string(),
            bio,
            created_at: Utc::now().to_rfc3339(),
        };

        self.users.lock().unwrap().insert(id, user.clone());
        user
    }

    /// Create a test post
    pub fn create_test_post(&self, author_id: &str, title: &str, content: &str) -> TestPost {
        let id = Uuid::new_v4().to_string();
        let pk_post = self.posts.lock().unwrap().len() as i32 + 1;
        let fk_author = self
            .users
            .lock()
            .unwrap()
            .values()
            .find(|u| u.id == author_id)
            .map(|u| u.pk_user)
            .unwrap_or(1);

        let post = TestPost {
            id: id.clone(),
            pk_post,
            title: title.to_string(),
            content: content.to_string(),
            fk_author,
            created_at: Utc::now().to_rfc3339(),
        };

        self.posts.lock().unwrap().insert(id, post.clone());
        post
    }

    /// Create a test comment
    pub fn create_test_comment(&self, author_id: &str, post_id: &str, content: &str) -> TestComment {
        let id = Uuid::new_v4().to_string();
        let pk_comment = 1; // Simplified for tests
        let fk_author = self
            .users
            .lock()
            .unwrap()
            .values()
            .find(|u| u.id == author_id)
            .map(|u| u.pk_user)
            .unwrap_or(1);
        let fk_post = self
            .posts
            .lock()
            .unwrap()
            .values()
            .find(|p| p.id == post_id)
            .map(|p| p.pk_post)
            .unwrap_or(1);

        TestComment {
            id: id.clone(),
            pk_comment,
            content: content.to_string(),
            fk_post,
            fk_author,
            created_at: Utc::now().to_rfc3339(),
        }
    }

    /// Get a user by ID
    pub fn get_user(&self, id: &str) -> Option<TestUser> {
        self.users.lock().unwrap().get(id).cloned()
    }

    /// Get a post by ID
    pub fn get_post(&self, id: &str) -> Option<TestPost> {
        self.posts.lock().unwrap().get(id).cloned()
    }

    /// Get all users
    pub fn get_all_users(&self) -> Vec<TestUser> {
        self.users
            .lock()
            .unwrap()
            .values()
            .cloned()
            .collect()
    }

    /// Get all posts
    pub fn get_all_posts(&self) -> Vec<TestPost> {
        self.posts
            .lock()
            .unwrap()
            .values()
            .cloned()
            .collect()
    }

    /// Get user count
    pub fn user_count(&self) -> usize {
        self.users.lock().unwrap().len()
    }

    /// Get post count
    pub fn post_count(&self) -> usize {
        self.posts.lock().unwrap().len()
    }

    /// Reset all test data
    pub fn reset(&self) {
        self.users.lock().unwrap().clear();
        self.posts.lock().unwrap().clear();
    }
}

impl Default for TestFactory {
    fn default() -> Self {
        Self::new()
    }
}

/// ValidationHelper provides common validation assertions
pub struct ValidationHelper;

impl ValidationHelper {
    /// Validate UUID format
    pub fn assert_uuid(value: &str) -> Result<(), String> {
        match Uuid::parse_str(value) {
            Ok(_) => Ok(()),
            Err(e) => Err(format!("Invalid UUID: {} - {}", value, e)),
        }
    }

    /// Validate string is not empty
    pub fn assert_not_empty(value: &str, name: &str) -> Result<(), String> {
        if value.is_empty() {
            Err(format!("{} should not be empty", name))
        } else {
            Ok(())
        }
    }

    /// Validate option is not none
    pub fn assert_is_some<T>(value: &Option<T>, name: &str) -> Result<(), String> {
        if value.is_none() {
            Err(format!("{} should not be None", name))
        } else {
            Ok(())
        }
    }

    /// Validate option is none
    pub fn assert_is_none<T>(value: &Option<T>, name: &str) -> Result<(), String> {
        if value.is_some() {
            Err(format!("{} should be None", name))
        } else {
            Ok(())
        }
    }

    /// Validate equality
    pub fn assert_equal<T: PartialEq + std::fmt::Debug>(
        expected: &T,
        actual: &T,
        name: &str,
    ) -> Result<(), String> {
        if expected != actual {
            Err(format!(
                "{} mismatch: expected {:?}, got {:?}",
                name, expected, actual
            ))
        } else {
            Ok(())
        }
    }
}

/// GraphQLTestHelper provides GraphQL-specific testing utilities
pub struct GraphQLTestHelper;

impl GraphQLTestHelper {
    /// Check if query has errors
    pub fn has_errors(response: &str) -> bool {
        response.contains("\"errors\"") || response.contains("error")
    }

    /// Extract error message
    pub fn extract_error_message(response: &str) -> Option<String> {
        if let Some(start) = response.find("\"message\"") {
            if let Some(quote_start) = response[start + 10..].find('\"') {
                if let Some(quote_end) = response[start + 10 + quote_start + 1..].find('\"') {
                    let msg_start = start + 10 + quote_start + 1;
                    let msg_end = msg_start + quote_end;
                    return Some(response[msg_start..msg_end].to_string());
                }
            }
        }
        None
    }
}

/// DataGenerator provides test data generation utilities
pub struct DataGenerator;

impl DataGenerator {
    /// Generate a string of specified length
    pub fn generate_long_string(length: usize) -> String {
        let mut result = String::with_capacity(length);
        for i in 0..length {
            result.push_str(&(i % 10).to_string());
        }
        result
    }

    /// Generate unique strings
    pub fn generate_unique_strings(count: usize) -> Vec<String> {
        (0..count)
            .map(|_| Uuid::new_v4().to_string())
            .collect()
    }

    /// Generate test users
    pub fn generate_users(factory: &TestFactory, count: usize) -> Vec<TestUser> {
        (0..count)
            .map(|i| {
                factory.create_test_user(
                    &format!("user{}", i),
                    &format!("user{}@example.com", i),
                    &format!("User {}", i),
                    "",
                )
            })
            .collect()
    }
}
