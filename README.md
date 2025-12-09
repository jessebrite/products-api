# Products API

A secure CRUD API built with FastAPI and JWT authentication for managing items. This application allows users to register, authenticate, and perform CRUD operations on items with background task processing for notifications and logging.

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

# For subsequent runs
uv run pre-commit run --all-files
```

### Running the Project
Make sure you have "make" (pun-unintended) installed on your system and you can
run alternative "make" commands that achieve the same results.

Make comes pre-installed on several Unix-like system but for Windows Powershell, run the following:
#### 1. Install Scoop (if you don’t have it yet)
```powershell
iwr -useb https://get.scoop.sh | iex
```

#### 2. Install make
```powershell
scoop install make
```
Now that you have everything configured, you can go ahead and the project
```bash
# change directory into src and run uvicorn from there
cd src && uv run uvicorn main:app --reload
# Or
make run
```

### Running Tests

```bash
uv run pytest tests/

# There's a "make" command that helps you format, lint, run all tests and generate test coverage in one go.
# Run the following:
make ci
```

## License

MIT

**Coverage**
[![codecov](https://codecov.io/gh/jessebrite/products-api/graph/badge.svg)](https://codecov.io/gh/jessebrite/products-api)
