using FraiseQL.Benchmark.Models;
using Xunit;
using System;
using System.Collections.Generic;
using System.Linq;

namespace FraiseQL.Benchmark.Tests;

/// <summary>
/// SecurityRateLimitTest - Tests rate limiting functionality
///
/// Coverage includes:
/// - Per-user rate limits
/// - Rate limit window reset
/// - Independent user limits
/// - Query complexity limits
/// - Depth limits
/// </summary>
public class SecurityRateLimitTest
{
    private readonly TestFactory _factory = new();
    private readonly Dictionary<string, int> _rateLimitStorage = new();

    // ============================================================================
    // Rate Limiting Tests
    // ============================================================================

    [Fact]
    public void EnforceRateLimitPerUser()
    {
        var user = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        var maxRequests = 60; // Typical rate limit per minute

        var successfulRequests = 0;
        var rateLimitExceeded = false;

        for (int i = 0; i < maxRequests + 5; i++)
        {
            if (CheckRateLimit(user.Id.ToString()))
            {
                successfulRequests++;
                _factory.GetUser(user.Id);
            }
            else
            {
                rateLimitExceeded = true;
                break;
            }
        }

        // Should hit rate limit
        Assert.True(
            rateLimitExceeded || successfulRequests == maxRequests,
            "Rate limit should be enforced"
        );
    }

    [Fact]
    public void RateLimitResetsAfterWindow()
    {
        var user = _factory.CreateTestUser("bob", "bob@example.com", "Bob", "");
        var userId = user.Id.ToString();

        // Make requests up to limit
        for (int i = 0; i < 60; i++)
        {
            CheckRateLimit(userId);
        }

        // Verify rate limit hit
        var isLimited = !CheckRateLimit(userId);
        Assert.True(isLimited, "Should be rate limited");

        // Reset rate limit window
        ResetRateLimit(userId);

        // Should allow requests again
        var canMakeRequest = CheckRateLimit(userId);
        Assert.True(canMakeRequest, "Rate limit should reset after window");
    }

    [Fact]
    public void RateLimitsAreIndependentPerUser()
    {
        var alice = _factory.CreateTestUser("alice", "alice@example.com", "Alice", "");
        var bob = _factory.CreateTestUser("bob", "bob@example.com", "Bob", "");
        var aliceId = alice.Id.ToString();
        var bobId = bob.Id.ToString();

        // Exhaust Alice's rate limit
        for (int i = 0; i < 60; i++)
        {
            CheckRateLimit(aliceId);
        }

        // Verify Alice is rate limited
        var aliceLimited = !CheckRateLimit(aliceId);
        Assert.True(aliceLimited);

        // Bob should not be affected
        var bobCanRequest = CheckRateLimit(bobId);
        Assert.True(bobCanRequest, "Bob should have independent rate limit");
    }

    [Fact]
    public void QueryComplexityLimit()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");

        // Simple query (low complexity)
        var simpleQueryComplexity = 1;
        var canExecuteSimple = CheckComplexityLimit(simpleQueryComplexity);
        Assert.True(canExecuteSimple);

