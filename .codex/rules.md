# Codex Task Rules — TradeLens Backend

## Goal
Define tasks that improve API reliability, data accuracy, or iOS app compatibility without ambiguity.

## Format

### Task
Clear, single-purpose description.

### Context
How this affects the iOS app, data integrity, or API contract.

### Requirements
- concrete endpoint or service changes
- schema changes spelled out explicitly
- acceptance criteria measurable in API terms

### Done When
- API_CONTRACT.md reflects implementation
- tests pass for new/modified endpoints
- iOS model compatibility maintained (or documented migration)

### Notes (optional)
- assumptions about external services (yfinance, OpenAI)
- edge cases to consider
- which services/files will likely be touched

## Guidance

### API Changes
- Update `docs/API_CONTRACT.md` first
- Maintain backward compatibility when possible
- Version breaking changes appropriately

### Service Integration
- Start with mock implementation
- Add external API integration behind feature flag
- Handle external service failures gracefully

### Schema Alignment
- Backend Pydantic models = authoritative schema
- iOS Swift structs should mirror these exactly
- Field naming: backend uses `snake_case`, iOS uses `camelCase`

### Testing
- Add tests for new endpoints
- Mock external services in tests
- Verify response schemas match API_CONTRACT.md

## Core Principle

This backend is the **single source of truth** for the iOS app.

Think like a platform engineer:
**reliability beats cleverness**.

