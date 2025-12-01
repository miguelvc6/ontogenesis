# OntoGenesis

Lifelong Capability Learning via Neuro-Symbolic Tool Synthesis.

## Project Structure

- `src/`: Source code for the project.
    - `ontology/`: Core ontology definitions (Types, Tools, Graph).
    - `synthesis/`: LLM interaction and code generation (to be implemented).
    - `execution/`: Code execution sandbox (to be implemented).
    - `utils/`: Helper functions.
- `tests/`: Unit tests.
- `notebooks/`: Jupyter notebooks for experiments.
- `data/`: Sample data for testing.
- `docs/`: Project documentation.
    - [Codebase Overview](docs/codebase_overview.md)
    - [v0 Results](docs/v0_results.md)
    - [v1 Results](docs/v1_results.md)
    - [Implementation Plan](docs/implementation_plan.md)

## Setup

1. Create a virtual environment: `python -m venv .venv`
2. Activate it: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)
3. Install dependencies: `pip install -r requirements.txt`

## Running

- Run tests: `pytest`
- Run main script: `python main.py`
