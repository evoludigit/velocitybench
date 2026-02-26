package main

import (
	"context"
	"fmt"
	"testing"

	"github.com/google/uuid"
	"github.com/benchmark/go-gqlgen/graph/model"
)

// TestFactory provides helper methods for creating test data
type TestFactory struct {
	t     *testing.T
	users map[string]*model.User
	posts map[string]*model.Post
}

// NewTestFactory creates a new test factory instance
func NewTestFactory(t *testing.T) *TestFactory {
	return &TestFactory{
		t:     t,
		users: make(map[string]*model.User),
		posts: make(map[string]*model.Post),
	}
}

// CreateTestUser creates a test user with provided details
func (tf *TestFactory) CreateTestUser(username, email, fullName, bio string) *model.User {
	id := uuid.New().String()
	user := &model.User{
		ID:       id,
		Username: username,
		FullName: &fullName,
		Bio:      &bio,
	}

	if fullName == "" {
		user.FullName = nil
	}
	if bio == "" {
		user.Bio = nil
	}

	tf.users[id] = user
	return user
}

// CreateTestPost creates a test post with provided details
func (tf *TestFactory) CreateTestPost(authorID, title, content string) *model.Post {
	id := uuid.New().String()
	post := &model.Post{
		ID:      id,
		Title:   title,
		Content: &content,
		Author: &model.User{
			ID: authorID,
		},
	}

	if content == "" {
		post.Content = nil
	}

	tf.posts[id] = post
	return post
}

// CreateTestComment creates a test comment
func (tf *TestFactory) CreateTestComment(authorID, postID, content string) *model.Comment {
	id := uuid.New().String()
	comment := &model.Comment{
		ID:      id,
		Content: content,
		Author: &model.User{
			ID: authorID,
		},
		Post: &model.Post{
			ID: postID,
		},
	}
	return comment
}

// GetUser retrieves a user by ID from factory cache
func (tf *TestFactory) GetUser(id string) *model.User {
	return tf.users[id]
}

// GetPost retrieves a post by ID from factory cache
func (tf *TestFactory) GetPost(id string) *model.Post {
	return tf.posts[id]
}

// Reset clears all test data
func (tf *TestFactory) Reset() {
	tf.users = make(map[string]*model.User)
	tf.posts = make(map[string]*model.Post)
}

// ValidationHelper provides common validation assertions
type ValidationHelper struct {
	t *testing.T
}

// NewValidationHelper creates validation helper
func NewValidationHelper(t *testing.T) *ValidationHelper {
	return &ValidationHelper{t: t}
}

// AssertUUID validates UUID format
func (vh *ValidationHelper) AssertUUID(value string) {
	_, err := uuid.Parse(value)
	if err != nil {
		vh.t.Errorf("Invalid UUID: %s - %v", value, err)
	}
}

// AssertNotNil asserts value is not nil
func (vh *ValidationHelper) AssertNotNil(value interface{}, name string) {
	if value == nil {
		vh.t.Errorf("%s should not be nil", name)
	}
}

// AssertNil asserts value is nil
func (vh *ValidationHelper) AssertNil(value interface{}, name string) {
	if value != nil {
		vh.t.Errorf("%s should be nil, got %v", name, value)
	}
}

// AssertEqual asserts two values are equal
func (vh *ValidationHelper) AssertEqual(expected, actual interface{}, name string) {
	if expected != actual {
		vh.t.Errorf("%s mismatch: expected %v, got %v", name, expected, actual)
	}
}

// AssertNotEqual asserts two values are not equal
func (vh *ValidationHelper) AssertNotEqual(notExpected, actual interface{}, name string) {
	if notExpected == actual {
		vh.t.Errorf("%s should not equal %v", name, actual)
	}
}

// AssertStringContains checks if string contains substring
func (vh *ValidationHelper) AssertStringContains(str, substring, name string) {
	if len(str) == 0 || len(substring) == 0 {
		return
	}
	// Simple string contains check
	found := false
	for i := 0; i <= len(str)-len(substring); i++ {
		if str[i:i+len(substring)] == substring {
			found = true
			break
		}
	}
	if !found {
		vh.t.Errorf("%s should contain '%s', got '%s'", name, substring, str)
	}
}

// GraphQLTestHelper provides GraphQL-specific testing utilities
type GraphQLTestHelper struct {
	t *testing.T
}

// NewGraphQLTestHelper creates GraphQL test helper
func NewGraphQLTestHelper(t *testing.T) *GraphQLTestHelper {
	return &GraphQLTestHelper{t: t}
}

// AssertNoErrors checks GraphQL response has no errors
func (gth *GraphQLTestHelper) AssertNoErrors(errors []error) {
	if len(errors) > 0 {
		gth.t.Errorf("Expected no GraphQL errors, got %d", len(errors))
		for _, err := range errors {
			gth.t.Logf("  - %v", err)
		}
	}
}

// AssertErrorCount validates error count
func (gth *GraphQLTestHelper) AssertErrorCount(expectedCount int, actualErrors []error) {
	if len(actualErrors) != expectedCount {
		gth.t.Errorf("Expected %d errors, got %d", expectedCount, len(actualErrors))
	}
}

// ContextWithFactory creates context with test factory
func ContextWithFactory(ctx context.Context, factory *TestFactory) context.Context {
	return context.WithValue(ctx, "factory", factory)
}

// DataGenerator provides test data generation utilities
type DataGenerator struct {
	t *testing.T
}

// NewDataGenerator creates data generator
func NewDataGenerator(t *testing.T) *DataGenerator {
	return &DataGenerator{t: t}
}

// GenerateLongString creates a string of specified length
func (dg *DataGenerator) GenerateLongString(length int) string {
	result := ""
	for i := 0; i < length; i++ {
		result += fmt.Sprintf("%d", i%10)
	}
	return result
}

// GenerateUniqueStrings creates N unique strings
func (dg *DataGenerator) GenerateUniqueStrings(count int) []string {
	result := make([]string, count)
	for i := 0; i < count; i++ {
		result[i] = uuid.New().String()
	}
	return result
}
