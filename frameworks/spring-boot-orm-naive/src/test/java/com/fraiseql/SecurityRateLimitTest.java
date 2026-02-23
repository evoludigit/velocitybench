package com.fraiseql;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.time.Instant;

/**
 * Rate Limiting Test Suite
 * Tests that the application properly enforces rate limits per user.
 */
class SecurityRateLimitTest {
    private TestFactory factory;
    private RateLimiter rateLimiter;

    @BeforeEach
    void setUp() {
        factory = new TestFactory();
        rateLimiter = new RateLimiter(5, 60); // 5 requests per 60 seconds
    }

    // ============================================================================
    // Rate Limiting Tests
    // ============================================================================

    @Test
    void testWithinRateLimit() {
        TestFactory.TestUser user = factory.createUser("user1", "user1@example.com", "User 1", "");

        // Make 5 requests (within limit)
        for (int i = 0; i < 5; i++) {
            assertTrue(rateLimiter.allowRequest(user.id));
        }
    }

    @Test
    void testExceedRateLimit() {
        TestFactory.TestUser user = factory.createUser("user1", "user1@example.com", "User 1", "");

        // Make 5 requests (within limit)
        for (int i = 0; i < 5; i++) {
            assertTrue(rateLimiter.allowRequest(user.id));
        }

        // 6th request should be blocked
        assertFalse(rateLimiter.allowRequest(user.id));
    }

    @Test
    void testRateLimitWindowReset() throws InterruptedException {
        TestFactory.TestUser user = factory.createUser("user1", "user1@example.com", "User 1", "");

        // Use a short window for testing
        RateLimiter shortLimiter = new RateLimiter(2, 1); // 2 requests per 1 second

        // Make 2 requests
        assertTrue(shortLimiter.allowRequest(user.id));
        assertTrue(shortLimiter.allowRequest(user.id));

        // 3rd request should be blocked
        assertFalse(shortLimiter.allowRequest(user.id));

        // Wait for window to reset
        Thread.sleep(1100);

        // Should allow new requests after window reset
        assertTrue(shortLimiter.allowRequest(user.id));
    }

    @Test
    void testIndependentUserLimits() {
        TestFactory.TestUser user1 = factory.createUser("user1", "user1@example.com", "User 1", "");
        TestFactory.TestUser user2 = factory.createUser("user2", "user2@example.com", "User 2", "");

        // User1 exhausts their limit
        for (int i = 0; i < 5; i++) {
            assertTrue(rateLimiter.allowRequest(user1.id));
        }
        assertFalse(rateLimiter.allowRequest(user1.id));

        // User2 should still have their full limit
        for (int i = 0; i < 5; i++) {
            assertTrue(rateLimiter.allowRequest(user2.id));
        }
    }

    @Test
    void testAnonymousRequestRateLimit() {
        String anonymousId = "anonymous";

        // Anonymous users should also be rate limited
        for (int i = 0; i < 5; i++) {
            assertTrue(rateLimiter.allowRequest(anonymousId));
        }

        assertFalse(rateLimiter.allowRequest(anonymousId));
    }

    @Test
    void testDifferentEndpointsShareLimit() {
        TestFactory.TestUser user = factory.createUser("user1", "user1@example.com", "User 1", "");

        // All endpoints share the same rate limit per user
        for (int i = 0; i < 3; i++) {
            assertTrue(rateLimiter.allowRequest(user.id));
        }

        for (int i = 0; i < 2; i++) {
            assertTrue(rateLimiter.allowRequest(user.id));
        }

        // Next request should be blocked
        assertFalse(rateLimiter.allowRequest(user.id));
    }

    @Test
    void testBurstRequests() {
        TestFactory.TestUser user = factory.createUser("user1", "user1@example.com", "User 1", "");

        // Simulate burst of requests
        int allowed = 0;
        int blocked = 0;

        for (int i = 0; i < 10; i++) {
            if (rateLimiter.allowRequest(user.id)) {
                allowed++;
            } else {
                blocked++;
            }
        }

        assertEquals(5, allowed);
        assertEquals(5, blocked);
    }

