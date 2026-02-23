package graphql

import models._
import repositories._
import sangria.schema._
import sangria.macros.derive._
import sangria.execution.deferred._
import scala.concurrent.{ExecutionContext, Future}

class SchemaDefinition(
  userRepository: UserRepository,
  postRepository: PostRepository,
  commentRepository: CommentRepository
)(implicit ec: ExecutionContext) {

  // Deferred resolvers for batching (Sangria Fetchers)
  val userFetcher = Fetcher.caching[GraphQLContext, User, Int](
    (ctx, ids) => Future {
      val users = ctx.userRepository.findByPks(ids.toSet)
      ids.map(id => users.getOrElse(id, throw new Exception(s"User not found: $id")))
    }
  )(HasId(_.pkUser))

  val postFetcher = Fetcher.caching[GraphQLContext, Post, Int](
    (ctx, ids) => Future {
      val posts = ctx.postRepository.findByPks(ids.toSet)
      ids.map(id => posts.getOrElse(id, throw new Exception(s"Post not found: $id")))
    }
  )(HasId(_.pkPost))

  lazy val CommentType: ObjectType[GraphQLContext, Comment] = ObjectType(
    "Comment",
    () => fields[GraphQLContext, Comment](
      Field("id", IDType, resolve = _.value.id.toString),
      Field("content", StringType, resolve = _.value.content),
      Field("createdAt", StringType, resolve = _.value.createdAt.toString),
      Field("author", OptionType(UserType),
        resolve = ctx => userFetcher.deferOpt(ctx.value.fkAuthor)),
      Field("post", OptionType(PostType),
        resolve = ctx => postFetcher.deferOpt(ctx.value.fkPost))
    )
  )

  lazy val PostType: ObjectType[GraphQLContext, Post] = ObjectType(
    "Post",
    () => fields[GraphQLContext, Post](
      Field("id", IDType, resolve = _.value.id.toString),
      Field("title", StringType, resolve = _.value.title),
      Field("content", OptionType(StringType), resolve = _.value.content),
      Field("createdAt", StringType, resolve = _.value.createdAt.toString),
      Field("author", UserType,
        resolve = ctx => userFetcher.defer(ctx.value.fkAuthor)),
      Field("comments", ListType(CommentType),
        arguments = Argument("limit", OptionInputType(IntType), 50) :: Nil,
        resolve = ctx => {
          val limit = ctx.arg[Option[Int]]("limit").getOrElse(50)
          Future {
            ctx.ctx.commentRepository.findByPostPks(Set(ctx.value.pkPost), Math.min(limit, 50))
              .getOrElse(ctx.value.pkPost, Seq.empty)
          }
        })
    )
  )

  lazy val UserType: ObjectType[GraphQLContext, User] = ObjectType(
    "User",
    () => fields[GraphQLContext, User](
      Field("id", IDType, resolve = _.value.id.toString),
      Field("username", StringType, resolve = _.value.username),
      Field("fullName", OptionType(StringType), resolve = _.value.fullName),
      Field("bio", OptionType(StringType), resolve = _.value.bio),
      Field("createdAt", StringType, resolve = _.value.createdAt.toString),
      Field("posts", ListType(PostType),
        arguments = Argument("limit", OptionInputType(IntType), 50) :: Nil,
        resolve = ctx => {
          val limit = ctx.arg[Option[Int]]("limit").getOrElse(50)
          Future {
            ctx.ctx.postRepository.findByAuthorPks(Set(ctx.value.pkUser), Math.min(limit, 50))
              .getOrElse(ctx.value.pkUser, Seq.empty)
          }
        }),
      Field("followers", ListType(UserType),
        arguments = Argument("limit", OptionInputType(IntType), 50) :: Nil,
        resolve = _ => Seq.empty[User]),
      Field("following", ListType(UserType),
        arguments = Argument("limit", OptionInputType(IntType), 50) :: Nil,
        resolve = _ => Seq.empty[User])
    )
  )

  val QueryType = ObjectType(
    "Query",
    fields[GraphQLContext, Unit](
      Field("ping", StringType, resolve = _ => "pong"),
      Field("user", OptionType(UserType),
        arguments = Argument("id", IDType) :: Nil,
        resolve = ctx => ctx.ctx.userRepository.findById(ctx.arg[String]("id"))),
      Field("users", ListType(UserType),
        arguments = Argument("limit", OptionInputType(IntType), 10) :: Nil,
        resolve = ctx => ctx.ctx.userRepository.findAll(Math.min(ctx.arg[Option[Int]]("limit").getOrElse(10), 100))),
      Field("post", OptionType(PostType),
        arguments = Argument("id", IDType) :: Nil,
        resolve = ctx => ctx.ctx.postRepository.findById(ctx.arg[String]("id"))),
      Field("posts", ListType(PostType),
        arguments = Argument("limit", OptionInputType(IntType), 10) :: Nil,
        resolve = ctx => ctx.ctx.postRepository.findAll(Math.min(ctx.arg[Option[Int]]("limit").getOrElse(10), 100)))
    )
  )

  val MutationType = ObjectType(
    "Mutation",
    fields[GraphQLContext, Unit](
      Field("updateUser", OptionType(UserType),
        arguments = Argument("id", IDType) :: Argument("fullName", OptionInputType(StringType)) :: Argument("bio", OptionInputType(StringType)) :: Nil,
        resolve = ctx => ctx.ctx.userRepository.update(ctx.arg[String]("id"), ctx.argOpt[String]("fullName"), ctx.argOpt[String]("bio"))),
      Field("updatePost", OptionType(PostType),
        arguments = Argument("id", IDType) :: Argument("title", OptionInputType(StringType)) :: Argument("content", OptionInputType(StringType)) :: Nil,
        resolve = ctx => ctx.ctx.postRepository.update(ctx.arg[String]("id"), ctx.argOpt[String]("title"), ctx.argOpt[String]("content")))
    )
  )

  val schema = Schema(QueryType, Some(MutationType))
  val deferredResolver = DeferredResolver.fetchers(userFetcher, postFetcher)
}

case class GraphQLContext(
  userRepository: UserRepository,
  postRepository: PostRepository,
  commentRepository: CommentRepository
)
