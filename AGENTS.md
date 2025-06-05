# AGENTS Instructions

This repository contains a Python FastAPI backend and a React frontend.
The following rules apply to any changes made in this repository:

## Scope Restrictions
- When a request involves fixing frontend design or bugs, only modify the React
  frontend and do not touch backend code.
- When a request involves backend functionality or bug fixes, keep frontend files
  unchanged.

## Required Checks
- Format Python code with `black .`.
- Lint Python code using `flake8`.
- Run Python tests with `pytest`.
- For frontend changes, run `npm test` inside `dry-martini-web`.

## Commit Guidelines
- Use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

## Pull Request Guidelines
- Summarize the changes and reference any relevant files in the PR description.
- Mention the outcome of the required checks in the PR description.
