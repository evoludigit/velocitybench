package test

import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers
import org.scalatest.BeforeAndAfterEach

/**
 * SQL Injection Prevention Test Suite for Play/Sangria GraphQL
 * Tests that the application properly handles malicious SQL injection attempts.
 */
class SecurityInjectionSpec extends AnyFlatSpec with Matchers with BeforeAndAfterEach {

  var factory: TestFactory = _

  override def beforeEach(): Unit = {
    factory = new TestFactory()
  }

  override def afterEach(): Unit = {
    factory.reset()
  }

  // ============================================================================
  // SQL Injection Prevention Tests
  // ============================================================================

  "SQL Injection Prevention" should "reject basic OR injection" in {
    val user = factory.createUser("admin", "admin@example.com", "Admin")

    val result = factory.getUser("' OR '1'='1")

    result shouldBe empty
  }

  it should "reject UNION-based injection" in {
    val user = factory.createUser("testuser", "test@example.com", "Test User")

    val injectionAttempt = "' UNION SELECT * FROM users--"
    val result = factory.getUser(injectionAttempt)

    result shouldBe empty
  }

  it should "reject stacked queries injection" in {
    val user = factory.createUser("victim", "victim@example.com", "Victim")

    val injectionAttempt = "'; DROP TABLE users;--"
    val result = factory.getUser(injectionAttempt)

    result shouldBe empty

    // Verify data is still intact
    factory.getAllUsers should have size 1
  }

  it should "reject time-based blind injection" in {
    val user = factory.createUser("user1", "user1@example.com", "User 1")

    val injectionAttempt = "' OR SLEEP(5)--"
    val startTime = System.currentTimeMillis()

    val result = factory.getUser(injectionAttempt)

    val duration = System.currentTimeMillis() - startTime

    result shouldBe empty
    duration should be < 1000L
  }

  it should "reject comment sequence injection" in {
    val user = factory.createUser("admin", "admin@example.com", "Admin")

    val injectionAttempt = "admin'--"
    val result = factory.getUser(injectionAttempt)

    result shouldBe empty
  }

  it should "reject boolean-based injection" in {
    val user = factory.createUser("testuser", "test@example.com", "Test")

    val injectionAttempt = "' OR 1=1--"
    val result = factory.getUser(injectionAttempt)

    result shouldBe empty
  }

  it should "reject second-order injection" in {
    val maliciousUsername = "user'; DROP TABLE posts;--"

    val result = factory.createUser(maliciousUsername, "mal@example.com", "Malicious")

    // The malicious username is stored as-is (sanitized by parameterization)
    // Verify no data corruption occurred - existing data is intact
    factory.getAllUsers should not be empty
  }

  it should "safely handle injection in post content" in {
    val author = factory.createUser("author", "author@example.com", "Author")

    val maliciousContent = "'; DELETE FROM users WHERE '1'='1"
    val post = factory.createPost(author.id, "Test Post", maliciousContent)

    post should not be null
    post.content shouldBe maliciousContent

    // Verify users are not deleted
    factory.getAllUsers should have size 1
  }

  it should "reject injection in search parameters" in {
    val user1 = factory.createUser("alice", "alice@example.com", "Alice")
    val user2 = factory.createUser("bob", "bob@example.com", "Bob")

    val searchInjection = "alice' OR '1'='1"
    val result = factory.getUser(searchInjection)

    result shouldBe empty
  }

  it should "handle escaped quotes properly" in {
    val user = factory.createUser("user", "user@example.com", "User's Name", Some("It's fine"))

    user should not be null
    user.fullName shouldBe "User's Name"
    user.bio shouldBe Some("It's fine")
  }

  // ============================================================================
  // GraphQL-Specific Injection Tests
  // ============================================================================

  "GraphQL Injection Prevention" should "reject injection in variables" in {
    val user = factory.createUser("admin", "admin@example.com", "Admin")

    val injectionAttempt = "{ \"id\": \"' OR '1'='1\" }"
    val result = factory.getUser(injectionAttempt)

    result shouldBe empty
  }

  it should "reject fragment-based injection" in {
    val user = factory.createUser("user", "user@example.com", "User")

    val fragmentInjection = "...on User { id } OR 1=1--"
    val result = factory.getUser(fragmentInjection)

    result shouldBe empty
  }

  it should "reject NoSQL injection attempts" in {
    val user = factory.createUser("admin", "admin@example.com", "Admin")

    val injectionAttempt = "{\"$ne\": null}"
    val result = factory.getUser(injectionAttempt)

    result shouldBe empty
  }
}
