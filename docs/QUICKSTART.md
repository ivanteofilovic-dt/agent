# Quick Start Guide

## Using uv (Recommended)

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Dependencies

```bash
uv sync
```

This will:
- Create a virtual environment (`.venv/`)
- Install all dependencies from `pyproject.toml`
- Generate `uv.lock` file

### 3. Run the Application

**Web UI:**
```bash
uv run streamlit run app.py
```

**Command Line:**
```bash
uv run python main.py [path_to_transcript.txt]
```

**Test Script:**
```bash
uv run python test_agent.py
```

### 4. Add New Dependencies

```bash
uv add package-name
```

### 5. Update Dependencies

```bash
uv sync --upgrade
```

## Using pip (Alternative)

If you prefer using pip:

```bash
pip install -e .
streamlit run app.py
```

## Environment Variables

Make sure to set up your `.env` file:

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Notes

- `uv` is faster and more reliable than pip
- `uv sync` automatically manages the virtual environment
- The `uv.lock` file ensures reproducible builds
- Use `uv run` to execute commands in the project's virtual environment





