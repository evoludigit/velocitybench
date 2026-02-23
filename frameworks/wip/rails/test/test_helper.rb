# frozen_string_literal: true

require 'minitest/autorun'
require 'securerandom'
require 'time'

# In-memory test factory for isolated tests
class TestFactory
  attr_reader :users, :posts, :comments

  def initialize
    @users = {}
    @posts = {}
    @comments = {}
    @user_counter = 0
    @post_counter = 0
    @comment_counter = 0
  end

  def create_user(username, email, full_name, bio = nil)
    @user_counter += 1
    user = {
      id: SecureRandom.uuid,
      pk_user: @user_counter,
      username: username,
      email: email,
      full_name: full_name,
      bio: bio,
      created_at: Time.now.utc,
      updated_at: Time.now.utc
    }
    @users[user[:id]] = user
    user
  end

  def create_post(author_id, title, content = 'Default content')
    author = @users[author_id]
    raise "Author not found: #{author_id}" unless author

    @post_counter += 1
    post = {
      id: SecureRandom.uuid,
      pk_post: @post_counter,
      fk_author: author[:pk_user],
      title: title,
      content: content,
      created_at: Time.now.utc,
      updated_at: Time.now.utc,
      author: author
    }
    @posts[post[:id]] = post
    post
  end

  def create_comment(author_id, post_id, content)
    author = @users[author_id]
    post = @posts[post_id]
    raise 'Author not found' unless author
    raise 'Post not found' unless post

    @comment_counter += 1
    comment = {
      id: SecureRandom.uuid,
      pk_comment: @comment_counter,
      fk_post: post[:pk_post],
      fk_author: author[:pk_user],
      content: content,
      created_at: Time.now.utc,
      author: author,
      post: post
    }
    @comments[comment[:id]] = comment
    comment
  end

  def get_user(id)
    @users[id]
  end

  def get_post(id)
    @posts[id]
  end

  def get_comment(id)
    @comments[id]
  end

  def get_all_users
    @users.values
  end

  def get_posts_by_author(author_pk)
    @posts.values.select { |p| p[:fk_author] == author_pk }
  end

  def get_comments_by_post(post_pk)
    @comments.values.select { |c| c[:fk_post] == post_pk }
  end

  def reset
    @users.clear
    @posts.clear
    @comments.clear
    @user_counter = 0
    @post_counter = 0
    @comment_counter = 0
  end
end

module ValidationHelper
  UUID_REGEX = /\A[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\z/i

  def self.valid_uuid?(str)
    UUID_REGEX.match?(str)
  end
end

module DataGenerator
  def self.generate_long_string(length)
    'x' * length
  end

  def self.generate_random_username
    "user_#{SecureRandom.hex(4)}"
  end
end
