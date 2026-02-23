package repositories

import db.Database
import models.Post
import javax.inject.{Inject, Singleton}
import java.util.UUID
import scala.collection.mutable

@Singleton
class PostRepository @Inject()(database: Database) {

  def findById(id: String): Option[Post] = {
    val conn = database.getConnection
    try {
      val stmt = conn.prepareStatement(
        "SELECT pk_post, id, fk_author, title, content, created_at, updated_at FROM tb_post WHERE id = ?"
      )
      stmt.setObject(1, UUID.fromString(id))
      val rs = stmt.executeQuery()
      if (rs.next()) Some(mapRow(rs)) else None
    } finally {
      conn.close()
    }
  }

  def findByPks(pks: Set[Int]): Map[Int, Post] = {
    if (pks.isEmpty) return Map.empty

    val conn = database.getConnection
    try {
      val placeholders = pks.map(_ => "?").mkString(",")
      val stmt = conn.prepareStatement(
        s"SELECT pk_post, id, fk_author, title, content, created_at, updated_at FROM tb_post WHERE pk_post IN ($placeholders)"
      )
      pks.zipWithIndex.foreach { case (pk, idx) => stmt.setInt(idx + 1, pk) }
      val rs = stmt.executeQuery()
      val result = mutable.Map[Int, Post]()
      while (rs.next()) {
        val post = mapRow(rs)
        result(post.pkPost) = post
      }
      result.toMap
    } finally {
      conn.close()
    }
  }

  def findByAuthorPks(authorPks: Set[Int], limit: Int): Map[Int, Seq[Post]] = {
    if (authorPks.isEmpty) return Map.empty

    val conn = database.getConnection
    try {
      val placeholders = authorPks.map(_ => "?").mkString(",")
      val sql =
        s"""SELECT * FROM (
           |  SELECT pk_post, id, fk_author, title, content, created_at, updated_at,
           |         ROW_NUMBER() OVER (PARTITION BY fk_author ORDER BY pk_post) as rn
           |  FROM tb_post WHERE fk_author IN ($placeholders)
           |) t WHERE rn <= ?
           |ORDER BY fk_author, pk_post""".stripMargin

      val stmt = conn.prepareStatement(sql)
      authorPks.zipWithIndex.foreach { case (pk, idx) => stmt.setInt(idx + 1, pk) }
      stmt.setInt(authorPks.size + 1, limit)

      val rs = stmt.executeQuery()
      val result = mutable.Map[Int, mutable.Buffer[Post]]()
      authorPks.foreach(pk => result(pk) = mutable.Buffer[Post]())

      while (rs.next()) {
        val post = mapRow(rs)
        result(post.fkAuthor) += post
      }
      result.view.mapValues(_.toSeq).toMap
    } finally {
      conn.close()
    }
  }

  def findAll(limit: Int): Seq[Post] = {
    val conn = database.getConnection
    try {
      val stmt = conn.prepareStatement(
        "SELECT pk_post, id, fk_author, title, content, created_at, updated_at FROM tb_post ORDER BY pk_post LIMIT ?"
      )
      stmt.setInt(1, Math.min(limit, 100))
      val rs = stmt.executeQuery()
      val posts = mutable.Buffer[Post]()
      while (rs.next()) {
        posts += mapRow(rs)
      }
      posts.toSeq
    } finally {
      conn.close()
    }
  }

  def update(id: String, title: Option[String], content: Option[String]): Option[Post] = {
    val conn = database.getConnection
    try {
      val sets = mutable.Buffer("updated_at = NOW()")
      val params = mutable.Buffer[Any]()

      title.foreach { t =>
        sets += "title = ?"
        params += t
      }
      content.foreach { c =>
        sets += "content = ?"
        params += c
      }

      val sql = s"UPDATE tb_post SET ${sets.mkString(", ")} WHERE id = ?"
      val stmt = conn.prepareStatement(sql)
      params.zipWithIndex.foreach { case (p, idx) => stmt.setObject(idx + 1, p) }
      stmt.setObject(params.size + 1, UUID.fromString(id))
      stmt.executeUpdate()
    } finally {
      conn.close()
    }
    findById(id)
  }

  private def mapRow(rs: java.sql.ResultSet): Post = {
    Post(
      pkPost = rs.getInt("pk_post"),
      id = java.util.UUID.fromString(rs.getString("id")),
      fkAuthor = rs.getInt("fk_author"),
      title = rs.getString("title"),
      content = Option(rs.getString("content")),
      createdAt = rs.getTimestamp("created_at").toLocalDateTime,
      updatedAt = Option(rs.getTimestamp("updated_at")).map(_.toLocalDateTime)
    )
  }
}
