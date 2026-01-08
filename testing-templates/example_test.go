/*
Package main provides example Go tests for VelocityBench.

This template shows the standard pattern for testing:
1. UNIT TESTS: Test functions without external dependencies
2. INTEGRATION TESTS: Test with database
*/
package main

import (
	"database/sql"
	"fmt"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	_ "github.com/lib/pq"
)

// ============================================================================
// Test Database Helpers
// ============================================================================

type TestDB struct {
	db *sql.DB
}

func setupTestDB(t *testing.T) *TestDB {
	connStr := "postgres://velocitybench:password@localhost:5432/velocitybench_test?sslmode=disable"
	db, err := sql.Open("postgres", connStr)
	require.NoError(t, err)

	err = db.Ping()
	require.NoError(t, err)

	return &TestDB{db: db}
}

func (tdb *TestDB) Close() error {
	return tdb.db.Close()
}

func (tdb *TestDB) Query(query string, args ...interface{}) (*sql.Rows, error) {
	return tdb.db.Query(query, args...)
}

func (tdb *TestDB) QueryRow(query string, args ...interface{}) *sql.Row {
	return tdb.db.QueryRow(query, args...)
}

func (tdb *TestDB) Exec(query string, args ...interface{}) (sql.Result, error) {
	return tdb.db.Exec(query, args...)
}

// ============================================================================
// Test Data Models
// ============================================================================

type User struct {
	ID    int
	Name  string
	Email string
}

type Company struct {
	ID   int
	Name string
}

type Product struct {
	ID        int
	Name      string
	Price     float64
	CompanyID int
}

// ============================================================================
// Test Factory
// ============================================================================

type TestFactory struct {
	db *TestDB
	t  *testing.T
}

func (f *TestFactory) CreateUser(name, email string) *User {
	row := f.db.QueryRow(
		"INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id, name, email",
		name, email,
	)

	var user User
	err := row.Scan(&user.ID, &user.Name, &user.Email)
	require.NoError(f.t, err)

	return &user
}

func (f *TestFactory) CreateCompany(name string) *Company {
	row := f.db.QueryRow(
		"INSERT INTO companies (name) VALUES ($1) RETURNING id, name",
		name,
	)

	var company Company
	err := row.Scan(&company.ID, &company.Name)
	require.NoError(f.t, err)

	return &company
}

func (f *TestFactory) CreateProduct(name string, price float64, companyID int) *Product {
	row := f.db.QueryRow(
		"INSERT INTO products (name, price, company_id) VALUES ($1, $2, $3) "+
			"RETURNING id, name, price, company_id",
		name, price, companyID,
	)

	var product Product
	err := row.Scan(&product.ID, &product.Name, &product.Price, &product.CompanyID)
	require.NoError(f.t, err)

	return &product
}

// ============================================================================
// Unit Tests (no database dependency)
// ============================================================================

func TestEmailValidation(t *testing.T) {
	isValidEmail := func(email string) bool {
		// Simple email validation
		return len(email) > 0 && strings.Contains(email, "@")
	}

	assert.True(t, isValidEmail("user@example.com"))
	assert.False(t, isValidEmail("invalid@"))
	assert.False(t, isValidEmail("no-at-sign.com"))
}

func TestNameNormalization(t *testing.T) {
	normalizeName := func(name string) string {
		// Normalize name to lowercase
		return strings.ToLower(strings.TrimSpace(name))
	}

	assert.Equal(t, "john doe", normalizeName("JOHN DOE"))
	assert.Equal(t, "alice", normalizeName("  alice  "))
}

func TestPriceFormatting(t *testing.T) {
	formatPrice := func(price float64) string {
		return fmt.Sprintf("$%.2f", price)
	}

	assert.Equal(t, "$19.99", formatPrice(19.99))
	assert.Equal(t, "$100.00", formatPrice(100.0))
}

// ============================================================================
// Integration Tests (with database)
// ============================================================================

