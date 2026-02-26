using FraiseQL.Benchmark.Models;
using System;
using System.Collections.Generic;
using System.Linq;

namespace FraiseQL.Benchmark.Tests;

public class TestFactory
{
    private readonly Dictionary<Guid, User> _users = new();
    private readonly Dictionary<Guid, Post> _posts = new();
    private int _userCounter = 1;
    private int _postCounter = 1;

    public User CreateTestUser(string username, string email, string fullName, string bio)
    {
        var user = new User
        {
            PkUser = _userCounter++,
            Id = Guid.NewGuid(),
            Username = username,
            FullName = fullName,
            Bio = string.IsNullOrEmpty(bio) ? null : bio,
            CreatedAt = DateTime.UtcNow,
            Posts = new List<Post>(),
            Comments = new List<Comment>()
        };

        _users[user.Id] = user;
        return user;
    }

    public Post CreateTestPost(Guid authorId, string title, string content)
    {
        if (!_users.TryGetValue(authorId, out var author))
        {
            throw new ArgumentException($"Author not found: {authorId}");
        }

        var post = new Post
        {
            PkPost = _postCounter++,
            Id = Guid.NewGuid(),
            Title = title,
            Content = string.IsNullOrEmpty(content) ? string.Empty : content,
            FkAuthor = author.PkUser,
            Author = author,
            CreatedAt = DateTime.UtcNow,
            Comments = new List<Comment>()
        };

        _posts[post.Id] = post;
        return post;
    }

    public Comment CreateTestComment(Guid authorId, Guid postId, string content)
    {
        if (!_users.TryGetValue(authorId, out var author))
        {
            throw new ArgumentException($"Author not found: {authorId}");
        }

        if (!_posts.TryGetValue(postId, out var post))
        {
            throw new ArgumentException($"Post not found: {postId}");
        }

        var comment = new Comment
        {
            Id = Guid.NewGuid(),
            Content = content,
            Author = author,
            Post = post,
            CreatedAt = DateTime.UtcNow
        };

        return comment;
    }

    public User? GetUser(Guid id)
    {
        _users.TryGetValue(id, out var user);
        return user;
    }

    public Post? GetPost(Guid id)
    {
        _posts.TryGetValue(id, out var post);
        return post;
    }

    public IEnumerable<User> GetAllUsers() => _users.Values;

    public IEnumerable<Post> GetAllPosts() => _posts.Values;

    public int GetUserCount() => _users.Count;

    public int GetPostCount() => _posts.Count;

    public void Reset()
    {
        _users.Clear();
        _posts.Clear();
        _userCounter = 1;
        _postCounter = 1;
    }
}
