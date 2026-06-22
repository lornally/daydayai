---
name: bugfix-protocol
description: >
  Strict doc-first TDD workflow for bug fixes. Use when fixing bugs,
  regressions, flaky behavior, production incidents, or when user asks for
  TDD, red-green, document-first, or "文档->测试->开发".
---

# Bugfix Protocol

Fix bugs by gate. Do not skip.

## Gate 0: Understand

If repro unclear, ask one question. No source edit.

## Gate 1: Doc

Create or update one short bug note before tests or source.

Default path: `bugfix-notes/<short-slug>.md` unless repo already has bug docs.

Doc rules:
- Brief.
- No code blocks.
- No code snippets.
- Explain with concrete cases, not implementation.
- Include only: symptom, case, expected, actual, acceptance command.

Template:

```markdown
# <bug>

Symptom: <one sentence>
Case: <user action/input/state that triggers bug>
Expected: <observable result>
Actual: <wrong observable result>
Acceptance: <test command>
```

## Gate 2: Red

Write only the regression test.

Run the acceptance command. Must fail for the documented bug.

If test passes, test is wrong or bug misunderstood. Do not edit source.

Record the shortest decisive failure line in the response.

## Gate 3: Green

Make the smallest source change.

Run the same acceptance command.

If green, stop. No refactor unless user asks.

## Hard Stops

- No doc: no test.
- No red: no source edit.
- Green achieved: stop.
- New unrelated bug found: new note, new test, new task.
