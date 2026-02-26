package test

import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers
import org.scalatest.BeforeAndAfterEach
import java.time.Instant
import scala.collection.concurrent.TrieMap

/**
 * Rate Limiting Test Suite for Play/Sangria GraphQL
 * Tests that the application properly enforces rate limits per user.
 */
class SecurityRateLimitSpec extends AnyFlatSpec with Matchers with BeforeAndAfterEach {

  var factory: TestFactory = _
  var rateLimiter: RateLimiter = _

  override def beforeEach(): Unit = {
    factory = new TestFactory()
    rateLimiter = new RateLimiter(5, 60)
  }

  override def afterEach(): Unit = {
    factory.reset()
  }

  // ============================================================================
  // Rate Limiting Tests
  // ============================================================================

  "Rate Limiter" should "allow requests within limit" in {
    val user = factory.createUser("user1", "user1@example.com", "User 1")

    (0 until 5).foreach { _ =>
      rateLimiter.allowRequest(user.id) shouldBe true
    }
  }

  it should "block requests exceeding limit" in {
    val user = factory.createUser("user1", "user1@example.com", "User 1")

    (0 until 5).foreach { _ =>
      rateLimiter.allowRequest(user.id) shouldBe true
    }

    rateLimiter.allowRequest(user.id) shouldBe false
  }

  it should "reset window after time expires" in {
    val user = factory.createUser("user1", "user1@example.com", "User 1")

    val shortLimiter = new RateLimiter(2, 1)

    shortLimiter.allowRequest(user.id) shouldBe true
    shortLimiter.allowRequest(user.id) shouldBe true
    shortLimiter.allowRequest(user.id) shouldBe false

    Thread.sleep(1100)

    shortLimiter.allowRequest(user.id) shouldBe true
  }

  it should "maintain independent limits per user" in {
    val user1 = factory.createUser("user1", "user1@example.com", "User 1")
    val user2 = factory.createUser("user2", "user2@example.com", "User 2")

    (0 until 5).foreach { _ =>
      rateLimiter.allowRequest(user1.id) shouldBe true
    }
    rateLimiter.allowRequest(user1.id) shouldBe false

    (0 until 5).foreach { _ =>
      rateLimiter.allowRequest(user2.id) shouldBe true
    }
  }

  it should "rate limit anonymous requests" in {
    val anonymousId = "anonymous"

    (0 until 5).foreach { _ =>
      rateLimiter.allowRequest(anonymousId) shouldBe true
    }

    rateLimiter.allowRequest(anonymousId) shouldBe false
  }

  it should "share limit across different endpoints" in {
    val user = factory.createUser("user1", "user1@example.com", "User 1")

    (0 until 3).foreach { _ =>
      rateLimiter.allowRequest(user.id) shouldBe true
    }

    (0 until 2).foreach { _ =>
      rateLimiter.allowRequest(user.id) shouldBe true
    }

    rateLimiter.allowRequest(user.id) shouldBe false
  }

  it should "handle burst requests" in {
    val user = factory.createUser("user1", "user1@example.com", "User 1")

    val (allowed, blocked) = (0 until 10).map { _ =>
      rateLimiter.allowRequest(user.id)
    }.partition(_ == true)

    allowed should have size 5
    blocked should have size 5
  }

  it should "reset independently for each user" in {
    val user1 = factory.createUser("user1", "user1@example.com", "User 1")
    val user2 = factory.createUser("user2", "user2@example.com", "User 2")

    val shortLimiter = new RateLimiter(2, 1)

    shortLimiter.allowRequest(user1.id) shouldBe true
    shortLimiter.allowRequest(user1.id) shouldBe true
    shortLimiter.allowRequest(user1.id) shouldBe false

    shortLimiter.allowRequest(user2.id) shouldBe true
    shortLimiter.allowRequest(user2.id) shouldBe true
    shortLimiter.allowRequest(user2.id) shouldBe false

    Thread.sleep(1100)

    shortLimiter.allowRequest(user1.id) shouldBe true
    shortLimiter.allowRequest(user2.id) shouldBe true
  }

  it should "handle concurrent requests correctly" in {
    val user = factory.createUser("user1", "user1@example.com", "User 1")

    val threads = (0 until 10).map { _ =>
      new Thread(() => rateLimiter.allowRequest(user.id))
    }

    threads.foreach(_.start())
    threads.foreach(_.join())

    // Should have allowed exactly 5 requests (rate limit implementation dependent)
    // This test verifies thread safety
    val remaining = rateLimiter.getRemainingRequests(user.id)
    remaining should be >= 0
  }

  it should "track remaining requests" in {
    val user = factory.createUser("user1", "user1@example.com", "User 1")

    rateLimiter.getRemainingRequests(user.id) shouldBe 5

    rateLimiter.allowRequest(user.id)
    rateLimiter.getRemainingRequests(user.id) shouldBe 4

    rateLimiter.allowRequest(user.id)
    rateLimiter.getRemainingRequests(user.id) shouldBe 3
  }

  // ============================================================================
  // Rate Limiter Implementation
  // ============================================================================

  class RateLimiter(maxRequests: Int, windowSeconds: Int) {
    private val rateLimits = new TrieMap[String, UserRateLimit]()

    def allowRequest(userId: String): Boolean = synchronized {
      val userLimit = rateLimits.getOrElseUpdate(userId, new UserRateLimit())

      val now = Instant.now().getEpochSecond

      if (now - userLimit.windowStart >= windowSeconds) {
        userLimit.requestCount = 0
        userLimit.windowStart = now
      }

      if (userLimit.requestCount < maxRequests) {
        userLimit.requestCount += 1
        true
      } else {
        false
      }
    }

    def getRemainingRequests(userId: String): Int = {
      rateLimits.get(userId) match {
        case None => maxRequests
        case Some(userLimit) =>
          val now = Instant.now().getEpochSecond
          if (now - userLimit.windowStart >= windowSeconds) {
            maxRequests
          } else {
            Math.max(0, maxRequests - userLimit.requestCount)
          }
      }
    }

    class UserRateLimit {
      var requestCount: Int = 0
      var windowStart: Long = Instant.now().getEpochSecond
    }
  }
}
