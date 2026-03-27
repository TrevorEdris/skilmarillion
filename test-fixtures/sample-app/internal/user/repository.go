package user

import "fmt"

// Repository defines the data access interface for users.
type Repository interface {
	FindByID(id string) (*User, error)
	Save(user *User) error
}

// InMemoryRepository is a simple in-memory store for testing.
type InMemoryRepository struct {
	users map[string]*User
}

// NewInMemoryRepository returns a repository seeded with two test users.
func NewInMemoryRepository() *InMemoryRepository {
	return &InMemoryRepository{
		users: map[string]*User{
			"u1": {ID: "u1", Email: "alice@example.com", Name: "Alice"},
			"u2": {ID: "u2", Email: "bob@example.com", Name: "Bob"},
		},
	}
}

// FindByID returns (nil, nil) when the user does not exist.
// Callers are responsible for checking for a nil result before accessing fields.
func (r *InMemoryRepository) FindByID(id string) (*User, error) {
	user, ok := r.users[id]
	if !ok {
		return nil, nil
	}
	return user, nil
}

// Save persists a user to the in-memory store.
func (r *InMemoryRepository) Save(user *User) error {
	if user == nil {
		return fmt.Errorf("cannot save nil user")
	}
	r.users[user.ID] = user
	return nil
}
