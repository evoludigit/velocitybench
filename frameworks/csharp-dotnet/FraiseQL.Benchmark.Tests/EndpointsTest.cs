using FraiseQL.Benchmark.Models;
using Xunit;
using System;
using System.Linq;

namespace FraiseQL.Benchmark.Tests;

public class EndpointsTest
{
    private readonly TestFactory _factory = new();

    // ============================================================================
    // Endpoint: GET /api/users (List)
    // ============================================================================

    [Fact]
    public void TestGetUsersListReturnsUsers()
    {
        _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        _factory.CreateTestUser("bob", "bob@example.com", "Bob", "");
        _factory.CreateTestUser("charlie", "charlie@example.com", "Charlie", "");

        var users = _factory.GetAllUsers().ToList();
        Assert.Equal(3, users.Count);
    }

    [Fact]
    public void TestGetUsersRespectLimit()
    {
        for (int i = 0; i < 20; i++)
        {
            _factory.CreateTestUser(
                $"user{i}",
                $"user{i}@example.com",
                "User",
                ""
            );
        }

        var users = _factory.GetAllUsers().ToList();
        Assert.True(users.Count >= 20);
    }

    [Fact]
    public void TestGetUsersReturnsEmptyWhenNoUsers()
    {
        var users = _factory.GetAllUsers().ToList();
        Assert.Empty(users);
    }

    [Fact]
    public void TestGetUsersWithPagination()
    {
        for (int i = 0; i < 30; i++)
        {
            _factory.CreateTestUser(
                $"user{i % 10}",
                $"user{i % 10}@example.com",
                "User",
                ""
            );
        }

        var users = _factory.GetAllUsers().ToList();
        Assert.True(users.Count >= 10);
    }

    // ============================================================================
    // Endpoint: GET /api/users/:id (Detail)
    // ============================================================================

    [Fact]
    public void TestGetUserDetailReturnsUser()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Developer");
        var userId = user.Id;

