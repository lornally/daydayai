# VS Code Codex blank webview

Symptom: The Codex sidebar in the VS Code deep window shows no conversation UI.
Case: Open the Codex sidebar in the deep workspace with the installed Codex extension.
Expected: The Webview frontend loads and sends its ready message to the extension host.
Actual: The app server initializes, but the Webview never sends ready and the conversation UI stays blank.
Acceptance: `zsh bugfix-notes/check-vscode-codex-webview.zsh`
