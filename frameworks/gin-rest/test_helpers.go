package main

import (
	"fmt"
	"testing"

	"github.com/benchmark/gin-rest/internal/models"
	"github.com/google/uuid"
)

// TestFactory provides helper methods for creating test data
type TestFactory struct {
	t     *testing.T
	users map[string]*models.User
	posts map[string]*models.Post
}

// NewTestFactory creates a new test factory instance
func NewTestFactory(t *testing.T) *TestFactory {
	return &TestFactory{
		t:     t,
		users: make(map[string]*models.User),
		posts: make(map[string]*models.Post),
	}
}

// CreateTestUser creates a test user
func (tf *TestFactory) CreateTestUser(username, email, fullName, bio string) *models.User {
	id := uuid.New().String()
	user := &models.User{
		ID:       id,
		Username: username,
	}

	if fullName != "" {
		user.FullName = &fullName
	}
	if bio != "" {
		user.Bio = &bio
	}

	tf.users[id] = user
	return user
}

// CreateTestPost creates a test post
func (tf *TestFactory) CreateTestPost(authorID, title, content string) *models.Post {
	id := uuid.New().String()
	post := &models.Post{
		ID:       id,
		Title:    title,
		AuthorID: authorID,
	}

	if content != "" {
		post.Content = &content
	}

	tf.posts[id] = post
	return post
}

// CreateTestComment creates a test comment
func (tf *TestFactory) CreateTestComment(authorID, postID, content string) *models.Comment {
	id := uuid.New().String()
	comment := &models.Comment{
		ID:       id,
		Content:  content,
		AuthorID: authorID,
		PostID:   postID,
	}
	return comment
}

// GetUser retrieves a user by ID
func (tf *TestFactory) GetUser(id string) *models.User {
	return tf.users[id]
}

// GetPost retrieves a post by ID
func (tf *TestFactory) GetPost(id string) *models.Post {
	return tf.posts[id]
}

// GetAllUsers returns all cached users
func (tf *TestFactory) GetAllUsers() map[string]*models.User {
	return tf.users
}

// GetAllPosts returns all cached posts
func (tf *TestFactory) GetAllPosts() map[string]*models.Post {
	return tf.posts
}

// UserCount returns number of users
func (tf *TestFactory) UserCount() int {
	return len(tf.users)
}

// PostCount returns number of posts
func (tf *TestFactory) PostCount() int {
	return len(tf.posts)
}

// Reset clears all test data
func (tf *TestFactory) Reset() {
	tf.users = make(map[string]*models.User)
	tf.posts = make(map[string]*models.Post)
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

// AssertGreater asserts value is greater than expected
func (vh *ValidationHelper) AssertGreater(actual, expected int, name string) {
	if actual <= expected {
		vh.t.Errorf("%s should be greater than %d, got %d", name, expected, actual)
	}
}

// AssertStringContains checks if string contains substring
func (vh *ValidationHelper) AssertStringContains(str, substring, name string) {
	if len(str) == 0 || len(substring) == 0 {
		return
	}
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

// HTTPTestHelper provides HTTP/REST-specific testing utilities
type HTTPTestHelper struct {
	t *testing.T
}

// NewHTTPTestHelper creates HTTP test helper
func NewHTTPTestHelper(t *testing.T) *HTTPTestHelper {
	return &HTTPTestHelper{t: t}
}

// AssertStatusCode validates HTTP status code
func (hth *HTTPTestHelper) AssertStatusCode(expected, actual int) {
	if expected != actual {
		hth.t.Errorf("Expected status code %d, got %d", expected, actual)
	}
}

// AssertContentType validates response content type
func (hth *HTTPTestHelper) AssertContentType(expected, actual string) {
	if expected != actual {
		hth.t.Errorf("Expected content type %s, got %s", expected, actual)
	}
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

// GenerateUsers creates N test users
func (dg *DataGenerator) GenerateUsers(factory *TestFactory, count int) []*models.User {
	result := make([]*models.User, count)
	for i := 0; i < count; i++ {
		result[i] = factory.CreateTestUser(
			"user"+fmt.Sprintf("%d", i),
			"user"+fmt.Sprintf("%d", i)+"@example.com",
			"User "+fmt.Sprintf("%d", i),
			"",
		)
	}
	return result
}

// Helper function to create string pointer
func strPtr(s string) *string {
	return &s
}

// Helper function to get string value or empty
func strValue(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}
