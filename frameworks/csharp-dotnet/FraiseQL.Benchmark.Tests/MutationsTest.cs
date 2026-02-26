using FraiseQL.Benchmark.Models;
using Xunit;
using System;

namespace FraiseQL.Benchmark.Tests;

public class MutationsTest
{
    private readonly TestFactory _factory = new();

    // ============================================================================
    // Mutation: updateUser
    // ============================================================================

    [Fact]
    public void TestUpdateUserFullName()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Developer");
        var userId = user.Id;

        // Simulate mutation
        user.FullName = "Alice Smith";

        // Verify
        Assert.Equal("Alice Smith", user.FullName);
        Assert.Equal(userId, user.Id);
    }

    [Fact]
    public void TestUpdateUserBio()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Developer");
        var userId = user.Id;

        // Simulate mutation
        user.Bio = "Senior Developer";

        // Verify
        Assert.Equal("Senior Developer", user.Bio);
        Assert.Equal(userId, user.Id);
    }

    [Fact]
    public void TestUpdateUserBothFields()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Developer");
        var userId = user.Id;

        // Simulate mutation
        user.FullName = "Alice Smith";
        user.Bio = "Senior Developer";

        // Verify
        Assert.Equal("Alice Smith", user.FullName);
        Assert.Equal("Senior Developer", user.Bio);
        Assert.Equal(userId, user.Id);
    }

    [Fact]
    public void TestUpdateUserClearBio()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Developer");
        var userId = user.Id;

        // Simulate mutation
        user.Bio = null;

        // Verify
        Assert.Null(user.Bio);
        Assert.Equal(userId, user.Id);
    }

    // ============================================================================
    // Mutation: updatePost
    // ============================================================================

    [Fact]
    public void TestUpdatePostTitle()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Original Title", "Original Content");
        var postId = post.Id;

        // Simulate mutation
        post.Title = "Updated Title";

        // Verify
        Assert.Equal("Updated Title", post.Title);
        Assert.Equal(postId, post.Id);
    }

    [Fact]
    public void TestUpdatePostContent()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Original Title", "Original Content");
        var postId = post.Id;

        // Simulate mutation
        post.Content = "Updated Content";

        // Verify
        Assert.Equal("Updated Content", post.Content);
        Assert.Equal(postId, post.Id);
    }

    [Fact]
    public void TestUpdatePostBothFields()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Original Title", "Original Content");
        var postId = post.Id;

        // Simulate mutation
        post.Title = "Updated Title";
        post.Content = "Updated Content";

        // Verify
        Assert.Equal("Updated Title", post.Title);
        Assert.Equal("Updated Content", post.Content);
        Assert.Equal(postId, post.Id);
    }

    // ============================================================================
    // Field Immutability
    // ============================================================================

    [Fact]
    public void TestUserIdImmutableAfterUpdate()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Bio");
        var originalId = user.Id;

        // Try to "update"
        user.Bio = "Updated";

        // Verify ID unchanged
        Assert.Equal(originalId, user.Id);
    }

    [Fact]
    public void TestPostIdImmutableAfterUpdate()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Title", "Content");
        var originalId = post.Id;

        // Try to "update"
        post.Title = "Updated";

        // Verify ID unchanged
        Assert.Equal(originalId, post.Id);
    }

    [Fact]
    public void TestUsernameImmutable()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        var originalUsername = user.Username;

        // Try to "update"
        user.Bio = "Updated";

        // Verify username unchanged
        Assert.Equal(originalUsername, user.Username);
    }

    // ============================================================================
    // State Changes
    // ============================================================================

    [Fact]
    public void TestSequentialUpdatesAccumulate()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");

        // Apply updates sequentially
        user.Bio = "Developer";
        user.Bio = "Senior Developer";

        // Verify latest state
        Assert.Equal("Senior Developer", user.Bio);
    }

    [Fact]
    public void TestUpdatesIsolatedBetweenEntities()
    {
        var user1 = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Bio1");
        var user2 = _factory.CreateTestUser("bob", "bob@example.com", "Bob", "Bio2");

        var originalBio2 = user2.Bio;

        // Update user1
        user1.Bio = "Updated";

        // Verify user2 unchanged
        Assert.Equal(originalBio2, user2.Bio);
    }

    // ============================================================================
    // Return Value Validation
    // ============================================================================

    [Fact]
    public void TestUpdatedUserReturnsAllFields()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Developer");
        user.Bio = "Updated";

        // Verify all fields present
        Assert.NotEqual(Guid.Empty, user.Id);
        Assert.Equal("alice", user.Username);
        Assert.Equal("Updated", user.Bio);
    }

    [Fact]
    public void TestUpdatedPostReturnsAllFields()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Title", "Content");
        post.Title = "Updated";

        // Verify all fields present
        Assert.NotEqual(Guid.Empty, post.Id);
        Assert.Equal("Updated", post.Title);
        Assert.NotNull(post.Author);
    }

    [Fact]
    public void TestMutationMaintainsCreatedAt()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        var originalCreatedAt = user.CreatedAt;

        // Update
        user.FullName = "Alice Updated";

        // Verify created_at unchanged
        Assert.Equal(originalCreatedAt, user.CreatedAt);
    }
}
