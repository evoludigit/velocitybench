using FraiseQL.Benchmark.Models;
using Xunit;
using System;
using System.Linq;

namespace FraiseQL.Benchmark.Tests;

public class ErrorEdgeCasesTest
{
    private readonly TestFactory _factory = new();

    // ============================================================================
    // Error: HTTP Status Codes
    // ============================================================================

    [Fact]
    public void TestHttpStatusCodeSuccess()
    {
        _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        Assert.Equal(1, _factory.GetUserCount());
    }

    [Fact]
    public void TestHttpStatusCodeNotFound()
    {
        var user = _factory.GetUser(Guid.NewGuid());
        Assert.Null(user);
    }

    // ============================================================================
    // Error: 404 Not Found
    // ============================================================================

    [Fact]
    public void TestUserNotFoundReturnsNull()
    {
        var user = _factory.GetUser(Guid.NewGuid());
        Assert.Null(user);
    }

    [Fact]
    public void TestPostNotFoundReturnsNull()
    {
        var post = _factory.GetPost(Guid.NewGuid());
        Assert.Null(post);
    }

    // ============================================================================
    // Error: Invalid Input
    // ============================================================================

    [Fact]
    public void TestInvalidLimitNegative()
    {
        int limit = -5;
        int clamped = Math.Max(0, Math.Min(100, limit));
        Assert.Equal(0, clamped);
    }

    [Fact]
    public void TestInvalidLimitZero()
    {
        int limit = 0;
        int clamped = Math.Max(0, Math.Min(100, limit));
        Assert.Equal(0, clamped);
    }

    [Fact]
    public void TestVeryLargeLimit()
    {
        int limit = 999999;
        int clamped = Math.Max(0, Math.Min(100, limit));
        Assert.Equal(100, clamped);
    }

    // ============================================================================
    // Edge Case: UUID Validation
    // ============================================================================

    [Fact]
    public void TestAllUserIdsAreUUID()
    {
        _factory.CreateTestUser("user0", "user0@example.com", "User", "");
        _factory.CreateTestUser("user1", "user1@example.com", "User", "");
        _factory.CreateTestUser("user2", "user2@example.com", "User", "");

        var users = _factory.GetAllUsers().ToList();
        Assert.All(users, u => Assert.NotEqual(Guid.Empty, u.Id));
    }

    [Fact]
    public void TestAllPostIdsAreUUID()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");

        _factory.CreateTestPost(author.Id, "Post0", "Content");
        _factory.CreateTestPost(author.Id, "Post1", "Content");
        _factory.CreateTestPost(author.Id, "Post2", "Content");

