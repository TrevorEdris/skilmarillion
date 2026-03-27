package notification

import "log"

// Service defines the interface for sending user notifications.
// Implementations: LogService (stub), EmailService (not yet implemented).
type Service interface {
	SendEmail(to, subject, body string) error
}

// LogService is a stub that logs the email instead of sending it.
// Replace with a real SMTP or transactional email client in production.
type LogService struct{}

// NewLogService returns a new LogService instance.
func NewLogService() *LogService {
	return &LogService{}
}

// SendEmail logs the email details instead of actually sending.
func (s *LogService) SendEmail(to, subject, body string) error {
	log.Printf("[notification] EMAIL to=%s subject=%q", to, subject)
	return nil
}
