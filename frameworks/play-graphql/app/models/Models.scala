package models

import java.time.LocalDateTime
import java.util.UUID

case class User(
  pkUser: Int,
  id: UUID,
  username: String,
  fullName: Option[String],
  bio: Option[String],
  createdAt: LocalDateTime,
  updatedAt: Option[LocalDateTime]
)

case class Post(
  pkPost: Int,
  id: UUID,
  fkAuthor: Int,
  title: String,
  content: Option[String],
  createdAt: LocalDateTime,
  updatedAt: Option[LocalDateTime]
)

case class Comment(
  pkComment: Int,
  id: UUID,
  fkPost: Int,
  fkAuthor: Int,
  content: String,
  createdAt: LocalDateTime,
  updatedAt: Option[LocalDateTime]
)

case class UpdateUserInput(fullName: Option[String], bio: Option[String])
case class UpdatePostInput(title: Option[String], content: Option[String])
