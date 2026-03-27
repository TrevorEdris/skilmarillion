package auth

import (
	"fmt"
	"time"
)

// Service handles authentication and session management.
type Service struct {
	credentials map[string]string  // userID → plaintext password (fixture only)
	sessions    map[string]*Session // token → session
}

// NewService returns an AuthService seeded with test credentials.
func NewService() *Service {
	return &Service{
		credentials: map[string]string{
			"u1": "password1",
			"u2": "password2",
		},
		sessions: make(map[string]*Session),
	}
}

// Login validates credentials and returns a new session.
func (s *Service) Login(userID, password string) (*Session, error) {
	stored, ok := s.credentials[userID]
	if !ok || stored != password {
		return nil, fmt.Errorf("invalid credentials")
	}
	token := fmt.Sprintf("tok-%s-%d", userID, time.Now().UnixNano())
	session := &Session{
		Token:     token,
		UserID:    userID,
		ExpiresAt: time.Now().Add(24 * time.Hour).Unix(),
	}
	s.sessions[token] = session
	return session, nil
}

// ChangePassword validates the old password, updates to the new one.
// NOTE: Does not notify the user. Sending a notification email is not yet implemented.
func (s *Service) ChangePassword(userID, oldPassword, newPassword string) error {
	stored, ok := s.credentials[userID]
	if !ok {
		return fmt.Errorf("user %s not found", userID)
	}
	if stored != oldPassword {
		return fmt.Errorf("invalid old password")
	}
	s.credentials[userID] = newPassword
	return nil
}

// ValidateToken checks if a token maps to a valid, non-expired session.
func (s *Service) ValidateToken(token string) (*Session, error) {
	session, ok := s.sessions[token]
	if !ok {
		return nil, fmt.Errorf("invalid token")
	}
	if time.Now().Unix() > session.ExpiresAt {
		delete(s.sessions, token)
		return nil, fmt.Errorf("token expired")
	}
	return session, nil
}
