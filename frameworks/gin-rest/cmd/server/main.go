package main

import (
	"log"
	"net/http"
	"os"

	"github.com/benchmark/gin-rest/internal/db"
	"github.com/benchmark/gin-rest/internal/handlers"
	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
	if err := db.Init(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	r := gin.Default()

	// Health check
	r.GET("/health", func(c *gin.Context) {
		if err := db.Pool.Ping(c.Request.Context()); err != nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{"status": "unhealthy"})
			return
		}
		c.JSON(http.StatusOK, gin.H{"status": "healthy", "framework": "gin-rest"})
	})

	// Metrics
	r.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// Ping
	r.GET("/ping", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "pong"})
	})

	// Users
	r.GET("/users", handlers.GetUsers)
	r.GET("/users/:id", handlers.GetUser)
	r.PUT("/users/:id", handlers.UpdateUser)

	// Posts
	r.GET("/posts", handlers.GetPosts)
	r.GET("/posts/:id", handlers.GetPost)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8006"
	}

	log.Printf("🚀 Gin REST server ready at http://localhost:%s", port)
	r.Run(":" + port)
}
