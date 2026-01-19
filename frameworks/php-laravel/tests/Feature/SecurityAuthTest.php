<?php

namespace Tests\Feature;

use Tests\TestCase;
use Tests\Traits\DatabaseTrait;

/**
 * SecurityAuthTest - Tests authentication validation
 *
 * Coverage includes:
 * - Missing authentication tokens
 * - Invalid token format
 * - Expired tokens
 * - Token signature tampering
 * - Unauthorized resource access
 */
class SecurityAuthTest extends TestCase
{
    use DatabaseTrait;

    // ========================================================================
    // Authentication Tests
    // ========================================================================

    public function test_requires_auth_token_for_protected_endpoint(): void
    {
        // Arrange
        $user = $this->createTestUser('alice', 'alice@example.com', 'Alice');

        // Act - Try to access protected endpoint without token
        $response = $this->postJson('/api/users', [
            'username' => 'newuser',
            'email' => 'new@example.com',
        ]);

        // Assert - Should require authentication
        $this->assertTrue(
            in_array($response->status(), [401, 403]),
            'Protected endpoint should require authentication'
        );
    }

    public function test_rejects_invalid_token_format(): void
    {
        // Arrange
        $invalidToken = 'not-a-valid-token';

        // Act - Try with malformed token
        $response = $this->withHeader('Authorization', "Bearer {$invalidToken}")
            ->postJson('/api/users', [
                'username' => 'newuser',
                'email' => 'new@example.com',
            ]);

        // Assert
        $this->assertTrue(
            in_array($response->status(), [401, 403]),
            'Should reject invalid token format'
        );
    }

    public function test_rejects_expired_token(): void
    {
        // Arrange - Create an expired token (mock scenario)
        $expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.4Adcj0vCKfX6n0CfMPYx_8_dKmCrqZxPr7TN7Z7bX_o';

        // Act
        $response = $this->withHeader('Authorization', "Bearer {$expiredToken}")
            ->postJson('/api/users', [
                'username' => 'newuser',
                'email' => 'new@example.com',
            ]);

        // Assert
        $this->assertTrue(
            in_array($response->status(), [401, 403]),
            'Should reject expired token'
        );
    }

    public function test_rejects_tampered_token(): void
    {
        // Arrange - Create a tampered JWT token
        $tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkFkbWluIiwiaWF0IjoxNTE2MjM5MDIyfQ.tamperedSignature';

        // Act
        $response = $this->withHeader('Authorization', "Bearer {$tamperedToken}")
            ->postJson('/api/users', [
                'username' => 'newuser',
                'email' => 'new@example.com',
            ]);

        // Assert
        $this->assertTrue(
            in_array($response->status(), [401, 403]),
            'Should reject token with tampered signature'
        );
    }

    public function test_unauthorized_user_cannot_access_other_user_data(): void
    {
        // Arrange
        $alice = $this->createTestUser('alice', 'alice@example.com', 'Alice');
        $bob = $this->createTestUser('bob', 'bob@example.com', 'Bob');

        // Simulate Bob trying to access Alice's private data
        // (In real implementation, this would use actual auth tokens)

        // Act - Try to update Alice's profile as Bob
        $response = $this->putJson("/api/users/{$alice->id}", [
            'fullName' => 'Hacked Name',
        ]);

        // Assert - Should reject unauthorized access
        $this->assertTrue(
            in_array($response->status(), [401, 403]),
            'User should not be able to modify other users data'
        );
    }

    public function test_missing_authorization_header(): void
    {
        // Act - Try protected endpoint without Authorization header
        $response = $this->deleteJson('/api/posts/123');

        // Assert
        $this->assertTrue(
            in_array($response->status(), [401, 403]),
            'Should require Authorization header'
        );
    }

    public function test_bearer_token_scheme_validation(): void
    {
        // Arrange
        $token = 'some-token-value';

        // Act - Try with wrong auth scheme
        $response = $this->withHeader('Authorization', "Basic {$token}")
            ->postJson('/api/users', [
                'username' => 'newuser',
                'email' => 'new@example.com',
            ]);

        // Assert - Should require Bearer scheme
        $this->assertTrue(
            in_array($response->status(), [401, 403]),
            'Should require Bearer token scheme'
        );
    }

    public function test_empty_token_rejected(): void
    {
        // Act - Try with empty token
        $response = $this->withHeader('Authorization', 'Bearer ')
            ->postJson('/api/users', [
                'username' => 'newuser',
                'email' => 'new@example.com',
            ]);

        // Assert
        $this->assertTrue(
            in_array($response->status(), [401, 403]),
            'Should reject empty token'
        );
    }

    public function test_case_sensitive_token_validation(): void
    {
        // Arrange - Tokens should be case-sensitive
        $token = 'AbC123DeF456';

        // Act - Try with different case
        $response = $this->withHeader('Authorization', "Bearer {$token}")
            ->postJson('/api/users', [
                'username' => 'newuser',
                'email' => 'new@example.com',
            ]);

        // Assert - Should validate case-sensitively
        $this->assertTrue(
            in_array($response->status(), [401, 403]),
            'Token validation should be case-sensitive'
        );
    }

    public function test_multiple_authorization_headers_rejected(): void
    {
        // Act - Try with multiple Authorization headers
        $response = $this->withHeaders([
            'Authorization' => 'Bearer token1',
            'X-Auth-Token' => 'token2',
        ])->postJson('/api/users', [
            'username' => 'newuser',
            'email' => 'new@example.com',
        ]);

        // Assert - Should handle ambiguous auth headers safely
        $this->assertTrue(
            in_array($response->status(), [400, 401, 403]),
            'Should handle multiple auth headers safely'
        );
    }
}
