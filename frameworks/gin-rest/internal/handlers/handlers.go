package handlers

import (
	"context"
	"net/http"
	"strconv"
	"strings"

	"github.com/benchmark/gin-rest/internal/db"
	"github.com/benchmark/gin-rest/internal/models"
	"github.com/gin-gonic/gin"
	"github.com/go-playground/validator/v10"
)

func GetUsers(c *gin.Context) {
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))

	rows, err := db.Pool.Query(c.Request.Context(), `
		SELECT id, username, full_name, bio
		FROM benchmark.tb_user
		ORDER BY created_at DESC
		LIMIT $1
	`, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var users []models.UserResponse
	for rows.Next() {
		var user models.UserResponse
		err := rows.Scan(&user.ID, &user.Username, &user.FullName, &user.Bio)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		users = append(users, user)
	}

	c.JSON(http.StatusOK, users)
}

func GetUser(c *gin.Context) {
	id := c.Param("id")
	include := strings.Split(c.Query("include"), ",")

	ctx := c.Request.Context()

	row := db.Pool.QueryRow(ctx, `
		SELECT id, username, full_name, bio
		FROM benchmark.tb_user WHERE id = $1
	`, id)

	var user models.UserResponse
	if err := row.Scan(&user.ID, &user.Username, &user.FullName, &user.Bio); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	for _, inc := range include {
		switch inc {
		case "posts":
			user.Posts = getPostsByUser(ctx, id)
		}
	}

	c.JSON(http.StatusOK, user)
}

func UpdateUser(c *gin.Context) {
	id := c.Param("id")

	var body models.UpdateUserRequest

	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate the input
	validate := validator.New()
	if err := validate.Struct(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Validation Error",
			"details": err.Error(),
		})
		return
	}

	query := "UPDATE benchmark.tb_user SET updated_at = NOW()"
	args := []interface{}{}
	argIdx := 1

	if body.FullName != nil {
		query += ", full_name = $" + strconv.Itoa(argIdx)
		args = append(args, *body.FullName)
		argIdx++
	}
	if body.Bio != nil {
		query += ", bio = $" + strconv.Itoa(argIdx)
		args = append(args, *body.Bio)
		argIdx++
	}

	query += " WHERE id = $" + strconv.Itoa(argIdx)
	args = append(args, id)

	_, err := db.Pool.Exec(c.Request.Context(), query, args...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "updated"})
}

func GetPosts(c *gin.Context) {
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	include := strings.Split(c.Query("include"), ",")

	ctx := c.Request.Context()

	rows, err := db.Pool.Query(ctx, `
		SELECT p.id, u.id as author_id, p.title, p.content
		FROM benchmark.tb_post p
		JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
		WHERE p.published = true
		ORDER BY p.created_at DESC
		LIMIT $1
	`, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var posts []map[string]interface{}
	for rows.Next() {
		var id, authorID, title string
		var content *string
		rows.Scan(&id, &authorID, &title, &content)
		post := map[string]interface{}{
			"id": id, "author_id": authorID, "title": title, "content": content,
		}

		// Add author details if requested
		for _, inc := range include {
			if inc == "author" {
				post["author"] = getAuthorByID(ctx, authorID)
				delete(post, "author_id")
			}
		}

		posts = append(posts, post)
	}

	c.JSON(http.StatusOK, posts)
}

func GetPost(c *gin.Context) {
	id := c.Param("id")

	row := db.Pool.QueryRow(c.Request.Context(), `
		SELECT p.id, u.id as author_id, p.title, p.content
		FROM benchmark.tb_post p
		JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
		WHERE p.id = $1
	`, id)

	var post struct {
		ID       string  `json:"id"`
		AuthorID string  `json:"author_id"`
		Title    string  `json:"title"`
		Content  *string `json:"content"`
	}
	if err := row.Scan(&post.ID, &post.AuthorID, &post.Title, &post.Content); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Post not found"})
		return
	}

	c.JSON(http.StatusOK, post)
}

func getPostsByUser(ctx context.Context, userID string) []models.Post {
	rows, err := db.Pool.Query(ctx, `
		SELECT p.id, p.title, p.content
		FROM benchmark.tb_post p
		JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
		WHERE u.id = $1 AND p.published = true
		ORDER BY p.created_at DESC LIMIT 10
	`, userID)
	if err != nil {
		return []models.Post{}
	}
	defer rows.Close()

	var posts []models.Post
	for rows.Next() {
		var post models.Post
		err := rows.Scan(&post.ID, &post.Title, &post.Content)
		if err != nil {
			continue
		}
		posts = append(posts, post)
	}
	return posts
}

func getAuthorByID(ctx context.Context, authorID string) map[string]interface{} {
	row := db.Pool.QueryRow(ctx, `
		SELECT id, username FROM benchmark.tb_user WHERE id = $1
	`, authorID)

	var id, username string
	if err := row.Scan(&id, &username); err != nil {
		return map[string]interface{}{}
	}

	return map[string]interface{}{"id": id, "username": username}
}
