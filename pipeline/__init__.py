"""Data pipeline: raw university Excel submissions -> clean, validated tables.

Built in Phases 2-4 (see docs/ROADMAP.md):
  extract   - read every yearly template version into one tidy format
  validate  - check totals, missing values and cross-checks against QF consolidated files
  metrics   - compute the story numbers the dashboard shows
"""
