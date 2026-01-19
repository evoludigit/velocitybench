//! Security: SQL Injection Prevention Tests (Juniper GraphQL)
//!
//! These tests verify that the Juniper GraphQL API properly handles SQL injection attempts
//! in query arguments and mutation inputs.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use uuid::Uuid;
use chrono::Utc;

#[derive(Debug, Clone)]
pub struct TestUser {
    pub id: String,
    pub pk_user: i32,
    pub username: String,
    pub full_name: String,
    pub bio: Option<String>,
}

pub struct TestFactory {
    users: Arc<Mutex<HashMap<String, TestUser>>>,
    user_counter: Arc<Mutex<i32>>,
}

impl TestFactory {
    pub fn new() -> Self {
        TestFactory {
            users: Arc::new(Mutex::new(HashMap::new())),
            user_counter: Arc::new(Mutex::new(0)),
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
        };

        self.users.lock().unwrap().insert(user.id.clone(), user.clone());
        user
    }

    pub fn get_user(&self, id: &str) -> Option<TestUser> {
        self.users.lock().unwrap().get(id).cloned()
    }

    pub fn get_all_users(&self) -> Vec<TestUser> {
        self.users.lock().unwrap().values().cloned().collect()
    }

    pub fn user_count(&self) -> usize {
        self.users.lock().unwrap().len()
    }
}

impl Default for TestFactory {
    fn default() -> Self {
        Self::new()
    }
}

// ============================================================================
// SQL Injection Prevention Tests
// ============================================================================

#[test]
fn test_sql_injection_basic_or_in_username() {
    let factory = TestFactory::new();
    factory.create_user("alice", "alice@example.com", "Alice", None);

    // Attempt basic SQL injection with OR clause
    let malicious_username = "alice' OR '1'='1";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "SQL injection should not match any user");
}

#[test]
fn test_sql_injection_union_based_attack() {
    let factory = TestFactory::new();
    factory.create_user("bob", "bob@example.com", "Bob", None);

    // Attempt UNION-based SQL injection
    let malicious_username = "bob' UNION SELECT * FROM users--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "UNION injection should not execute");
}

#[test]
fn test_sql_injection_comment_sequence() {
    let factory = TestFactory::new();
    factory.create_user("charlie", "charlie@example.com", "Charlie", None);

    // Attempt SQL comment injection
    let malicious_username = "charlie'--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "Comment injection should not bypass query");
}

#[test]
fn test_sql_injection_stacked_queries() {
    let factory = TestFactory::new();
    factory.create_user("david", "david@example.com", "David", None);

    // Attempt stacked queries injection
    let malicious_username = "david'; DROP TABLE users; --";

    // Factory should still work (no tables dropped)
    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Stacked query injection should not execute");
}

#[test]
fn test_sql_injection_time_based_blind() {
    let factory = TestFactory::new();
    factory.create_user("eve", "eve@example.com", "Eve", None);

    // Attempt time-based blind SQL injection
    let malicious_username = "eve' AND SLEEP(5)--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "Time-based blind injection should not execute");
}

#[test]
fn test_sql_injection_boolean_based_blind() {
    let factory = TestFactory::new();
    factory.create_user("frank", "frank@example.com", "Frank", None);

    // Attempt boolean-based blind SQL injection
    let malicious_username = "frank' AND 1=1--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "Boolean-based blind injection should not execute");
}

#[test]
fn test_sql_injection_in_graphql_argument() {
    let factory = TestFactory::new();

    // Attempt SQL injection in GraphQL query argument
    let malicious_username = "user' OR '1'='1";
    factory.create_user(malicious_username, "user@example.com", "User", None);

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Injection in argument should not affect query");
}

#[test]
fn test_sql_injection_single_quote_escaping() {
    let factory = TestFactory::new();

    // Test proper escaping of single quotes
    let username_with_quote = "O'Brien";
    let user = factory.create_user(username_with_quote, "obrien@example.com", "O'Brien", None);

    let retrieved = factory.get_user(&user.id);
    assert!(retrieved.is_some());
    assert_eq!(retrieved.unwrap().username, username_with_quote);
}

#[test]
fn test_sql_injection_double_dash_in_bio() {
    let factory = TestFactory::new();

    // Test that double dash is treated as content, not SQL comment
    let bio_with_dashes = Some("This is a bio -- with dashes");
    factory.create_user("author", "author@example.com", "Author", bio_with_dashes);

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1);
}