func TestCreateUser(t *testing.T) {
	db := setupTestDB(t)
	defer db.Close()

	// Clean up
	db.Exec("DELETE FROM users")

	factory := &TestFactory{db: db, t: t}

	// Arrange & Act
	user := factory.CreateUser("Alice", "alice@example.com")

	// Assert
	assert.NotNil(t, user)
	assert.Equal(t, "Alice", user.Name)
	assert.Equal(t, "alice@example.com", user.Email)
	assert.Greater(t, user.ID, 0)
}

func TestGetUserByID(t *testing.T) {
	db := setupTestDB(t)
	defer db.Close()

	// Clean up
	db.Exec("DELETE FROM users")

	factory := &TestFactory{db: db, t: t}

	// Arrange
	created := factory.CreateUser("Bob", "bob@example.com")
	userID := created.ID

	// Act
	row := db.QueryRow("SELECT id, name, email FROM users WHERE id = $1", userID)
	var user User
	err := row.Scan(&user.ID, &user.Name, &user.Email)

	// Assert
	require.NoError(t, err)
	assert.Equal(t, userID, user.ID)
	assert.Equal(t, "Bob", user.Name)
	assert.Equal(t, "bob@example.com", user.Email)
}

func TestListUsers(t *testing.T) {
	db := setupTestDB(t)
	defer db.Close()

	// Clean up
	db.Exec("DELETE FROM users")

	factory := &TestFactory{db: db, t: t}

	// Arrange
	factory.CreateUser("Alice", "alice@example.com")
	factory.CreateUser("Bob", "bob@example.com")
	factory.CreateUser("Charlie", "charlie@example.com")

	// Act
	rows, err := db.Query("SELECT id, name, email FROM users ORDER BY name")
	require.NoError(t, err)
	defer rows.Close()

	var users []User
	for rows.Next() {
		var user User
		err := rows.Scan(&user.ID, &user.Name, &user.Email)
		require.NoError(t, err)
		users = append(users, user)
	}

	// Assert
	assert.Equal(t, 3, len(users))
	assert.Equal(t, "Alice", users[0].Name)
	assert.Equal(t, "Bob", users[1].Name)
	assert.Equal(t, "Charlie", users[2].Name)
}

func TestUpdateUser(t *testing.T) {
	db := setupTestDB(t)
	defer db.Close()

	// Clean up
	db.Exec("DELETE FROM users")

	factory := &TestFactory{db: db, t: t}

	// Arrange
	created := factory.CreateUser("Alice", "alice@example.com")
	userID := created.ID

	// Act
	_, err := db.Exec(
		"UPDATE users SET email = $1 WHERE id = $2",
		"alice.new@example.com", userID,
	)
	require.NoError(t, err)

	// Assert
	row := db.QueryRow("SELECT email FROM users WHERE id = $1", userID)
	var email string
	err = row.Scan(&email)
	require.NoError(t, err)
	assert.Equal(t, "alice.new@example.com", email)
}

func TestDeleteUser(t *testing.T) {
	db := setupTestDB(t)
	defer db.Close()

	// Clean up
	db.Exec("DELETE FROM users")

	factory := &TestFactory{db: db, t: t}

	// Arrange
	created := factory.CreateUser("Alice", "alice@example.com")
	userID := created.ID

	// Act
	_, err := db.Exec("DELETE FROM users WHERE id = $1", userID)
	require.NoError(t, err)

	// Assert
	row := db.QueryRow("SELECT id FROM users WHERE id = $1", userID)
	var id int
	err = row.Scan(&id)
	assert.Error(t, err)
	assert.Equal(t, sql.ErrNoRows, err)
}

// ============================================================================
// Product Tests
// ============================================================================

func TestCreateProduct(t *testing.T) {
	db := setupTestDB(t)
	defer db.Close()

	// Clean up
	db.Exec("DELETE FROM products")
	db.Exec("DELETE FROM companies")

	factory := &TestFactory{db: db, t: t}

	// Arrange
	company := factory.CreateCompany("ACME Corp")

	// Act
	product := factory.CreateProduct("Widget", 19.99, company.ID)

	// Assert
	assert.NotNil(t, product)
	assert.Equal(t, "Widget", product.Name)
	assert.Equal(t, 19.99, product.Price)
	assert.Equal(t, company.ID, product.CompanyID)
}
