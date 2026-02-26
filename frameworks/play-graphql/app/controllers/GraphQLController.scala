package controllers

import graphql.{GraphQLContext, SchemaDefinition}
import models._
import play.api.libs.json._
import play.api.mvc._
import repositories._
import sangria.execution._
import sangria.marshalling.playJson._
import sangria.parser.QueryParser

import javax.inject._
import scala.concurrent.{ExecutionContext, Future}
import scala.util.{Failure, Success}

@Singleton
class GraphQLController @Inject()(
  cc: ControllerComponents,
  userRepository: UserRepository,
  postRepository: PostRepository,
  commentRepository: CommentRepository
)(implicit ec: ExecutionContext) extends AbstractController(cc) {

  private val schemaDefinition = new SchemaDefinition(userRepository, postRepository, commentRepository)

  def graphql: Action[JsValue] = Action.async(parse.json) { request =>
    val query = (request.body \ "query").as[String]
    val variables = (request.body \ "variables").asOpt[JsObject].getOrElse(Json.obj())
    val operation = (request.body \ "operationName").asOpt[String]

    QueryParser.parse(query) match {
      case Success(queryAst) =>
        val context = GraphQLContext(userRepository, postRepository, commentRepository)

        Executor.execute(
          schemaDefinition.schema,
          queryAst,
          context,
          variables = variables,
          operationName = operation,
          deferredResolver = schemaDefinition.deferredResolver
        ).map(result => Ok(result))
          .recover {
            case error: QueryAnalysisError => BadRequest(error.resolveError)
            case error: ErrorWithResolver => InternalServerError(error.resolveError)
          }

      case Failure(error) =>
        Future.successful(BadRequest(Json.obj(
          "errors" -> Json.arr(Json.obj("message" -> error.getMessage))
        )))
    }
  }
}
