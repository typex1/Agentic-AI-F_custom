---
name: commit-message-writer
description: The `commit-message-writer` skill turns a plain-language description of a code change into a Conventional Commits message. It is triggered when the user wants help writing a git commit message. The skill outputs a single Conventional Commits subject line, optionally with a short body.
---

## Usage

To use the `commit-message-writer` skill, simply provide a plain-language description of the code change. The skill will generate a Conventional Commits message based on the description.

## Examples

**Example 1:**

Input: Added user authentication with JWT tokens

Output: feat(auth): implement JWT-based authentication

**Example 2:**

Input: Fixed a bug in the payment processing module

Output: fix(payment): resolve issue with payment processing