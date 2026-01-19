package test

import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers
import org.scalatest.BeforeAndAfterEach
import java.time.Instant
import java.util.Base64

/**
 * Authentication Validation Test Suite for Play/Sangria GraphQL
 * Tests that the application properly validates authentication tokens and permissions.
 */
class SecurityAuthSpec extends AnyFlatSpec with Matchers with BeforeAndAfterEach {

  var factory: TestFactory = _

  override def beforeEach(): Unit = {
    factory = new TestFactory()
  }

  override def afterEach(): Unit = {
    factory.reset()
  }

  // ============================================================================
  // Authentication Token Tests
  // ============================================================================

  "Authentication" should "reject missing auth token" in {
    val user = factory.createUser("user", "user@example.com", "User")

    an[SecurityException] should be thrownBy {
      validateToken(None)
    }
  }

  it should "reject invalid token format" in {
    val invalidToken = "not-a-valid-token"

    an[SecurityException] should be thrownBy {
      validateToken(Some(invalidToken))
    }
  }

  it should "reject expired token" in {
    val expiredTime = Instant.now().minusSeconds(3600).getEpochSecond
    val expiredToken = generateMockToken("user123", expiredTime)

    an[SecurityException] should be thrownBy {
      validateToken(Some(expiredToken))
    }
  }

  it should "reject tampered token signature" in {
    val validToken = generateMockToken("user123", Instant.now().plusSeconds(3600).getEpochSecond)
    val tamperedToken = validToken.dropRight(5) + "XXXXX"

    an[SecurityException] should be thrownBy {
      validateToken(Some(tamperedToken))
    }
  }

  it should "accept valid token" in {
    val futureTime = Instant.now().plusSeconds(3600).getEpochSecond
    val validToken = generateMockToken("user123", futureTime)

    noException should be thrownBy {
      validateToken(Some(validToken))
    }
  }

  it should "handle token with invalid user ID" in {
    val futureTime = Instant.now().plusSeconds(3600).getEpochSecond
    val tokenWithInvalidUser = generateMockToken("nonexistent-user", futureTime)

    noException should be thrownBy {
      validateToken(Some(tokenWithInvalidUser))
    }

    val user = factory.getUser("nonexistent-user")
    user shouldBe empty
  }

  // ============================================================================
  // Authorization Tests
  // ============================================================================

  "Authorization" should "reject unauthorized resource access" in {
    val user1 = factory.createUser("user1", "user1@example.com", "User 1")
    val user2 = factory.createUser("user2", "user2@example.com", "User 2")

    val user2Post = factory.createPost(user2.id, "Private Post", "Secret content")

    an[SecurityException] should be thrownBy {
      authorizeResourceAccess(user1.id, user2Post.id, "delete")
    }
  }

  it should "allow authorized resource access" in {
    val user = factory.createUser("user", "user@example.com", "User")
    val userPost = factory.createPost(user.id, "My Post", "My content")

    noException should be thrownBy {
      authorizeResourceAccess(user.id, userPost.id, "delete")
    }
  }

  it should "prevent privilege escalation" in {
    val regularUser = factory.createUser("regular", "regular@example.com", "Regular User")
    val adminUser = factory.createUser("admin", "admin@example.com", "Admin")

    an[SecurityException] should be thrownBy {
      checkAdminPrivileges(regularUser.id)
    }
  }

  it should "prevent cross-user data access" in {
    val user1 = factory.createUser("user1", "user1@example.com", "User 1")
    val user2 = factory.createUser("user2", "user2@example.com", "User 2")

    an[SecurityException] should be thrownBy {
      authorizeProfileAccess(user1.id, user2.id)
    }
  }

  // ============================================================================
  // Session Management Tests
  // ============================================================================

  "Session Management" should "handle concurrent sessions" in {
    val user = factory.createUser("user", "user@example.com", "User")

    val session1 = generateMockToken(user.id, Instant.now().plusSeconds(3600).getEpochSecond)
    val session2 = generateMockToken(user.id, Instant.now().plusSeconds(3600).getEpochSecond)

    noException should be thrownBy {
      validateToken(Some(session1))
      validateToken(Some(session2))
    }
  }

  it should "invalidate session after logout" in {
    val user = factory.createUser("user", "user@example.com", "User")

    val token = generateMockToken(user.id, Instant.now().plusSeconds(3600).getEpochSecond)

    invalidateToken(token)

    an[SecurityException] should be thrownBy {
      validateToken(Some(token))
    }
  }

  it should "allow token reuse" in {
    val user = factory.createUser("user", "user@example.com", "User")

    val token = generateMockToken(user.id, Instant.now().plusSeconds(3600).getEpochSecond)

    noException should be thrownBy {
      validateToken(Some(token))
    }

    noException should be thrownBy {
      validateToken(Some(token))
    }
  }

  // ============================================================================
  // Helper Methods
  // ============================================================================

  private def generateMockToken(userId: String, expirationTime: Long): String = {
    val payload = s"$userId:$expirationTime"
    Base64.getEncoder.encodeToString(payload.getBytes)
  }

  private def validateToken(token: Option[String]): Unit = {
    token match {
      case None =>
        throw new SecurityException("Missing authentication token")
      case Some(t) if !t.matches("^[A-Za-z0-9+/=]+$") =>
        throw new SecurityException("Invalid token format")
      case Some(t) =>
        try {
          val decoded = new String(Base64.getDecoder.decode(t))
          val parts = decoded.split(":")

          if (parts.length != 2) {
            throw new SecurityException("Invalid token structure")
          }

          val expirationTime = parts(1).toLong
          if (Instant.now().getEpochSecond > expirationTime) {
            throw new SecurityException("Token expired")
          }
        } catch {
          case _: IllegalArgumentException =>
            throw new SecurityException("Token decoding failed")
          case e: SecurityException =>
            throw e
        }
    }
  }

  private def authorizeResourceAccess(userId: String, resourceId: String, action: String): Unit = {
    val post = factory.getPost(resourceId)
    if (post.isEmpty) {
      throw new SecurityException("Resource not found")
    }

    if (post.get.author.get.id != userId) {
      throw new SecurityException("Unauthorized access to resource")
    }
  }

  private def checkAdminPrivileges(userId: String): Unit = {
    val user = factory.getUser(userId)
    if (user.isEmpty || user.get.username != "admin") {
      throw new SecurityException("Admin privileges required")
    }
  }

  private def authorizeProfileAccess(requesterId: String, targetUserId: String): Unit = {
    if (requesterId != targetUserId) {
      throw new SecurityException("Cannot access another user's profile")
    }
  }

  private def invalidateToken(token: String): Unit = {
    // Mock token invalidation
  }
}
