# Add Audit Log for User Profile Updates Spec

## Problem Statement

When a user's profile is updated via `UpdateProfile`, no record of the change is persisted.
Support and compliance teams cannot determine what changed, when, or by whom. An audit log
attached to the user service layer will provide an immutable record of all profile mutations.

## Acceptance Criteria

### Slice 1: Audit Log Storage

**AC-1.1:**
Given a valid user ID and a new display name,
When `UpdateProfile` is called,
Then an audit entry is appended to the log recording the userID, field changed, old value, new value, and timestamp.

**AC-1.2:**
Given an invalid user ID,
When `UpdateProfile` is called,
Then no audit entry is written and an error is returned to the caller.

**AC-1.3:**
Given audit log storage is unavailable,
When `UpdateProfile` is called,
Then the profile update is rolled back and the caller receives an error indicating storage failure.

## Architecture Recommendation

_To be filled by architecture-advisor_

## TDD Plan

_To be filled by tdd-planner_
