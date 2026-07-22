# VS Code Kimi uses stale migrated credentials

Symptom: Kimi works in the terminal but VS Code Kimi returns an authentication error.
Case: Send a prompt after VS Code Kimi 0.6.4 reads the migrated `~/.kimi-code/config.toml`.
Expected: The request succeeds and returns `OK`.
Actual: The request fails with HTTP 401 because the migrated key differs from the working terminal configuration.
Acceptance: `env -u KIMI_API_KEY kimi --config-file "$HOME/.kimi-code/config.toml" --quiet -p '只回复 OK'`
