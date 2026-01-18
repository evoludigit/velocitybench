package controllers

import db.Database
import play.api.libs.json._
import play.api.mvc._

import javax.inject._

@Singleton
class HealthController @Inject()(
  cc: ControllerComponents,
  database: Database
) extends AbstractController(cc) {

  def health: Action[AnyContent] = Action {
    val healthy = database.isHealthy
    val response = Json.obj(
      "status" -> (if (healthy) "healthy" else "unhealthy"),
      "framework" -> "play-graphql"
    )
    if (healthy) Ok(response) else ServiceUnavailable(response)
  }

  def metrics: Action[AnyContent] = Action {
    val metricsText =
      s"""# HELP play_requests_total Total number of GraphQL requests
         |# TYPE play_requests_total counter
         |play_requests_total 0
         |# HELP play_db_pool_size Database connection pool size
         |# TYPE play_db_pool_size gauge
         |play_db_pool_size ${database.poolSize}
         |""".stripMargin

    Ok(metricsText).as("text/plain")
  }
}
