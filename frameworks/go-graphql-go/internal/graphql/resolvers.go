package graphql

import (
	"context"
	"log"
	"strings"

	"github.com/benchmark/go-graphql-go/internal/db"
	"github.com/graphql-go/graphql"
)

// resolveUser resolves a single user by ID
func resolveUser(p graphql.ResolveParams) (interface{}, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, nil
	}

	ctx := p.Context.(context.Context)
	gctx := ctx.Value("graphql_context").(*Context)

	thunk := gctx.UserLoader.Load(ctx, id)
	result, err := thunk()
	if err != nil {
		log.Printf("Error loading user %s: %v", id, err)
		return nil, err
	}

	return result, nil
}

// resolveUsers resolves multiple users with optional limit
func resolveUsers(p graphql.ResolveParams) (interface{}, error) {
	limit, ok := p.Args["limit"].(int)
	if !ok {
		limit = 10
	}

	query := `
		SELECT id, username, full_name, bio
		FROM benchmark.tb_user
		LIMIT $1
	`

	rows, err := db.Pool.Query(p.Context, query, limit)
	if err != nil {
		log.Printf("Error querying users: %v", err)
		return nil, err
	}
	defer rows.Close()

	var users []*User
	for rows.Next() {
		var user User
		err := rows.Scan(&user.ID, &user.Username, &user.FullName, &user.Bio)
		if err != nil {
			log.Printf("Error scanning user: %v", err)
			continue
		}
		users = append(users, &user)
	}

	return users, nil
}

// resolvePost resolves a single post by ID
func resolvePost(p graphql.ResolveParams) (interface{}, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, nil
	}

	ctx := p.Context.(context.Context)
	gctx := ctx.Value("graphql_context").(*Context)

	thunk := gctx.PostLoader.Load(ctx, id)
	result, err := thunk()
	if err != nil {
		log.Printf("Error loading post %s: %v", id, err)
		return nil, err
	}

	return result, nil
}

// resolvePosts resolves multiple posts with optional limit
func resolvePosts(p graphql.ResolveParams) (interface{}, error) {
	limit, ok := p.Args["limit"].(int)
	if !ok {
		limit = 10
	}

	query := `
		SELECT p.id, p.title, p.content, u.id as author_id
		FROM benchmark.tb_post p
		JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
		LIMIT $1
	`

	rows, err := db.Pool.Query(p.Context, query, limit)
	if err != nil {
		log.Printf("Error querying posts: %v", err)
		return nil, err
	}
	defer rows.Close()

	var posts []*Post
	for rows.Next() {
		var post Post
		err := rows.Scan(&post.ID, &post.Title, &post.Content, &post.AuthorID)
		if err != nil {
			log.Printf("Error scanning post: %v", err)
			continue
		}
		posts = append(posts, &post)
	}

	return posts, nil
}

// resolveComment resolves a single comment by ID
func resolveComment(p graphql.ResolveParams) (interface{}, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, nil
	}

	ctx := p.Context.(context.Context)
	gctx := ctx.Value("graphql_context").(*Context)

	thunk := gctx.CommentLoader.Load(ctx, id)
	result, err := thunk()
	if err != nil {
		log.Printf("Error loading comment %s: %v", id, err)
		return nil, err
	}

	return result, nil
}

// resolveUserPosts resolves posts for a user
func resolveUserPosts(p graphql.ResolveParams) (interface{}, error) {
	user, ok := p.Source.(*User)
	if !ok || user == nil {
		return []*Post{}, nil
	}

	limit, ok := p.Args["limit"].(int)
	if !ok {
		limit = 50
	}

	ctx := p.Context.(context.Context)
	gctx := ctx.Value("graphql_context").(*Context)

	thunk := gctx.PostsByAuthorLoader.Load(ctx, user.ID)
	result, err := thunk()
	if err != nil {
		log.Printf("Error loading posts for user %s: %v", user.ID, err)
		return []*Post{}, err
	}

	// Apply limit
	if len(result) > limit {
		result = result[:limit]
	}

	return result, nil
}

