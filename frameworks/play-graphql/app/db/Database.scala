package db

import com.zaxxer.hikari.{HikariConfig, HikariDataSource}
import play.api.Configuration
import javax.inject.{Inject, Singleton}
import java.sql.Connection

@Singleton
class Database @Inject()(config: Configuration) {

  private val hikariConfig = new HikariConfig()
  hikariConfig.setJdbcUrl(s"jdbc:postgresql://${config.get[String]("db.host")}:${config.get[Int]("db.port")}/${config.get[String]("db.name")}")
  hikariConfig.setUsername(config.get[String]("db.user"))
  hikariConfig.setPassword(config.get[String]("db.password"))
  hikariConfig.setMinimumIdle(config.get[Int]("db.pool.minSize"))
  hikariConfig.setMaximumPoolSize(config.get[Int]("db.pool.maxSize"))
  hikariConfig.setConnectionInitSql("SET search_path TO benchmark, public")

  private val dataSource = new HikariDataSource(hikariConfig)

  def getConnection: Connection = dataSource.getConnection

  def isHealthy: Boolean = {
    try {
      val conn = dataSource.getConnection
      try {
        conn.isValid(5)
      } finally {
        conn.close()
      }
    } catch {
      case _: Exception => false
    }
  }

  def poolSize: Int = dataSource.getMaximumPoolSize
}
