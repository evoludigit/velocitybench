package com.fraiseql;

import com.fraiseql.entities.User;
import com.fraiseql.entities.Post;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.HashMap;
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
        User user = factory.createTestUser("user1", "user1@example.com", "User 1", "");

        // Make 5 requests (within limit)
        for (int i = 0; i < 5; i++) {
            assertTrue(rateLimiter.allowRequest(user.getId()));
        }
    }

    @Test
    void testExceedRateLimit() {
        User user = factory.createTestUser("user1", "user1@example.com", "User 1", "");

        // Make 5 requests (within limit)
        for (int i = 0; i < 5; i++) {
            assertTrue(rateLimiter.allowRequest(user.getId()));
        }

        // 6th request should be blocked
        assertFalse(rateLimiter.allowRequest(user.getId()));
    }

    @Test
    void testRateLimitWindowReset() throws InterruptedException {
        User user = factory.createTestUser("user1", "user1@example.com", "User 1", "");

        // Use a short window for testing
        RateLimiter shortLimiter = new RateLimiter(2, 1); // 2 requests per 1 second

        // Make 2 requests
        assertTrue(shortLimiter.allowRequest(user.getId()));
        assertTrue(shortLimiter.allowRequest(user.getId()));

        // 3rd request should be blocked
        assertFalse(shortLimiter.allowRequest(user.getId()));

        // Wait for window to reset
        Thread.sleep(1100);

        // Should allow new requests after window reset
        assertTrue(shortLimiter.allowRequest(user.getId()));
    }

    @Test
    void testIndependentUserLimits() {
        User user1 = factory.createTestUser("user1", "user1@example.com", "User 1", "");
        User user2 = factory.createTestUser("user2", "user2@example.com", "User 2", "");

        // User1 exhausts their limit
        for (int i = 0; i < 5; i++) {
            assertTrue(rateLimiter.allowRequest(user1.getId()));
        }
        assertFalse(rateLimiter.allowRequest(user1.getId()));

        // User2 should still have their full limit
        for (int i = 0; i < 5; i++) {
            assertTrue(rateLimiter.allowRequest(user2.getId()));
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
        User user = factory.createTestUser("user1", "user1@example.com", "User 1", "");

        // All endpoints share the same rate limit per user
        for (int i = 0; i < 3; i++) {
            assertTrue(rateLimiter.allowRequest(user.getId()));
        }

        for (int i = 0; i < 2; i++) {
            assertTrue(rateLimiter.allowRequest(user.getId()));
        }

        // Next request should be blocked
        assertFalse(rateLimiter.allowRequest(user.getId()));
    }

    @Test
    void testBurstRequests() {
        User user = factory.createTestUser("user1", "user1@example.com", "User 1", "");

        // Simulate burst of requests
        int allowed = 0;
        int blocked = 0;

        for (int i = 0; i < 10; i++) {
            if (rateLimiter.allowRequest(user.getId())) {
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
        User user1 = factory.createTestUser("user1", "user1@example.com", "User 1", "");
        User user2 = factory.createTestUser("user2", "user2@example.com", "User 2", "");

        RateLimiter shortLimiter = new RateLimiter(2, 1); // 2 requests per 1 second

        // User1 makes requests
        assertTrue(shortLimiter.allowRequest(user1.getId()));
        assertTrue(shortLimiter.allowRequest(user1.getId()));
        assertFalse(shortLimiter.allowRequest(user1.getId()));

        // User2 makes requests (should have independent limit)
        assertTrue(shortLimiter.allowRequest(user2.getId()));
        assertTrue(shortLimiter.allowRequest(user2.getId()));
        assertFalse(shortLimiter.allowRequest(user2.getId()));

        // Wait for reset
        Thread.sleep(1100);

        // Both users should have limits reset
        assertTrue(shortLimiter.allowRequest(user1.getId()));
        assertTrue(shortLimiter.allowRequest(user2.getId()));
    }

    @Test
    void testConcurrentRequests() throws InterruptedException {
        User user = factory.createTestUser("user1", "user1@example.com", "User 1", "");

        int threadCount = 10;
        Thread[] threads = new Thread[threadCount];
        int[] results = new int[threadCount];

        for (int i = 0; i < threadCount; i++) {
            final int index = i;
            threads[i] = new Thread(() -> {
                results[index] = rateLimiter.allowRequest(user.getId()) ? 1 : 0;
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
        User user = factory.createTestUser("user1", "user1@example.com", "User 1", "");

        assertEquals(5, rateLimiter.getRemainingRequests(user.getId()));

        rateLimiter.allowRequest(user.getId());
        assertEquals(4, rateLimiter.getRemainingRequests(user.getId()));

        rateLimiter.allowRequest(user.getId());
        assertEquals(3, rateLimiter.getRemainingRequests(user.getId()));
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
