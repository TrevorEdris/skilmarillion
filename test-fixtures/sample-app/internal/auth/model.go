package auth

// Credentials stores a user's authentication data.
type Credentials struct {
	UserID       string
	PasswordHash string // stored as plain text for fixture simplicity
}

// Session represents an active authenticated session.
type Session struct {
	Token     string
	UserID    string
	ExpiresAt int64
}