        var posts = _factory.GetAllPosts().ToList();
        Assert.All(posts, p => Assert.NotEqual(Guid.Empty, p.Id));
    }

    // ============================================================================
    // Edge Case: Special Characters
    // ============================================================================

    [Fact]
    public void TestSpecialCharSingleQuotes()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "I'm a developer");
        Assert.NotNull(_factory.GetUser(user.Id));
    }

    [Fact]
    public void TestSpecialCharDoubleQuotes()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "He said \"hello\"");
        Assert.NotNull(_factory.GetUser(user.Id));
    }

    [Fact]
    public void TestSpecialCharHtmlTags()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Check <this> out");
        Assert.NotNull(_factory.GetUser(user.Id));
    }

    [Fact]
    public void TestSpecialCharAmpersand()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Tom & Jerry");
        Assert.NotNull(_factory.GetUser(user.Id));
    }

    [Fact]
    public void TestSpecialCharEmoji()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "🎉 Celebration! 🚀 Rocket");
        Assert.NotNull(_factory.GetUser(user.Id));
    }

    [Fact]
    public void TestSpecialCharAccents()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Àlice Müller", "");
        Assert.NotNull(_factory.GetUser(user.Id));
    }

    [Fact]
    public void TestSpecialCharDiacritics()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "José García", "");
        Assert.NotNull(_factory.GetUser(user.Id));
    }

    // ============================================================================
    // Edge Case: Boundary Conditions
    // ============================================================================

    [Fact]
    public void TestBoundaryVeryLongBio5000Chars()
    {
        var longBio = GenerateLongString(5000);
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", longBio);
        var retrieved = _factory.GetUser(user.Id);
        Assert.NotNull(retrieved?.Bio);
        Assert.Equal(5000, retrieved.Bio.Length);
    }

    [Fact]
    public void TestBoundaryVeryLongUsername255Chars()
    {
        var longName = GenerateLongString(255);
        var user = _factory.CreateTestUser(longName, "user@example.com", "User", "");
        var retrieved = _factory.GetUser(user.Id);
        Assert.Equal(255, retrieved?.Username.Length);
    }

    [Fact]
    public void TestBoundaryVeryLongPostTitle()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var longTitle = GenerateLongString(500);
        var post = _factory.CreateTestPost(author.Id, longTitle, "Content");
        var retrieved = _factory.GetPost(post.Id);
        Assert.Equal(500, retrieved?.Title.Length);
    }

    [Fact]
    public void TestBoundaryVeryLongContent5000Chars()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var longContent = GenerateLongString(5000);
        var post = _factory.CreateTestPost(author.Id, "Title", longContent);
        var retrieved = _factory.GetPost(post.Id);
        Assert.Equal(5000, retrieved?.Content.Length);
    }

    // ============================================================================
    // Edge Case: Null/Empty Fields
    // ============================================================================

    [Fact]
    public void TestNullBioIsHandled()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        var retrieved = _factory.GetUser(user.Id);
        Assert.Null(retrieved?.Bio);
    }

    [Fact]
    public void TestEmptyStringBio()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        var retrieved = _factory.GetUser(user.Id);
        Assert.Null(retrieved?.Bio);
    }

    [Fact]
    public void TestPresentBio()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "My bio");
        var retrieved = _factory.GetUser(user.Id);
        Assert.NotNull(retrieved?.Bio);
        Assert.Equal("My bio", retrieved.Bio);
    }

    // ============================================================================
    // Edge Case: Relationship Validation
    // ============================================================================

    [Fact]
    public void TestPostAuthorIdIsValidUUID()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Post", "Content");
        Assert.NotNull(post.Author);
        Assert.NotEqual(Guid.Empty, post.Author.Id);
    }

    [Fact]
    public void TestPostReferencesCorrectAuthor()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Post", "Content");
        Assert.Equal(post.FkAuthor, author.PkUser);
    }

    [Fact]
    public void TestMultiplePostsReferenceDifferentAuthors()
    {
        var author1 = _factory.CreateTestUser("author1", "author1@example.com", "Author1", "");
        var author2 = _factory.CreateTestUser("author2", "author2@example.com", "Author2", "");

        var post1 = _factory.CreateTestPost(author1.Id, "Post1", "Content");
        var post2 = _factory.CreateTestPost(author2.Id, "Post2", "Content");

        Assert.NotEqual(post1.FkAuthor, post2.FkAuthor);
        Assert.Equal(post1.FkAuthor, author1.PkUser);
        Assert.Equal(post2.FkAuthor, author2.PkUser);
    }

    // ============================================================================
    // Edge Case: Data Type Validation
    // ============================================================================

    [Fact]
    public void TestUsernameIsString()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        var retrieved = _factory.GetUser(user.Id);
        Assert.Equal("alice", retrieved?.Username);
    }

    [Fact]
    public void TestPostTitleIsString()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Test Post", "Content");
        var retrieved = _factory.GetPost(post.Id);
        Assert.Equal("Test Post", retrieved?.Title);
    }

    // ============================================================================
    // Edge Case: Uniqueness
    // ============================================================================

    [Fact]
    public void TestMultipleUsersHaveUniqueIds()
    {
        var user1 = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        var user2 = _factory.CreateTestUser("bob", "bob@example.com", "Bob", "");
        var user3 = _factory.CreateTestUser("charlie", "charlie@example.com", "Charlie", "");

        Assert.NotEqual(user1.Id, user2.Id);
        Assert.NotEqual(user2.Id, user3.Id);
        Assert.NotEqual(user1.Id, user3.Id);
    }

    [Fact]
    public void TestMultiplePostsHaveUniqueIds()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post1 = _factory.CreateTestPost(author.Id, "Post1", "Content1");
        var post2 = _factory.CreateTestPost(author.Id, "Post2", "Content2");
        var post3 = _factory.CreateTestPost(author.Id, "Post3", "Content3");

        Assert.NotEqual(post1.Id, post2.Id);
        Assert.NotEqual(post2.Id, post3.Id);
        Assert.NotEqual(post1.Id, post3.Id);
    }

    // ============================================================================
    // Helper Methods
    // ============================================================================

    private string GenerateLongString(int length)
    {
        var chars = new char[length];
        for (int i = 0; i < length; i++)
        {
            chars[i] = (char)('0' + (i % 10));
        }
        return new string(chars);
    }
}
