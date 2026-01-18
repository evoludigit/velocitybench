# frozen_string_literal: true

require_relative 'test_helper'

class ResolverTest < Minitest::Test
  def setup
    @factory = TestFactory.new
  end

  def teardown
    @factory.reset
  end

  # ============================================================================
  # User Query Tests
  # ============================================================================

  def test_query_user_by_uuid
    user = @factory.create_user('alice', 'alice@example.com', 'Alice Smith', 'Hello!')

    result = @factory.get_user(user[:id])

    assert result
    assert_equal user[:id], result[:id]
    assert_equal 'alice', result[:username]
    assert_equal 'Alice Smith', result[:full_name]
    assert_equal 'Hello!', result[:bio]
  end

  def test_query_users_returns_list
    @factory.create_user('alice', 'alice@example.com', 'Alice')
    @factory.create_user('bob', 'bob@example.com', 'Bob')
    @factory.create_user('charlie', 'charlie@example.com', 'Charlie')

    users = @factory.get_all_users

    assert_equal 3, users.length
  end

  def test_query_user_not_found
    result = @factory.get_user('non-existent-id')

    assert_nil result
  end

  # ============================================================================
  # Post Query Tests
  # ============================================================================

  def test_query_post_by_id
    user = @factory.create_user('author', 'author@example.com', 'Author')
    post = @factory.create_post(user[:id], 'Test Post', 'Test content')

    result = @factory.get_post(post[:id])

    assert result
    assert_equal 'Test Post', result[:title]
    assert_equal 'Test content', result[:content]
  end

  def test_query_posts_by_author
    user = @factory.create_user('author', 'author@example.com', 'Author')
    @factory.create_post(user[:id], 'Post 1', 'Content 1')
    @factory.create_post(user[:id], 'Post 2', 'Content 2')

    posts = @factory.get_posts_by_author(user[:pk_user])

    assert_equal 2, posts.length
  end

  # ============================================================================
  # Comment Query Tests
  # ============================================================================

  def test_query_comment_by_id
    author = @factory.create_user('author', 'author@example.com', 'Author')
    post = @factory.create_post(author[:id], 'Test Post', 'Content')
    commenter = @factory.create_user('commenter', 'commenter@example.com', 'Commenter')
    comment = @factory.create_comment(commenter[:id], post[:id], 'Great post!')

    result = @factory.get_comment(comment[:id])

    assert result
    assert_equal 'Great post!', result[:content]
  end

  def test_query_comments_by_post
    author = @factory.create_user('author', 'author@example.com', 'Author')
    post = @factory.create_post(author[:id], 'Test Post', 'Content')
    commenter = @factory.create_user('commenter', 'commenter@example.com', 'Commenter')
    @factory.create_comment(commenter[:id], post[:id], 'Comment 1')
    @factory.create_comment(commenter[:id], post[:id], 'Comment 2')

    comments = @factory.get_comments_by_post(post[:pk_post])

    assert_equal 2, comments.length
  end

  # ============================================================================
  # Relationship Tests
  # ============================================================================

  def test_user_posts_relationship
    user = @factory.create_user('author', 'author@example.com', 'Author')
    post1 = @factory.create_post(user[:id], 'Post 1', 'Content 1')
    post2 = @factory.create_post(user[:id], 'Post 2', 'Content 2')

    posts = @factory.get_posts_by_author(user[:pk_user])

    assert_equal 2, posts.length
    post_ids = posts.map { |p| p[:id] }
    assert_includes post_ids, post1[:id]
    assert_includes post_ids, post2[:id]
  end

  def test_post_author_relationship
    author = @factory.create_user('author', 'author@example.com', 'Author')
    post = @factory.create_post(author[:id], 'Test Post', 'Content')

    assert post[:author]
    assert_equal author[:pk_user], post[:author][:pk_user]
  end

  def test_comment_author_relationship
    author = @factory.create_user('author', 'author@example.com', 'Author')
    post = @factory.create_post(author[:id], 'Test Post', 'Content')
    commenter = @factory.create_user('commenter', 'commenter@example.com', 'Commenter')
    comment = @factory.create_comment(commenter[:id], post[:id], 'Great!')

    assert comment[:author]
    assert_equal commenter[:pk_user], comment[:author][:pk_user]
  end

  # ============================================================================
  # Edge Case Tests
  # ============================================================================

  def test_null_bio
    user = @factory.create_user('user', 'user@example.com', 'User')

    assert_nil user[:bio]
  end

  def test_empty_posts_list
    user = @factory.create_user('newuser', 'new@example.com', 'New User')

    posts = @factory.get_posts_by_author(user[:pk_user])

    assert_empty posts
  end

  def test_special_characters_in_content
    user = @factory.create_user('author', 'author@example.com', 'Author')
    special_content = "Test with 'quotes' and \"double quotes\" and <html>"
    post = @factory.create_post(user[:id], 'Special', special_content)

    assert_equal special_content, post[:content]
  end

  def test_unicode_content
    user = @factory.create_user('author', 'author@example.com', 'Author')
    unicode_content = 'Test with émojis 🎉 and ñ and 中文'
    post = @factory.create_post(user[:id], 'Unicode', unicode_content)

    assert_equal unicode_content, post[:content]
  end

  # ============================================================================
  # Performance Tests
  # ============================================================================

  def test_create_many_posts
    user = @factory.create_user('author', 'author@example.com', 'Author')

    50.times do |i|
      @factory.create_post(user[:id], "Post #{i}", 'Content')
    end

    posts = @factory.get_posts_by_author(user[:pk_user])
    assert_equal 50, posts.length
  end

  def test_reset
    @factory.create_user('user1', 'user1@example.com', 'User 1')
    @factory.create_user('user2', 'user2@example.com', 'User 2')

    @factory.reset

    assert_empty @factory.get_all_users
  end

  # ============================================================================
  # Validation Tests
  # ============================================================================

  def test_valid_uuid
    user = @factory.create_user('user', 'user@example.com', 'User')

    assert ValidationHelper.valid_uuid?(user[:id])
  end

  def test_create_post_with_invalid_author
    assert_raises(RuntimeError) do
      @factory.create_post('invalid-author', 'Test', 'Content')
    end
  end

  def test_create_comment_with_invalid_post
    user = @factory.create_user('user', 'user@example.com', 'User')

    assert_raises(RuntimeError) do
      @factory.create_comment(user[:id], 'invalid-post', 'Content')
    end
  end

  def test_long_content
    user = @factory.create_user('author', 'author@example.com', 'Author')
    long_content = DataGenerator.generate_long_string(100_000)
    post = @factory.create_post(user[:id], 'Long', long_content)

    assert_equal 100_000, post[:content].length
  end
end
