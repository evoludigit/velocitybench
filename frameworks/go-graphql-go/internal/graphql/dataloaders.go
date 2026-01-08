package graphql

import (
	"context"
	"log"

	"github.com/benchmark/go-graphql-go/internal/db"
	"github.com/graph-gophers/dataloader/v7"
)

// NewContext creates a new GraphQL context with initialized dataloaders
func NewContext() *Context {
	return &Context{
		UserLoader:           dataloader.NewBatchedLoader(loadUsersBatch),
		PostLoader:           dataloader.NewBatchedLoader(loadPostsBatch),
		PostsByAuthorLoader:  dataloader.NewBatchedLoader(loadPostsByAuthorBatch),
		CommentsByPostLoader: dataloader.NewBatchedLoader(loadCommentsByPostBatch),
		CommentLoader:        dataloader.NewBatchedLoader(loadCommentsBatch),
	}
}

// loadUsersBatch loads users by their IDs in batch
func loadUsersBatch(ctx context.Context, keys []string) []*dataloader.Result[*User] {
	results := make([]*dataloader.Result[*User], len(keys))

	// Build query to fetch all users
	query := `
		SELECT id, username, full_name, bio
		FROM benchmark.tb_user
		WHERE id = ANY($1)
	`

	rows, err := db.Pool.Query(ctx, query, keys)
	if err != nil {
		log.Printf("Error loading users batch: %v", err)
		for i := range results {
			results[i] = &dataloader.Result[*User]{Error: err}
		}
		return results
	}
	defer rows.Close()

	// Create a map for O(1) lookup
	userMap := make(map[string]*User)
	for rows.Next() {
		var user User
		err := rows.Scan(&user.ID, &user.Username, &user.FullName, &user.Bio)
		if err != nil {
			log.Printf("Error scanning user: %v", err)
			continue
		}
		userMap[user.ID] = &user
	}

	// Return results in the same order as keys
	for i, key := range keys {
		if user, exists := userMap[key]; exists {
			results[i] = &dataloader.Result[*User]{Data: user}
		} else {
			results[i] = &dataloader.Result[*User]{Data: nil}
		}
	}

	return results
}

// loadPostsBatch loads posts by their IDs in batch
func loadPostsBatch(ctx context.Context, keys []string) []*dataloader.Result[*Post] {
	results := make([]*dataloader.Result[*Post], len(keys))

	query := `
		SELECT p.id, p.title, p.content, u.id as author_id
		FROM benchmark.tb_post p
		JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
		WHERE p.id = ANY($1)
	`

	rows, err := db.Pool.Query(ctx, query, keys)
	if err != nil {
		log.Printf("Error loading posts batch: %v", err)
		for i := range results {
			results[i] = &dataloader.Result[*Post]{Error: err}
		}
		return results
	}
	defer rows.Close()

	postMap := make(map[string]*Post)
	for rows.Next() {
		var post Post
		err := rows.Scan(&post.ID, &post.Title, &post.Content, &post.AuthorID)
		if err != nil {
			log.Printf("Error scanning post: %v", err)
			continue
		}
		postMap[post.ID] = &post
	}

	for i, key := range keys {
		if post, exists := postMap[key]; exists {
			results[i] = &dataloader.Result[*Post]{Data: post}
		} else {
			results[i] = &dataloader.Result[*Post]{Data: nil}
		}
	}

	return results
}

// loadPostsByAuthorBatch loads posts by author IDs in batch
func loadPostsByAuthorBatch(ctx context.Context, keys []string) []*dataloader.Result[[]*Post] {
	results := make([]*dataloader.Result[[]*Post], len(keys))

	query := `
		SELECT p.id, p.title, p.content, u.id as author_id
		FROM benchmark.tb_post p
		JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
		WHERE u.id = ANY($1)
		ORDER BY u.id, p.created_at DESC
	`

	rows, err := db.Pool.Query(ctx, query, keys)
	if err != nil {
		log.Printf("Error loading posts by author batch: %v", err)
		for i := range results {
			results[i] = &dataloader.Result[[]*Post]{Error: err}
		}
		return results
	}
	defer rows.Close()

	// Group posts by author_id
	postsByAuthor := make(map[string][]*Post)
	for _, key := range keys {
		postsByAuthor[key] = []*Post{}
	}

	for rows.Next() {
		var post Post
		err := rows.Scan(&post.ID, &post.Title, &post.Content, &post.AuthorID)
		if err != nil {
			log.Printf("Error scanning post: %v", err)
			continue
		}
		if post.AuthorID != nil {
			postsByAuthor[*post.AuthorID] = append(postsByAuthor[*post.AuthorID], &post)
		}
	}

	for i, key := range keys {
		results[i] = &dataloader.Result[[]*Post]{Data: postsByAuthor[key]}
	}

	return results
}

// loadCommentsByPostBatch loads comments by post IDs in batch
func loadCommentsByPostBatch(ctx context.Context, keys []string) []*dataloader.Result[[]*Comment] {
	results := make([]*dataloader.Result[[]*Comment], len(keys))

	query := `
		SELECT c.id, c.content, u.id as author_id, p.id as post_id
		FROM benchmark.tb_comment c
		JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
		JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
		WHERE p.id = ANY($1)
		ORDER BY p.id, c.created_at DESC
	`

	rows, err := db.Pool.Query(ctx, query, keys)
	if err != nil {
		log.Printf("Error loading comments by post batch: %v", err)
		for i := range results {
			results[i] = &dataloader.Result[[]*Comment]{Error: err}
		}
		return results
	}
	defer rows.Close()

	// Group comments by post_id
	commentsByPost := make(map[string][]*Comment)
	for _, key := range keys {
		commentsByPost[key] = []*Comment{}
	}

	for rows.Next() {
		var comment Comment
		err := rows.Scan(&comment.ID, &comment.Content, &comment.AuthorID, &comment.PostID)
		if err != nil {
			log.Printf("Error scanning comment: %v", err)
			continue
		}
		if comment.PostID != nil {
			commentsByPost[*comment.PostID] = append(commentsByPost[*comment.PostID], &comment)
		}
	}

	// Limit to 50 comments per post
	for i, key := range keys {
		comments := commentsByPost[key]
		if len(comments) > 50 {
			comments = comments[:50]
		}
		results[i] = &dataloader.Result[[]*Comment]{Data: comments}
	}

	return results
}

// loadCommentsBatch loads comments by their IDs in batch
func loadCommentsBatch(ctx context.Context, keys []string) []*dataloader.Result[*Comment] {
	results := make([]*dataloader.Result[*Comment], len(keys))

	query := `
		SELECT c.id, c.content, u.id as author_id, p.id as post_id
		FROM benchmark.tb_comment c
		JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
		JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
		WHERE c.id = ANY($1)
	`

	rows, err := db.Pool.Query(ctx, query, keys)
	if err != nil {
		log.Printf("Error loading comments batch: %v", err)
		for i := range results {
			results[i] = &dataloader.Result[*Comment]{Error: err}
		}
		return results
	}
	defer rows.Close()

	commentMap := make(map[string]*Comment)
	for rows.Next() {
		var comment Comment
		err := rows.Scan(&comment.ID, &comment.Content, &comment.AuthorID, &comment.PostID)
		if err != nil {
			log.Printf("Error scanning comment: %v", err)
			continue
		}
		commentMap[comment.ID] = &comment
	}

	for i, key := range keys {
		if comment, exists := commentMap[key]; exists {
			results[i] = &dataloader.Result[*Comment]{Data: comment}
		} else {
			results[i] = &dataloader.Result[*Comment]{Data: nil}
		}
	}

	return results
}
