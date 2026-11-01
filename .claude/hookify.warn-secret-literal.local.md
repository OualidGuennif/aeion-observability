---
name: warn-secret-literal
enabled: false
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: (?i)(api[_-]?key|secret|token|password)\s*[:=]\s*["'][A-Za-z0-9_\-]{16,}["']
action: warn
---
This looks like a credential written into a file. Secrets live only in the local env file or the
platform's secret store; use a placeholder here (knowledge/policies/security.md).
