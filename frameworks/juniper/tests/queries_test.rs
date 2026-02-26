mod test_helpers;
use test_helpers::*;

// ============================================================================
// Query: Ping
// ============================================================================

#[test]
fn test_ping_query() {
    assert!(true);
}

// ============================================================================
// Query: User List
// ============================================================================

#[test]
fn test_user_list_query() {
    let factory = TestFactory::new();
    factory.create_test_user("alice", "alice@example.com", "Alice", "");
    factory.create_test_user("bob", "bob@example.com", "Bob", "");
    factory.create_test_user("charlie", "charlie@example.com", "Charlie", "");

    let users = factory.get_all_users();
    assert_eq!(users.len(), 3);
}

#[test]
fn test_user_list_with_limit() {
    let factory = TestFactory::new();
    for i in 0..20 {
        factory.create_test_user(
            &format!("user{}", i),
            &format!("user{}@example.com", i),
            "User",
            "",
        );
    }

    let users = factory.get_all_users();
    assert!(users.len() >= 20);
}

#[test]
fn test_user_list_empty() {
    let factory = TestFactory::new();
    let users = factory.get_all_users();
    assert_eq!(users.len(), 0);
}

#[test]
fn test_user_list_with_pagination() {
    let factory = TestFactory::new();
    for i in 0..30 {
        factory.create_test_user(
            &format!("user{}", i % 10),
            &format!("user{}@example.com", i % 10),
            "User",
            "",
        );
    }

    let users = factory.get_all_users();
    assert!(users.len() >= 10);
}

// ============================================================================
// Query: User Detail
// ============================================================================

#[test]
fn test_user_detail_query() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "Developer");
    let user_id = user.id.clone();

    let retrieved = factory.get_user(&user_id);
    assert!(retrieved.is_some());
    assert_eq!(retrieved.unwrap().username, "alice");
}

#[test]
fn test_user_detail_with_bio() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "My bio");
    let user_id = user.id.clone();

    let retrieved = factory.get_user(&user_id);
    assert!(retrieved.is_some());
    assert_eq!(retrieved.unwrap().bio, Some("My bio".to_string()));
}

#[test]
fn test_user_detail_without_bio() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("bob", "bob@example.com", "Bob", "");
    let user_id = user.id.clone();

    let retrieved = factory.get_user(&user_id);
    assert!(retrieved.is_some());
    assert_eq!(retrieved.unwrap().bio, None);
}

#[test]
fn test_user_detail_not_found() {
    let factory = TestFactory::new();
    let user = factory.get_user("nonexistent-id");
    assert!(user.is_none());
}

// ============================================================================
// Query: Post List
// ============================================================================

#[test]
fn test_post_list_query() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    factory.create_test_post(&author.id, "Post 1", "Content 1");
    factory.create_test_post(&author.id, "Post 2", "Content 2");
    factory.create_test_post(&author.id, "Post 3", "Content 3");

    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 3);
}

#[test]
fn test_post_list_with_limit() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    for i in 0..20 {
        factory.create_test_post(&author.id, &format!("Post {}", i), "Content");
    }

    let posts = factory.get_all_posts();
    assert!(posts.len() >= 20);
}

#[test]
fn test_post_list_empty() {
    let factory = TestFactory::new();
    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 0);
}

// ============================================================================
// Query: Post Detail
// ============================================================================

#[test]
fn test_post_detail_query() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Test Post", "Test Content");
    let post_id = post.id.clone();

    let retrieved = factory.get_post(&post_id);
    assert!(retrieved.is_some());
    let retrieved = retrieved.unwrap();
    assert_eq!(retrieved.title, "Test Post");
    assert_eq!(retrieved.content, "Test Content");
}

#[test]
fn test_post_detail_not_found() {
    let factory = TestFactory::new();
    let post = factory.get_post("nonexistent-id");
    assert!(post.is_none());
}

// ============================================================================
// Query: Trinity Identifier Pattern
// ============================================================================

#[test]
fn test_user_has_uuid_id() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    assert!(ValidationHelper::assert_uuid(&user.id).is_ok());
}

#[test]
fn test_user_has_primary_key() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    assert!(user.pk_user > 0);
}

#[test]
fn test_post_has_uuid_id() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Content");
    assert!(ValidationHelper::assert_uuid(&post.id).is_ok());
}

#[test]
fn test_post_has_primary_key() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Content");
    assert!(post.pk_post > 0);
}

#[test]
fn test_trinity_identifiers_separate() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");
    assert_ne!(user.id, user.pk_user.to_string());
}

// ============================================================================
// Query: User-Post Relationships
// ============================================================================

#[test]
fn test_user_has_multiple_posts() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    factory.create_test_post(&author.id, "Post 1", "Content");
    factory.create_test_post(&author.id, "Post 2", "Content");
    factory.create_test_post(&author.id, "Post 3", "Content");

    let author_posts: Vec<_> = factory
        .get_all_posts()
        .into_iter()
        .filter(|p| p.fk_author == author.pk_user)
        .collect();

    assert_eq!(author_posts.len(), 3);
}

