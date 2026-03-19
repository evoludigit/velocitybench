package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/benchmark/go-graphql-go/internal/db"
	"github.com/benchmark/go-graphql-go/internal/graphql"
	gql "github.com/graphql-go/graphql"
)

func main() {
	// Initialize database
	if err := db.Init(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	// Create GraphQL schema
	schema, err := graphql.NewSchema()
	if err != nil {
		log.Fatalf("Failed to create GraphQL schema: %v", err)
	}

	// Health check handler
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		if err := db.Pool.Ping(r.Context()); err != nil {
			http.Error(w, `{"status": "unhealthy"}`, http.StatusServiceUnavailable)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status": "healthy", "framework": "go-graphql-go"}`))
	})

	// Metrics handler (placeholder)
	http.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("# HELP go_graphql_go_up Framework is running\n# TYPE go_graphql_go_up gauge\ngo_graphql_go_up 1\n"))
	})

	// Ping handler
	http.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"message": "pong"}`))
	})

	// GraphQL handler
	http.HandleFunc("/graphql", func(w http.ResponseWriter, r *http.Request) {
		// Create GraphQL context with dataloaders
		gctx := graphql.NewContext()

		// Parse GraphQL request
		var params struct {
			Query         string                 `json:"query"`
			OperationName *string                `json:"operationName,omitempty"`
			Variables     map[string]interface{} `json:"variables,omitempty"`
		}

		if err := json.NewDecoder(r.Body).Decode(&params); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		// Add context to execution
		ctx := context.WithValue(r.Context(), "graphql_context", gctx)

		// Execute GraphQL query
		var operationName string
		if params.OperationName != nil {
			operationName = *params.OperationName
		}

		result := gql.Do(gql.Params{
			Schema:         schema,
			RequestString:  params.Query,
			RootObject:     map[string]interface{}{},
			VariableValues: params.Variables,
			OperationName:  operationName,
			Context:        ctx,
		})

		// Return result
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8008" // Different port from gin-rest and spring-boot
	}

	log.Printf("🚀 Go GraphQL server ready at http://localhost:%s", port)
	log.Printf("📊 GraphQL endpoint available at http://localhost:%s/graphql", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
