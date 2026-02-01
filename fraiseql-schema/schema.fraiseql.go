package main

import (
	"encoding/json"
	"fmt"
	"os"
)

// FieldDefinition represents a GraphQL field with type information
type FieldDefinition struct {
	Type     string `json:"type"`
	Required bool   `json:"required"`
}

// ObjectType represents a GraphQL object type (e.g., User, Post)
type ObjectType struct {
	Name   string                     `json:"name"`
	Fields map[string]FieldDefinition `json:"fields"`
}

// QueryRoot represents the root Query type
type QueryRoot map[string]map[string]interface{}

// MutationRoot represents the root Mutation type
type MutationRoot map[string]map[string]interface{}

// Schema is the root schema container
type Schema struct {
	Types    map[string]ObjectType `json:"types"`
	Query    QueryRoot             `json:"query"`
	Mutation MutationRoot          `json:"mutation"`
}

// NewObjectType creates a new object type
func NewObjectType(name string) *ObjectType {
	return &ObjectType{
		Name:   name,
		Fields: make(map[string]FieldDefinition),
	}
}

// AddField adds a field to an object type
func (ot *ObjectType) AddField(name, fieldType string, required bool) {
	ot.Fields[name] = FieldDefinition{
		Type:     fieldType,
		Required: required,
	}
}

// BuildSchema builds and returns the FraiseQL schema definition
func BuildSchema() *Schema {
	schema := &Schema{
		Types:    make(map[string]ObjectType),
		Query:    make(QueryRoot),
		Mutation: make(MutationRoot),
	}

	// User type: represents a user in the system
	userType := NewObjectType("User")
	userType.AddField("id", "ID", true)
	userType.AddField("name", "String", true)
	userType.AddField("email", "String", true)
	userType.AddField("created_at", "DateTime", false)
	userType.AddField("is_active", "Boolean", false)
	schema.Types["User"] = *userType

	// Post type: represents a blog post
	postType := NewObjectType("Post")
	postType.AddField("id", "ID", true)
	postType.AddField("title", "String", true)
	postType.AddField("content", "String", true)
	postType.AddField("author_id", "ID", true)
	postType.AddField("published", "Boolean", false)
	postType.AddField("created_at", "DateTime", false)
	schema.Types["Post"] = *postType

	// Comment type: represents a comment on a post
	commentType := NewObjectType("Comment")
	commentType.AddField("id", "ID", true)
	commentType.AddField("content", "String", true)
	commentType.AddField("post_id", "ID", true)
	commentType.AddField("author_id", "ID", true)
	commentType.AddField("created_at", "DateTime", false)
	schema.Types["Comment"] = *commentType

	// Query root: defines all available queries
	schema.Query["users"] = map[string]interface{}{
		"type":      "[User]",
		"arguments": map[string]interface{}{},
	}
	schema.Query["posts"] = map[string]interface{}{
		"type":      "[Post]",
		"arguments": map[string]interface{}{},
	}

	// Mutation root: defines all available mutations
	schema.Mutation["create_user"] = map[string]interface{}{
		"type": "User",
		"arguments": map[string]interface{}{
			"name":  "String!",
			"email": "String!",
		},
	}

	return schema
}

func main() {
	schema := BuildSchema()
	jsonData, err := json.MarshalIndent(schema, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling schema: %v\n", err)
		os.Exit(1)
	}
	fmt.Println(string(jsonData))
}
