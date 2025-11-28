# OntoGenesis Codebase Overview

This document provides a high-level overview of the OntoGenesis codebase structure and key components.

## Directory Structure

```
ontogenesis/
├── data/                   # Sample data for simulations (logs, profiles, etc.)
├── docs/                   # Project documentation
├── src/                    # Source code
│   ├── execution/          # Code execution engine
│   ├── ontology/           # Core ontology definitions (Types, Graph)
│   ├── synthesis/          # LLM interaction layer
│   └── utils/              # Utilities (Tracing, Parsing)
├── tests/                  # Unit tests
├── notebooks/              # Jupyter notebooks for experiments
├── .env                    # Configuration (API Keys)
├── main.py                 # Entry point (currently minimal)
└── requirements.txt        # Python dependencies
```

## Key Components

### 1. Ontology (`src/ontology/`)
- **`types.py`**: Defines `DataType`. Represents the nodes in our graph (e.g., `PDF`, `HTML`, `JSON`).
- **`tools.py`**: Defines `Tool`. Represents the edges (capabilities) between types.
- **`graph.py`**: `CapabilityGraph`. Manages the graph structure and implements the **Gap Detection** logic (`detect_gap`).

### 2. Synthesis (`src/synthesis/`)
- **`factory.py`**: `LLMFactory`. Creates LLM providers based on configuration.
- **`providers/`**:
    - `openai_provider.py`: Interface for OpenAI API.
    - `ollama_provider.py`: Interface for local Ollama models.

### 3. Execution (`src/execution/`)
- **`runner.py`**: `CodeRunner`. Executes synthesized Python code in a local namespace.
    - *Note:* Currently uses `exec()` which is not sandboxed. Future versions will use Docker.

### 4. Utilities (`src/utils/`)
- **`tracer.py`**: `Tracer`. Provides structured logging (JSONL) for observability.
- **`code_parsing.py`**: Extracts code blocks from LLM markdown responses.

## Simulation (`src/v0_simulation.py`)
This script orchestrates the "v0 Logic Probe":
1.  Initializes the Ontology with types from `data/`.
2.  Visualizes the initial graph.
3.  Detects a gap between `ConsultantProfile` (HTML) and `KGTriples` (JSON).
4.  Synthesizes a tool using the configured LLM.
5.  Executes the tool on `data/consultant_profile_mark.html`.
6.  Verifies the output.

## Running the Project

1.  **Setup**:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    ```
2.  **Configuration**:
    Copy `.env.example` to `.env` and set your `OPENAI_API_KEY` and `OPENAI_MODEL`.
3.  **Run Simulation**:
    ```bash
    python src/v0_simulation.py
    ```
4.  **View Results**:
    - Traces: `data/traces.jsonl`
    - Graph: `ontology_initial.png`
    - Generated Code: `generated_tool.py`
