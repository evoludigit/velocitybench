package models

import "github.com/google/uuid"

// Comment represents a comment in the system
type Comment struct {
	ID       uuid.UUID `json:"id" db:"id"`
	Content  string    `json:"content" db:"content"`
	AuthorID uuid.UUID `json:"author_id" db:"author_id"`
	PostID   uuid.UUID `json:"post_id" db:"post_id"`
	Author   *User     `json:"author,omitempty"`
	Post     *Post     `json:"post,omitempty"`
}

// CommentResponse represents the comment data returned in API responses
type CommentResponse struct {
	ID      uuid.UUID `json:"id"`
	Content string    `json:"content"`
	Author  *User     `json:"author,omitempty"`
	Post    *Post     `json:"post,omitempty"`
}
