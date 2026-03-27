// sample-app: minimal layered Go HTTP service for dream plugin test fixtures.
// Architecture: MVC/layered — handlers → services → repositories.
// Each package owns one layer of responsibility.
package main

import (
	"log"
	"net/http"

	"github.com/example/sample-app/internal/auth"
	"github.com/example/sample-app/internal/billing"
	"github.com/example/sample-app/internal/notification"
	"github.com/example/sample-app/internal/user"
)

func main() {
	// Data layer
	userRepo := user.NewInMemoryRepository()

	// Service layer
	userSvc := user.NewService(userRepo)
	_ = notification.NewLogService()
	authSvc := auth.NewService()
	_ = billing.NewService()

	// Handler layer
	userHandler := user.NewHandler(userSvc)
	authHandler := auth.NewHandler(authSvc)

	// Routing
	mux := http.NewServeMux()
	mux.HandleFunc("GET /users/{id}/profile", userHandler.GetProfile)
	mux.HandleFunc("POST /auth/login", authHandler.Login)
	mux.Handle("POST /auth/change-password", auth.RequireAuth(authSvc)(http.HandlerFunc(authHandler.ChangePassword)))

	log.Println("sample-app listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", mux))
}
