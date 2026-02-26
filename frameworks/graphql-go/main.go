package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/benchmark/graphql-go/internal/dataloader"
	"github.com/benchmark/graphql-go/internal/db"
	"github.com/benchmark/graphql-go/internal/schema"
	"github.com/graphql-go/handler"
)

const defaultPort = "4000"

func main() {
	// Initialize database
	if err := db.Init(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	port := os.Getenv("PORT")
	if port == "" {
		port = defaultPort
	}

	// GraphQL handler with DataLoader middleware
	h := handler.New(&handler.Config{
		Schema:   &schema.Schema,
		Pretty:   false,
		GraphiQL: false,
	})

	// Health check endpoint
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		// Check database connectivity
		if err := db.Pool.Ping(r.Context()); err != nil {
			w.WriteHeader(http.StatusServiceUnavailable)
			json.NewEncoder(w).Encode(map[string]string{
				"status": "unhealthy",
				"error":  err.Error(),
			})
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]string{
			"status":    "healthy",
			"framework": "graphql-go",
		})
	})

	// Metrics endpoint (placeholder for Prometheus)
	http.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		fmt.Fprintf(w, "# HELP graphql_go_requests_total Total number of GraphQL requests\n")
		fmt.Fprintf(w, "# TYPE graphql_go_requests_total counter\n")
		fmt.Fprintf(w, "graphql_go_requests_total 0\n")
	})

	// GraphQL endpoint with DataLoader context
	http.HandleFunc("/graphql", func(w http.ResponseWriter, r *http.Request) {
		// Create fresh dataloaders for each request
		loaders := dataloader.NewLoaders()
		ctx := dataloader.WithLoaders(r.Context(), loaders)
		r = r.WithContext(ctx)
		h.ServeHTTP(w, r)
	})

	log.Printf("graphql-go server starting on http://localhost:%s", port)
	log.Printf("GraphQL endpoint: http://localhost:%s/graphql", port)
	log.Printf("Health check: http://localhost:%s/health", port)

	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
