require "test_helper"

class SecurityInjectionTest < ActionDispatch::IntegrationTest
  # ============================================================================
  # SQL Injection Prevention Tests
  # ============================================================================

  test "prevents basic OR injection in user query" do
    # Arrange
    user1 = create_test_user("alice", "alice@example.com", "Alice")
    user2 = create_test_user("bob", "bob@example.com", "Bob")

    # Attempt SQL injection: ' OR '1'='1
    malicious_input = "' OR '1'='1"

    # Act - query with malicious input
    get "/api/users?username=#{CGI.escape(malicious_input)}"

    # Assert - should return empty or error, not all users
    assert_response :success
    data = JSON.parse(@response.body)
    # Should not return all users (injection failed)
    refute_equal 2, data.length, "SQL injection should not return multiple users"
  end

  test "prevents UNION-based SQL injection" do
    # Arrange
    user = create_test_user("testuser", "test@example.com", "Test User")

    # Attempt UNION-based injection
    malicious_username = "admin' UNION SELECT id, username, email FROM users--"

    # Act
    get "/api/users?username=#{CGI.escape(malicious_username)}"

    # Assert - injection should not return data
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 0, data.length, "UNION injection should not return data"
  end

  test "prevents stacked queries in post creation" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")

    # Attempt stacked query injection
    malicious_title = "Valid Title'; DROP TABLE posts; --"

    # Act - create post with malicious title
    post "/api/posts", params: {
      fk_author: author.pk_user,
      title: malicious_title,
      content: "Test content"
    }

    # Assert - post should be created with literal title
    assert_response :success
    created_post = JSON.parse(@response.body)
    assert_equal malicious_title, created_post["title"]

    # Assert - posts table should still exist (can query posts)
    get "/api/posts"
    assert_response :success
  end

  test "prevents comment injection in content" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    post = create_test_post(author.pk_user, "Test Post", "Content")

    # Attempt comment sequence injection
    malicious_content = "Valid content /* */ -- SELECT * FROM users"

    # Act
    post "/api/comments", params: {
      fk_post: post.pk_post,
      fk_author: author.pk_user,
      content: malicious_content
    }

    # Assert - content should be stored as literal string
    assert_response :success
    created_comment = JSON.parse(@response.body)
    assert_equal malicious_content, created_comment["content"]
  end

  test "prevents injection with encoded characters" do
    # Arrange
    user = create_test_user("testuser", "test@example.com", "Test User")

    # Attempt injection with URL-encoded characters
    malicious_input = "admin%27%20OR%201=1--"

    # Act
    get "/api/users?username=#{malicious_input}"

    # Assert - should not find any user
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 0, data.length
  end

  test "prevents time-based blind SQL injection" do
    # Arrange
    user = create_test_user("testuser", "test@example.com", "Test User")

    # Attempt time-based blind SQL injection
    malicious_input = "admin' AND SLEEP(5)--"

    # Act
    start_time = Time.now
    get "/api/users?username=#{CGI.escape(malicious_input)}"
    elapsed_time = Time.now - start_time

    # Assert - should not delay execution (< 1 second)
    assert elapsed_time < 1, "Query should not be delayed by SQL injection"
    assert_response :success
  end

  test "prevents boolean-based blind injection" do
    # Arrange
    user = create_test_user("admin", "admin@example.com", "Admin")

    # Attempt boolean-based blind injection
    malicious_input = "admin' AND '1'='1"

    # Act
    get "/api/users?username=#{CGI.escape(malicious_input)}"

    # Assert - should not find user (entire string treated as literal)
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 0, data.length
  end

  test "escapes special characters in bio" do
    # Arrange
    special_bio = "My bio with 'single quotes' and \"double quotes\" and <script>alert('xss')</script>"
    user = create_test_user("testuser", "test@example.com", "Test User", special_bio)

    # Act
    get "/api/users/#{user.id}"

    # Assert - special characters should be preserved
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal special_bio, data["bio"]
  end

  test "handles null byte injection attempt" do
    # Arrange - Null byte injection attempt
    malicious_username = "admin\x00malicious"

    # Act - attempt to create user with null byte
    post "/api/users", params: {
      username: malicious_username,
      email: "test@example.com",
      full_name: "Test User"
    }

    # Assert - should handle gracefully (either accept or reject)
    assert_response :success
    created_user = JSON.parse(@response.body)
    assert created_user["username"]
  end

  test "prevents nested injection patterns" do
    # Arrange
    user = create_test_user("testuser", "test@example.com", "Test User")

    # Attempt nested injection
    malicious_input = "test' OR ('1'='1' AND username='admin')--"

    # Act
    get "/api/users?username=#{CGI.escape(malicious_input)}"

    # Assert - should not find any user
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 0, data.length
  end

  # ============================================================================
  # XSS Prevention Tests (Data Layer)
  # ============================================================================

  test "stores HTML tags as literal strings in post content" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    html_content = '<script>alert("XSS")</script><img src=x onerror=alert(1)>'

    # Act
    post "/api/posts", params: {
      fk_author: author.pk_user,
      title: "Test Post",
      content: html_content
    }

    # Assert - HTML should be stored as-is
    assert_response :success
    created_post = JSON.parse(@response.body)
    assert_equal html_content, created_post["content"]
  end

  test "preserves legitimate HTML entities" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    content_with_entities = 'Test &lt;div&gt; and &amp; symbol'

    # Act
    post "/api/posts", params: {
      fk_author: author.pk_user,
      title: "Test Post",
      content: content_with_entities
    }

    # Assert - entities should be preserved
    assert_response :success
    created_post = JSON.parse(@response.body)
    assert_equal content_with_entities, created_post["content"]
  end

  test "handles multiple injection attempts in single request" do
    # Arrange
    author = create_test_user("author", "author@example.com", "Author")
    malicious_title = "Title'; DROP TABLE posts;--"
    malicious_content = "Content' UNION SELECT * FROM users--"

    # Act
    post "/api/posts", params: {
      fk_author: author.pk_user,
      title: malicious_title,
      content: malicious_content
    }

    # Assert - both fields should store literal values
    assert_response :success
    created_post = JSON.parse(@response.body)
    assert_equal malicious_title, created_post["title"]
    assert_equal malicious_content, created_post["content"]
  end
end