// resolvePostAuthor resolves the author of a post
func resolvePostAuthor(p graphql.ResolveParams) (interface{}, error) {
	post, ok := p.Source.(*Post)
	if !ok || post == nil || post.AuthorID == nil {
		return nil, nil
	}

	ctx := p.Context.(context.Context)
	gctx := ctx.Value("graphql_context").(*Context)

	thunk := gctx.UserLoader.Load(ctx, *post.AuthorID)
	result, err := thunk()
	if err != nil {
		log.Printf("Error loading author %s for post %s: %v", *post.AuthorID, post.ID, err)
		return nil, err
	}

	return result, nil
}

// resolvePostComments resolves comments for a post
func resolvePostComments(p graphql.ResolveParams) (interface{}, error) {
	post, ok := p.Source.(*Post)
	if !ok || post == nil {
		return []*Comment{}, nil
	}

	limit, ok := p.Args["limit"].(int)
	if !ok {
		limit = 50
	}

	ctx := p.Context.(context.Context)
	gctx := ctx.Value("graphql_context").(*Context)

	thunk := gctx.CommentsByPostLoader.Load(ctx, post.ID)
	result, err := thunk()
	if err != nil {
		log.Printf("Error loading comments for post %s: %v", post.ID, err)
		return []*Comment{}, err
	}

	// Apply limit
	if len(result) > limit {
		result = result[:limit]
	}

	return result, nil
}

// resolveCommentAuthor resolves the author of a comment
func resolveCommentAuthor(p graphql.ResolveParams) (interface{}, error) {
	comment, ok := p.Source.(*Comment)
	if !ok || comment == nil || comment.AuthorID == nil {
		return nil, nil
	}

	ctx := p.Context.(context.Context)
	gctx := ctx.Value("graphql_context").(*Context)

	thunk := gctx.UserLoader.Load(ctx, *comment.AuthorID)
	result, err := thunk()
	if err != nil {
		log.Printf("Error loading author %s for comment %s: %v", *comment.AuthorID, comment.ID, err)
		return nil, err
	}

	return result, nil
}

// resolveCommentPost resolves the post of a comment
func resolveCommentPost(p graphql.ResolveParams) (interface{}, error) {
	comment, ok := p.Source.(*Comment)
	if !ok || comment == nil || comment.PostID == nil {
		return nil, nil
	}

	ctx := p.Context.(context.Context)
	gctx := ctx.Value("graphql_context").(*Context)

	thunk := gctx.PostLoader.Load(ctx, *comment.PostID)
	result, err := thunk()
	if err != nil {
		log.Printf("Error loading post %s for comment %s: %v", *comment.PostID, comment.ID, err)
		return nil, err
	}

	return result, nil
}

// resolveUpdateUser updates a user
func resolveUpdateUser(p graphql.ResolveParams) (interface{}, error) {
	id, ok := p.Args["id"].(string)
	if !ok {
		return nil, nil
	}

	ctx := p.Context.(context.Context)

	// Build update query dynamically
	updateFields := []string{}
	params := []interface{}{id}
	paramIdx := 2

	if bio, ok := p.Args["bio"].(*string); ok && bio != nil {
		updateFields = append(updateFields, "bio = $"+string(rune(paramIdx+'0')))
		params = append(params, *bio)
		paramIdx++
	}

	if fullName, ok := p.Args["fullName"].(*string); ok && fullName != nil {
		updateFields = append(updateFields, "full_name = $"+string(rune(paramIdx+'0')))
		params = append(params, *fullName)
		paramIdx++
	}

	if len(updateFields) > 0 {
		updateQuery := `
			UPDATE benchmark.tb_user
			SET ` + strings.Join(updateFields, ", ") + `, updated_at = NOW()
			WHERE id = $1
		`

		_, err := db.Pool.Exec(ctx, updateQuery, params...)
		if err != nil {
			log.Printf("Error updating user %s: %v", id, err)
			return nil, err
		}
	}

	// Return updated user
	query := `
		SELECT id, username, full_name, bio
		FROM benchmark.tb_user
		WHERE id = $1
	`

	var user User
	err := db.Pool.QueryRow(ctx, query, id).Scan(
		&user.ID, &user.Username, &user.FullName, &user.Bio,
	)
	if err != nil {
		log.Printf("Error fetching updated user %s: %v", id, err)
		return nil, err
	}

	return &user, nil
}
