# ADR-003: DynamoDB single-table design

**Status:** Accepted  
**Date:** 2026-09-09

## Decision
Use the Case-centered PK/SK/GSI model in `TECHNICAL_DESIGN.md`.

## Consequences
Efficient aggregate/query access patterns, but access-pattern changes must be designed deliberately.
