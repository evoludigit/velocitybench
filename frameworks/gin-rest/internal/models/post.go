package models

import "github.com/google/uuid"

// Post represents a post in the system
type Post struct {
	ID       uuid.UUID `json:"id" db:"id"`
	Title    string    `json:"title" db:"title"`
	Content  *string   `json:"content,omitempty" db:"content"`
	AuthorID uuid.UUID `json:"author_id" db:"author_id"`
	Author   *User     `json:"author,omitempty"`
	Comments []Comment `json:"comments,omitempty"`
}

// PostResponse represents the post data returned in API responses
type PostResponse struct {
	ID       uuid.UUID `json:"id"`
	Title    string    `json:"title"`
	Content  *string   `json:"content,omitempty"`
	Author   *User     `json:"author,omitempty"`
	Comments []Comment `json:"comments,omitempty"`
}
