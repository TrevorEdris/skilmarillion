package user

import (
	"encoding/json"
	"net/http"
)

// Handler provides HTTP endpoints for user operations.
type Handler struct {
	svc *Service
}

// NewHandler creates a new user Handler.
func NewHandler(svc *Service) *Handler {
	return &Handler{svc: svc}
}

// GetProfile handles GET /users/{id}/profile
// Extracts {id} from the URL path using r.PathValue("id") (Go 1.22 stdlib routing).
// Calls svc.GetProfile. Returns 500 on error, 200+JSON on success.
func (h *Handler) GetProfile(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if id == "" {
		http.Error(w, "missing user id", http.StatusBadRequest)
		return
	}

	profile, err := h.svc.GetProfile(id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(profile)
}
