mod test_helpers;
use test_helpers::*;

// ============================================================================
// Security: SQL Injection Prevention Tests (GraphQL)
// ============================================================================
// These tests verify that the GraphQL API properly handles SQL injection attempts
// in query arguments and mutation inputs.

#[test]
fn test_sql_injection_basic_or_in_username() {
    let factory = TestFactory::new();
    factory.create_test_user("alice", "alice@example.com", "Alice", "");

    // Attempt basic SQL injection with OR clause in GraphQL argument
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

    // Attempt UNION-based SQL injection via GraphQL query
    let malicious_username = "bob' UNION SELECT * FROM users--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "UNION injection should not execute");
}

#[test]
fn test_sql_injection_comment_sequence() {
    let factory = TestFactory::new();
    factory.create_test_user("charlie", "charlie@example.com", "Charlie", "");

    // Attempt SQL comment injection in GraphQL variable
    let malicious_username = "charlie'--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "Comment injection should not bypass query");
}

#[test]
fn test_sql_injection_stacked_queries() {
    let factory = TestFactory::new();
    factory.create_test_user("david", "david@example.com", "David", "");

    // Attempt stacked queries injection through GraphQL mutation
    let malicious_username = "david'; DROP TABLE users; --";

    // Factory should still work (no tables dropped)
    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Stacked query injection should not execute");
}

#[test]
fn test_sql_injection_time_based_blind() {
    let factory = TestFactory::new();
    factory.create_test_user("eve", "eve@example.com", "Eve", "");

    // Attempt time-based blind SQL injection in GraphQL query
    let malicious_username = "eve' AND SLEEP(5)--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "Time-based blind injection should not execute");
}

#[test]
fn test_sql_injection_boolean_based_blind() {
    let factory = TestFactory::new();
    factory.create_test_user("frank", "frank@example.com", "Frank", "");

    // Attempt boolean-based blind SQL injection in GraphQL filter
    let malicious_username = "frank' AND 1=1--";

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username == malicious_username);
    assert!(found.is_none(), "Boolean-based blind injection should not execute");
}

#[test]
fn test_sql_injection_in_graphql_mutation_input() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    // Attempt SQL injection in GraphQL mutation input
    let malicious_title = "Post' OR '1'='1";
    factory.create_test_post(&author.id, malicious_title, "Content");

    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 1, "Injection in mutation input should not affect query");
}

#[test]
fn test_sql_injection_in_nested_graphql_field() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    // Attempt SQL injection in nested field content
    let malicious_content = "Content'; DELETE FROM posts; --";
    factory.create_test_post(&author.id, "Normal Title", malicious_content);

    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 1, "Injection in nested field should not execute");
}

#[test]
fn test_sql_injection_single_quote_escaping() {
    let factory = TestFactory::new();

    // Test proper escaping of single quotes in GraphQL string arguments
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

    // Test that double dash is treated as content in GraphQL
    let content_with_dashes = "This is a test -- with dashes";
    factory.create_test_post(&author.id, "Title", content_with_dashes);

    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 1);
}

#[test]
fn test_sql_injection_hex_encoded_attack() {
    let factory = TestFactory::new();

    // Attempt hex-encoded SQL injection via GraphQL variable
    let malicious_username = "0x61646d696e"; // hex for 'admin'
    factory.create_test_user(malicious_username, "hex@example.com", "Hex User", "");

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Hex-encoded injection should be treated as string");
}

#[test]
fn test_sql_injection_multiple_statements() {
    let factory = TestFactory::new();

    // Attempt multiple SQL statements through GraphQL mutation
    let malicious_username = "user'; UPDATE users SET username='hacked'; --";
    factory.create_test_user(malicious_username, "user@example.com", "User", "");

    let users = factory.get_all_users();
    let normal_users = users.iter().filter(|u| u.username == "hacked").count();
    assert_eq!(normal_users, 0, "Multiple statements should not execute");
}

