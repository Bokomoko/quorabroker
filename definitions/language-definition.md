# Project Language Definition

All project content MUST be written in English, even if a user prompt, issue, or external source is provided in another language.

## Scope

This applies to:

1. Source code (identifiers, comments, docstrings)
2. Documentation (`README.md`, design docs, ADRs, etc.)
3. Commit messages and pull request titles/descriptions
4. Issue titles and descriptions (when authored internally)
5. Test names and fixtures

## Style Guidelines

- Prefer clear, neutral international English (avoid idioms/slang)
- Use American spelling consistently (e.g., "color", "behavior", "initialize")
- Use sentence case for sentences; Title Case for document headings
- Avoid unnecessary abbreviations unless they are well-known (e.g., API, HTTP)
- Write docstrings using Google or reStructuredText style (consistent project-wide once chosen)
- Keep line width reasonable (≈ 100–120 chars) for prose in Markdown

## Code Conventions (language-related)

- Variable/function/class names must be in English and descriptive
- Do not mix languages within a single identifier
- Avoid transliterations of non-English words—translate their meaning instead
- If a domain concept has no clear English equivalent, document it in a glossary section

## Handling Non-English Input

If external data (e.g., user content) contains other languages, it may appear in:

- Test fixtures (must be labeled clearly and commented)
- Data samples (store under a `samples/` or `fixtures/` directory)

## Glossary (Create As Needed)

Add domain-specific terms here as they appear:

- (none yet)

## Enforcement Suggestions

- Add a pre-commit hook to reject commits containing non-ASCII alphabetic words outside approved fixtures
- Add a lint rule or script scanning for common Portuguese words if relevant
- Include this file in contribution guidelines

## Rationale

Consistency in language improves maintainability, onboarding, and searchability across the codebase.

## Change Log

- v1.0: Initial structured definition (replaces earlier informal sentence)

