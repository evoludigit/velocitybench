package graphql

import (
	"github.com/graph-gophers/dataloader/v7"
	"github.com/graphql-go/graphql"
)

// User represents a user in the system
type User struct {
	ID       string  `json:"id"`
	Username string  `json:"username"`
	FullName *string `json:"fullName"`
	Bio      *string `json:"bio"`
}

// Post represents a post in the system
type Post struct {
	ID       string  `json:"id"`
	Title    string  `json:"title"`
	Content  *string `json:"content"`
	AuthorID *string `json:"authorId"`
}

// Comment represents a comment on a post
type Comment struct {
	ID       string  `json:"id"`
	Content  string  `json:"content"`
	AuthorID *string `json:"authorId"`
	PostID   *string `json:"postId"`
}

// Context holds the dataloaders and database connection
type Context struct {
	UserLoader           *dataloader.Loader[string, *User]
	PostLoader           *dataloader.Loader[string, *Post]
	PostsByAuthorLoader  *dataloader.Loader[string, []*Post]
	CommentsByPostLoader *dataloader.Loader[string, []*Comment]
	CommentLoader        *dataloader.Loader[string, *Comment]
}

// NewSchema creates the GraphQL schema
func NewSchema() (graphql.Schema, error) {
	// Define types with circular references using FieldsThunk
	var userType *graphql.Object
	var postType *graphql.Object
	var commentType *graphql.Object

	userType = graphql.NewObject(graphql.ObjectConfig{
		Name: "User",
		Fields: graphql.FieldsThunk(func() graphql.Fields {
			return graphql.Fields{
				"id": &graphql.Field{
					Type: graphql.NewNonNull(graphql.String),
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
					Type: graphql.NewList(postType),
					Args: graphql.FieldConfigArgument{
						"limit": &graphql.ArgumentConfig{
							Type:         graphql.Int,
							DefaultValue: 50,
						},
					},
					Resolve: resolveUserPosts,
				},
			}
		}),
	})

	postType = graphql.NewObject(graphql.ObjectConfig{
		Name: "Post",
		Fields: graphql.FieldsThunk(func() graphql.Fields {
			return graphql.Fields{
				"id": &graphql.Field{
					Type: graphql.NewNonNull(graphql.String),
				},
				"title": &graphql.Field{
					Type: graphql.NewNonNull(graphql.String),
				},
				"content": &graphql.Field{
					Type: graphql.String,
				},
				"authorId": &graphql.Field{
					Type: graphql.String,
				},
				"author": &graphql.Field{
					Type:    userType,
					Resolve: resolvePostAuthor,
				},
				"comments": &graphql.Field{
					Type: graphql.NewList(commentType),
					Args: graphql.FieldConfigArgument{
						"limit": &graphql.ArgumentConfig{
							Type:         graphql.Int,
							DefaultValue: 50,
						},
					},
					Resolve: resolvePostComments,
				},
			}
		}),
	})

	commentType = graphql.NewObject(graphql.ObjectConfig{
		Name: "Comment",
		Fields: graphql.FieldsThunk(func() graphql.Fields {
			return graphql.Fields{
				"id": &graphql.Field{
					Type: graphql.NewNonNull(graphql.String),
				},
				"content": &graphql.Field{
					Type: graphql.NewNonNull(graphql.String),
				},
				"authorId": &graphql.Field{
					Type: graphql.String,
				},
				"postId": &graphql.Field{
					Type: graphql.String,
				},
				"author": &graphql.Field{
					Type:    userType,
					Resolve: resolveCommentAuthor,
				},
				"post": &graphql.Field{
					Type:    postType,
					Resolve: resolveCommentPost,
				},
			}
		}),
	})

	// Define Query type
	queryType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"ping": &graphql.Field{
				Type: graphql.String,
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					return "pong", nil
				},
			},
			"user": &graphql.Field{
				Type: userType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolveUser,
			},
			"users": &graphql.Field{
				Type: graphql.NewList(userType),
				Args: graphql.FieldConfigArgument{
					"limit": &graphql.ArgumentConfig{
						Type:         graphql.Int,
						DefaultValue: 10,
					},
				},
				Resolve: resolveUsers,
			},
			"post": &graphql.Field{
				Type: postType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolvePost,
			},
			"posts": &graphql.Field{
				Type: graphql.NewList(postType),
				Args: graphql.FieldConfigArgument{
					"limit": &graphql.ArgumentConfig{
						Type:         graphql.Int,
						DefaultValue: 10,
					},
				},
				Resolve: resolvePosts,
			},
			"comment": &graphql.Field{
				Type: commentType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolveComment,
			},
		},
	})

	// Define Mutation type
	mutationType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Mutation",
		Fields: graphql.Fields{
			"updateUser": &graphql.Field{
				Type: userType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
					"bio": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
					"fullName": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
				},
				Resolve: resolveUpdateUser,
			},
		},
	})

	schemaConfig := graphql.SchemaConfig{
		Query:    queryType,
		Mutation: mutationType,
	}

	return graphql.NewSchema(schemaConfig)
}
