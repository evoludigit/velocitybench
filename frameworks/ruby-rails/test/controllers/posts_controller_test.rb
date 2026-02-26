require "test_helper"

class PostsControllerTest < ActionDispatch::IntegrationTest
  # ========================================================================
  # GET /posts Tests
  # ========================================================================

  test "list posts returns list" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post1 = create_test_post(author.pk_user, "Post 1", "Content 1")
    post2 = create_test_post(author.pk_user, "Post 2", "Content 2")

    # Act
    get "/api/posts"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_instance_of Array, data
    assert_equal 2, data.length
  end

  test "list posts pagination" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    15.times { |i| create_test_post(author.pk_user, "Post #{i}", "Content #{i}") }

    # Act
    get "/api/posts?page=0&size=10"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 10, data.length
  end

  test "list posts includes author id" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Act
    get "/api/posts"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_not_empty data
    assert_includes data[0].keys, "authorId"
  end

  test "list posts response structure" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Test Content")

    # Act
    get "/api/posts"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_not_empty data
    assert_includes data[0].keys, "id"
    assert_includes data[0].keys, "title"
    assert_includes data[0].keys, "content"
    assert_includes data[0].keys, "authorId"
    assert_includes data[0].keys, "createdAt"
  end

  # ========================================================================
  # GET /posts/:id Tests
  # ========================================================================

  test "get post by id" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Test Content")

    # Act
    get "/api/posts/#{post.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal post.id, data["id"]
    assert_equal "Test Post", data["title"]
    assert_equal "Test Content", data["content"]
  end

  test "get post includes created at" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Act
    get "/api/posts/#{post.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_includes data.keys, "createdAt"
    assert_not_nil data["createdAt"]
  end

  test "get post response structure" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Test Content")

    # Act
    get "/api/posts/#{post.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_includes data.keys, "id"
    assert_includes data.keys, "title"
    assert_includes data.keys, "content"
    assert_includes data.keys, "authorId"
    assert_includes data.keys, "createdAt"
  end

  # ========================================================================
  # GET /posts/by-author/:authorId Tests
  # ========================================================================

  test "get posts by author returns author posts" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    other = create_test_user("other", "other@example.com", "Other")

    post1 = create_test_post(author.pk_user, "Author Post 1", "Content 1")
    post2 = create_test_post(author.pk_user, "Author Post 2", "Content 2")
    post3 = create_test_post(other.pk_user, "Other Post", "Content 3")

    # Act
    get "/api/posts/by-author/#{author.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 2, data.length
  end

  test "get posts by author returns empty for no posts" do
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

  test "get posts by author pagination" do
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
end
