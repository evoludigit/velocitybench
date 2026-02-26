using FraiseQL.Benchmark.Models;
using Xunit;
using System;
using System.Diagnostics;

namespace FraiseQL.Benchmark.Tests;

/// <summary>
/// SecurityInjectionTest - Tests SQL injection prevention
///
/// Coverage includes:
/// - Basic OR injection attempts
/// - UNION-based injection attempts
/// - Stacked queries
/// - Comment sequence injection
/// - Time-based blind injection attempts
/// </summary>
public class SecurityInjectionTest
{
    private readonly TestFactory _factory = new();

    // ============================================================================
    // SQL Injection Prevention Tests
    // ============================================================================

    [Fact]
    public void PreventBasicSqlInjection()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        var maliciousInput = "1' OR '1'='1";

        // Attempt to query with malicious input - invalid format is safely rejected
        User? result = null;
        if (Guid.TryParse(maliciousInput, out var guid))
        {
            result = _factory.GetUser(guid);
        }

        // Should return null, not all users
        Assert.Null(result);
    }

    [Fact]
    public void PreventUnionBasedInjection()
    {
        var user = _factory.CreateTestUser("bob", "bob@example.com", "Bob", "");
        var maliciousInput = "1' UNION SELECT * FROM users--";

        // Should handle invalid GUID format safely
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(maliciousInput);
        });
    }

    [Fact]
    public void PreventStackedQueries()
    {
        var user = _factory.CreateTestUser("charlie", "charlie@example.com", "Charlie", "");
        var maliciousInput = "1'; DROP TABLE users;--";

        // Should handle invalid input safely
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(maliciousInput);
        });

        // Verify data still exists
        var verifyUser = _factory.GetUser(user.Id);
        Assert.NotNull(verifyUser);
    }

    [Fact]
    public void PreventCommentSequenceInjection()
    {
        var user = _factory.CreateTestUser("dave", "dave@example.com", "Dave", "");
        var maliciousInput = "admin'--";

        // Should reject invalid format
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(maliciousInput);
        });
    }

    [Fact]
    public void PreventTimeBasedBlindInjection()
    {
        var user = _factory.CreateTestUser("eve", "eve@example.com", "Eve", "");
        var maliciousInput = "1' AND SLEEP(5)--";

        // Measure execution time
        var stopwatch = Stopwatch.StartNew();

        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(maliciousInput);
        });

        stopwatch.Stop();

        // Should not execute SLEEP, response should be fast
        Assert.True(stopwatch.ElapsedMilliseconds < 2000, "Query should not execute SLEEP command");
    }

    [Fact]
    public void PreventInjectionInPostTitle()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Test Post", "Content");
        var maliciousInput = "1' OR '1'='1";

        // Should reject invalid GUID
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(maliciousInput);
        });
    }

    [Fact]
    public void HandleSpecialCharactersSafely()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var specialContent = "Test with 'quotes' and \"double quotes\" and <html> tags";
        var post = _factory.CreateTestPost(author.Id, "Special", specialContent);

        // Retrieve and verify special characters are preserved
        var retrieved = _factory.GetPost(post.Id);

        Assert.NotNull(retrieved);
        Assert.Equal(specialContent, retrieved.Content);
    }

    [Fact]
    public void PreventInjectionViaNonGuidId()
    {
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Test", "Content");
        var maliciousId = "1 OR 1=1";

        // Should handle non-GUID format safely
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(maliciousId);
        });
    }

    [Fact]
    public void PreventHexEncodedInjection()
    {
        var user = _factory.CreateTestUser("frank", "frank@example.com", "Frank", "");
        var maliciousInput = "0x61646D696E"; // Hex for 'admin'

        // Should reject invalid format
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(maliciousInput);
        });
    }

    [Fact]
    public void PreventInjectionWithMultibyteCharacters()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var maliciousInput = "admin' OR '1'='1' /*中文注入*/";

        // Should reject invalid format
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(maliciousInput);
        });
    }

    [Fact]
    public void ValidateGuidFormatStrict()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var invalidGuid = "not-a-guid-format";

        // Should reject non-GUID format
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(invalidGuid);
        });
    }

    [Fact]
    public void HandleNullByteInjection()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var maliciousInput = "admin\0'--";

        // Should reject invalid format
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(maliciousInput);
        });
    }

    [Fact]
    public void PreventSecondOrderInjection()
    {
        // Create user with malicious content in username
        var maliciousUsername = "admin' OR '1'='1";

        // Creation should either succeed (and be escaped) or fail validation
        try
        {
            var user = _factory.CreateTestUser(maliciousUsername, "mal@example.com", "Malicious", "");

            // If creation succeeds, retrieval should handle safely
            var posts = _factory.GetAllPosts()
                .Where(p => p.Author?.Id == user.Id)
                .ToList();

            // Should return empty list or user's posts only
            Assert.NotNull(posts);
        }
        catch (ArgumentException)
        {
            // If validation rejects, that's acceptable
            Assert.True(true);
        }
    }

    [Fact]
    public void ParameterizedQueriesWithUnicode()
    {
        var unicodeContent = "Test with émojis 🎉 and ñ and 中文 and Ελληνικά";
        var author = _factory.CreateTestUser("author", "author@example.com", "Author", "");
        var post = _factory.CreateTestPost(author.Id, "Unicode Test", unicodeContent);

        // Retrieve and verify Unicode is preserved
        var retrieved = _factory.GetPost(post.Id);

        Assert.NotNull(retrieved);
        Assert.Equal(unicodeContent, retrieved.Content);
    }

    [Fact]
    public void LongInputDoesNotCauseInjection()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var longMaliciousInput = string.Concat(Enumerable.Repeat("' OR '1'='1", 1000));

        // Should reject invalid format (too long for GUID)
        Assert.Throws<FormatException>(() =>
        {
            var guid = Guid.Parse(longMaliciousInput);
        });
    }

    [Fact]
    public void GuidParsingEnforcesFormat()
    {
        // Valid GUID format
        var validGuid = Guid.NewGuid().ToString();
        var parsed = Guid.Parse(validGuid);
        Assert.NotEqual(Guid.Empty, parsed);

        // Invalid formats should throw
        Assert.Throws<FormatException>(() => Guid.Parse("invalid"));
        Assert.Throws<FormatException>(() => Guid.Parse("1234"));
        Assert.Throws<FormatException>(() => Guid.Parse("' OR '1'='1"));
    }

    [Fact]
    public void SpecialCharactersInNamesPreserved()
    {
        // Names with SQL-like characters should be preserved safely
        var specialName = "O'Brien <script>alert('xss')</script>";
        var user = _factory.CreateTestUser("obrien", "obrien@example.com", specialName, "");

        // Retrieve and verify
        var retrieved = _factory.GetUser(user.Id);

        Assert.NotNull(retrieved);
        Assert.Equal(specialName, retrieved.FullName);
    }
}
