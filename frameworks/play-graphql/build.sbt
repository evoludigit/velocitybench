name := "play-graphql"
organization := "com.velocitybench"
version := "1.0-SNAPSHOT"

lazy val root = (project in file(".")).enablePlugins(PlayScala)

scalaVersion := "2.13.12"

libraryDependencies ++= Seq(
  guice,
  // GraphQL
  "org.sangria-graphql" %% "sangria" % "4.1.0",
  "org.sangria-graphql" %% "sangria-play-json" % "2.0.2",
  // Database
  "org.postgresql" % "postgresql" % "42.7.1",
  "com.zaxxer" % "HikariCP" % "5.1.0",
  // Testing
  "org.scalatestplus.play" %% "scalatestplus-play" % "7.0.0" % Test
)

// Play settings
PlayKeys.playDefaultPort := 4000

// JVM options
javaOptions ++= Seq(
  "-Xms256m",
  "-Xmx512m"
)
