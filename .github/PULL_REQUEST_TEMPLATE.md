## Description

<!-- Provide a clear and concise description of what this PR does -->

## Motivation

<!-- Why is this change needed? Link to related issues if applicable -->

Closes #<!-- issue number -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test coverage improvement
- [ ] CI/CD or tooling change

## Changes Made

<!-- List the main changes made in this PR -->

-
-
-

## Testing

<!-- Describe the tests you ran and how to reproduce them -->

### Test Coverage

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated (if applicable)
- [ ] All existing tests pass locally

### Manual Testing

<!-- Describe any manual testing performed -->

```bash
# Commands used to test
make test
make test-integration
```

## Checklist

<!-- Mark completed items with an "x" -->

### Code Quality

- [ ] Code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new linter warnings (`make lint`)
- [ ] Type checking passes (`make mypy`)
- [ ] All tests pass (`make test`)

### Documentation

- [ ] I have updated the documentation accordingly
- [ ] Docstrings follow Google style with imperative mood
- [ ] I have added examples for new features (if applicable)
- [ ] README.md updated (if applicable)

### Dependencies

- [ ] No new dependencies added
- [ ] If dependencies added, they are justified and minimal
- [ ] `uv.lock` updated (if dependencies changed)

### Compatibility

- [ ] Changes are compatible with Python 3.8-3.13
- [ ] No use of `type[...]` syntax (use `Type[...]` for Python 3.8)
- [ ] Async/sync variants both work correctly (if applicable)

### Commits

- [ ] Commit messages are clear and follow conventional commits style
- [ ] Commits are logically organized
- [ ] No debug code or commented-out code left in

## Additional Context

<!-- Add any other context, screenshots, or information about the PR here -->

## Pre-merge Actions

<!-- For maintainers -->

- [ ] Changelog updated (if applicable)
- [ ] Version bump considered (if applicable)
