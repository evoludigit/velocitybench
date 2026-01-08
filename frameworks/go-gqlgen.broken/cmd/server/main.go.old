package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"

	"github.com/benchmark/go-gqlgen/graph"
	"github.com/benchmark/go-gqlgen/internal/db"
	"github.com/graphql-go/graphql"
)

func main() {
	// Initialize database
	if err := db.Init(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	// Create GraphQL schema
	schema, err := graph.NewSchema()
	if err != nil {
		log.Fatalf("Failed to create GraphQL schema: %v", err)
	}

	// GraphQL handler with dataloader middleware
	http.Handle("/query", graph.DataloaderMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
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

		// Execute GraphQL query
		var operationName string
		if params.OperationName != nil {
			operationName = *params.OperationName
		}

		result := graphql.Do(graphql.Params{
			Schema:         schema,
			RequestString:  params.Query,
			RootObject:     map[string]interface{}{},
			VariableValues: params.Variables,
			OperationName:  operationName,
			Context:        r.Context(),
		})

		// Return result
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	})))

	// Health check
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		if err := db.Pool.Ping(r.Context()); err != nil {
			http.Error(w, "Database unavailable", http.StatusServiceUnavailable)
			return
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ok"}`))
	})

	// Ping handler
	http.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"message": "pong"}`))
	})

	// Root handler
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(`<h1>GraphQL Server</h1><p><a href="/playground">GraphQL Playground</a></p><p><a href="/query">GraphQL Endpoint</a></p>`))
	})

	// GraphQL playground
	http.HandleFunc("/playground", func(w http.ResponseWriter, r *http.Request) {
		html := `<!DOCTYPE html>
		<html>
		<head>
			<title>GraphQL Playground</title>
			<style>
				body { font-family: monospace; padding: 20px; }
				#editor { width: 100%; height: 300px; font-family: monospace; border: 1px solid #ccc; }
				button { padding: 10px 20px; margin: 10px 0; }
			</style>
		</head>
		<body>
			<h1>GraphQL API</h1>
			<textarea id="editor">{ ping }</textarea><br>
			<button onclick="sendQuery()">Run Query</button>
			<pre id="result"></pre>
			<script>
				function sendQuery() {
					fetch('/query', {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({ query: document.getElementById('editor').value })
					}).then(r => r.json()).then(d => {
						document.getElementById('result').textContent = JSON.stringify(d, null, 2);
					});
				}
			</script>
		</body>
		</html>`
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(html))
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "4009"
	}

	log.Printf("🚀 gqlgen server ready at http://localhost:%s", port)
	log.Printf("📊 GraphQL playground: http://localhost:%s", port)
	log.Printf("🔗 GraphQL endpoint: http://localhost:%s/query", port)

	log.Fatal(http.ListenAndServe(":"+port, nil))
}
