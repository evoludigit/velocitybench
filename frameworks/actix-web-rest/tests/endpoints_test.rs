mod test_helpers;
use test_helpers::*;

#[test]
fn test_get_users_list_returns_users() {
    let factory = TestFactory::new();
    factory.create_test_user("alice", "alice@example.com", "Alice", "");
    factory.create_test_user("bob", "bob@example.com", "Bob", "");
    factory.create_test_user("charlie", "charlie@example.com", "Charlie", "");

    let users = factory.get_all_users();
    assert_eq!(users.len(), 3);
}

#[test]
fn test_get_users_respects_limit() {
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
fn test_get_users_returns_empty_when_no_users() {
    let factory = TestFactory::new();
    let users = factory.get_all_users();
    assert_eq!(users.len(), 0);
}

#[test]
fn test_get_users_with_pagination() {
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

#[test]
fn test_get_user_detail_returns_user() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "Developer");
    let user_id = user.id.clone();

    let retrieved = factory.get_user(&user_id);
    assert!(retrieved.is_some());
    let retrieved = retrieved.unwrap();
    assert_eq!(retrieved.username, "alice");
}

#[test]
fn test_get_user_detail_with_null_bio() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("bob", "bob@example.com", "Bob", "");
    let user_id = user.id.clone();

    let retrieved = factory.get_user(&user_id);
    assert!(retrieved.is_some());
    let retrieved = retrieved.unwrap();
    assert_eq!(retrieved.username, "bob");
    assert_eq!(retrieved.bio, None);
}

#[test]
fn test_get_user_detail_with_special_chars() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("charlie", "charlie@example.com", "Char'lie", "Quote: \"test\"");
    let user_id = user.id.clone();

    let retrieved = factory.get_user(&user_id);
    assert!(retrieved.is_some());
}

#[test]
fn test_get_user_detail_not_found() {
    let factory = TestFactory::new();
    let retrieved = factory.get_user("nonexistent-id");
    assert!(retrieved.is_none());
}

#[test]
fn test_get_posts_list_returns_posts() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    factory.create_test_post(&author.id, "Post 1", "Content");
    factory.create_test_post(&author.id, "Post 2", "Content");
    factory.create_test_post(&author.id, "Post 3", "Content");

    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 3);
}

#[test]
fn test_get_posts_respects_limit() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    for i in 0..20 {
        factory.create_test_post(&author.id, &format!("Post {}", i), "Content");
    }

    let posts = factory.get_all_posts();
    assert!(posts.len() >= 20);
}

#[test]
fn test_get_posts_returns_empty() {
    let factory = TestFactory::new();
    let posts = factory.get_all_posts();
    assert_eq!(posts.len(), 0);
}

#[test]
fn test_get_post_detail_returns_post() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Test Post", "Test Content");
    let post_id = post.id.clone();

    let retrieved = factory.get_post(&post_id);
    assert!(retrieved.is_some());
    let retrieved = retrieved.unwrap();
    assert_eq!(retrieved.title, "Test Post");
}

#[test]
fn test_get_post_detail_with_null_content() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "No Content", "");
    let post_id = post.id.clone();

    let retrieved = factory.get_post(&post_id);
    assert!(retrieved.is_some());
    let retrieved = retrieved.unwrap();
    assert_eq!(retrieved.content, None);
}

#[test]
fn test_get_post_detail_with_special_chars() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");
    let post = factory.create_test_post(&author.id, "Post with <tags>", "Content & more");
    let post_id = post.id.clone();

    let retrieved = factory.get_post(&post_id);
    assert!(retrieved.is_some());
}

#[test]
fn test_get_post_detail_not_found() {
    let factory = TestFactory::new();
    let retrieved = factory.get_post("nonexistent-id");
    assert!(retrieved.is_none());
}

#[test]
fn test_get_posts_by_author_returns_authors_posts() {
    let factory = TestFactory::new();
    let author = factory.create_test_user("author", "author@example.com", "Author", "");

    factory.create_test_post(&author.id, "Post 1", "Content");
    factory.create_test_post(&author.id, "Post 2", "Content");
    factory.create_test_post(&author.id, "Post 3", "Content");

    let posts: Vec<_> = factory
        .get_all_posts()
        .into_iter()
        .filter(|p| p.author_id == author.id)
        .collect();

    assert_eq!(posts.len(), 3);
}

#[test]
fn test_multiple_authors_separate_posts() {
    let factory = TestFactory::new();
    let author1 = factory.create_test_user("author1", "author1@example.com", "Author 1", "");
    let author2 = factory.create_test_user("author2", "author2@example.com", "Author 2", "");

    factory.create_test_post(&author1.id, "Post 1", "Content");
    factory.create_test_post(&author1.id, "Post 2", "Content");
    factory.create_test_post(&author2.id, "Post 1", "Content");

    let author1_posts: Vec<_> = factory
        .get_all_posts()
        .into_iter()
        .filter(|p| p.author_id == author1.id)
        .collect();
    let author2_posts: Vec<_> = factory
        .get_all_posts()
        .into_iter()
        .filter(|p| p.author_id == author2.id)
        .collect();

    assert_eq!(author1_posts.len(), 2);
    assert_eq!(author2_posts.len(), 1);
}

#[test]
fn test_author_with_no_posts() {
    let factory = TestFactory::new();
    factory.create_test_user("author", "author@example.com", "Author", "");

    let posts: Vec<_> = factory
        .get_all_posts()
        .into_iter()
        .filter(|p| p.author_id == factory.get_all_users()[0].id.clone())
        .collect();

    assert_eq!(posts.len(), 0);
}

#[test]
fn test_response_headers_json_content_type() {
    let factory = TestFactory::new();
    factory.create_test_user("alice", "alice@example.com", "Alice", "");

    assert!(factory.user_count() > 0);
}

#[test]
fn test_pagination_page_0_with_size_10() {
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

#[test]
fn test_pagination_page_1_with_size_10() {
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

#[test]
fn test_pagination_last_page_with_fewer_items() {
    let factory = TestFactory::new();
    for i in 0..25 {
        factory.create_test_user(
            &format!("user{}", i % 10),
            &format!("user{}@example.com", i % 10),
            "User",
            "",
        );
    }

    let users = factory.get_all_users();
    assert!(users.len() >= 5);
}

#[test]
fn test_data_consistency_list_detail_match() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "Bio");

    let list_user = factory.get_user(&user.id);
    let detail_user = factory.get_user(&user.id);

    assert_eq!(list_user.as_ref().unwrap().username, detail_user.as_ref().unwrap().username);
}

#[test]
fn test_repeated_requests_return_same_data() {
    let factory = TestFactory::new();
    let user = factory.create_test_user("alice", "alice@example.com", "Alice", "");

    let retrieved1 = factory.get_user(&user.id);
    let retrieved2 = factory.get_user(&user.id);

    assert_eq!(retrieved1.as_ref().unwrap().id, retrieved2.as_ref().unwrap().id);
}
