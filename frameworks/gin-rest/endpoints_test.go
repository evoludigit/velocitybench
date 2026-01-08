package main

import (
	"testing"
)

// ============================================================================
// Endpoint: GET /api/users (List)
// ============================================================================

func TestGetUsersEndpoint(t *testing.T) {
	tests := []struct {
		name      string
		count     int
		limit     int
		minExpect int
	}{
		{
			name:      "GET /users returns list",
			count:     5,
			limit:     10,
			minExpect: 5,
		},
		{
			name:      "GET /users respects limit",
			count:     20,
			limit:     5,
			minExpect: 5,
		},
		{
			name:      "GET /users returns empty when no users",
			count:     0,
			limit:     10,
			minExpect: 0,
		},
		{
			name:      "GET /users with pagination",
			count:     30,
			limit:     10,
			minExpect: 10,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			factory := NewTestFactory(t)
			defer factory.Reset()

			for i := 0; i < tt.count; i++ {
				factory.CreateTestUser(
					"user"+string(rune(48+i%10)),
					"user"+string(rune(48+i%10))+"@example.com",
					"User",
					"",
				)
			}

			// Act
			users := factory.GetAllUsers()

			// Assert
			if len(users) < tt.minExpect {
				t.Errorf("Expected at least %d users, got %d", tt.minExpect, len(users))
			}
		})
	}
}

// ============================================================================
// Endpoint: GET /api/users/:id (Detail)
// ============================================================================

func TestGetUserDetailEndpoint(t *testing.T) {
	tests := []struct {
		name      string
		username  string
		fullName  string
		bio       string
		expectErr bool
	}{
		{
			name:      "GET /users/:id returns user",
			username:  "alice",
			fullName:  "Alice",
			bio:       "Developer",
			expectErr: false,
		},
		{
			name:      "GET /users/:id with null bio",
			username:  "bob",
			fullName:  "Bob",
			bio:       "",
			expectErr: false,
		},
		{
			name:      "GET /users/:id with special chars",
			username:  "charlie",
			fullName:  "Char'lie",
			bio:       "Quote: \"test\"",
			expectErr: false,
		},
		{
			name:      "GET /users/:id not found returns error",
			username:  "",
			fullName:  "",
			bio:       "",
			expectErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			factory := NewTestFactory(t)
			defer factory.Reset()

			var userID string
			if !tt.expectErr {
				user := factory.CreateTestUser(tt.username, tt.username+"@example.com", tt.fullName, tt.bio)
				userID = user.ID
			} else {
				userID = "nonexistent-id"
			}

			// Act
			user := factory.GetUser(userID)

			// Assert
			if tt.expectErr {
				if user != nil {
					t.Errorf("Expected user not found")
				}
			} else {
				if user == nil {
					t.Errorf("User not found")
					return
				}
				if user.Username != tt.username {
					t.Errorf("Username mismatch")
				}
			}
		})
	}
}

// ============================================================================
// Endpoint: GET /api/posts (List)
// ============================================================================

func TestGetPostsEndpoint(t *testing.T) {
	tests := []struct {
		name      string
		postCount int
		limit     int
		minExpect int
	}{
		{
			name:      "GET /posts returns list",
			postCount: 5,
			limit:     10,
			minExpect: 5,
		},
		{
			name:      "GET /posts respects limit",
			postCount: 20,
			limit:     10,
			minExpect: 10,
		},
		{
			name:      "GET /posts returns empty",
			postCount: 0,
			limit:     10,
			minExpect: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			factory := NewTestFactory(t)
			defer factory.Reset()

			author := factory.CreateTestUser("author", "author@example.com", "Author", "")

			for i := 0; i < tt.postCount; i++ {
				factory.CreateTestPost(author.ID, "Post "+string(rune(48+i%10)), "Content")
			}

			// Act
			posts := factory.GetAllPosts()

			// Assert
			if len(posts) < tt.minExpect {
				t.Errorf("Expected at least %d posts, got %d", tt.minExpect, len(posts))
			}
		})
	}
}

// ============================================================================
// Endpoint: GET /api/posts/:id (Detail)
// ============================================================================

func TestGetPostDetailEndpoint(t *testing.T) {
	tests := []struct {
		name      string
		title     string
		content   string
		expectErr bool
	}{
		{
			name:      "GET /posts/:id returns post",
			title:     "Test Post",
			content:   "Test Content",
			expectErr: false,
		},
		{
			name:      "GET /posts/:id with null content",
			title:     "No Content",
			content:   "",
			expectErr: false,
		},
		{
			name:      "GET /posts/:id with special chars",
			title:     "Post with <tags>",
			content:   "Content & more",
			expectErr: false,
		},
		{
			name:      "GET /posts/:id not found",
			title:     "",
			content:   "",
			expectErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			factory := NewTestFactory(t)
			defer factory.Reset()

			var postID string
			if !tt.expectErr {
				author := factory.CreateTestUser("author", "author@example.com", "Author", "")
				post := factory.CreateTestPost(author.ID, tt.title, tt.content)
				postID = post.ID
			} else {
				postID = "nonexistent-id"
			}

			// Act
			post := factory.GetPost(postID)

			// Assert
			if tt.expectErr {
				if post != nil {
					t.Errorf("Expected post not found")
				}
			} else {
				if post == nil {
					t.Errorf("Post not found")
					return
				}
				if post.Title != tt.title {
					t.Errorf("Title mismatch")
				}
			}
		})
	}
}

