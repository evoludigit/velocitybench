package models

// User represents a user in the system
type User struct {
	ID       string  `json:"id" db:"id"`
	Username string  `json:"username" db:"username"`
	FullName *string `json:"full_name,omitempty" db:"full_name"`
	Bio      *string `json:"bio,omitempty" db:"bio"`
	Posts    []Post  `json:"posts,omitempty"`
}

// UserResponse represents the user data returned in API responses
type UserResponse struct {
	ID       string  `json:"id"`
	Username string  `json:"username"`
	FullName *string `json:"full_name,omitempty"`
	Bio      *string `json:"bio,omitempty"`
	Posts    []Post  `json:"posts,omitempty"`
}

// UpdateUserRequest represents the request payload for updating a user
type UpdateUserRequest struct {
	FullName *string `json:"full_name" validate:"omitempty,max=255"`
	Bio      *string `json:"bio" validate:"omitempty,max=1000"`
}
