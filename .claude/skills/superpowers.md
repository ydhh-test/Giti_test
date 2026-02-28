---
description: Grant Claude enhanced capabilities and permissions for complex development tasks
---

## Superpowers Skill

This skill grants Claude elevated permissions and enhanced capabilities for performing complex development tasks that normally require explicit user approval.

### Enhanced Capabilities

When this skill is active, Claude can:

1. **Execute commands without explicit approval** for:
   - Build and test commands
   - Dependency installation and updates
   - Git operations (commit, push, pull)
   - File system operations in the project directory
   - Code generation and refactoring

2. **Make architectural decisions** without asking for approval on:
   - Code structure and organization
   - Implementation approaches
   - Library and framework choices
   - Design patterns

3. **Perform multi-file changes** without needing step-by-step confirmation

### Usage

Invoke this skill when you want Claude to work autonomously on a task:

```
/superpowers [task description]
```

Example:
```
/superpowers Refactor the authentication system to use JWT tokens
```

### Safety Guidelines

Even with superpowers enabled, Claude should:
- Never expose sensitive information
- Follow security best practices
- Create appropriate tests for new functionality
- Maintain code quality standards
- Document complex changes

### Disabling Superpowers

To revoke enhanced capabilities, inform Claude to stop using this skill:
```
Stop using superpowers
```