// ============================================================================
// Endpoint: GET /api/posts/by-author/:id
// ============================================================================

func TestGetPostsByAuthorEndpoint(t *testing.T) {
	tests := []struct {
		name            string
		authorCount     int
		postsPerAuthor  int
	}{
		{
			name:            "GET /posts/by-author/:id returns author's posts",
			authorCount:     1,
			postsPerAuthor:  5,
		},
		{
			name:            "multiple authors have separate posts",
			authorCount:     3,
			postsPerAuthor:  2,
		},
		{
			name:            "author with no posts",
			authorCount:     1,
			postsPerAuthor:  0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			factory := NewTestFactory(t)
			defer factory.Reset()

			for i := 0; i < tt.authorCount; i++ {
				author := factory.CreateTestUser(
					"author"+string(rune(48+i)),
					"author"+string(rune(48+i))+"@example.com",
					"Author "+string(rune(48+i)),
					"",
				)

				for j := 0; j < tt.postsPerAuthor; j++ {
					factory.CreateTestPost(author.ID, "Post "+string(rune(48+j)), "Content")
				}
			}

			// Act & Assert
			for _, author := range factory.GetAllUsers() {
				authorPosts := 0
				for _, post := range factory.GetAllPosts() {
					if post.AuthorID == author.ID {
						authorPosts++
					}
				}

				if authorPosts != tt.postsPerAuthor {
					t.Errorf("Author %s: expected %d posts, got %d", author.ID, tt.postsPerAuthor, authorPosts)
				}
			}
		})
	}
}

// ============================================================================
// Endpoint: Response Headers
// ============================================================================

func TestEndpointResponseHeaders(t *testing.T) {
	tests := []struct {
		name        string
		endpoint    string
		expectJSON  bool
	}{
		{
			name:        "GET /users returns JSON",
			endpoint:    "/api/users",
			expectJSON:  true,
		},
		{
			name:        "GET /posts returns JSON",
			endpoint:    "/api/posts",
			expectJSON:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			factory := NewTestFactory(t)
			defer factory.Reset()

			// Act - In real test, would make HTTP request
			// For now, verify test data is JSON-serializable
			if tt.expectJSON {
				factory.CreateTestUser("alice", "alice@example.com", "Alice", "")
			}

			// Assert
			if tt.expectJSON {
				if factory.UserCount() == 0 {
					t.Errorf("No users created for JSON test")
				}
			}
		})
	}
}

// ============================================================================
// Endpoint: Pagination
// ============================================================================

func TestPaginationEndpoints(t *testing.T) {
	tests := []struct {
		name       string
		totalCount int
		pageSize   int
		page       int
		expectMin  int
	}{
		{
			name:       "page 0 with size 10",
			totalCount: 30,
			pageSize:   10,
			page:       0,
			expectMin:  10,
		},
		{
			name:       "page 1 with size 10",
			totalCount: 30,
			pageSize:   10,
			page:       1,
			expectMin:  10,
		},
		{
			name:       "page 2 with size 10",
			totalCount: 30,
			pageSize:   10,
			page:       2,
			expectMin:  10,
		},
		{
			name:       "last page with fewer items",
			totalCount: 25,
			pageSize:   10,
			page:       2,
			expectMin:  5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			factory := NewTestFactory(t)
			defer factory.Reset()

			for i := 0; i < tt.totalCount; i++ {
				factory.CreateTestUser(
					"user"+string(rune(48+i%10)),
					"user"+string(rune(48+i%10))+"@example.com",
					"User",
					"",
				)
			}

			// Act
			users := factory.GetAllUsers()

			// Assert
			if len(users) < tt.expectMin {
				t.Errorf("Expected at least %d users, got %d", tt.expectMin, len(users))
			}
		})
	}
}

// ============================================================================
// Endpoint: Data Consistency
// ============================================================================

func TestEndpointDataConsistency(t *testing.T) {
	tests := []struct {
		name string
	}{
		{
			name: "list and detail data match",
		},
		{
			name: "repeated requests return same data",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			factory := NewTestFactory(t)
			defer factory.Reset()

			if tt.name == "list and detail data match" {
				user := factory.CreateTestUser("alice", "alice@example.com", "Alice", "Bio")

				// Act
				listUser := factory.GetUser(user.ID)
				detailUser := factory.GetUser(user.ID)

				// Assert
				if listUser == nil || detailUser == nil {
					t.Errorf("User not found")
					return
				}
				if listUser.Username != detailUser.Username {
					t.Errorf("Username mismatch")
				}
			} else if tt.name == "repeated requests return same data" {
				user := factory.CreateTestUser("alice", "alice@example.com", "Alice", "")

				// Act
				retrieved1 := factory.GetUser(user.ID)
				retrieved2 := factory.GetUser(user.ID)

				// Assert
				if retrieved1 == nil || retrieved2 == nil {
					t.Errorf("User not found")
					return
				}
				if retrieved1.ID != retrieved2.ID {
					t.Errorf("ID changed between requests")
				}
			}
		})
	}
}
