# ADR-001: Serverless-first Project 1

**Status:** Accepted  
**Date:** 2026-09-09

## Context
DocFlow must demonstrate AWS architecture while remaining affordable, understandable, and deployable as a portfolio project.

## Decision
Use a serverless-first architecture for Project 1. Keep Bedrock/RAG and always-on compute/data platforms outside the MVP.

## Consequences
Benefits: lower idle cost, less operational overhead, clearer AWS architecture story.  
Trade-off: future workloads may justify containers or relational storage; that requires a new ADR.
