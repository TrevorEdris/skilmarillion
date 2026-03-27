package billing

import "fmt"

// Service manages plan subscriptions.
// Stub implementation — production billing integration not yet built.
type Service struct {
	subscriptions map[string]*Subscription
	plans         []Plan
}

// NewService returns a BillingService seeded with default plans.
func NewService() *Service {
	return &Service{
		subscriptions: make(map[string]*Subscription),
		plans: []Plan{
			{ID: "free", Name: "Free", PriceUSD: 0},
			{ID: "pro", Name: "Pro", PriceUSD: 20},
			{ID: "enterprise", Name: "Enterprise", PriceUSD: 100},
		},
	}
}

// GetSubscription returns the active subscription for a user, or nil if none.
func (s *Service) GetSubscription(userID string) (*Subscription, error) {
	sub, ok := s.subscriptions[userID]
	if !ok {
		return nil, nil
	}
	return sub, nil
}

// CreateSubscription assigns a plan to a user.
func (s *Service) CreateSubscription(userID, planID string) (*Subscription, error) {
	var found bool
	for _, p := range s.plans {
		if p.ID == planID {
			found = true
			break
		}
	}
	if !found {
		return nil, fmt.Errorf("plan %s not found", planID)
	}
	sub := &Subscription{
		ID:          fmt.Sprintf("sub-%s-%s", userID, planID),
		UserID:      userID,
		PlanID:      planID,
		ActiveSince: "2024-01-01",
	}
	s.subscriptions[userID] = sub
	return sub, nil
}
