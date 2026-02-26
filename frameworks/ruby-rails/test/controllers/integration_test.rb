require "test_helper"

class IntegrationTest < ActionDispatch::IntegrationTest
  # ========================================================================
  # User-Post Relationship Tests
  # ========================================================================

  test "get posts by specific author" do
    # Arrange
    author1 = create_test_user("author1", "author1@example.com", "Author 1")
    author2 = create_test_user("author2", "author2@example.com", "Author 2")

    post1 = create_test_post(author1.pk_user, "Post 1", "Content 1")
    post2 = create_test_post(author1.pk_user, "Post 2", "Content 2")
    post3 = create_test_post(author2.pk_user, "Post 3", "Content 3")

    # Act
    get "/api/posts/by-author/#{author1.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 2, data.length
    assert_equal "Post 1", data[0]["title"]
    assert_equal "Post 2", data[1]["title"]
  end

  test "author posts pagination" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")

    15.times { |i| create_test_post(author.pk_user, "Post #{i}", "Content #{i}") }

    # Act
    get "/api/posts/by-author/#{author.id}?page=0&size=10"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 10, data.length
  end

  test "author with no posts returns empty list" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    other = create_test_user("other", "other@example.com", "Other")

    create_test_post(other.pk_user, "Other Post", "Content")

    # Act
    get "/api/posts/by-author/#{author.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 0, data.length
  end

  # ========================================================================
  # Trinity Pattern Validation Tests
  # ========================================================================

  test "user has uuid id" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice")

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)

    # Verify UUID format (8-4-4-4-12)
    uuid_parts = data["id"].split("-")
    assert_equal 5, uuid_parts.length
  end

  test "post has uuid id" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Act
    get "/api/posts/#{post.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)

    # Verify UUID format
    uuid_parts = data["id"].split("-")
    assert_equal 5, uuid_parts.length
  end

  test "post author id is user uuid" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Act
    get "/api/posts/#{post.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)

    # Author ID in post should match user's UUID
    assert_equal author.id, data["authorId"]
  end

  # ========================================================================
  # Data Consistency Tests
  # ========================================================================

  test "list users returns consistent data" do
    # Arrange
    user1 = create_test_user("alice", "alice@example.com", "Alice")
    user2 = create_test_user("bob", "bob@example.com", "Bob")

    # Act
    list_response = get "/api/users"
    get_response = get "/api/users/#{user1.id}"

    # Assert
    list_data = JSON.parse(list_response.body)
    get_data = JSON.parse(get_response.body)

    # Data from list and detail should match
    list_user = list_data.find { |u| u["id"] == user1.id }
    assert_equal list_user["username"], get_data["username"]
    assert_equal list_user["fullName"], get_data["fullName"]
  end

  test "list posts returns consistent data" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Test Content")

    # Act
    list_response = get "/api/posts"
    get_response = get "/api/posts/#{post.id}"

    # Assert
    list_data = JSON.parse(list_response.body)
    get_data = JSON.parse(get_response.body)

    list_post = list_data.find { |p| p["id"] == post.id }
    assert_equal list_post["title"], get_data["title"]
    assert_equal list_post["content"], get_data["content"]
  end

  test "post author relationship integrity" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post1 = create_test_post(author.pk_user, "Post 1", "Content 1")
    post2 = create_test_post(author.pk_user, "Post 2", "Content 2")

    # Act
    response = get "/api/posts"

    # Assert
    posts = JSON.parse(response.body)

    author_posts = posts.select { |p| p["authorId"] == author.id }
    assert_equal 2, author_posts.length
  end

  # ========================================================================
  # Timestamp Tests
  # ========================================================================

  test "user created at timestamp set" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice")

    # Act & Assert
    assert_not_nil user.created_at
  end

  test "post created at timestamp set" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Act & Assert
    assert_not_nil post.created_at
  end

  test "post created at returned in response" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Act
    get "/api/posts/#{post.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_not_nil data["createdAt"]
  end

  # ========================================================================
  # Different Users Relationship Tests
  # ========================================================================

  test "different users have separate posts" do
    # Arrange
    user1 = create_test_user("author1", "author1@example.com", "Author 1")
    user2 = create_test_user("author2", "author2@example.com", "Author 2")
    post1 = create_test_post(user1.pk_user, "Post 1", "Content 1")
    post2 = create_test_post(user2.pk_user, "Post 2", "Content 2")

    # Act
    get "/api/posts/by-author/#{user1.id}"
    user1_posts_response = @response.body
    get "/api/posts/by-author/#{user2.id}"
    user2_posts_response = @response.body

    # Assert
    user1_posts = JSON.parse(user1_posts_response)
    user2_posts = JSON.parse(user2_posts_response)

    assert_equal 1, user1_posts.length
    assert_equal 1, user2_posts.length
    assert_not_equal user1_posts[0]["id"], user2_posts[0]["id"]
  end
end