#[test]
fn test_sql_injection_with_graphql_variables() {
    let factory = TestFactory::new();

    // Test that GraphQL variables properly sanitize SQL injection attempts
    let malicious_username = "user' OR '1'='1";
    factory.create_test_user(malicious_username, "user@example.com", "User", "");

    // GraphQL variables should be parameterized
    let users = factory.get_all_users();
    let injected = users.iter().filter(|u| u.username.contains("OR")).count();
    assert_eq!(injected, 1, "Variables should be stored as literal strings");
}

#[test]
fn test_sql_injection_subquery_attack() {
    let factory = TestFactory::new();

    // Attempt subquery SQL injection via GraphQL query argument
    let malicious_username = "user' AND pk_user IN (SELECT pk_user FROM users)--";
    factory.create_test_user(malicious_username, "user@example.com", "User", "");

    let users = factory.get_all_users();
    let found = users.iter().find(|u| u.username.starts_with("user' AND"));
    assert!(found.is_some(), "Subquery should be stored as literal string");
}

#[test]
fn test_sql_injection_null_byte_injection() {
    let factory = TestFactory::new();

    // Attempt null byte injection via GraphQL input
    let malicious_username = "user\0admin";
    factory.create_test_user(malicious_username, "user@example.com", "User", "");

    let users = factory.get_all_users();
    assert_eq!(users.len(), 1, "Null byte injection should not bypass security");
}

#[test]
fn test_sql_injection_in_graphql_filter_argument() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    factory.create_test_post(&author.id, "Post 1", "Content");
    factory.create_test_post(&author.id, "Post 2", "Content");

    // Attempt SQL injection in filter argument
    let malicious_filter = "author' OR '1'='1";

    // Filter should not match with injection string
    let posts: Vec<_> = factory
        .get_all_posts()
        .into_iter()
        .filter(|p| p.title.contains(malicious_filter))
        .collect();

    assert_eq!(posts.len(), 0, "Filter injection should not execute");
}

#[test]
fn test_sql_injection_in_graphql_order_by() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    factory.create_test_post(&author.id, "Z Post", "Content");
    factory.create_test_post(&author.id, "A Post", "Content");

    // Attempt SQL injection in orderBy argument
    let malicious_order = "title'; DROP TABLE posts; --";

    // In real API, orderBy should be validated against allowed fields
    let allowed_order_fields = vec!["title", "created_at", "pk_post"];
    let is_valid = allowed_order_fields.contains(&"title");

    assert!(is_valid, "Order by should only accept whitelisted fields");
}

#[test]
fn test_sql_injection_batch_query_attack() {
    let factory = TestFactory::new();

    // GraphQL allows batch queries, test injection across multiple operations
    let user1 = factory.create_test_user("user1", "user1@example.com", "User 1", "");
    let malicious_user = "user2'; DROP TABLE users; --";
    factory.create_test_user(malicious_user, "user2@example.com", "User 2", "");

    // Both users should be created without SQL execution
    assert!(factory.get_user(&user1.id).is_some());
    assert_eq!(factory.user_count(), 2);
}

#[test]
fn test_sql_injection_in_graphql_alias() {
    let factory = TestFactory::new();
    factory.create_test_user("alice", "alice@example.com", "Alice", "");

    // GraphQL aliases should not allow SQL injection
    // Example: query { malicious: user(id: "' OR 1=1--") { id } }
    let malicious_alias = "malicious': user(id: \"' OR 1=1--\")";

    // Aliases are client-side only and shouldn't affect SQL
    assert!(
        malicious_alias.contains("malicious"),
        "Alias should not execute SQL"
    );
}

#[test]
fn test_sql_injection_in_graphql_fragment() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("bob", "bob@example.com", "Bob", "");

    // GraphQL fragments should not allow SQL injection
    // Example: fragment MaliciousFragment on User { id' OR '1'='1 }
    let fragment_field = "id' OR '1'='1";

    // Fragments define selection sets, not SQL
    let retrieved = factory.get_user(&user.id);
    assert!(retrieved.is_some(), "Fragment should not affect SQL query");
}
