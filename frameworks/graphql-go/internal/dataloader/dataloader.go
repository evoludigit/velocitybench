package dataloader

import (
	"context"
	"time"

	"github.com/benchmark/graphql-go/internal/db"
	"github.com/benchmark/graphql-go/internal/model"
	"github.com/graph-gophers/dataloader/v7"
)

// Loaders contains all dataloaders for N+1 prevention
type Loaders struct {
	UserLoader           *dataloader.Loader[string, *model.User]
	PostLoader           *dataloader.Loader[string, *model.Post]
	PostsByAuthorLoader  *dataloader.Loader[string, []*model.Post]
	CommentsByPostLoader *dataloader.Loader[string, []*model.Comment]
}

// NewLoaders creates new dataloader instances
func NewLoaders() *Loaders {
	return &Loaders{
		UserLoader: dataloader.NewBatchedLoader(
			batchUsers,
			dataloader.WithWait[string, *model.User](2*time.Millisecond),
			dataloader.WithBatchCapacity[string, *model.User](100),
		),
		PostLoader: dataloader.NewBatchedLoader(
			batchPosts,
			dataloader.WithWait[string, *model.Post](2*time.Millisecond),
			dataloader.WithBatchCapacity[string, *model.Post](100),
		),
		PostsByAuthorLoader: dataloader.NewBatchedLoader(
			batchPostsByAuthor,
			dataloader.WithWait[string, []*model.Post](2*time.Millisecond),
			dataloader.WithBatchCapacity[string, []*model.Post](100),
		),
		CommentsByPostLoader: dataloader.NewBatchedLoader(
			batchCommentsByPost,
			dataloader.WithWait[string, []*model.Comment](2*time.Millisecond),
			dataloader.WithBatchCapacity[string, []*model.Comment](100),
		),
	}
}

func batchUsers(ctx context.Context, keys []string) []*dataloader.Result[*model.User] {
	results := make([]*dataloader.Result[*model.User], len(keys))

	rows, err := db.Pool.Query(ctx, `
		SELECT id, username, full_name, bio
		FROM benchmark.tb_user
		WHERE id = ANY($1)
	`, keys)
	if err != nil {
		for i := range results {
			results[i] = &dataloader.Result[*model.User]{Error: err}
		}
		return results
	}
	defer rows.Close()

	userMap := make(map[string]*model.User)
	for rows.Next() {
		var u model.User
		var fullName, bio *string
		if err := rows.Scan(&u.ID, &u.Username, &fullName, &bio); err != nil {
			continue
		}
		u.FullName = fullName
		u.Bio = bio
		userMap[u.ID] = &u
	}

	for i, key := range keys {
		if user, ok := userMap[key]; ok {
			results[i] = &dataloader.Result[*model.User]{Data: user}
		} else {
			results[i] = &dataloader.Result[*model.User]{Data: nil}
		}
	}

	return results
}

func batchPosts(ctx context.Context, keys []string) []*dataloader.Result[*model.Post] {
	results := make([]*dataloader.Result[*model.Post], len(keys))

	rows, err := db.Pool.Query(ctx, `
		SELECT p.id, u.id as author_id, p.title, p.content, p.created_at
		FROM benchmark.tb_post p
		JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
		WHERE p.id = ANY($1)
	`, keys)
	if err != nil {
		for i := range results {
			results[i] = &dataloader.Result[*model.Post]{Error: err}
		}
		return results
	}
	defer rows.Close()

	postMap := make(map[string]*model.Post)
	for rows.Next() {
		var p model.Post
		var content *string
		var createdAt string
		if err := rows.Scan(&p.ID, &p.AuthorID, &p.Title, &content, &createdAt); err != nil {
			continue
		}
		p.Content = content
		p.CreatedAt = createdAt
		postMap[p.ID] = &p
	}

	for i, key := range keys {
		if post, ok := postMap[key]; ok {
			results[i] = &dataloader.Result[*model.Post]{Data: post}
		} else {
			results[i] = &dataloader.Result[*model.Post]{Data: nil}
		}
	}

	return results
}

func batchPostsByAuthor(ctx context.Context, authorIDs []string) []*dataloader.Result[[]*model.Post] {
	results := make([]*dataloader.Result[[]*model.Post], len(authorIDs))

	rows, err := db.Pool.Query(ctx, `
		SELECT p.id, u.id as author_id, p.title, p.content, p.created_at
		FROM benchmark.tb_post p
		JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
		WHERE u.id = ANY($1)
		ORDER BY p.created_at DESC
	`, authorIDs)
	if err != nil {
		for i := range results {
			results[i] = &dataloader.Result[[]*model.Post]{Error: err}
		}
		return results
	}
	defer rows.Close()

	postMap := make(map[string][]*model.Post)
	for rows.Next() {
		var p model.Post
		var content *string
		var createdAt string
		if err := rows.Scan(&p.ID, &p.AuthorID, &p.Title, &content, &createdAt); err != nil {
			continue
		}
		p.Content = content
		p.CreatedAt = createdAt
		postMap[p.AuthorID] = append(postMap[p.AuthorID], &p)
	}

	for i, authorID := range authorIDs {
		posts := postMap[authorID]
		if posts == nil {
			posts = []*model.Post{}
		}
		results[i] = &dataloader.Result[[]*model.Post]{Data: posts}
	}

	return results
}

func batchCommentsByPost(ctx context.Context, postIDs []string) []*dataloader.Result[[]*model.Comment] {
	results := make([]*dataloader.Result[[]*model.Comment], len(postIDs))

	rows, err := db.Pool.Query(ctx, `
		SELECT c.id, c.content, u.id as author_id, p.id as post_id
		FROM benchmark.tb_comment c
		LEFT JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
		LEFT JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
		WHERE p.id = ANY($1)
		ORDER BY c.created_at DESC
	`, postIDs)
	if err != nil {
		for i := range results {
			results[i] = &dataloader.Result[[]*model.Comment]{Error: err}
		}
		return results
	}
	defer rows.Close()

	commentMap := make(map[string][]*model.Comment)
	for rows.Next() {
		var c model.Comment
		var authorID, postID *string
		if err := rows.Scan(&c.ID, &c.Content, &authorID, &postID); err != nil {
			continue
		}
		c.AuthorID = authorID
		c.PostID = postID
		if postID != nil {
			commentMap[*postID] = append(commentMap[*postID], &c)
		}
	}

	for i, postID := range postIDs {
		comments := commentMap[postID]
		if comments == nil {
			comments = []*model.Comment{}
		}
		results[i] = &dataloader.Result[[]*model.Comment]{Data: comments}
	}

	return results
}

// Context key for dataloaders
type loadersKey struct{}

// WithLoaders adds loaders to context
func WithLoaders(ctx context.Context, loaders *Loaders) context.Context {
	return context.WithValue(ctx, loadersKey{}, loaders)
}

// GetLoaders retrieves loaders from context
func GetLoaders(ctx context.Context) *Loaders {
	return ctx.Value(loadersKey{}).(*Loaders)
}
