package billing

// Plan represents a subscription tier.
type Plan struct {
	ID       string
	Name     string
	PriceUSD int
}

// Subscription links a user to a plan.
type Subscription struct {
	ID          string
	UserID      string
	PlanID      string
	ActiveSince string
}
