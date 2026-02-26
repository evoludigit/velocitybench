package repositories

import db.Database
import models.Comment
import javax.inject.{Inject, Singleton}
import scala.collection.mutable

@Singleton
class CommentRepository @Inject()(database: Database) {

  def findByPostPks(postPks: Set[Int], limit: Int): Map[Int, Seq[Comment]] = {
    if (postPks.isEmpty) return Map.empty

    val conn = database.getConnection
    try {
      val placeholders = postPks.map(_ => "?").mkString(",")
      val sql =
        s"""SELECT * FROM (
           |  SELECT pk_comment, id, fk_post, fk_author, content, created_at, updated_at,
           |         ROW_NUMBER() OVER (PARTITION BY fk_post ORDER BY pk_comment) as rn
           |  FROM tb_comment WHERE fk_post IN ($placeholders)
           |) t WHERE rn <= ?
           |ORDER BY fk_post, pk_comment""".stripMargin

      val stmt = conn.prepareStatement(sql)
      postPks.zipWithIndex.foreach { case (pk, idx) => stmt.setInt(idx + 1, pk) }
      stmt.setInt(postPks.size + 1, limit)

      val rs = stmt.executeQuery()
      val result = mutable.Map[Int, mutable.Buffer[Comment]]()
      postPks.foreach(pk => result(pk) = mutable.Buffer[Comment]())

      while (rs.next()) {
        val comment = mapRow(rs)
        result(comment.fkPost) += comment
      }
      result.view.mapValues(_.toSeq).toMap
    } finally {
      conn.close()
    }
  }

  private def mapRow(rs: java.sql.ResultSet): Comment = {
    Comment(
      pkComment = rs.getInt("pk_comment"),
      id = java.util.UUID.fromString(rs.getString("id")),
      fkPost = rs.getInt("fk_post"),
      fkAuthor = rs.getInt("fk_author"),
      content = rs.getString("content"),
      createdAt = rs.getTimestamp("created_at").toLocalDateTime,
      updatedAt = Option(rs.getTimestamp("updated_at")).map(_.toLocalDateTime)
    )
  }
}
