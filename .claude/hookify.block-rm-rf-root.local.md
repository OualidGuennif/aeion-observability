---
name: block-rm-rf-root
enabled: false
event: bash
pattern: rm\s+-rf\s+(/|~|\$HOME)(\s|$)
action: block
---
Refused: this deletes a home or root directory. Delete the exact path you mean.
