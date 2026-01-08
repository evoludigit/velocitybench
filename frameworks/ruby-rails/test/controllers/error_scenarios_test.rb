require "test_helper"

class ErrorScenariosTest < ActionDispatch::IntegrationTest
  # ========================================================================
  # 404 Not Found Tests
  # ========================================================================

  test "get nonexistent user returns 404" do
    # Arrange
    nonexistent_id = SecureRandom.uuid

    # Act
    get "/api/users/#{nonexistent_id}"

    # Assert
    assert_response :not_found
  end

  test "get nonexistent post returns 404" do
    # Arrange
    nonexistent_id = SecureRandom.uuid

    # Act
    get "/api/posts/#{nonexistent_id}"

    # Assert
    assert_response :not_found
  end

  test "get posts by nonexistent author returns 404" do
    # Arrange
    nonexistent_id = SecureRandom.uuid

    # Act
    get "/api/posts/by-author/#{nonexistent_id}"

    # Assert
    assert_response :not_found
  end

  # ========================================================================
  # Invalid Input Tests
  # ========================================================================

  test "list users with invalid page parameter" do
    # Arrange
    create_test_user("alice", "alice@example.com", "Alice")

    # Act
    get "/api/users?page=invalid&size=10"

    # Assert
    assert_response :success
  end

  test "list users with zero size" do
    # Arrange
    5.times { |i| create_test_user("user#{i}", "user#{i}@example.com") }

    # Act
    get "/api/users?page=0&size=0"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 0, data.length
  end

  test "list users with negative page" do
    # Arrange
    create_test_user("alice", "alice@example.com", "Alice")

    # Act
    get "/api/users?page=-1&size=10"

    # Assert
    assert_response :success
  end

  # ========================================================================
  # Null/Optional Field Tests
  # ========================================================================

  test "user without bio returns null" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice", nil)

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_nil data["bio"]
  end

  test "user with empty bio returns empty string" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice", "")

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal "", data["bio"]
  end

  # ========================================================================
  # Special Character Handling Tests
  # ========================================================================

  test "user bio with special characters" do
    # Arrange
    special_bio = "Bio with 'quotes' and \"double quotes\" and <html>"
    user = create_test_user("alice", "alice@example.com", "Alice", special_bio)

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal special_bio, data["bio"]
  end

  test "user with emoji in bio" do
    # Arrange
    emoji_bio = "Bio with emoji 🎉 and 💚"
    user = create_test_user("alice", "alice@example.com", "Alice", emoji_bio)

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal emoji_bio, data["bio"]
  end

  test "user with unicode characters" do
    # Arrange
    unicode_name = "Àlice Müller"
    user = create_test_user("alice", "alice@example.com", unicode_name)

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal unicode_name, data["fullName"]
  end

  test "post content with special characters" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    special_content = "Content with 'quotes' and \"double quotes\" and <html>"
    post = create_test_post(author.pk_user, "Special Post", special_content)

    # Act
    get "/api/posts/#{post.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal special_content, data["content"]
  end

  test "post content with emoji" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    emoji_content = "Content with emoji 🚀 and ✨"
    post = create_test_post(author.pk_user, "Emoji Post", emoji_content)

    # Act
    get "/api/posts/#{post.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal emoji_content, data["content"]
  end

  # ========================================================================
  # Boundary Condition Tests
  # ========================================================================

  test "very long bio text" do
    # Arrange
    long_bio = "x" * 5000
    user = create_test_user("alice", "alice@example.com", "Alice", long_bio)

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 5000, data["bio"].length
  end

  test "very long post content" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    long_content = "x" * 5000
    post = create_test_post(author.pk_user, "Long Post", long_content)

    # Act
    get "/api/posts/#{post.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 5000, data["content"].length
  end

  test "list users with large limit" do
    # Arrange
    10.times { |i| create_test_user("user#{i}", "user#{i}@example.com") }

    # Act
    get "/api/users?page=0&size=1000"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 10, data.length
  end

  test "multiple users have unique ids" do
    # Arrange
    user1 = create_test_user("alice", "alice@example.com", "Alice")
    user2 = create_test_user("bob", "bob@example.com", "Bob")
    user3 = create_test_user("charlie", "charlie@example.com", "Charlie")

    # Act
    ids = [user1.id, user2.id, user3.id]

    # Assert
    assert_equal 3, ids.length
    assert_equal 3, ids.uniq.length
  end
end