    @Test
    void testRateLimitResetDoesNotAffectOtherUsers() throws InterruptedException {
        TestFactory.TestUser user1 = factory.createUser("user1", "user1@example.com", "User 1", "");
        TestFactory.TestUser user2 = factory.createUser("user2", "user2@example.com", "User 2", "");

        RateLimiter shortLimiter = new RateLimiter(2, 1); // 2 requests per 1 second

        // User1 makes requests
        assertTrue(shortLimiter.allowRequest(user1.id));
        assertTrue(shortLimiter.allowRequest(user1.id));
        assertFalse(shortLimiter.allowRequest(user1.id));

        // User2 makes requests (should have independent limit)
        assertTrue(shortLimiter.allowRequest(user2.id));
        assertTrue(shortLimiter.allowRequest(user2.id));
        assertFalse(shortLimiter.allowRequest(user2.id));

        // Wait for reset
        Thread.sleep(1100);

        // Both users should have limits reset
        assertTrue(shortLimiter.allowRequest(user1.id));
        assertTrue(shortLimiter.allowRequest(user2.id));
    }

    @Test
    void testConcurrentRequests() throws InterruptedException {
        TestFactory.TestUser user = factory.createUser("user1", "user1@example.com", "User 1", "");

        int threadCount = 10;
        Thread[] threads = new Thread[threadCount];
        int[] results = new int[threadCount];

        for (int i = 0; i < threadCount; i++) {
            final int index = i;
            threads[i] = new Thread(() -> {
                results[index] = rateLimiter.allowRequest(user.id) ? 1 : 0;
            });
            threads[i].start();
        }

        for (Thread thread : threads) {
            thread.join();
        }

        int allowedCount = 0;
        for (int result : results) {
            allowedCount += result;
        }

        // Should allow exactly 5 requests
        assertEquals(5, allowedCount);
    }

    @Test
    void testGetRemainingRequests() {
        TestFactory.TestUser user = factory.createUser("user1", "user1@example.com", "User 1", "");

        assertEquals(5, rateLimiter.getRemainingRequests(user.id));

        rateLimiter.allowRequest(user.id);
        assertEquals(4, rateLimiter.getRemainingRequests(user.id));

        rateLimiter.allowRequest(user.id);
        assertEquals(3, rateLimiter.getRemainingRequests(user.id));
    }

    // ============================================================================
    // Rate Limiter Implementation (Mock)
    // ============================================================================

    static class RateLimiter {
        private final int maxRequests;
        private final int windowSeconds;
        private final Map<String, UserRateLimit> rateLimits;

        public RateLimiter(int maxRequests, int windowSeconds) {
            this.maxRequests = maxRequests;
            this.windowSeconds = windowSeconds;
            this.rateLimits = new ConcurrentHashMap<>();
        }

        public synchronized boolean allowRequest(String userId) {
            UserRateLimit userLimit = rateLimits.computeIfAbsent(userId, k -> new UserRateLimit());

            long now = Instant.now().getEpochSecond();

            // Reset if window has passed
            if (now - userLimit.windowStart >= windowSeconds) {
                userLimit.requestCount = 0;
                userLimit.windowStart = now;
            }

            // Check if under limit
            if (userLimit.requestCount < maxRequests) {
                userLimit.requestCount++;
                return true;
            }

            return false;
        }

        public int getRemainingRequests(String userId) {
            UserRateLimit userLimit = rateLimits.get(userId);
            if (userLimit == null) {
                return maxRequests;
            }

            long now = Instant.now().getEpochSecond();
            if (now - userLimit.windowStart >= windowSeconds) {
                return maxRequests;
            }

            return Math.max(0, maxRequests - userLimit.requestCount);
        }

        private static class UserRateLimit {
            int requestCount = 0;
            long windowStart = Instant.now().getEpochSecond();
        }
    }
}
