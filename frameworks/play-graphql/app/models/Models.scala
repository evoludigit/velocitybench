package models

import java.time.LocalDateTime

case class User(
  pkUser: Int,
  id: String,
  username: String,
  fullName: Option[String],
  bio: Option[String],
  createdAt: LocalDateTime,
  updatedAt: Option[LocalDateTime]
)

case class Post(
  pkPost: Int,
  id: String,
  fkAuthor: Int,
  title: String,
  content: Option[String],
  createdAt: LocalDateTime,
  updatedAt: Option[LocalDateTime]
)

case class Comment(
  pkComment: Int,
  id: String,
  fkPost: Int,
  fkAuthor: Int,
  content: String,
  createdAt: LocalDateTime,
  updatedAt: Option[LocalDateTime]
)

case class UpdateUserInput(fullName: Option[String], bio: Option[String])
case class UpdatePostInput(title: Option[String], content: Option[String])
