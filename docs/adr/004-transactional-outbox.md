# ADR-004: Transactional Outbox

**Status:** Accepted  
**Date:** 2026-09-11

## Context
Updating DynamoDB and publishing separately to EventBridge creates a dual-write failure window.

## Decision
Write state + audit + Outbox in one DynamoDB transaction, then publish through DynamoDB Streams.

## Consequences
Reliable event intent after commit; at-least-once delivery still requires idempotent consumers and monitoring.
