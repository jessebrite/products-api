# Python Project

A simple Python project starter template.

## Project Structure

```
.
├── src/                 # Source code
├── tests/               # Unit tests
├── requirements.txt     # Project dependencies
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.11 or higher

## Setting up the project

This project uses **uv** for everything (virtual environments, package management, and even pre-commit hooks).

### 1. First-time setup (or when cloning on a new machine)

```bash
# Install uv if you don’t have it yet
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or visit (https://docs.astral.sh/uv/getting-started/installation/) for the Windows equivalent

# Clone + enter the repo
git clone https://github.com/jessebrite/products-api.git
git checkout products-api

# Create the venv and install dependencies + dev tools (including pre-commit)
uv sync --all-extras --dev && uv run pre-commit install
```

### Running the Project

```bash
# change directory into src and run uvicorn from there
cd src && uv run uvicorn main:app --reload
```

### Running Tests

```bash
uv run pytest tests/

# There's a make command that helps you format, run all tests and generate test coverage in one go. Make sure you have make installed on your system and run the followinf:
make ci
```

## License

MIT

**Coverage**
[![codecov](https://codecov.io/gh/jessebrite/products-api/graph/badge.svg)](https://codecov.io/gh/jessebrite/products-api)
