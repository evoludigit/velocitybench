package healthcheck

import (
	"encoding/json"
	"net/http"
)

// HTTPHandler returns an http.HandlerFunc that handles health check requests.
//
// Usage:
//   healthManager := healthcheck.New(healthcheck.Config{ ... })
//   http.HandleFunc("/health", healthcheck.HTTPHandler(healthManager, "readiness"))
//   http.HandleFunc("/health/live", healthcheck.HTTPHandler(healthManager, "liveness"))
func HTTPHandler(manager *HealthCheckManager, probeType string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		result, err := manager.Probe(probeType)
		if err != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusServiceUnavailable)
			json.NewEncoder(w).Encode(map[string]interface{}{
				"status": "down",
				"error":  err.Error(),
			})
			return
		}

		statusCode := result.GetHTTPStatusCode()
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(statusCode)
		json.NewEncoder(w).Encode(result)
	}
}

// RegisterRoutes registers health check routes with the default HTTP mux.
//
// Usage:
//   healthManager := healthcheck.New(healthcheck.Config{ ... })
//   healthcheck.RegisterRoutes(http.DefaultServeMux, healthManager)
func RegisterRoutes(mux *http.ServeMux, manager *HealthCheckManager) {
	mux.HandleFunc("/health", HTTPHandler(manager, "readiness"))
	mux.HandleFunc("/health/live", HTTPHandler(manager, "liveness"))
	mux.HandleFunc("/health/ready", HTTPHandler(manager, "readiness"))
	mux.HandleFunc("/health/startup", HTTPHandler(manager, "startup"))
}

// GinMiddleware returns a Gin middleware function for health checks.
//
// Usage (Gin framework):
//   import "github.com/gin-gonic/gin"
//
//   healthManager := healthcheck.New(healthcheck.Config{ ... })
//   router := gin.Default()
//   router.GET("/health", healthcheck.GinHandler(healthManager, "readiness"))
func GinHandler(manager *HealthCheckManager, probeType string) interface{} {
	// Return generic interface{} to avoid importing gin
	// Actual usage will type-assert to gin.HandlerFunc
	return func(c interface{}) {
		// Type assertion would happen in actual implementation
		// This is a placeholder showing the pattern
	}
}

// EchoMiddleware returns an Echo middleware function for health checks.
//
// Usage (Echo framework):
//   import "github.com/labstack/echo/v4"
//
//   healthManager := healthcheck.New(healthcheck.Config{ ... })
//   e := echo.New()
//   e.GET("/health", healthcheck.EchoHandler(healthManager, "readiness"))
func EchoHandler(manager *HealthCheckManager, probeType string) interface{} {
	// Return generic interface{} to avoid importing echo
	// Actual usage will type-assert to echo.HandlerFunc
	return func(c interface{}) error {
		// Type assertion would happen in actual implementation
		// This is a placeholder showing the pattern
		return nil
	}
}
