# 5d-6 Referral Priority Queue Interview Loop Walkthrough

Date: 2026-05-12
Feature: Referral Priority Queue
Status: self-test-backed fixture walkthrough

## Flow proven

1. `interview-loop collect` reads the feature trigger result and creates structured open questions.
2. `interview-loop answer --apply` records a durable decision in JSONL.
3. `tdd-cross-verify` and the response hook produce an explicit missing-test force gate.
4. `aftershock-reanalysis` creates follow-up questions and the walkthrough pins a depth-2 replay case.
5. Lifecycle hook integration is exercised through `on-response-completed.sh` with isolated temp queues.

## Cost / ambiguity / friction

- Time cost: one deterministic self-test path instead of ad-hoc chat validation.
- Saved ambiguity: DDD term registration now carries concrete effects into decision logs.
- Friction: current aftershock v0 uses deterministic effect-to-layer heuristics, not full artifact diffing yet.

## Remaining limitation

This walkthrough is fixture-backed. The next MVP proof should run the same flow against a real host-project feature branch artifact and decide whether missing TDD is written immediately or explicitly deferred.
