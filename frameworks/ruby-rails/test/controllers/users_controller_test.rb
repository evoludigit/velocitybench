require "test_helper"

class UsersControllerTest < ActionDispatch::IntegrationTest
  # ========================================================================
  # GET /users Tests
  # ========================================================================

  test "list users returns list" do
    # Arrange
    alice = create_test_user("alice", "alice@example.com", "Alice")
    bob = create_test_user("bob", "bob@example.com", "Bob")

    # Act
    get "/api/users"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_instance_of Array, data
    assert_equal 2, data.length
  end

  test "list users pagination default limit" do
    # Arrange - Create 20 users
    20.times { |i| create_test_user("user#{i}", "user#{i}@example.com") }

    # Act
    get "/api/users?page=0&size=10"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 10, data.length
  end

  test "list users custom limit" do
    # Arrange
    15.times { |i| create_test_user("user#{i}", "user#{i}@example.com") }

    # Act
    get "/api/users?page=0&size=5"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 5, data.length
  end

  test "list users pagination second page" do
    # Arrange
    20.times { |i| create_test_user("user#{i}", "user#{i}@example.com") }

    # Act
    get "/api/users?page=1&size=10"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal 10, data.length
  end

  # ========================================================================
  # GET /users/:id Tests
  # ========================================================================

  test "get user by id" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice")

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal user.id, data["id"]
    assert_equal "alice", data["username"]
    assert_equal "Alice", data["fullName"]
  end

  test "get user includes optional bio" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice", "Alice bio")

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_equal "Alice bio", data["bio"]
  end

  test "get user bio null when not provided" do
    # Arrange
    user = create_test_user("bob", "bob@example.com", "Bob")

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_nil data["bio"]
  end

  test "get user response structure" do
    # Arrange
    user = create_test_user("alice", "alice@example.com", "Alice", "Alice bio")

    # Act
    get "/api/users/#{user.id}"

    # Assert
    assert_response :success
    data = JSON.parse(@response.body)
    assert_includes data.keys, "id"
    assert_includes data.keys, "username"
    assert_includes data.keys, "fullName"
    assert_includes data.keys, "bio"
  end
end