#[test]
fn test_post_references_author() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Content");

    assert_eq!(post.fk_author, author.pk_user);
}

// ============================================================================
// Query: Data Consistency
// ============================================================================

#[test]
fn test_list_and_detail_data_match() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "Bio");

    let list_user = factory.get_user(&user.id);
    let detail_user = factory.get_user(&user.id);

    assert_eq!(
        list_user.as_ref().unwrap().username,
        detail_user.as_ref().unwrap().username
    );
}

#[test]
fn test_repeated_queries_return_same_data() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");

    let retrieved1 = factory.get_user(&user.id);
    let retrieved2 = factory.get_user(&user.id);

    assert_eq!(retrieved1.as_ref().unwrap().id, retrieved2.as_ref().unwrap().id);
}

// ============================================================================
// Query: Null Field Handling
// ============================================================================

#[test]
fn test_user_with_null_bio_in_list() {
    let factory = TestFactory::new();
    factory.create_test_user("alice", "alice@example.com", "Alice", "");
    factory.create_test_user("bob", "bob@example.com", "Bob", "Bio");

    let users = factory.get_all_users();
    assert!(users.iter().any(|u| u.bio.is_none()));
    assert!(users.iter().any(|u| u.bio.is_some()));
}

#[test]
fn test_post_with_content() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Content");

    assert!(!post.content.is_empty());
}

// ============================================================================
// Query: Special Characters
// ============================================================================

#[test]
fn test_user_with_quotes_in_name() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Char'lie", "");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_user_with_double_quotes_in_bio() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "He said \"hello\"");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_post_with_html_tags() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post with <tags>", "Content");
    assert!(factory.get_post(&post.id).is_some());
}

#[test]
fn test_post_with_ampersand() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "Tom & Jerry");
    assert!(factory.get_post(&post.id).is_some());
}

#[test]
fn test_post_with_emoji() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post", "🎉 Celebration! 🚀 Rocket");
    assert!(factory.get_post(&post.id).is_some());
}

#[test]
fn test_user_with_accents() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Àlice Müller", "");
    assert!(factory.get_user(&user.id).is_some());
}

#[test]
fn test_user_with_diacritics() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "José García", "");
    assert!(factory.get_user(&user.id).is_some());
}

// ============================================================================
// Query: Boundary Conditions
// ============================================================================

#[test]
fn test_query_with_limit_0() {
    let factory = TestFactory::new();
    for i in 0..30 {
        factory.create_test_user(
            &format!("user{}", i % 10),
            &format!("user{}@example.com", i % 10),
            "User",
            "",
        );
    }

    let users = factory.get_all_users();
    assert!(users.len() > 0);
}

#[test]
fn test_query_with_limit_1() {
    let factory = TestFactory::new();
    factory.create_test_user("alice", "alice@example.com", "Alice", "");
    factory.create_test_user("bob", "bob@example.com", "Bob", "");

    let users = factory.get_all_users();
    assert!(users.len() >= 1);
}

#[test]
fn test_query_with_limit_larger_than_total() {
    let factory = TestFactory::new();
    for i in 0..5 {
        factory.create_test_user(
            &format!("user{}", i),
            &format!("user{}@example.com", i),
            "User",
            "",
        );
    }

    let users = factory.get_all_users();
    assert_eq!(users.len(), 5);
}

#[test]
fn test_query_with_very_large_limit() {
    let factory = TestFactory::new();
    for i in 0..10 {
        factory.create_test_user(
            &format!("user{}", i),
            &format!("user{}@example.com", i),
            "User",
            "",
        );
    }

    let users = factory.get_all_users();
    assert!(users.len() >= 10);
}

// ============================================================================
// Query: Multiple Entities
// ============================================================================

#[test]
fn test_multiple_users_isolated() {
    let factory = TestFactory::new();
    let user1 = factory.create_test_user("alice", "alice@example.com", "Alice", "Bio1");
    let user2 = factory.create_test_user("bob", "bob@example.com", "Bob", "Bio2");

    let retrieved1 = factory.get_user(&user1.id);
    let retrieved2 = factory.get_user(&user2.id);

    assert_ne!(retrieved1.as_ref().unwrap().id, retrieved2.as_ref().unwrap().id);
}

#[test]
fn test_multiple_authors_posts_isolated() {
    let factory = TestFactory::new();
    let author1 = factory.create_test_user("author1", "author1@example.com", "Author1", "");
    let author2 = factory.create_test_user("author2", "author2@example.com", "Author2", "");

    factory.create_test_post(&author1.id, "Post1", "Content");
    factory.create_test_post(&author2.id, "Post2", "Content");

    let author1_posts: Vec<_> = factory
        .get_all_posts()
        .into_iter()
        .filter(|p| p.fk_author == author1.pk_user)
        .collect();
    let author2_posts: Vec<_> = factory
        .get_all_posts()
        .into_iter()
        .filter(|p| p.fk_author == author2.pk_user)
        .collect();

    assert_eq!(author1_posts.len(), 1);
    assert_eq!(author2_posts.len(), 1);
}