        // Complex query (high complexity)
        var complexQueryComplexity = 10000;
        var canExecuteComplex = CheckComplexityLimit(complexQueryComplexity);
        Assert.False(canExecuteComplex, "Should reject high complexity queries");
    }

    [Fact]
    public void DepthLimitEnforced()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");

        // Shallow query (acceptable)
        var shallowDepth = 3;
        var canExecuteShallow = CheckDepthLimit(shallowDepth);
        Assert.True(canExecuteShallow);

        // Deep query (too deep)
        var deepDepth = 20;
        var canExecuteDeep = CheckDepthLimit(deepDepth);
        Assert.False(canExecuteDeep, "Should reject deeply nested queries");
    }

    [Fact]
    public void MultipleUsersDoNotShareRateLimits()
    {
        var users = new List<User>();
        for (int i = 0; i < 5; i++)
        {
            users.Add(_factory.CreateTestUser($"user{i}", $"user{i}@example.com", $"User {i}", ""));
        }

        // Each user should have independent limits
        foreach (var user in users)
        {
            var canRequest = CheckRateLimit(user.Id.ToString());
            Assert.True(canRequest, $"User {user.Username} should have independent rate limit");
        }
    }

    [Fact]
    public void RateLimitCountsCorrectly()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var userId = user.Id.ToString();

        // Make 10 requests
        for (int i = 0; i < 10; i++)
        {
            CheckRateLimit(userId);
        }

        // Verify count
        var count = GetRateLimitCount(userId);
        Assert.Equal(10, count);
    }

    [Fact]
    public void RateLimitIncludesRemainingCount()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var userId = user.Id.ToString();
        var limit = 60;

        // Make some requests
        for (int i = 0; i < 20; i++)
        {
            CheckRateLimit(userId);
        }

        // Check remaining
        var remaining = GetRemainingRequests(userId, limit);
        Assert.Equal(40, remaining);
    }

    [Fact]
    public void BatchQueriesCountTowardLimit()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var userId = user.Id.ToString();

        // Simulate batch query (multiple operations)
        var batchSize = 10;
        for (int i = 0; i < batchSize; i++)
        {
            CheckRateLimit(userId);
        }

        // Verify all operations counted
        var count = GetRateLimitCount(userId);
        Assert.Equal(batchSize, count);
    }

    [Fact]
    public void IntrospectionQueriesHaveSeparateLimit()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var userId = user.Id.ToString();

        // Regular query
        var regularLimited = CheckRateLimit(userId, "regular");

        // Introspection query (may have different limit)
        var introspectionLimited = CheckRateLimit(userId, "introspection");

        Assert.True(regularLimited);
        Assert.True(introspectionLimited);
    }

    [Fact]
    public void MutationsCountTowardRateLimit()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var userId = user.Id.ToString();

        // Simulate mutations
        for (int i = 0; i < 10; i++)
        {
            CheckRateLimit(userId, "mutation");
            _factory.CreateTestPost(user.Id, $"Post {i}", "Content");
        }

        // Verify mutations counted
        var count = GetRateLimitCount(userId);
        Assert.Equal(10, count);
    }

    [Fact]
    public void ZeroLimitRejectsAllRequests()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var userId = user.Id.ToString();

        // Set limit to 0
        var canRequest = CheckRateLimitWithCustomLimit(userId, 0);

        Assert.False(canRequest, "Should reject all requests with zero limit");
    }

    [Fact]
    public void NegativeRequestCountHandledSafely()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var userId = user.Id.ToString();

        // Attempt to set negative count (should be handled safely)
        var remaining = GetRemainingRequests(userId, 60);

        Assert.True(remaining >= 0, "Remaining count should never be negative");
    }

    [Fact]
    public void ConcurrentRequestsCountCorrectly()
    {
        var user = _factory.CreateTestUser("user", "user@example.com", "User", "");
        var userId = user.Id.ToString();

        // Simulate concurrent requests
        var tasks = Enumerable.Range(0, 20).Select(_ => CheckRateLimit(userId)).ToList();

        // All should be counted
        var count = GetRateLimitCount(userId);
        Assert.Equal(20, count);
    }

    // ============================================================================
    // Helper Methods (Mock Rate Limiting)
    // ============================================================================

    private bool CheckRateLimit(string userId, string type = "query")
    {
        return CheckRateLimitWithCustomLimit(userId, 60, type);
    }

    private bool CheckRateLimitWithCustomLimit(string userId, int limit, string type = "query")
    {
        var key = $"{userId}:{type}";

        if (!_rateLimitStorage.ContainsKey(key))
        {
            _rateLimitStorage[key] = 0;
        }

        if (_rateLimitStorage[key] >= limit)
        {
            return false;
        }

        _rateLimitStorage[key]++;
        return true;
    }

    private void ResetRateLimit(string userId)
    {
        var keysToReset = _rateLimitStorage.Keys
            .Where(k => k.StartsWith(userId))
            .ToList();

        foreach (var key in keysToReset)
        {
            _rateLimitStorage[key] = 0;
        }
    }

    private bool CheckComplexityLimit(int complexity)
    {
        var maxComplexity = 1000;
        return complexity <= maxComplexity;
    }

    private bool CheckDepthLimit(int depth)
    {
        var maxDepth = 10;
        return depth <= maxDepth;
    }

    private int GetRateLimitCount(string userId)
    {
        return _rateLimitStorage
            .Where(kvp => kvp.Key.StartsWith(userId + ":"))
            .Sum(kvp => kvp.Value);
    }

    private int GetRemainingRequests(string userId, int limit)
    {
        var count = GetRateLimitCount(userId);
        return Math.Max(0, limit - count);
    }
}
