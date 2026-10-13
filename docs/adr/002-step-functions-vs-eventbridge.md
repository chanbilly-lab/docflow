# ADR-002: Step Functions for workflow, EventBridge for domain events

**Status:** Accepted  
**Date:** 2026-09-09

## Decision
Use Step Functions Standard for one Case's deterministic workflow and EventBridge for distribution of domain facts.

## Consequences
Workflow remains explicit; subscribers evolve independently; the event bus is not used as an implicit workflow engine.
