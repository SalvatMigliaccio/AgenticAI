---
name: no-hardcoded-secrets
description: Prevents committing credentials, API keys, tokens, or connection strings with embedded passwords into source or version-controlled config. Use whenever you write or edit config files (docker-compose.yml, .env-like files, settings modules) or any code that connects to a database, API, or external service.
---

Never write a real credential — password, API key, token, private connection string — directly into a file that gets committed to git.

## What counts as a violation

- A database URL/DSN with a plaintext password embedded (`postgresql://user:realpassword@host/db`).
- An API key or token as a literal string in source code, YAML, or `docker-compose.yml`.
- A `.env`-style file that is *not* gitignored, containing real (non-placeholder) secret values.

## What's fine

- Placeholder/example values in a file explicitly meant to be a template (`.env.example`, docs) — as long as they're obviously fake (`your-password-here`, `changeme`, a value already used for local-only dev tooling that has no real-world access, like a default Ollama/local-only dev password) and the corresponding real file (`.env`, `secrets.yaml`) is gitignored.
- Reading a secret from an environment variable, a secrets manager, or a gitignored `.env` file at runtime.

## What to do when you find or need to add a secret-shaped value

1. If you're adding a new service/integration that needs a credential, wire it through an environment variable (or the project's existing settings mechanism) instead of writing the literal value into a tracked file.
2. If you find an existing hardcoded credential while working nearby, flag it to the user rather than silently "fixing" it — changing a password/DSN can break a running deployment, so this needs a human decision, not a silent edit. Note it clearly: which file, which line, what it should become.
3. Double-check any file you're about to write or edit isn't tracked-and-committed with a real secret before finishing — `git status`/`git diff` the file if unsure whether it's gitignored.
