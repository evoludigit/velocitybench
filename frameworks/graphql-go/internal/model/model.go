package model

// User represents a user in the system
type User struct {
	ID       string  `json:"id"`
	Username string  `json:"username"`
	FullName *string `json:"fullName,omitempty"`
	Bio      *string `json:"bio,omitempty"`
}

// Post represents a blog post
type Post struct {
	ID        string  `json:"id"`
	Title     string  `json:"title"`
	Content   *string `json:"content,omitempty"`
	AuthorID  string  `json:"-"` // Internal: for dataloader
	CreatedAt string  `json:"createdAt"`
}

// Comment represents a comment on a post
type Comment struct {
	ID       string  `json:"id"`
	Content  string  `json:"content"`
	AuthorID *string `json:"-"` // Internal: for dataloader
	PostID   *string `json:"-"` // Internal: for dataloader
}
