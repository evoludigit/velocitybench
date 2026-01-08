package models

// Post represents a post in the system
type Post struct {
	ID       string    `json:"id" db:"id"`
	Title    string    `json:"title" db:"title"`
	Content  *string   `json:"content,omitempty" db:"content"`
	AuthorID string    `json:"author_id" db:"author_id"`
	Author   *User     `json:"author,omitempty"`
	Comments []Comment `json:"comments,omitempty"`
}

// PostResponse represents the post data returned in API responses
type PostResponse struct {
	ID       string    `json:"id"`
	Title    string    `json:"title"`
	Content  *string   `json:"content,omitempty"`
	Author   *User     `json:"author,omitempty"`
	Comments []Comment `json:"comments,omitempty"`
}
