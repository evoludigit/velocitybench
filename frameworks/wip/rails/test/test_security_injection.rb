# frozen_string_literal: true

require_relative 'test_helper'

class SecurityInjectionTest < Minitest::Test
  def setup
    @factory = TestFactory.new
  end

  def teardown
    @factory.reset
  end

  # ============================================================================
  # SQL Injection Prevention Tests
  # ============================================================================

  def test_prevents_basic_or_injection_in_user_query
    # Arrange
    user1 = @factory.create_user('alice', 'alice@example.com', 'Alice')
    user2 = @factory.create_user('bob', 'bob@example.com', 'Bob')

    # Attempt SQL injection: ' OR '1'='1
    malicious_input = "' OR '1'='1"

    # Act - should treat the entire string as a literal username
    result = @factory.get_user(malicious_input)

    # Assert - injection should fail (no user found)
    assert_nil result
  end

  def test_prevents_union_based_injection_in_search
    # Arrange
    user = @factory.create_user('testuser', 'test@example.com', 'Test User')

    # Attempt UNION-based injection
    malicious_username = "admin' UNION SELECT * FROM users--"

    # Act
    result = @factory.get_user(malicious_username)

    # Assert - injection should not return data
    assert_nil result
  end

  def test_prevents_stacked_queries_in_post_title
    # Arrange
    user = @factory.create_user('author', 'author@example.com', 'Author')

    # Attempt stacked query injection
    malicious_title = "Valid Title'; DROP TABLE posts; --"

    # Act - create post with malicious title
    post = @factory.create_post(user[:id], malicious_title, 'Content')

    # Assert - title should be stored as literal string
    assert_equal malicious_title, post[:title]

    # Assert - posts table should still exist (query the factory)
    assert @factory.get_post(post[:id])
  end

  def test_prevents_comment_injection_in_content
    # Arrange
    author = @factory.create_user('author', 'author@example.com', 'Author')
    post = @factory.create_post(author[:id], 'Test Post', 'Content')
    commenter = @factory.create_user('commenter', 'commenter@example.com', 'Commenter')

    # Attempt comment sequence injection
    malicious_content = "Valid content /* */ -- SELECT * FROM users"

    # Act
    comment = @factory.create_comment(commenter[:id], post[:id], malicious_content)

    # Assert - content should be stored as literal string
    assert_equal malicious_content, comment[:content]
  end

  def test_prevents_injection_with_encoded_characters
    # Arrange
    user = @factory.create_user('testuser', 'test@example.com', 'Test User')

    # Attempt injection with URL-encoded characters
    malicious_input = "admin%27%20OR%201=1--"

    # Act
    result = @factory.get_user(malicious_input)

    # Assert - should not find any user
    assert_nil result
  end

  def test_prevents_time_based_blind_injection
    # Arrange
    user = @factory.create_user('testuser', 'test@example.com', 'Test User')

    # Attempt time-based blind SQL injection
    malicious_input = "admin' AND SLEEP(5)--"

    # Act
    start_time = Time.now
    result = @factory.get_user(malicious_input)
    elapsed_time = Time.now - start_time

    # Assert - should not delay execution (< 1 second)
    assert elapsed_time < 1
    assert_nil result
  end

  def test_prevents_boolean_based_blind_injection
    # Arrange
    user = @factory.create_user('admin', 'admin@example.com', 'Admin')

    # Attempt boolean-based blind injection
    malicious_input = "admin' AND '1'='1"

    # Act
    result = @factory.get_user(malicious_input)

    # Assert - should not find user (entire string treated as literal)
    assert_nil result
  end

  def test_escapes_special_characters_in_bio
    # Arrange
    special_bio = "My bio with 'single quotes' and \"double quotes\" and <script>alert('xss')</script>"
    user = @factory.create_user('testuser', 'test@example.com', 'Test User', special_bio)

    # Act
    retrieved_user = @factory.get_user(user[:id])

    # Assert - special characters should be preserved
    assert_equal special_bio, retrieved_user[:bio]
  end

  def test_handles_null_byte_injection
    # Arrange
    # Null byte injection attempt
    malicious_username = "admin\x00malicious"

    # Act
    user = @factory.create_user(malicious_username, 'test@example.com', 'Test User')

    # Assert - username should be stored (with or without null byte based on implementation)
    assert user
    assert_includes user[:username], 'admin'
  end

  def test_prevents_nested_injection_patterns
    # Arrange
    user = @factory.create_user('testuser', 'test@example.com', 'Test User')

    # Attempt nested injection
    malicious_input = "test' OR ('1'='1' AND username='admin')--"

    # Act
    result = @factory.get_user(malicious_input)

    # Assert - should not find any user
    assert_nil result
  end

  # ============================================================================
  # XSS Prevention Tests (Data Layer)
  # ============================================================================

  def test_stores_html_tags_as_literal_strings
    # Arrange
    user = @factory.create_user('author', 'author@example.com', 'Author')
    html_content = '<script>alert("XSS")</script><img src=x onerror=alert(1)>'

    # Act
    post = @factory.create_post(user[:id], 'Test', html_content)
    retrieved_post = @factory.get_post(post[:id])

    # Assert - HTML should be stored as-is (escaping happens at presentation layer)
    assert_equal html_content, retrieved_post[:content]
  end

  def test_preserves_legitimate_html_entities
    # Arrange
    user = @factory.create_user('author', 'author@example.com', 'Author')
    content_with_entities = 'Test &lt;div&gt; and &amp; symbol'

    # Act
    post = @factory.create_post(user[:id], 'Test', content_with_entities)

    # Assert - entities should be preserved
    assert_equal content_with_entities, post[:content]
  end
end
