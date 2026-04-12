---
description: Generate and manage technical documentation
---

# Documentation Skill

A skill for automating documentation generation and management tasks.

## Purpose

This skill helps with:
- Generating API documentation from code comments
- Maintaining README files with up-to-date usage examples
- Creating technical guides and tutorials
- Managing documentation consistency

## Features

- **Automatic Generation**: Extract docs from code
- **Template Support**: Pre-built templates for common doc types
- **Validation**: Check documentation completeness
- **Formatting**: Standardize documentation format

## Usage Example

```bash
# Generate documentation for a project
doc-skill generate --source ./src --output ./docs

# Validate documentation
doc-skill validate ./docs
```

## Configuration

See `config.json` for detailed configuration options.

## Related Documentation

- [API Reference](../api-reference-skill/SKILL.md)
- [Code Review Skill](../code-review-skill/SKILL.md)
