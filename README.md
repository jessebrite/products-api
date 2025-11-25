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

- Python 3.8 or higher

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Project

```bash
python src/main.py
```

### Running Tests

```bash
pytest tests/
```

## Development

Make sure to activate the virtual environment before working on the project.

## How to Check in Your Code Changes

Follow these steps to properly check in your code changes:

1. Pull the latest changes from the main branch:
    ```bash
    git pull origin main
    ```

2. Create a new branch for your changes:
    ```bash
    git checkout -b <branch>
    ```

3. Make your code changes.

4. Once your changes are done, format your code with:
    ```bash
    ruff format .
    ```

5. Check your code for linting errors:
    ```bash
    ruff check .
    ```

6. Stage the files you want to commit:
    ```bash
    git add <file>
    ```

7. Commit your changes with a meaningful message (the pre-commit hook will run automatically):
    ```bash
    git commit -m "Your commit message"
    ```

8. (Only for the first time) Set the upstream branch if it does not exist remotely:
    ```bash
    git --set-upstream origin <branch>
    ```

9. Push your changes to the remote repository:
    ```bash
    git push origin <branch>
    ```

## License

MIT
