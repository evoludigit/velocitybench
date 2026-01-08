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
    pub username: String,
    pub full_name: String,
    pub bio: Option<String>,
}

#[derive(Clone, Debug)]
pub struct TestPost {
    pub id: String,
    pub title: String,
    pub content: Option<String>,
    pub author_id: String,
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
        let bio = if bio.is_empty() { None } else { Some(bio.to_string()) };

        let user = TestUser {
            id: id.clone(),
            username: username.to_string(),
            full_name: full_name.to_string(),
            bio,
        };

        self.users.lock().unwrap().insert(id, user.clone());
        user
    }

    /// Create a test post
    pub fn create_test_post(&self, author_id: &str, title: &str, content: &str) -> TestPost {
        let id = Uuid::new_v4().to_string();
        let content = if content.is_empty() {
            None
        } else {
            Some(content.to_string())
        };

        let post = TestPost {
            id: id.clone(),
            title: title.to_string(),
            content,
            author_id: author_id.to_string(),
            created_at: Utc::now().to_rfc3339(),
        };

        self.posts.lock().unwrap().insert(id, post.clone());
        post
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

/// HTTPTestHelper provides HTTP/REST-specific testing utilities
pub struct HTTPTestHelper;

impl HTTPTestHelper {
    /// Validate HTTP status code
    pub fn assert_status_code(expected: u16, actual: u16) -> Result<(), String> {
        if expected != actual {
            Err(format!("Expected status code {}, got {}", expected, actual))
        } else {
            Ok(())
        }
    }

    /// Validate content type
    pub fn assert_content_type(expected: &str, actual: &str) -> Result<(), String> {
        if expected != actual {
            Err(format!("Expected content type {}, got {}", expected, actual))
        } else {
            Ok(())
        }
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
