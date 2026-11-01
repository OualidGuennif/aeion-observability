---
name: warn-debug-log
enabled: false
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: console\.log\(|print\(f?["']DEBUG
action: warn
---
Debug output left in the code: remove it or use the project's logger.
