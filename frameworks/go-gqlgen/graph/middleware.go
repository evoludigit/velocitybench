package graph

import (
	"net/http"
)

// DataloaderMiddleware adds dataloaders to request context
func DataloaderMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		loaders := NewLoaders()
		ctx := WithLoaders(r.Context(), loaders)
		r = r.WithContext(ctx)
		next.ServeHTTP(w, r)
	})
}
