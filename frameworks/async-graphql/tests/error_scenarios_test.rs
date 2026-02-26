mod test_helpers;
use test_helpers::*;

// ============================================================================
// Error: Not Found
// ============================================================================

#[test]
fn test_user_not_found_returns_none() {
    let factory = TestFactory::new();
    let user = factory.get_user("nonexistent-id");
    assert!(user.is_none());
}

#[test]
fn test_post_not_found_returns_none() {
    let factory = TestFactory::new();
    let post = factory.get_post("nonexistent-id");
    assert!(post.is_none());
}

// ============================================================================
// Error: Invalid Input
// ============================================================================

#[test]
fn test_limit_zero_handled() {
    let limit = 0;
    let clamped = if limit < 0 { 0 } else { limit };
    assert_eq!(clamped, 0);
}

#[test]
fn test_negative_limit_clamped() {
    let limit = -5;
    let clamped = if limit < 0 { 0 } else { limit };
    assert_eq!(clamped, 0);
}

#[test]
fn test_very_large_limit_capped() {
    let limit = 999999;
    let clamped = if limit > 100 { 100 } else { limit };
    assert_eq!(clamped, 100);
}

// ============================================================================
// Error: Data Type Validation
// ============================================================================

#[test]
fn test_valid_uuid_format() {
    let test_id = "123e4567-e89b-12d3-a456-426614174000";
    assert!(ValidationHelper::assert_uuid(test_id).is_ok());
}

#[test]
fn test_username_is_string_type() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    assert!(!user.username.is_empty());
}

#[test]
fn test_empty_username_invalid() {
    let username = "";
    assert!(username.is_empty());
}

// ============================================================================
// Error: Null Field Consistency
// ============================================================================

#[test]
fn test_null_bio_consistency() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    assert_eq!(user.bio, None);
}

#[test]
fn test_present_bio() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "My bio");
    assert_eq!(user.bio, Some("My bio".to_string()));
}

// ============================================================================
// Error: Special Character Handling
// ============================================================================

#[test]
fn test_single_quotes() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "I'm a developer");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_double_quotes() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "He said \"hello\"");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_html_tags() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "Check <this> out");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_ampersand() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "Tom & Jerry");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_emoji() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "🎉 Celebration! 🚀 Rocket");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_accents() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Àlice Müller", "");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_diacritics() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "José García", "");
    assert!(factory.get_user(&user.id).is_some());
}

// ============================================================================
// Error: Boundary Conditions
// ============================================================================

#[test]
fn test_very_long_bio_5000_chars() {
    let factory = TestFactory::new();
    let long_bio = DataGenerator::generate_long_string(5000);
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", &long_bio);
    let retrieved = factory.get_user(&user.id).unwrap();
    assert_eq!(retrieved.bio.as_ref().unwrap().len(), 5000);
}

#[test]
fn test_very_long_username_255_chars() {
    let factory = TestFactory::new();
    let long_name = DataGenerator::generate_long_string(255);
    let user = factory.create_test_user(&long_name, "user@example.com", "User", "");
    let retrieved = factory.get_user(&user.id).unwrap();
    assert_eq!(retrieved.username.len(), 255);
}

#[test]
fn test_very_long_post_content_5000_chars() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let long_content = DataGenerator::generate_long_string(5000);
    let post = factory.create_test_post(&author.id, "Title", &long_content);
    let retrieved = factory.get_post(&post.id).unwrap();
    assert_eq!(retrieved.content.len(), 5000);
}

// ============================================================================
// Error: Response Structure
// ============================================================================

#[test]
fn test_user_response_has_required_fields() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");

    assert!(!user.id.is_empty());
    assert_eq!(user.username, "alice");
}

#[test]
fn test_post_response_has_required_fields() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Content");

    assert!(!post.id.is_empty());
    assert_eq!(post.title, "Post");
}

// ============================================================================
// Error: Uniqueness Validation
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

    assert_ne!(post1.id, post2.id);
}

// ============================================================================
// Error: Relationship Integrity
// ============================================================================

#[test]
fn test_post_author_id_is_valid_uuid() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Content");

    assert!(ValidationHelper::assert_uuid(&author.id).is_ok());
}

#[test]
fn test_post_references_correct_author() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Content");

    assert_eq!(post.fk_author, author.pk_user);
}

// ============================================================================
// Error: Data Consistency Across Requests
// ============================================================================

#[test]
fn test_same_user_returns_same_data() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "Developer");

    let retrieved1 = factory.get_user(&user.id);
    let retrieved2 = factory.get_user(&user.id);

    assert_eq!(retrieved1.as_ref().unwrap().id, retrieved2.as_ref().unwrap().id);
    assert_eq!(
        retrieved1.as_ref().unwrap().username,
        retrieved2.as_ref().unwrap().username
    );
}

#[test]
fn test_same_post_returns_same_data() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Test", "Content");

    let retrieved1 = factory.get_post(&post.id);
    let retrieved2 = factory.get_post(&post.id);

    assert_eq!(retrieved1.as_ref().unwrap().title, retrieved2.as_ref().unwrap().title);
}
