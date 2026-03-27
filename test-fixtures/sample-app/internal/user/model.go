package user

// User represents a registered user in the system.
type User struct {
	ID    string
	Email string
	Name  string
}

// Profile is the public-facing view of a user's information.
type Profile struct {
	UserID string
	Email  string
	Name   string
}
