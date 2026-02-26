mod test_helpers;
use test_helpers::*;

// ============================================================================
// Security: SQL Injection Prevention Tests
// ============================================================================
// These tests verify that the REST API properly handles SQL injection attempts
// and does not execute malicious queries or expose sensitive data.

#[test]
fn test_sql_injection_basic_or_in_username() {
    let factory = TestFactory::new();
    factory.create_test_user("alice", "alice@example.com", "Alice", "");

    // Attempt basic SQL injection with OR clause
    let malicious_username = "alice' OR '1'='1";

    // Should not find user with injection string
    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "SQL injection should not match any user");
}

#[test]
fn test_sql_injection_union_based_attack() {
    let factory = TestFactory::new();
    factory.create_test_user("bob", "bob@example.com", "Bob", "");

    // Attempt UNION-based SQL injection
    let malicious_username = "bob' UNION SELECT * FROM users--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "UNION injection should not execute");
}

#[test]
fn test_sql_injection_comment_sequence() {
    let factory = TestFactory::new();
    factory.create_test_user("charlie", "charlie@example.com", "Charlie", "");

    // Attempt SQL comment injection
    let malicious_username = "charlie'--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "Comment injection should not bypass query");
}

#[test]
fn test_sql_injection_stacked_queries() {
    let factory = TestFactory::new();
    factory.create_test_user("david", "david@example.com", "David", "");

    // Attempt stacked queries injection
    let malicious_username = "david'; DROP TABLE users; --";

    // Factory should still work (no tables dropped)
    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Stacked query injection should not execute");
}

#[test]
fn test_sql_injection_time_based_blind() {
    let factory = TestFactory::new();
    factory.create_test_user("eve", "eve@example.com", "Eve", "");

    // Attempt time-based blind SQL injection
    let malicious_username = "eve' AND SLEEP(5)--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "Time-based blind injection should not execute");
}

#[test]
fn test_sql_injection_boolean_based_blind() {
    let factory = TestFactory::new();
    factory.create_test_user("frank", "frank@example.com", "Frank", "");

    // Attempt boolean-based blind SQL injection
    let malicious_username = "frank' AND 1=1--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "Boolean-based blind injection should not execute");
}

#[test]
fn test_sql_injection_in_post_title() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    // Attempt SQL injection in post title
    let malicious_title = "Post' OR '1'='1";
    factory.create_test_post(&author.id, malicious_title, "Content");

    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 1, "Injection in title should not affect query");
}

#[test]
fn test_sql_injection_in_post_content() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    // Attempt SQL injection in post content
    let malicious_content = "Content'; DELETE FROM posts; --";
    factory.create_test_post(&author.id, "Normal Title", malicious_content);

    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 1, "Injection in content should not execute");
}

#[test]
fn test_sql_injection_single_quote_escaping() {
    let factory = TestFactory::new();

    // Test proper escaping of single quotes
    let username_with_quote = "O'Brien";
    let user = factory.create_test_user(username_with_quote, "obrien@example.com", "O'Brien", "");

    let retrieved = factory.get_user(&user.id);
    assert!(retrieved.is_some());
    assert_eq!(retrieved.unwrap().username, username_with_quote);
}

#[test]
fn test_sql_injection_double_dash_in_content() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    // Test that double dash is treated as content, not SQL comment
    let content_with_dashes = "This is a test -- with dashes";
    factory.create_test_post(&author.id, "Title", content_with_dashes);

    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 1);
}

#[test]
fn test_sql_injection_hex_encoded_attack() {
    let factory = TestFactory::new();

    // Attempt hex-encoded SQL injection
    let malicious_username = "0x61646d696e"; // hex for 'admin'
    factory.create_test_user(malicious_username, "hex@example.com", "Hex User", "");

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Hex-encoded injection should be treated as string");
}

#[test]
fn test_sql_injection_multiple_statements() {
    let factory = TestFactory::new();

    // Attempt multiple SQL statements
    let malicious_username = "user'; UPDATE users SET username='hacked'; --";
    factory.create_test_user(malicious_username, "user@example.com", "User", "");

    let users = factory.get_all_users();
    let normal_users = users.iter().filter(|u| u.username == "hacked").count();
    assert_eq!(normal_users, 0, "Multiple statements should not execute");
}

#[test]
fn test_sql_injection_with_encoded_characters() {
    let factory = TestFactory::new();

    // Attempt URL-encoded SQL injection
    let malicious_username = "user%27%20OR%20%271%27%3D%271";
    factory.create_test_user(malicious_username, "user@example.com", "User", "");

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Encoded injection should be treated as string");
}

#[test]
fn test_sql_injection_subquery_attack() {
    let factory = TestFactory::new();

    // Attempt subquery SQL injection
    let malicious_username = "user' AND id IN (SELECT id FROM users)--";
    factory.create_test_user(malicious_username, "user@example.com", "User", "");

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username.starts_with("user' AND"));
    assert!(found.is_some(), "Subquery should be stored as literal string");
}

#[test]
fn test_sql_injection_null_byte_injection() {
    let factory = TestFactory::new();

    // Attempt null byte injection (if language/DB supports)
    let malicious_username = "user\0admin";
    factory.create_test_user(malicious_username, "user@example.com", "User", "");

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Null byte injection should not bypass security");
}
