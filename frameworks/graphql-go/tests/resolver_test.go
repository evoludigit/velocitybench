package tests

import (
	"sync"
	"testing"
	"time"

	"github.com/google/uuid"
)

// TestUser represents a user in tests
type TestUser struct {
	ID        string
	PkUser    int
	Username  string
	FullName  string
	Bio       *string
	CreatedAt time.Time
	UpdatedAt time.Time
}

// TestPost represents a post in tests
type TestPost struct {
	ID        string
	PkPost    int
	FkAuthor  int
	Title     string
	Content   string
	CreatedAt time.Time
	UpdatedAt time.Time
	Author    *TestUser
}

// TestComment represents a comment in tests
type TestComment struct {
	ID        string
	PkComment int
	FkPost    int
	FkAuthor  int
	Content   string
	CreatedAt time.Time
	Author    *TestUser
	Post      *TestPost
}

// TestFactory creates test data
type TestFactory struct {
	users          map[string]*TestUser
	posts          map[string]*TestPost
	comments       map[string]*TestComment
	userCounter    int
	postCounter    int
	commentCounter int
	mu             sync.RWMutex
}

// NewTestFactory creates a new test factory
func NewTestFactory() *TestFactory {
	return &TestFactory{
		users:    make(map[string]*TestUser),
		posts:    make(map[string]*TestPost),
		comments: make(map[string]*TestComment),
	}
}

