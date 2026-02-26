require "test_helper"

class AdvancedIntegrationTest < ActionDispatch::IntegrationTest
  # ========================================================================
  # Multi-User Relationship Tests
  # ========================================================================

  test "multiple authors have separate posts" do
    # Arrange
    author1 = create_test_user("author1", "author1@example.com", "Author 1")
    author2 = create_test_user("author2", "author2@example.com", "Author 2")
    author3 = create_test_user("author3", "author3@example.com", "Author 3")

    post1 = create_test_post(author1.pk_user, "Author 1 Post", "Content 1")
    post2 = create_test_post(author2.pk_user, "Author 2 Post", "Content 2")
    post3 = create_test_post(author3.pk_user, "Author 3 Post", "Content 3")

    # Act
    response1 = get "/api/posts/by-author/#{author1.id}"
    response2 = get "/api/posts/by-author/#{author2.id}"
    response3 = get "/api/posts/by-author/#{author3.id}"

    # Assert
    data1 = JSON.parse(response1.body)
    data2 = JSON.parse(response2.body)
    data3 = JSON.parse(response3.body)

    assert_equal 1, data1.length
    assert_equal 1, data2.length
    assert_equal 1, data3.length
  end

  test "post relationships are independent" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post1 = create_test_post(author.pk_user, "Post 1", "Content 1")
    post2 = create_test_post(author.pk_user, "Post 2", "Content 2")

    # Act
    response1 = get "/api/posts/#{post1.id}"
    response2 = get "/api/posts/#{post2.id}"

    # Assert
    data1 = JSON.parse(response1.body)
    data2 = JSON.parse(response2.body)

    assert_not_equal data1["id"], data2["id"]
    assert_equal "Post 1", data1["title"]
    assert_equal "Post 2", data2["title"]
  end

  # ========================================================================
  # Pagination Edge Cases
  # ========================================================================

  test "pagination boundary at exact limit" do
    # Arrange
    author = create_test_user("author", "author@example.com")
    15.times { |i| create_test_post(author.pk_user, "Post #{i}", "Content #{i}") }

    # Act
    response = get "/api/posts/by-author/#{author.id}?page=0&size=15"

    # Assert
    data = JSON.parse(response.body)
    assert_equal 15, data.length
  end

  test "pagination page alignment" do
    # Arrange
    30.times { |i| create_test_user("user#{i}", "user#{i}@example.com") }

    # Act
    response1 = get "/api/users?page=0&size=15"
    response2 = get "/api/users?page=1&size=15"

    # Assert
    data1 = JSON.parse(response1.body)
    data2 = JSON.parse(response2.body)

    assert_equal 15, data1.length
    assert_equal 15, data2.length
  end

  # ========================================================================
  # Field Immutability Tests
  # ========================================================================

  test "username remains immutable" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice")
    original_username = user.username

    # Act
    user.update(bio: "New bio")

    # Verify
    response = get "/api/users/#{user.id}"

    # Assert
    data = JSON.parse(response.body)
    assert_equal original_username, data["username"]
  end

  test "id remains immutable" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice")
    original_id = user.id

    # Act
    user.update(bio: "New bio")

    # Verify
    response = get "/api/users/#{user.id}"

    # Assert
    data = JSON.parse(response.body)
    assert_equal original_id, data["id"]
  end

  # ========================================================================
  # Data Type Validation
  # ========================================================================

  test "all user ids are uuid" do
    # Arrange
    users = [
      create_test_user("alice", "alice@example.com"),
      create_test_user("bob", "bob@example.com"),
      create_test_user("charlie", "charlie@example.com"),
    ]

    # Act & Assert
    users.each do |user|
      parts = user.id.split("-")
      assert_equal 5, parts.length
    end
  end

  test "all post ids are uuid" do
    # Arrange
    author = create_test_user("author", "author@example.com")
    posts = [
      create_test_post(author.pk_user, "Post 1", "Content 1"),
      create_test_post(author.pk_user, "Post 2", "Content 2"),
      create_test_post(author.pk_user, "Post 3", "Content 3"),
    ]

    # Act & Assert
    posts.each do |post|
      parts = post.id.split("-")
      assert_equal 5, parts.length
    end
  end

  # ========================================================================
  # Response Structure Consistency
  # ========================================================================

  test "list and detail structure match" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice", "Alice bio")

    # Act
    list_response = get "/api/users"
    detail_response = get "/api/users/#{user.id}"

    # Assert
    list_data = JSON.parse(list_response.body)
    detail_data = JSON.parse(detail_response.body)

    list_user = list_data.find { |u| u["id"] == user.id }

    assert_equal list_user["username"], detail_data["username"]
    assert_equal list_user["fullName"], detail_data["fullName"]
  end

  test "post list and detail structure match" do
    # Arrange
    author = create_test_user("author", "author@example.com")
    post = create_test_post(author.pk_user, "Test Post", "Test Content")

    # Act
    list_response = get "/api/posts"
    detail_response = get "/api/posts/#{post.id}"

    # Assert
    list_data = JSON.parse(list_response.body)
    detail_data = JSON.parse(detail_response.body)

    list_post = list_data.find { |p| p["id"] == post.id }

    assert_equal list_post["title"], detail_data["title"]
    assert_equal list_post["content"], detail_data["content"]
  end

  # ========================================================================
  # Timestamp Consistency Tests
  # ========================================================================

  test "user timestamps are set" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice")

    # Act & Assert
    assert_not_nil user.created_at
  end

  test "post timestamps are set" do
    # Arrange
    author = create_test_user("author", "author@example.com")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Act & Assert
    assert_not_nil post.created_at
  end

  test "timestamps returned in responses" do
    # Arrange
    author = create_test_user("author", "author@example.com")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Act
    response = get "/api/posts/#{post.id}"

    # Assert
    data = JSON.parse(response.body)
    assert_not_nil data["createdAt"]
  end

  # ========================================================================
  # Null Field Consistency Tests
  # ========================================================================

  test "null bio consistency" do
    # Arrange
    user1 = create_test_user("alice", "alice@example.com", "Alice", nil)
    user2 = create_test_user("bob", "bob@example.com", "Bob", "Bob's bio")

    # Act
    response1 = get "/api/users/#{user1.id}"
    response2 = get "/api/users/#{user2.id}"

    # Assert
    data1 = JSON.parse(response1.body)
    data2 = JSON.parse(response2.body)

    assert_nil data1["bio"]
    assert_not_nil data2["bio"]
  end

  test "empty string vs null bio" do
    # Arrange
    user1 = create_test_user("alice", "alice@example.com", "Alice", "")
    user2 = create_test_user("bob", "bob@example.com", "Bob", nil)

    # Act
    response1 = get "/api/users/#{user1.id}"
    response2 = get "/api/users/#{user2.id}"

    # Assert
    data1 = JSON.parse(response1.body)
    data2 = JSON.parse(response2.body)

    assert_equal "", data1["bio"]
    assert_nil data2["bio"]
  end

  # ========================================================================
  # Query Result Consistency Tests
  # ========================================================================

  test "same user returns same data" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice", "Alice bio")
    user_id = user.id

    # Act
    response1 = get "/api/users/#{user_id}"
    response2 = get "/api/users/#{user_id}"

    # Assert
    data1 = JSON.parse(response1.body)
    data2 = JSON.parse(response2.body)

    assert_equal data1["id"], data2["id"]
    assert_equal data1["username"], data2["username"]
    assert_equal data1["bio"], data2["bio"]
  end

  test "same post returns same data" do
    # Arrange
    author = create_test_user("author", "author@example.com")
    post = create_test_post(author.pk_user, "Test Post", "Test Content")
    post_id = post.id

    # Act
    response1 = get "/api/posts/#{post_id}"
    response2 = get "/api/posts/#{post_id}"

    # Assert
    data1 = JSON.parse(response1.body)
    data2 = JSON.parse(response2.body)

    assert_equal data1["id"], data2["id"]
    assert_equal data1["title"], data2["title"]
    assert_equal data1["content"], data2["content"]
  end

  # ========================================================================
  # Trinity Pattern Consistency
  # ========================================================================

  test "post author id references user" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Act
    response = get "/api/posts/#{post.id}"

    # Assert
    data = JSON.parse(response.body)
    assert_equal author.id, data["authorId"]
  end

  test "multiple posts reference correct authors" do
    # Arrange
    author1 = create_test_user("author1", "author1@example.com")
    author2 = create_test_user("author2", "author2@example.com")

    post1 = create_test_post(author1.pk_user, "Post 1", "Content")
    post2 = create_test_post(author2.pk_user, "Post 2", "Content")

    # Act
    response1 = get "/api/posts/#{post1.id}"
    response2 = get "/api/posts/#{post2.id}"

    # Assert
    data1 = JSON.parse(response1.body)
    data2 = JSON.parse(response2.body)

    assert_equal author1.id, data1["authorId"]
    assert_equal author2.id, data2["authorId"]
  end
end
