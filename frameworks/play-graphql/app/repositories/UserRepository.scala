package repositories

import db.Database
import models.User
import javax.inject.{Inject, Singleton}
import java.util.UUID
import scala.collection.mutable

@Singleton
class UserRepository @Inject()(database: Database) {

  def findById(id: String): Option[User] = {
    val conn = database.getConnection
    try {
      val stmt = conn.prepareStatement(
        "SELECT pk_user, id, username, full_name, bio, created_at, updated_at FROM tb_user WHERE id = ?"
      )
      stmt.setObject(1, UUID.fromString(id))
      val rs = stmt.executeQuery()
      if (rs.next()) Some(mapRow(rs)) else None
    } finally {
      conn.close()
    }
  }

  def findByPks(pks: Set[Int]): Map[Int, User] = {
    if (pks.isEmpty) return Map.empty

    val conn = database.getConnection
    try {
      val pkSeq = pks.toSeq
      val placeholders = Seq.fill(pkSeq.size)("?").mkString(",")
      val stmt = conn.prepareStatement(
        s"SELECT pk_user, id, username, full_name, bio, created_at, updated_at FROM tb_user WHERE pk_user IN ($placeholders)"
      )
      pkSeq.zipWithIndex.foreach { case (pk, idx) => stmt.setInt(idx + 1, pk) }
      val rs = stmt.executeQuery()
      val result = mutable.Map[Int, User]()
      while (rs.next()) {
        val user = mapRow(rs)
        result(user.pkUser) = user
      }
      result.toMap
    } finally {
      conn.close()
    }
  }

  def findAll(limit: Int): Seq[User] = {
    val conn = database.getConnection
    try {
      val stmt = conn.prepareStatement(
        "SELECT pk_user, id, username, full_name, bio, created_at, updated_at FROM tb_user ORDER BY pk_user LIMIT ?"
      )
      stmt.setInt(1, Math.min(limit, 100))
      val rs = stmt.executeQuery()
      val users = mutable.Buffer[User]()
      while (rs.next()) {
        users += mapRow(rs)
      }
      users.toSeq
    } finally {
      conn.close()
    }
  }

  def update(id: String, fullName: Option[String], bio: Option[String]): Option[User] = {
    val conn = database.getConnection
    try {
      val sets = mutable.Buffer("updated_at = NOW()")
      val params = mutable.Buffer[Any]()

      fullName.foreach { fn =>
        sets += "full_name = ?"
        params += fn
      }
      bio.foreach { b =>
        sets += "bio = ?"
        params += b
      }

      val sql = s"UPDATE tb_user SET ${sets.mkString(", ")} WHERE id = ?"
      val stmt = conn.prepareStatement(sql)
      params.zipWithIndex.foreach { case (p, idx) => stmt.setObject(idx + 1, p) }
      stmt.setObject(params.size + 1, UUID.fromString(id))
      stmt.executeUpdate()
    } finally {
      conn.close()
    }
    findById(id)
  }

  private def mapRow(rs: java.sql.ResultSet): User = {
    User(
      pkUser = rs.getInt("pk_user"),
      id = java.util.UUID.fromString(rs.getString("id")),
      username = rs.getString("username"),
      fullName = Option(rs.getString("full_name")),
      bio = Option(rs.getString("bio")),
      createdAt = rs.getTimestamp("created_at").toLocalDateTime,
      updatedAt = Option(rs.getTimestamp("updated_at")).map(_.toLocalDateTime)
    )
  }
}
