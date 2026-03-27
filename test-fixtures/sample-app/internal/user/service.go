package user

// Service contains business logic for user operations.
type Service struct {
	repo Repository
}

// NewService creates a new UserService backed by the given repository.
func NewService(repo Repository) *Service {
	return &Service{repo: repo}
}

// GetProfile returns a Profile for the given userID.
// BUG: does not check if user is nil before accessing user.Email and user.Name.
// When repo.FindByID returns (nil, nil), this will panic.
func (s *Service) GetProfile(userID string) (*Profile, error) {
	user, err := s.repo.FindByID(userID)
	if err != nil {
		return nil, err
	}
	return &Profile{
		UserID: userID,
		Email:  user.Email, // panics if user is nil
		Name:   user.Name,
	}, nil
}

// UpdateProfile updates the user's display name.
// BUG: does not check if user is nil before accessing user.Name — same class of bug as GetProfile.
// Does not produce an audit log entry (gap intentional — see Mode A fixture).
func (s *Service) UpdateProfile(userID, name string) error {
	user, err := s.repo.FindByID(userID)
	if err != nil {
		return err
	}
	user.Name = name // panics if user is nil
	return s.repo.Save(user)
}
