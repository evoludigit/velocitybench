package main

import (
	"log"
	"net/http"
	"os"

	"github.com/99designs/gqlgen/graphql/handler"
	"github.com/99designs/gqlgen/graphql/playground"
	"github.com/benchmark/go-gqlgen/graph"
	"github.com/benchmark/go-gqlgen/internal/db"
)

func main() {
	// Initialize database
	if err := db.Init(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	// Create gqlgen server
	srv := handler.NewDefaultServer(graph.NewExecutableSchema(graph.Config{
		Resolvers: &graph.Resolver{},
	}))

	// Wrap with dataloader middleware
	http.Handle("/query", graph.DataloaderMiddleware(srv))
	http.Handle("/", playground.Handler("GraphQL Playground", "/query"))

	// Health check
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		if err := db.Pool.Ping(r.Context()); err != nil {
			http.Error(w, "Database unavailable", http.StatusServiceUnavailable)
			return
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ok"}`))
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "4009"
	}

	log.Printf("🚀 gqlgen server ready at http://localhost:%s", port)
	log.Printf("📊 GraphQL playground: http://localhost:%s/", port)
	log.Printf("🔗 GraphQL endpoint: http://localhost:%s/query", port)

	log.Fatal(http.ListenAndServe(":"+port, nil))
}
