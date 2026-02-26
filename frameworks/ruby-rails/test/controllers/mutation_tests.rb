require "test_helper"

class MutationTests < ActionDispatch::IntegrationTest
  # ========================================================================
  # Single Field Update Tests
  # ========================================================================

  test "update user bio single field" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice", "Old bio")
    user_id = user.id
    new_bio = "Updated bio"

    # Act
    user.update(bio: new_bio)

    # Verify
    get "/api/users/#{user_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal new_bio, data["bio"]
    # Verify other fields unchanged
    assert_equal "Alice", data["fullName"]
  end

  test "update user full name single field" do
    # Arrange
    user = create_test_user("bob", "bob@example.com", "Bob")
    user_id = user.id
    new_name = "Bob Smith Updated"

    # Act
    user.update(full_name: new_name)

    # Verify
    get "/api/users/#{user_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal new_name, data["fullName"]
  end

  test "update post title" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Original Title", "Original Content")
    post_id = post.id
    new_title = "Updated Title"

    # Act
    post.update(title: new_title)

    # Verify
    get "/api/posts/#{post_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal new_title, data["title"]
    assert_equal "Original Content", data["content"]
  end

  test "update post content" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Title", "Original Content")
    post_id = post.id
    new_content = "Updated Content"

    # Act
    post.update(content: new_content)

    # Verify
    get "/api/posts/#{post_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal new_content, data["content"]
  end

  # ========================================================================
  # Multi-Field Update Tests
  # ========================================================================

  test "update user multiple fields" do
    # Arrange
    user = create_test_user("charlie", "charlie@example.com", "Charlie")
    user_id = user.id
    new_bio = "New bio"
    new_name = "Charlie Updated"

    # Act
    user.update(bio: new_bio, full_name: new_name)

    # Verify
    get "/api/users/#{user_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal new_bio, data["bio"]
    assert_equal new_name, data["fullName"]
  end

  test "update post title and content" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Original Title", "Original Content")
    post_id = post.id
    new_title = "Updated Title"
    new_content = "Updated Content"

    # Act
    post.update(title: new_title, content: new_content)

    # Verify
    get "/api/posts/#{post_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal new_title, data["title"]
    assert_equal new_content, data["content"]
  end

  # ========================================================================
  # State Change Verification Tests
  # ========================================================================

  test "sequential updates accumulate" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice")
    user_id = user.id

    # Act - first update
    user.update(bio: "Bio v1")

    # Verify first change
    get "/api/users/#{user_id}"
    data1 = JSON.parse(@response.body)
    assert_equal "Bio v1", data1["bio"]

    # Second update
    user.update(full_name: "Alice Updated")

    # Verify both changes accumulated
    get "/api/users/#{user_id}"

    # Assert
    assert_response :success
    data2 = JSON.parse(@response.body)
    assert_equal "Bio v1", data2["bio"]
    assert_equal "Alice Updated", data2["fullName"]
  end

  test "update one user does not affect others" do
    # Arrange
    user1 = create_test_user("alice", "alice@example.com", "Alice")
    user2 = create_test_user("bob", "bob@example.com", "Bob")
    new_bio = "Alice's new bio"

    # Act
    user1.update(bio: new_bio)

    # Verify
    get "/api/users/#{user1.id}"
    response1 = @response.body
    get "/api/users/#{user2.id}"
    response2 = @response.body

    # Assert
    data1 = JSON.parse(response1)
    data2 = JSON.parse(response2)
    assert_equal new_bio, data1["bio"]
    assert_nil data2["bio"]
  end

  test "update one post does not affect others" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post1 = create_test_post(author.pk_user, "Post 1", "Content 1")
    post2 = create_test_post(author.pk_user, "Post 2", "Content 2")
    new_title = "Updated Title"

    # Act
    post1.update(title: new_title)

    # Verify
    get "/api/posts/#{post1.id}"
    response1 = @response.body
    get "/api/posts/#{post2.id}"
    response2 = @response.body

    # Assert
    data1 = JSON.parse(response1)
    data2 = JSON.parse(response2)
    assert_equal new_title, data1["title"]
    assert_equal "Post 2", data2["title"]
  end

  # ========================================================================
  # Input Validation in Updates
  # ========================================================================

  test "update user with special characters" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice")
    user_id = user.id
    special_bio = "Bio with 'quotes', \"double quotes\", <html>, & ampersand"

    # Act
    user.update(bio: special_bio)

    # Verify
    get "/api/users/#{user_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal special_bio, data["bio"]
  end

  test "update user with unicode characters" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice")
    user_id = user.id
    unicode_bio = "Bio with émojis 🎉 and spëcial chàrs"

    # Act
    user.update(bio: unicode_bio)

    # Verify
    get "/api/users/#{user_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal unicode_bio, data["bio"]
  end

  test "update post content with long text" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Title", "Short content")
    post_id = post.id
    long_content = "x" * 5000

    # Act
    post.update(content: long_content)

    # Verify
    get "/api/posts/#{post_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 5000, data["content"].length
  end

  test "update user bio to null" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice", "Old bio")
    user_id = user.id

    # Act
    user.update(bio: nil)

    # Verify
    get "/api/users/#{user_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_nil data["bio"]
  end

  test "update user bio to empty string" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice", "Old bio")
    user_id = user.id

    # Act
    user.update(bio: "")

    # Verify
    get "/api/users/#{user_id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal "", data["bio"]
  end
end
