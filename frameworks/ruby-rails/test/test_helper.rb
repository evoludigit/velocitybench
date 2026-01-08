ENV["RAILS_ENV"] ||= "test"
require_relative "../config/environment"
require "rails/test_help"

module ActiveSupport
  class TestCase
    # Run tests in parallel with specified workers
    parallelize(workers: :number_of_processors)

    # Setup all fixtures in test/fixtures/*.yml for all tests in alphabetical order.
    fixtures :all

    # Add more helper methods to be used by all tests here...

    # Factory methods for test data creation
    # Follows the Trinity Identifier Pattern:
    # - pk_{entity}: Internal INTEGER primary key for database joins
    # - id: UUID for public API access
    # - identifier: TEXT slug for human-readable access (future)

    def create_test_user(username, email = nil, full_name = nil, bio = nil)
      """Create a test user with flexible parameters."""
      email ||= "#{username}@example.com"
      full_name ||= username.capitalize

      User.create!(
        username: username,
        email: email,
        full_name: full_name,
        bio: bio
      )
    end

    def create_test_post(author_id, title, content = nil)
      """Create a test post with flexible parameters."""
      content ||= "Test content for #{title}"

      Post.create!(
        fk_author: author_id,
        title: title,
        content: content
      )
    end

    def create_test_comment(post_id, author_id, content = nil)
      """Create a test comment with flexible parameters."""
      content ||= "Test comment"

      Comment.create!(
        fk_post: post_id,
        fk_author: author_id,
        content: content
      )
    end
  end
end