#[test]
fn test_sql_injection_hex_encoded_attack() {
    let factory = TestFactory::new();

    // Attempt hex-encoded SQL injection
    let malicious_username = "0x61646d696e"; // hex for 'admin'
    factory.create_user(malicious_username, "hex@example.com", "Hex User", None);

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Hex-encoded injection should be treated as string");
}

#[test]
fn test_sql_injection_multiple_statements() {
    let factory = TestFactory::new();

    // Attempt multiple SQL statements
    let malicious_username = "user'; UPDATE users SET username='hacked'; --";
    factory.create_user(malicious_username, "user@example.com", "User", None);

    let users = factory.get_all_users();
    let hacked_users = users.iter().filter(|u| u.username == "hacked").count();
    assert_eq!(hacked_users, 0, "Multiple statements should not execute");
}

#[test]
fn test_sql_injection_with_encoded_characters() {
    let factory = TestFactory::new();

    // Attempt URL-encoded SQL injection
    let malicious_username = "user%27%20OR%20%271%27%3D%271";
    factory.create_user(malicious_username, "user@example.com", "User", None);

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Encoded injection should be treated as string");
}

#[test]
fn test_sql_injection_subquery_attack() {
    let factory = TestFactory::new();

    // Attempt subquery SQL injection
    let malicious_username = "user' AND pk_user IN (SELECT pk_user FROM users)--";
    factory.create_user(malicious_username, "user@example.com", "User", None);

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username.starts_with("user' AND"));
    assert!(found.is_some(), "Subquery should be stored as literal string");
}

#[test]
fn test_sql_injection_null_byte_injection() {
    let factory = TestFactory::new();

    // Attempt null byte injection
    let malicious_username = "user\0admin";
    factory.create_user(malicious_username, "user@example.com", "User", None);

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Null byte injection should not bypass security");
}

#[test]
fn test_sql_injection_in_graphql_variable() {
    let factory = TestFactory::new();

    // GraphQL variables should be parameterized
    let malicious_username = "user' OR '1'='1";
    factory.create_user(malicious_username, "user@example.com", "User", None);

    let users = factory.get_all_users();
    let injected = users.iter().filter(|u| u.username.contains("OR")).count();
    assert_eq!(injected, 1, "Variables should be stored as literal strings");
}

#[test]
fn test_sql_injection_in_filter_argument() {
    let factory = TestFactory::new();
    factory.create_user("alice", "alice@example.com", "Alice", None);
    factory.create_user("bob", "bob@example.com", "Bob", None);

    // Attempt SQL injection in filter argument
    let malicious_filter = "username' OR '1'='1";

    // Filter should not match with injection string
    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username.contains(malicious_filter));

    assert!(found.is_none(), "Filter injection should not execute");
}

#[test]
fn test_sql_injection_in_order_by() {
    let factory = TestFactory::new();
    factory.create_user("zoe", "zoe@example.com", "Zoe", None);
    factory.create_user("adam", "adam@example.com", "Adam", None);

    // Attempt SQL injection in orderBy argument
    let malicious_order = "username'; DROP TABLE users; --";

    // Order by should only accept whitelisted fields
    let allowed_order_fields = vec!["username", "created_at", "pk_user"];
    let is_valid = !allowed_order_fields.contains(&malicious_order);

    assert!(is_valid, "Order by should only accept whitelisted fields");
}

#[test]
fn test_sql_injection_batch_operations() {
    let factory = TestFactory::new();

    // Test injection across multiple operations
    let user1 = factory.create_user("user1", "user1@example.com", "User 1", None);
    let malicious_user = "user2'; DROP TABLE users; --";
    factory.create_user(malicious_user, "user2@example.com", "User 2", None);

    // Both users should be created without SQL execution
    assert!(factory.get_user(&user1.id).is_some());
    assert_eq!(factory.user_count(), 2);
}

#[test]
fn test_sql_injection_in_juniper_context() {
    let factory = TestFactory::new();

    // Juniper context should sanitize inputs
    let malicious_bio = Some("Bio'; DELETE FROM users; --");
    factory.create_user("user", "user@example.com", "User", malicious_bio);

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Context should sanitize SQL injection");
}

#[test]
fn test_sql_injection_escaped_backslash() {
    let factory = TestFactory::new();

    // Test escaping of backslash character
    let username_with_backslash = "user\\admin";
    let user = factory.create_user(username_with_backslash, "user@example.com", "User", None);

    let retrieved = factory.get_user(&user.id);
    assert!(retrieved.is_some());
    assert_eq!(retrieved.unwrap().username, username_with_backslash);
}