// CreateUser creates a test user
func (f *TestFactory) CreateUser(username, email, fullName string, bio *string) *TestUser {
	f.mu.Lock()
	defer f.mu.Unlock()

	f.userCounter++
	user := &TestUser{
		ID:        uuid.New().String(),
		PkUser:    f.userCounter,
		Username:  username,
		FullName:  fullName,
		Bio:       bio,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	f.users[user.ID] = user
	return user
}

// CreatePost creates a test post
func (f *TestFactory) CreatePost(authorID, title, content string) *TestPost {
	f.mu.Lock()
	defer f.mu.Unlock()

	author := f.users[authorID]
	if author == nil {
		panic("author not found: " + authorID)
	}

	f.postCounter++
	post := &TestPost{
		ID:        uuid.New().String(),
		PkPost:    f.postCounter,
		FkAuthor:  author.PkUser,
		Title:     title,
		Content:   content,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Author:    author,
	}
	f.posts[post.ID] = post
	return post
}

// CreateComment creates a test comment
func (f *TestFactory) CreateComment(authorID, postID, content string) *TestComment {
	f.mu.Lock()
	defer f.mu.Unlock()

	author := f.users[authorID]
	post := f.posts[postID]
	if author == nil || post == nil {
		panic("author or post not found")
	}

	f.commentCounter++
	comment := &TestComment{
		ID:        uuid.New().String(),
		PkComment: f.commentCounter,
		FkPost:    post.PkPost,
		FkAuthor:  author.PkUser,
		Content:   content,
		CreatedAt: time.Now(),
		Author:    author,
		Post:      post,
	}
	f.comments[comment.ID] = comment
	return comment
}

// GetUser returns a user by ID
func (f *TestFactory) GetUser(id string) *TestUser {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.users[id]
}

// GetPost returns a post by ID
func (f *TestFactory) GetPost(id string) *TestPost {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.posts[id]
}

// GetComment returns a comment by ID
func (f *TestFactory) GetComment(id string) *TestComment {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.comments[id]
}

// GetAllUsers returns all users
func (f *TestFactory) GetAllUsers() []*TestUser {
	f.mu.RLock()
	defer f.mu.RUnlock()
	users := make([]*TestUser, 0, len(f.users))
	for _, u := range f.users {
		users = append(users, u)
	}
	return users
}

// GetPostsByAuthor returns posts by author pk
func (f *TestFactory) GetPostsByAuthor(authorPk int) []*TestPost {
	f.mu.RLock()
	defer f.mu.RUnlock()
	posts := make([]*TestPost, 0)
	for _, p := range f.posts {
		if p.FkAuthor == authorPk {
			posts = append(posts, p)
		}
	}
	return posts
}

// GetCommentsByPost returns comments by post pk
func (f *TestFactory) GetCommentsByPost(postPk int) []*TestComment {
	f.mu.RLock()
	defer f.mu.RUnlock()
	comments := make([]*TestComment, 0)
	for _, c := range f.comments {
		if c.FkPost == postPk {
			comments = append(comments, c)
		}
	}
	return comments
}

// Reset clears all data
func (f *TestFactory) Reset() {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.users = make(map[string]*TestUser)
	f.posts = make(map[string]*TestPost)
	f.comments = make(map[string]*TestComment)
	f.userCounter = 0
	f.postCounter = 0
	f.commentCounter = 0
}

// ============================================================================
// User Query Tests
// ============================================================================

func TestQueryUserByUUID(t *testing.T) {
	factory := NewTestFactory()
	bio := "Hello!"
	user := factory.CreateUser("alice", "alice@example.com", "Alice Smith", &bio)

	result := factory.GetUser(user.ID)

	if result == nil {
		t.Fatal("expected user, got nil")
	}
	if result.ID != user.ID {
		t.Errorf("expected ID %s, got %s", user.ID, result.ID)
	}
	if result.Username != "alice" {
		t.Errorf("expected username alice, got %s", result.Username)
	}
	if result.FullName != "Alice Smith" {
		t.Errorf("expected full_name Alice Smith, got %s", result.FullName)
	}
}

func TestQueryUsersReturnsList(t *testing.T) {
	factory := NewTestFactory()
	factory.CreateUser("alice", "alice@example.com", "Alice", nil)
	factory.CreateUser("bob", "bob@example.com", "Bob", nil)
	factory.CreateUser("charlie", "charlie@example.com", "Charlie", nil)

	users := factory.GetAllUsers()

	if len(users) != 3 {
		t.Errorf("expected 3 users, got %d", len(users))
	}
}

func TestQueryUserNotFound(t *testing.T) {
	factory := NewTestFactory()

	result := factory.GetUser("non-existent-id")

	if result != nil {
		t.Error("expected nil for non-existent user")
	}
}

// ============================================================================
// Post Query Tests
// ============================================================================

func TestQueryPostByID(t *testing.T) {
	factory := NewTestFactory()
	user := factory.CreateUser("author", "author@example.com", "Author", nil)
	post := factory.CreatePost(user.ID, "Test Post", "Test content")

	result := factory.GetPost(post.ID)

	if result == nil {
		t.Fatal("expected post, got nil")
	}
	if result.Title != "Test Post" {
		t.Errorf("expected title 'Test Post', got '%s'", result.Title)
	}
}

func TestQueryPostsByAuthor(t *testing.T) {
	factory := NewTestFactory()
	user := factory.CreateUser("author", "author@example.com", "Author", nil)
	factory.CreatePost(user.ID, "Post 1", "Content 1")
	factory.CreatePost(user.ID, "Post 2", "Content 2")

	posts := factory.GetPostsByAuthor(user.PkUser)

	if len(posts) != 2 {
		t.Errorf("expected 2 posts, got %d", len(posts))
	}
}

// ============================================================================
// Comment Query Tests
// ============================================================================

func TestQueryCommentByID(t *testing.T) {
	factory := NewTestFactory()
	author := factory.CreateUser("author", "author@example.com", "Author", nil)
	post := factory.CreatePost(author.ID, "Test Post", "Content")
	commenter := factory.CreateUser("commenter", "commenter@example.com", "Commenter", nil)
	comment := factory.CreateComment(commenter.ID, post.ID, "Great post!")

	result := factory.GetComment(comment.ID)

	if result == nil {
		t.Fatal("expected comment, got nil")
	}
	if result.Content != "Great post!" {
		t.Errorf("expected content 'Great post!', got '%s'", result.Content)
	}
}

func TestQueryCommentsByPost(t *testing.T) {
	factory := NewTestFactory()
	author := factory.CreateUser("author", "author@example.com", "Author", nil)
	post := factory.CreatePost(author.ID, "Test Post", "Content")
	commenter := factory.CreateUser("commenter", "commenter@example.com", "Commenter", nil)
	factory.CreateComment(commenter.ID, post.ID, "Comment 1")
	factory.CreateComment(commenter.ID, post.ID, "Comment 2")

	comments := factory.GetCommentsByPost(post.PkPost)

	if len(comments) != 2 {
		t.Errorf("expected 2 comments, got %d", len(comments))
	}
}

// ============================================================================
// Relationship Tests
// ============================================================================

func TestUserPostsRelationship(t *testing.T) {
	factory := NewTestFactory()
	user := factory.CreateUser("author", "author@example.com", "Author", nil)
	post1 := factory.CreatePost(user.ID, "Post 1", "Content 1")
	post2 := factory.CreatePost(user.ID, "Post 2", "Content 2")

	posts := factory.GetPostsByAuthor(user.PkUser)

	if len(posts) != 2 {
		t.Errorf("expected 2 posts, got %d", len(posts))
	}

	postIDs := make(map[string]bool)
	for _, p := range posts {
		postIDs[p.ID] = true
	}
	if !postIDs[post1.ID] || !postIDs[post2.ID] {
		t.Error("expected both posts to be present")
	}
}

func TestPostAuthorRelationship(t *testing.T) {
	factory := NewTestFactory()
	author := factory.CreateUser("author", "author@example.com", "Author", nil)
	post := factory.CreatePost(author.ID, "Test Post", "Content")

	if post.Author == nil {
		t.Fatal("expected author to be set")
	}
	if post.Author.PkUser != author.PkUser {
		t.Errorf("expected author pk %d, got %d", author.PkUser, post.Author.PkUser)
	}
}

func TestCommentAuthorRelationship(t *testing.T) {
	factory := NewTestFactory()
	author := factory.CreateUser("author", "author@example.com", "Author", nil)
	post := factory.CreatePost(author.ID, "Test Post", "Content")
	commenter := factory.CreateUser("commenter", "commenter@example.com", "Commenter", nil)
	comment := factory.CreateComment(commenter.ID, post.ID, "Great!")

	if comment.Author == nil {
		t.Fatal("expected comment author to be set")
	}
	if comment.Author.PkUser != commenter.PkUser {
		t.Errorf("expected author pk %d, got %d", commenter.PkUser, comment.Author.PkUser)
	}
}

// ============================================================================
// Edge Case Tests
// ============================================================================

func TestNullBio(t *testing.T) {
	factory := NewTestFactory()
	user := factory.CreateUser("user", "user@example.com", "User", nil)

	if user.Bio != nil {
		t.Error("expected nil bio")
	}
}

func TestEmptyPostsList(t *testing.T) {
	factory := NewTestFactory()
	user := factory.CreateUser("newuser", "new@example.com", "New User", nil)

	posts := factory.GetPostsByAuthor(user.PkUser)

	if len(posts) != 0 {
		t.Errorf("expected 0 posts, got %d", len(posts))
	}
}

func TestSpecialCharactersInContent(t *testing.T) {
	factory := NewTestFactory()
	user := factory.CreateUser("author", "author@example.com", "Author", nil)
	specialContent := "Test with 'quotes' and \"double quotes\" and <html>"
	post := factory.CreatePost(user.ID, "Special", specialContent)

	if post.Content != specialContent {
		t.Errorf("expected special content to be preserved")
	}
}

func TestUnicodeContent(t *testing.T) {
	factory := NewTestFactory()
	user := factory.CreateUser("author", "author@example.com", "Author", nil)
	unicodeContent := "Test with émojis 🎉 and ñ and 中文"
	post := factory.CreatePost(user.ID, "Unicode", unicodeContent)

	if post.Content != unicodeContent {
		t.Errorf("expected unicode content to be preserved")
	}
}

// ============================================================================
// Performance Tests
// ============================================================================

func TestCreateManyPosts(t *testing.T) {
	factory := NewTestFactory()
	user := factory.CreateUser("author", "author@example.com", "Author", nil)

	for i := 0; i < 50; i++ {
		factory.CreatePost(user.ID, "Post", "Content")
	}

	posts := factory.GetPostsByAuthor(user.PkUser)

	if len(posts) != 50 {
		t.Errorf("expected 50 posts, got %d", len(posts))
	}
}

func TestReset(t *testing.T) {
	factory := NewTestFactory()
	factory.CreateUser("user1", "user1@example.com", "User 1", nil)
	factory.CreateUser("user2", "user2@example.com", "User 2", nil)

	factory.Reset()

	if len(factory.GetAllUsers()) != 0 {
		t.Error("expected 0 users after reset")
	}
}

// ============================================================================
// Validation Tests
// ============================================================================

func TestValidUUID(t *testing.T) {
	factory := NewTestFactory()
	user := factory.CreateUser("user", "user@example.com", "User", nil)

	_, err := uuid.Parse(user.ID)
	if err != nil {
		t.Errorf("expected valid UUID, got error: %v", err)
	}
}
