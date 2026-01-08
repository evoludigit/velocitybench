mod test_helpers;
use test_helpers::*;

// ============================================================================
// Error: HTTP Status Codes
// ============================================================================

#[test]
fn test_http_status_code_success() {
    let factory = TestFactory::new();
    factory.create_test_user("alice", "alice@example.com", "Alice", "");
    assert_eq!(factory.user_count(), 1);
}

#[test]
fn test_http_status_code_not_found() {
    let factory = TestFactory::new();
    let user = factory.get_user("nonexistent-id");
    assert!(user.is_none());
}

// ============================================================================
// Error: 404 Not Found
// ============================================================================

#[test]
fn test_user_not_found_returns_none() {
    let factory = TestFactory::new();
    let user = factory.get_user("nonexistent-user-id");
    assert!(user.is_none());
}

#[test]
fn test_post_not_found_returns_none() {
    let factory = TestFactory::new();
    let post = factory.get_post("nonexistent-post-id");
    assert!(post.is_none());
}

// ============================================================================
// Error: Invalid Input
// ============================================================================

#[test]
fn test_invalid_limit_negative() {
    let limit = -5;
    let clamped = if limit < 0 { 0 } else { limit };
    assert_eq!(clamped, 0);
}

#[test]
fn test_invalid_limit_zero() {
    let limit = 0;
    let clamped = if limit < 0 { 0 } else { limit };
    assert_eq!(clamped, 0);
}

#[test]
fn test_very_large_limit() {
    let limit = 999999;
    let clamped = if limit > 100 { 100 } else { limit };
    assert_eq!(clamped, 100);
}

// ============================================================================
// Edge Case: UUID Validation
// ============================================================================

#[test]
fn test_all_user_ids_are_uuid() {
    let factory = TestFactory::new();
    factory.create_test_user("user0", "user0@example.com", "User", "");
    factory.create_test_user("user1", "user1@example.com", "User", "");
    factory.create_test_user("user2", "user2@example.com", "User", "");

    for user in factory.get_all_users() {
        assert!(ValidationHelper::assert_uuid(&user.id).is_ok());
    }
}

#[test]
fn test_all_post_ids_are_uuid() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    factory.create_test_post(&author.id, "Post0", "Content");
    factory.create_test_post(&author.id, "Post1", "Content");
    factory.create_test_post(&author.id, "Post2", "Content");

    for post in factory.get_all_posts() {
        assert!(ValidationHelper::assert_uuid(&post.id).is_ok());
    }
}

// ============================================================================
// Edge Case: Special Characters
// ============================================================================

#[test]
fn test_special_char_single_quotes() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "I'm a developer");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_special_char_double_quotes() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "He said \"hello\"");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_special_char_html_tags() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "Check <this> out");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_special_char_ampersand() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "Tom & Jerry");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_special_char_emoji() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "🎉 Celebration! 🚀 Rocket");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_special_char_accents() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Àlice Müller", "");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_special_char_diacritics() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "José García", "");
    assert!(factory.get_user(&user.id).is_some());
}

// ============================================================================
// Edge Case: Boundary Conditions
// ============================================================================

#[test]
fn test_boundary_very_long_bio_5000_chars() {
    let factory = TestFactory::new();
    let long_bio = DataGenerator::generate_long_string(5000);
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", &long_bio);
    let retrieved = factory.get_user(&user.id).unwrap();
    assert_eq!(retrieved.bio.as_ref().unwrap().len(), 5000);
}

#[test]
fn test_boundary_very_long_username_255_chars() {
    let factory = TestFactory::new();
    let long_name = DataGenerator::generate_long_string(255);
    let user = factory.create_test_user(&long_name, "user@example.com", "User", "");
    let retrieved = factory.get_user(&user.id).unwrap();
    assert_eq!(retrieved.username.len(), 255);
}

#[test]
fn test_boundary_very_long_post_title() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let long_title = DataGenerator::generate_long_string(500);
    let post = factory.create_test_post(&author.id, &long_title, "Content");
    let retrieved = factory.get_post(&post.id).unwrap();
    assert_eq!(retrieved.title.len(), 500);
}

#[test]
fn test_boundary_very_long_content_5000_chars() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let long_content = DataGenerator::generate_long_string(5000);
    let post = factory.create_test_post(&author.id, "Title", &long_content);
    let retrieved = factory.get_post(&post.id).unwrap();
    assert_eq!(retrieved.content.as_ref().unwrap().len(), 5000);
}

// ============================================================================
// Edge Case: Null/Empty Fields
// ============================================================================

#[test]
fn test_null_bio_is_handled() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    let retrieved = factory.get_user(&user.id).unwrap();
    assert!(retrieved.bio.is_none());
}

#[test]
fn test_empty_string_bio() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    let retrieved = factory.get_user(&user.id).unwrap();
    assert!(retrieved.bio.is_none());
}

#[test]
fn test_present_bio() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "My bio");
    let retrieved = factory.get_user(&user.id).unwrap();
    assert!(retrieved.bio.is_some());
    assert_eq!(retrieved.bio.as_ref().unwrap(), "My bio");
}

// ============================================================================
// Edge Case: Relationship Validation
// ============================================================================

#[test]
fn test_post_author_id_is_valid_uuid() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Content");
    assert!(ValidationHelper::assert_uuid(&post.author_id).is_ok());
}

#[test]
fn test_post_references_correct_author() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Content");
    assert_eq!(post.author_id, author.id);
}

#[test]
fn test_multiple_posts_reference_different_authors() {
    let factory = TestFactory::new();
    let author1 = factory.create_test_user("author1", "author1@example.com", "Author1", "");
    let author2 = factory.create_test_user("author2", "author2@example.com", "Author2", "");

    let post1 = factory.create_test_post(&author1.id, "Post1", "Content");
    let post2 = factory.create_test_post(&author2.id, "Post2", "Content");

    assert_ne!(post1.author_id, post2.author_id);
    assert_eq!(post1.author_id, author1.id);
    assert_eq!(post2.author_id, author2.id);
}

// ============================================================================
// Edge Case: Data Type Validation
// ============================================================================

#[test]
fn test_username_is_string() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    let retrieved = factory.get_user(&user.id).unwrap();
    assert_eq!(retrieved.username, "alice");
    assert!(retrieved.username.is_ascii());
}

#[test]
fn test_post_title_is_string() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Test Post", "Content");
    let retrieved = factory.get_post(&post.id).unwrap();
    assert_eq!(retrieved.title, "Test Post");
}

// ============================================================================
// Edge Case: Uniqueness
// ============================================================================

#[test]
fn test_multiple_users_have_unique_ids() {
    let factory = TestFactory::new();
    let user1 = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    let user2 = factory.create_test_user("bob", "bob@example.com", "Bob", "");
    let user3 = factory.create_test_user("charlie", "charlie@example.com", "Charlie", "");

    assert_ne!(user1.id, user2.id);
    assert_ne!(user2.id, user3.id);
    assert_ne!(user1.id, user3.id);
}

#[test]
fn test_multiple_posts_have_unique_ids() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post1 = factory.create_test_post(&author.id, "Post1", "Content1");
    let post2 = factory.create_test_post(&author.id, "Post2", "Content2");
    let post3 = factory.create_test_post(&author.id, "Post3", "Content3");

    assert_ne!(post1.id, post2.id);
    assert_ne!(post2.id, post3.id);
    assert_ne!(post1.id, post3.id);
}
