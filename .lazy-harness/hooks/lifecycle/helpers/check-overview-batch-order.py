#!/usr/bin/env python3
"""Retired compatibility helper for the old overview batch hard block.

This helper intentionally emits no output and exits successfully. Older
generated hook wrappers may still invoke it, and the wrapper treats any helper
output as a deny reason. Keeping this file as a no-op removes the tool block
while preserving compatibility across downstream hosts until their hook chains
are regenerated.

The policy is now advisory: `lazy map --overview` remains the recommended first
inventory step before dependent follow-up queries/reads, but read-only batch or
parallel tool shapes are not blocked. The generic search/read evidence guard in
`check-read-debt-permit.py` remains responsible for blocking mutation before
root-bound evidence exists.
"""
from __future__ import annotations

raise SystemExit(0)
