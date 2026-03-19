package graph

// UpdateUserRequest holds validated input for the updateUser mutation.
type UpdateUserRequest struct {
	ID       string  `validate:"required,uuid"`
	FullName *string `validate:"omitempty,max=255"`
	Bio      *string `validate:"omitempty,max=1000"`
}
