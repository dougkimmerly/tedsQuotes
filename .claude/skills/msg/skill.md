---
name: msg
description: Check and execute all pending tasks
triggers:
  - msg
location: project
---

# Message Queue Auto-Execute

**FULLY AUTONOMOUS**

## Steps

1. Connect: `curl -s -X POST "http://localhost:9500/api/sessions/CC-quotes/connect" -H "Content-Type: application/json" -d "{\"directory\":\"$(pwd)\",\"pid\":$$,\"repo\":\"dougkimmerly/tedsQuotes\"}" > /dev/null 2>&1 || true`
2. Active: `curl -s -X POST "http://localhost:9500/api/sessions/CC-quotes/status" -H "Content-Type: application/json" -d '{"status":"active"}' > /dev/null 2>&1 || true`
3. Pull: `git pull`
4. Process tasks
5. POST responses: `curl -X POST "http://localhost:9500/api/responses" ...`
6. Idle: `curl -s -X POST "http://localhost:9500/api/sessions/CC-quotes/status" -H "Content-Type: application/json" -d '{"status":"idle"}' > /dev/null 2>&1 || true`
