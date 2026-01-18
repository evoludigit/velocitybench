package test

import java.time.Instant
import java.util.UUID
import scala.collection.mutable

/**
 * Test data models
 */
case class TestUser(
  id: String,
  pkUser: Int,
  username: String,
  fullName: String,
  bio: Option[String],
  createdAt: Instant,
  updatedAt: Instant
)

case class TestPost(
  id: String,
  pkPost: Int,
  fkAuthor: Int,
  title: String,
  content: String,
  createdAt: Instant,
  updatedAt: Instant,
  author: Option[TestUser]
)

case class TestComment(
  id: String,
  pkComment: Int,
  fkPost: Int,
  fkAuthor: Int,
  content: String,
  createdAt: Instant,
  author: Option[TestUser],
  post: Option[TestPost]
)

/**
 * In-memory test factory for isolated tests
 */
class TestFactory {
  private val users = mutable.Map[String, TestUser]()
  private val posts = mutable.Map[String, TestPost]()
  private val comments = mutable.Map[String, TestComment]()

  private var userCounter = 0
  private var postCounter = 0
  private var commentCounter = 0

  def createUser(
    username: String,
    email: String,
    fullName: String,
    bio: Option[String] = None
  ): TestUser = {
    userCounter += 1
    val user = TestUser(
      id = UUID.randomUUID().toString,
      pkUser = userCounter,
      username = username,
      fullName = fullName,
      bio = bio,
      createdAt = Instant.now(),
      updatedAt = Instant.now()
    )
    users(user.id) = user
    user
  }

  def createPost(
    authorId: String,
    title: String,
    content: String = "Default content"
  ): TestPost = {
    val author = users.getOrElse(authorId,
      throw new RuntimeException(s"Author not found: $authorId"))

    postCounter += 1
    val post = TestPost(
      id = UUID.randomUUID().toString,
      pkPost = postCounter,
      fkAuthor = author.pkUser,
      title = title,
      content = content,
      createdAt = Instant.now(),
      updatedAt = Instant.now(),
      author = Some(author)
    )
    posts(post.id) = post
    post
  }

  def createComment(
    authorId: String,
    postId: String,
    content: String
  ): TestComment = {
    val author = users.getOrElse(authorId,
      throw new RuntimeException("Author not found"))
    val post = posts.getOrElse(postId,
      throw new RuntimeException("Post not found"))

    commentCounter += 1
    val comment = TestComment(
      id = UUID.randomUUID().toString,
      pkComment = commentCounter,
      fkPost = post.pkPost,
      fkAuthor = author.pkUser,
      content = content,
      createdAt = Instant.now(),
      author = Some(author),
      post = Some(post)
    )
    comments(comment.id) = comment
    comment
  }

  def getUser(id: String): Option[TestUser] = users.get(id)

  def getPost(id: String): Option[TestPost] = posts.get(id)

  def getComment(id: String): Option[TestComment] = comments.get(id)

  def getAllUsers: Seq[TestUser] = users.values.toSeq

  def getPostsByAuthor(authorPk: Int): Seq[TestPost] =
    posts.values.filter(_.fkAuthor == authorPk).toSeq

  def getCommentsByPost(postPk: Int): Seq[TestComment] =
    comments.values.filter(_.fkPost == postPk).toSeq

  def reset(): Unit = {
    users.clear()
    posts.clear()
    comments.clear()
    userCounter = 0
    postCounter = 0
    commentCounter = 0
  }
}

object ValidationHelper {
  private val UuidRegex = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$".r

  def isValidUuid(value: String): Boolean =
    UuidRegex.findFirstIn(value.toLowerCase).isDefined
}

object DataGenerator {
  def generateLongString(length: Int): String = "x" * length

  def generateRandomUsername(): String = s"user_${UUID.randomUUID().toString.take(8)}"
}