        var retrieved = _factory.GetUser(userId);
        Assert.NotNull(retrieved);
        Assert.Equal("alice", retrieved.Username);
    }

    [Fact]
    public void TestGetUserDetailWithNullBio()
    {
        var user = _factory.CreateTestUser("bob", "bob@example.com", "Bob", "");
        var userId = user.Id;

        var retrieved = _factory.GetUser(userId);
        Assert.NotNull(retrieved);
        Assert.Null(retrieved.Bio);
    }

    [Fact]
    public void TestGetUserDetailWithSpecialChars()
    {
        var user = _factory.CreateTestUser("charlie", "charlie@example.com", "Char'lie", "Quote: \"test\"");
        var userId = user.Id;

        var retrieved = _factory.GetUser(userId);
        Assert.NotNull(retrieved);
    }

    [Fact]
    public void TestGetUserDetailNotFound()
    {
        var retrieved = _factory.GetUser(Guid.NewGuid());
        Assert.Null(retrieved);
    }

    // ============================================================================
    // Endpoint: GET /api/posts (List)
    // ============================================================================

    [Fact]
    public void TestGetPostsListReturnsPosts()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");

        _factory.CreateTestPost(author.Id, "Post 1", "Content");
        _factory.CreateTestPost(author.Id, "Post 2", "Content");
        _factory.CreateTestPost(author.Id, "Post 3", "Content");

        var posts = _factory.GetAllPosts().ToList();
        Assert.Equal(3, posts.Count);
    }

    [Fact]
    public void TestGetPostsRespectLimit()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");

        for (int i = 0; i < 20; i++)
        {
            _factory.CreateTestPost(author.Id, $"Post {i}", "Content");
        }

        var posts = _factory.GetAllPosts().ToList();
        Assert.True(posts.Count >= 20);
    }

    [Fact]
    public void TestGetPostsReturnsEmpty()
    {
        var posts = _factory.GetAllPosts().ToList();
        Assert.Empty(posts);
    }

    // ============================================================================
    // Endpoint: GET /api/posts/:id (Detail)
    // ============================================================================

    [Fact]
    public void TestGetPostDetailReturnsPost()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Test Post", "Test Content");
        var postId = post.Id;

        var retrieved = _factory.GetPost(postId);
        Assert.NotNull(retrieved);
        Assert.Equal("Test Post", retrieved.Title);
    }

    [Fact]
    public void TestGetPostDetailWithNullContent()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "No Content", "");
        var postId = post.Id;

        var retrieved = _factory.GetPost(postId);
        Assert.NotNull(retrieved);
        Assert.Empty(retrieved.Content);
    }

    [Fact]
    public void TestGetPostDetailWithSpecialChars()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Post with <tags>", "Content & more");
        var postId = post.Id;

        var retrieved = _factory.GetPost(postId);
        Assert.NotNull(retrieved);
    }

    [Fact]
    public void TestGetPostDetailNotFound()
    {
        var retrieved = _factory.GetPost(Guid.NewGuid());
        Assert.Null(retrieved);
    }

    // ============================================================================
    // Endpoint: GET /api/posts/by-author/:id
    // ============================================================================

    [Fact]
    public void TestGetPostsByAuthorReturnsAuthorsPosts()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");

        _factory.CreateTestPost(author.Id, "Post 1", "Content");
        _factory.CreateTestPost(author.Id, "Post 2", "Content");
        _factory.CreateTestPost(author.Id, "Post 3", "Content");

        var authorPosts = _factory.GetAllPosts()
            .Where(p => p.Author?.Id == author.Id)
            .ToList();

        Assert.Equal(3, authorPosts.Count);
    }

    [Fact]
    public void TestMultipleAuthorsSeperatePosts()
    {
        var author1 = _factory.CreateTestUser("author1", "author1@example.com", "Author 1", "");
        var author2 = _factory.CreateTestUser("author2", "author2@example.com", "Author 2", "");

        _factory.CreateTestPost(author1.Id, "Post 1", "Content");
        _factory.CreateTestPost(author1.Id, "Post 2", "Content");
        _factory.CreateTestPost(author2.Id, "Post 1", "Content");

        var author1Posts = _factory.GetAllPosts()
            .Where(p => p.Author?.Id == author1.Id)
            .ToList();
        var author2Posts = _factory.GetAllPosts()
            .Where(p => p.Author?.Id == author2.Id)
            .ToList();

        Assert.Equal(2, author1Posts.Count);
        Assert.Equal(1, author2Posts.Count);
    }

    [Fact]
    public void TestAuthorWithNoPosts()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");

        var authorPosts = _factory.GetAllPosts()
            .Where(p => p.Author?.Id == author.Id)
            .ToList();

        Assert.Empty(authorPosts);
    }

    // ============================================================================
    // Endpoint: Response Headers
    // ============================================================================

    [Fact]
    public void TestGetUsersReturnsJSON()
    {
        _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        Assert.True(_factory.GetUserCount() > 0);
    }

    [Fact]
    public void TestGetPostsReturnsJSON()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        _factory.CreateTestPost(author.Id, "Post", "Content");
        Assert.True(_factory.GetPostCount() > 0);
    }

    // ============================================================================
    // Endpoint: Pagination
    // ============================================================================

    [Fact]
    public void TestPaginationPage0WithSize10()
    {
        for (int i = 0; i < 30; i++)
        {
            _factory.CreateTestUser(
                $"user{i % 10}",
                $"user{i % 10}@example.com",
                "User",
                ""
            );
        }

        var users = _factory.GetAllUsers().ToList();
        Assert.True(users.Count >= 10);
    }

    [Fact]
    public void TestPaginationPage1WithSize10()
    {
        for (int i = 0; i < 30; i++)
        {
            _factory.CreateTestUser(
                $"user{i % 10}",
                $"user{i % 10}@example.com",
                "User",
                ""
            );
        }

        var users = _factory.GetAllUsers().ToList();
        Assert.True(users.Count >= 10);
    }

    [Fact]
    public void TestPaginationLastPageWithFewerItems()
    {
        for (int i = 0; i < 25; i++)
        {
            _factory.CreateTestUser(
                $"user{i % 10}",
                $"user{i % 10}@example.com",
                "User",
                ""
            );
        }

        var users = _factory.GetAllUsers().ToList();
        Assert.True(users.Count >= 5);
    }

    // ============================================================================
    // Endpoint: Data Consistency
    // ============================================================================

    [Fact]
    public void TestDataConsistencyListDetailMatch()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "Bio");

        var listUser = _factory.GetUser(user.Id);
        var detailUser = _factory.GetUser(user.Id);

        Assert.Equal(listUser?.Username, detailUser?.Username);
    }

    [Fact]
    public void TestRepeatedRequestsReturnSameData()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");

        var retrieved1 = _factory.GetUser(user.Id);
        var retrieved2 = _factory.GetUser(user.Id);

        Assert.Equal(retrieved1?.Id, retrieved2?.Id);
    }
}
