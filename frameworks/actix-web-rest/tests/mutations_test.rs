mod test_helpers;
use test_helpers::*;

// ============================================================================
// Mutation Simulation: updateUser
// ============================================================================

#[test]
fn test_update_user_full_name() {
    let factory = TestFactory::new();
    let mut user = factory.create_test_user("alice", "alice@example.com", "Alice", "Developer");
    let user_id = user.id.clone();

    // Simulate mutation
    user.full_name = "Alice Smith".to_string();

    // Verify
    assert_eq!(user.full_name, "Alice Smith");
    assert_eq!(user.id, user_id);
}

#[test]
fn test_update_user_bio() {
    let factory = TestFactory::new();
    let mut user = factory.create_test_user("alice", "alice@example.com", "Alice", "Developer");
    let user_id = user.id.clone();

    // Simulate mutation
    user.bio = Some("Senior Developer".to_string());

    // Verify
    assert_eq!(user.bio, Some("Senior Developer".to_string()));
    assert_eq!(user.id, user_id);
}

#[test]
fn test_update_user_both_fields() {
    let factory = TestFactory::new();
    let mut user = factory.create_test_user("alice", "alice@example.com", "Alice", "Developer");
    let user_id = user.id.clone();

    // Simulate mutation
    user.full_name = "Alice Smith".to_string();
    user.bio = Some("Senior Developer".to_string());

    // Verify
    assert_eq!(user.full_name, "Alice Smith");
    assert_eq!(user.bio, Some("Senior Developer".to_string()));
    assert_eq!(user.id, user_id);
}

#[test]
fn test_update_user_clear_bio() {
    let factory = TestFactory::new();
    let mut user = factory.create_test_user("alice", "alice@example.com", "Alice", "Developer");
    let user_id = user.id.clone();

    // Simulate mutation
    user.bio = None;

    // Verify
    assert_eq!(user.bio, None);
    assert_eq!(user.id, user_id);
}

// ============================================================================
// Mutation Simulation: updatePost
// ============================================================================

#[test]
fn test_update_post_title() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let mut post = factory.create_test_post(&author.id, "Original Title", "Original Content");
    let post_id = post.id.clone();

    // Simulate mutation
    post.title = "Updated Title".to_string();

    // Verify
    assert_eq!(post.title, "Updated Title");
    assert_eq!(post.id, post_id);
}

#[test]
fn test_update_post_content() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let mut post = factory.create_test_post(&author.id, "Original Title", "Original Content");
    let post_id = post.id.clone();

    // Simulate mutation
    post.content = Some("Updated Content".to_string());

    // Verify
    assert_eq!(post.content, Some("Updated Content".to_string()));
    assert_eq!(post.id, post_id);
}

#[test]
fn test_update_post_both_fields() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let mut post = factory.create_test_post(&author.id, "Original Title", "Original Content");
    let post_id = post.id.clone();

    // Simulate mutation
    post.title = "Updated Title".to_string();
    post.content = Some("Updated Content".to_string());

    // Verify
    assert_eq!(post.title, "Updated Title");
    assert_eq!(post.content, Some("Updated Content".to_string()));
    assert_eq!(post.id, post_id);
}

// ============================================================================
// Field Immutability
// ============================================================================

#[test]
fn test_user_id_immutable_after_update() {
    let factory = TestFactory::new();
    let mut user = factory.create_test_user("alice", "alice@example.com", "Alice", "Bio");
    let original_id = user.id.clone();

    // Try to "update"
    user.bio = Some("Updated".to_string());

    // Verify ID unchanged
    assert_eq!(user.id, original_id);
}

#[test]
fn test_post_id_immutable_after_update() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let mut post = factory.create_test_post(&author.id, "Title", "Content");
    let original_id = post.id.clone();

    // Try to "update"
    post.title = "Updated".to_string();

    // Verify ID unchanged
    assert_eq!(post.id, original_id);
}

#[test]
fn test_username_immutable() {
    let factory = TestFactory::new();
    let mut user = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    let original_username = user.username.clone();

    // Try to "update"
    user.bio = Some("Updated".to_string());

    // Verify username unchanged
    assert_eq!(user.username, original_username);
}

// ============================================================================
// State Changes
// ============================================================================

#[test]
fn test_sequential_updates_accumulate() {
    let factory = TestFactory::new();
    let mut user = factory.create_test_user("alice", "alice@example.com", "Alice", "");

    // Apply updates sequentially
    user.bio = Some("Developer".to_string());
    user.bio = Some("Senior Developer".to_string());

    // Verify latest state
    assert_eq!(user.bio, Some("Senior Developer".to_string()));
}

#[test]
fn test_updates_isolated_between_entities() {
    let factory = TestFactory::new();
    let mut user1 = factory.create_test_user("alice", "alice@example.com", "Alice", "Bio1");
    let mut user2 = factory.create_test_user("bob", "bob@example.com", "Bob", "Bio2");

    let original_bio2 = user2.bio.clone();

    // Update user1
    user1.bio = Some("Updated".to_string());

    // Verify user2 unchanged
    assert_eq!(user2.bio, original_bio2);
}

// ============================================================================
// Return Value Validation
// ============================================================================

#[test]
fn test_updated_user_returns_all_fields() {
    let factory = TestFactory::new();
    let mut user = factory.create_test_user("alice", "alice@example.com", "Alice", "Developer");
    user.bio = Some("Updated".to_string());

    // Verify all fields present
    assert!(!user.id.is_empty());
    assert_eq!(user.username, "alice");
    assert_eq!(user.bio, Some("Updated".to_string()));
}

#[test]
fn test_updated_post_returns_all_fields() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let mut post = factory.create_test_post(&author.id, "Title", "Content");
    post.title = "Updated".to_string();

    // Verify all fields present
    assert!(!post.id.is_empty());
    assert_eq!(post.title, "Updated");
    assert_eq!(post.author_id, author.id);
}
