package test

import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers
import org.scalatest.BeforeAndAfterEach

/**
 * Comprehensive test suite for Play/Sangria GraphQL resolvers.
 * Uses in-memory TestFactory for fast, isolated tests.
 */
class ResolverSpec extends AnyFlatSpec with Matchers with BeforeAndAfterEach {

  var factory: TestFactory = _

  override def beforeEach(): Unit = {
    factory = new TestFactory()
  }

  override def afterEach(): Unit = {
    factory.reset()
  }

  // ============================================================================
  // User Query Tests
  // ============================================================================

  "User queries" should "return user by UUID" in {
    val user = factory.createUser("alice", "alice@example.com", "Alice Smith", Some("Hello!"))

    val result = factory.getUser(user.id)

    result shouldBe defined
    result.get.id shouldBe user.id
    result.get.username shouldBe "alice"
    result.get.fullName shouldBe "Alice Smith"
    result.get.bio shouldBe Some("Hello!")
  }

  it should "return list of users" in {
    factory.createUser("alice", "alice@example.com", "Alice")
    factory.createUser("bob", "bob@example.com", "Bob")
    factory.createUser("charlie", "charlie@example.com", "Charlie")

    val users = factory.getAllUsers

    users should have size 3
  }

  it should "return None for non-existent user" in {
    val result = factory.getUser("non-existent-id")

    result shouldBe empty
  }

  // ============================================================================
  // Post Query Tests
  // ============================================================================

  "Post queries" should "return post by ID" in {
    val user = factory.createUser("author", "author@example.com", "Author")
    val post = factory.createPost(user.id, "Test Post", "Test content")

    val result = factory.getPost(post.id)

    result shouldBe defined
    result.get.title shouldBe "Test Post"
    result.get.content shouldBe "Test content"
  }

  it should "return posts by author" in {
    val user = factory.createUser("author", "author@example.com", "Author")
    factory.createPost(user.id, "Post 1", "Content 1")
    factory.createPost(user.id, "Post 2", "Content 2")

    val posts = factory.getPostsByAuthor(user.pkUser)

    posts should have size 2
  }

  // ============================================================================
  // Comment Query Tests
  // ============================================================================

  "Comment queries" should "return comment by ID" in {
    val author = factory.createUser("author", "author@example.com", "Author")
    val post = factory.createPost(author.id, "Test Post", "Content")
    val commenter = factory.createUser("commenter", "commenter@example.com", "Commenter")
    val comment = factory.createComment(commenter.id, post.id, "Great post!")

    val result = factory.getComment(comment.id)

    result shouldBe defined
    result.get.content shouldBe "Great post!"
  }

  it should "return comments by post" in {
    val author = factory.createUser("author", "author@example.com", "Author")
    val post = factory.createPost(author.id, "Test Post", "Content")
    val commenter = factory.createUser("commenter", "commenter@example.com", "Commenter")
    factory.createComment(commenter.id, post.id, "Comment 1")
    factory.createComment(commenter.id, post.id, "Comment 2")

    val comments = factory.getCommentsByPost(post.pkPost)

    comments should have size 2
  }

  // ============================================================================
  // Relationship Tests
  // ============================================================================

  "Relationships" should "resolve user posts" in {
    val user = factory.createUser("author", "author@example.com", "Author")
    val post1 = factory.createPost(user.id, "Post 1", "Content 1")
    val post2 = factory.createPost(user.id, "Post 2", "Content 2")

    val posts = factory.getPostsByAuthor(user.pkUser)

    posts should have size 2
    posts.map(_.id) should contain allOf (post1.id, post2.id)
  }

  it should "resolve post author" in {
    val author = factory.createUser("author", "author@example.com", "Author")
    val post = factory.createPost(author.id, "Test Post", "Content")

    post.author shouldBe defined
    post.author.get.pkUser shouldBe author.pkUser
  }

  it should "resolve comment author" in {
    val author = factory.createUser("author", "author@example.com", "Author")
    val post = factory.createPost(author.id, "Test Post", "Content")
    val commenter = factory.createUser("commenter", "commenter@example.com", "Commenter")
    val comment = factory.createComment(commenter.id, post.id, "Great!")

    comment.author shouldBe defined
    comment.author.get.pkUser shouldBe commenter.pkUser
  }

  // ============================================================================
  // Edge Case Tests
  // ============================================================================

  "Edge cases" should "handle null bio" in {
    val user = factory.createUser("user", "user@example.com", "User")

    user.bio shouldBe empty
  }

  it should "handle empty posts list" in {
    val user = factory.createUser("newuser", "new@example.com", "New User")

    val posts = factory.getPostsByAuthor(user.pkUser)

    posts shouldBe empty
  }

  it should "handle special characters in content" in {
    val user = factory.createUser("author", "author@example.com", "Author")
    val specialContent = "Test with 'quotes' and \"double quotes\" and <html>"
    val post = factory.createPost(user.id, "Special", specialContent)

    post.content shouldBe specialContent
  }

  it should "handle unicode content" in {
    val user = factory.createUser("author", "author@example.com", "Author")
    val unicodeContent = "Test with émojis \uD83C\uDF89 and ñ and 中文"
    val post = factory.createPost(user.id, "Unicode", unicodeContent)

    post.content shouldBe unicodeContent
  }

  // ============================================================================
  // Performance Tests
  // ============================================================================

  "Performance" should "handle many posts" in {
    val user = factory.createUser("author", "author@example.com", "Author")

    (0 until 50).foreach { i =>
      factory.createPost(user.id, s"Post $i", "Content")
    }

    val posts = factory.getPostsByAuthor(user.pkUser)
    posts should have size 50
  }

  it should "reset properly" in {
    factory.createUser("user1", "user1@example.com", "User 1")
    factory.createUser("user2", "user2@example.com", "User 2")

    factory.reset()

    factory.getAllUsers shouldBe empty
  }

  // ============================================================================
  // Validation Tests
  // ============================================================================

  "Validation" should "generate valid UUIDs" in {
    val user = factory.createUser("user", "user@example.com", "User")

    ValidationHelper.isValidUuid(user.id) shouldBe true
  }

  it should "throw for invalid author" in {
    an[RuntimeException] should be thrownBy {
      factory.createPost("invalid-author", "Test", "Content")
    }
  }

  it should "throw for invalid post" in {
    val user = factory.createUser("user", "user@example.com", "User")

    an[RuntimeException] should be thrownBy {
      factory.createComment(user.id, "invalid-post", "Content")
    }
  }

  it should "handle long content" in {
    val user = factory.createUser("author", "author@example.com", "Author")
    val longContent = DataGenerator.generateLongString(100000)
    val post = factory.createPost(user.id, "Long", longContent)

    post.content.length shouldBe 100000
  }
}
