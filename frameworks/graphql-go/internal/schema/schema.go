package schema

import (
	"context"

	"github.com/benchmark/graphql-go/internal/dataloader"
	"github.com/benchmark/graphql-go/internal/db"
	"github.com/benchmark/graphql-go/internal/model"
	"github.com/graphql-go/graphql"
)

// Schema is the GraphQL schema
var Schema graphql.Schema

func init() {
	// Forward declarations for recursive types
	var userType *graphql.Object
	var postType *graphql.Object
	var commentType *graphql.Object

	// Comment type
	commentType = graphql.NewObject(graphql.ObjectConfig{
		Name: "Comment",
		Fields: graphql.FieldsThunk(func() graphql.Fields {
			return graphql.Fields{
				"id": &graphql.Field{
					Type: graphql.NewNonNull(graphql.ID),
				},
				"content": &graphql.Field{
					Type: graphql.NewNonNull(graphql.String),
				},
				"author": &graphql.Field{
					Type: userType,
					Resolve: func(p graphql.ResolveParams) (interface{}, error) {
						comment := p.Source.(*model.Comment)
						if comment.AuthorID == nil {
							return nil, nil
						}
						loaders := dataloader.GetLoaders(p.Context)
						return loaders.UserLoader.Load(p.Context, *comment.AuthorID)()
					},
				},
				"post": &graphql.Field{
					Type: postType,
					Resolve: func(p graphql.ResolveParams) (interface{}, error) {
						comment := p.Source.(*model.Comment)
						if comment.PostID == nil {
							return nil, nil
						}
						loaders := dataloader.GetLoaders(p.Context)
						return loaders.PostLoader.Load(p.Context, *comment.PostID)()
					},
				},
			}
		}),
	})

	// Post type
	postType = graphql.NewObject(graphql.ObjectConfig{
		Name: "Post",
		Fields: graphql.FieldsThunk(func() graphql.Fields {
			return graphql.Fields{
				"id": &graphql.Field{
					Type: graphql.NewNonNull(graphql.ID),
				},
				"title": &graphql.Field{
					Type: graphql.NewNonNull(graphql.String),
				},
				"content": &graphql.Field{
					Type: graphql.String,
				},
				"createdAt": &graphql.Field{
					Type: graphql.NewNonNull(graphql.String),
				},
				"author": &graphql.Field{
					Type: graphql.NewNonNull(userType),
					Resolve: func(p graphql.ResolveParams) (interface{}, error) {
						post := p.Source.(*model.Post)
						loaders := dataloader.GetLoaders(p.Context)
						return loaders.UserLoader.Load(p.Context, post.AuthorID)()
					},
				},
				"comments": &graphql.Field{
					Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(commentType))),
					Args: graphql.FieldConfigArgument{
						"limit": &graphql.ArgumentConfig{
							Type:         graphql.Int,
							DefaultValue: 50,
						},
					},
					Resolve: func(p graphql.ResolveParams) (interface{}, error) {
						post := p.Source.(*model.Post)
						limit := 50
						if l, ok := p.Args["limit"].(int); ok {
							limit = l
						}

						loaders := dataloader.GetLoaders(p.Context)
						comments, err := loaders.CommentsByPostLoader.Load(p.Context, post.ID)()
						if err != nil {
							return nil, err
						}

						if len(comments) > limit {
							comments = comments[:limit]
						}
						return comments, nil
					},
				},
			}
		}),
	})

	// User type
	userType = graphql.NewObject(graphql.ObjectConfig{
		Name: "User",
		Fields: graphql.FieldsThunk(func() graphql.Fields {
			return graphql.Fields{
				"id": &graphql.Field{
					Type: graphql.NewNonNull(graphql.ID),
				},
				"username": &graphql.Field{
					Type: graphql.NewNonNull(graphql.String),
				},
				"fullName": &graphql.Field{
					Type: graphql.String,
				},
				"bio": &graphql.Field{
					Type: graphql.String,
				},
				"posts": &graphql.Field{
					Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(postType))),
					Args: graphql.FieldConfigArgument{
						"limit": &graphql.ArgumentConfig{
							Type:         graphql.Int,
							DefaultValue: 50,
						},
					},
					Resolve: func(p graphql.ResolveParams) (interface{}, error) {
						user := p.Source.(*model.User)
						limit := 50
						if l, ok := p.Args["limit"].(int); ok {
							limit = l
						}

						loaders := dataloader.GetLoaders(p.Context)
						posts, err := loaders.PostsByAuthorLoader.Load(p.Context, user.ID)()
						if err != nil {
							return nil, err
						}

						if len(posts) > limit {
							posts = posts[:limit]
						}
						return posts, nil
					},
				},
				"followers": &graphql.Field{
					Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(userType))),
					Args: graphql.FieldConfigArgument{
						"limit": &graphql.ArgumentConfig{
							Type:         graphql.Int,
							DefaultValue: 50,
						},
					},
					Resolve: func(p graphql.ResolveParams) (interface{}, error) {
						// Followers relationship not implemented in benchmark schema
						return []*model.User{}, nil
					},
				},
				"following": &graphql.Field{
					Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(userType))),
					Args: graphql.FieldConfigArgument{
						"limit": &graphql.ArgumentConfig{
							Type:         graphql.Int,
							DefaultValue: 50,
						},
					},
					Resolve: func(p graphql.ResolveParams) (interface{}, error) {
						// Following relationship not implemented in benchmark schema
						return []*model.User{}, nil
					},
				},
			}
		}),
	})

	// Query type
	queryType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"ping": &graphql.Field{
				Type: graphql.NewNonNull(graphql.String),
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					return "pong", nil
				},
			},
			"user": &graphql.Field{
				Type: userType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.ID),
					},
				},
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					id := p.Args["id"].(string)
					loaders := dataloader.GetLoaders(p.Context)
					return loaders.UserLoader.Load(p.Context, id)()
				},
			},
			"users": &graphql.Field{
				Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(userType))),
				Args: graphql.FieldConfigArgument{
					"limit": &graphql.ArgumentConfig{
						Type:         graphql.Int,
						DefaultValue: 10,
					},
				},
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					limit := 10
					if l, ok := p.Args["limit"].(int); ok {
						limit = l
					}

					rows, err := db.Pool.Query(p.Context, `
						SELECT id, username, full_name, bio
						FROM benchmark.tb_user
						ORDER BY created_at DESC
						LIMIT $1
					`, limit)
					if err != nil {
						return nil, err
					}
					defer rows.Close()

					var users []*model.User
					for rows.Next() {
						var u model.User
						var fullName, bio *string
						if err := rows.Scan(&u.ID, &u.Username, &fullName, &bio); err != nil {
							continue
						}
						u.FullName = fullName
						u.Bio = bio
						users = append(users, &u)
					}

					if users == nil {
						users = []*model.User{}
					}
					return users, nil
				},
			},
			"post": &graphql.Field{
				Type: postType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.ID),
					},
				},
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					id := p.Args["id"].(string)
					loaders := dataloader.GetLoaders(p.Context)
					return loaders.PostLoader.Load(p.Context, id)()
				},
			},
			"posts": &graphql.Field{
				Type: graphql.NewNonNull(graphql.NewList(graphql.NewNonNull(postType))),
				Args: graphql.FieldConfigArgument{
					"limit": &graphql.ArgumentConfig{
						Type:         graphql.Int,
						DefaultValue: 10,
					},
				},
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					limit := 10
					if l, ok := p.Args["limit"].(int); ok {
						limit = l
					}

					rows, err := db.Pool.Query(p.Context, `
						SELECT p.id, u.id as author_id, p.title, p.content, p.created_at
						FROM benchmark.tb_post p
						JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
						ORDER BY p.created_at DESC
						LIMIT $1
					`, limit)
					if err != nil {
						return nil, err
					}
					defer rows.Close()

					var posts []*model.Post
					for rows.Next() {
						var p model.Post
						var content *string
						var createdAt string
						if err := rows.Scan(&p.ID, &p.AuthorID, &p.Title, &content, &createdAt); err != nil {
							continue
						}
						p.Content = content
						p.CreatedAt = createdAt
						posts = append(posts, &p)
					}

					if posts == nil {
						posts = []*model.Post{}
					}
					return posts, nil
				},
			},
		},
	})

	// Mutation type
	mutationType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Mutation",
		Fields: graphql.Fields{
			"updateUser": &graphql.Field{
				Type: userType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.ID),
					},
					"fullName": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
					"bio": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
				},
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					id := p.Args["id"].(string)
					fullName, hasFullName := p.Args["fullName"].(string)
					bio, hasBio := p.Args["bio"].(string)

					query := "UPDATE benchmark.tb_user SET updated_at = NOW()"
					args := []interface{}{}
					argIdx := 1

					if hasFullName {
						query += ", full_name = $" + string(rune('0'+argIdx))
						args = append(args, fullName)
						argIdx++
					}
					if hasBio {
						query += ", bio = $" + string(rune('0'+argIdx))
						args = append(args, bio)
						argIdx++
					}

					query += " WHERE id = $" + string(rune('0'+argIdx))
					args = append(args, id)

					_, err := db.Pool.Exec(p.Context, query, args...)
					if err != nil {
						return nil, err
					}

					// Return updated user via dataloader
					loaders := dataloader.GetLoaders(p.Context)
					loaders.UserLoader.Clear(p.Context, id)
					return loaders.UserLoader.Load(p.Context, id)()
				},
			},
			"updatePost": &graphql.Field{
				Type: postType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.ID),
					},
					"title": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
					"content": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
				},
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					id := p.Args["id"].(string)
					title, hasTitle := p.Args["title"].(string)
					content, hasContent := p.Args["content"].(string)

					query := "UPDATE benchmark.tb_post SET updated_at = NOW()"
					args := []interface{}{}
					argIdx := 1

					if hasTitle {
						query += ", title = $" + string(rune('0'+argIdx))
						args = append(args, title)
						argIdx++
					}
					if hasContent {
						query += ", content = $" + string(rune('0'+argIdx))
						args = append(args, content)
						argIdx++
					}

					query += " WHERE id = $" + string(rune('0'+argIdx))
					args = append(args, id)

					_, err := db.Pool.Exec(p.Context, query, args...)
					if err != nil {
						return nil, err
					}

					// Return updated post via dataloader
					loaders := dataloader.GetLoaders(p.Context)
					loaders.PostLoader.Clear(p.Context, id)
					return loaders.PostLoader.Load(p.Context, id)()
				},
			},
		},
	})

	// Build schema
	var err error
	Schema, err = graphql.NewSchema(graphql.SchemaConfig{
		Query:    queryType,
		Mutation: mutationType,
	})
	if err != nil {
		panic(err)
	}
}

// ExecuteQuery executes a GraphQL query
func ExecuteQuery(ctx context.Context, query string, variables map[string]interface{}) *graphql.Result {
	return graphql.Do(graphql.Params{
		Schema:         Schema,
		RequestString:  query,
		VariableValues: variables,
		Context:        ctx,
	})
}
