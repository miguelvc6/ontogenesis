This implementation plan is structured to move you rapidly from "idea" to "measurable experiments."

We will proceed in three versions:

1. **v0: The Logic Probe** (Manual validation of the hypothesis).
2. **v1: The Closed-Loop System** (Automated synthesis and execution).
3. **v2: The Research Rig** (Evaluation against baselines for publication).

---

### **Version 0: The Logic Probe**

**Goal:** Validate that "Gap Detection via Types" actually produces better synthesis prompts than standard "ReAct" reasoning. No complex infrastructure yet.
**Status:** [COMPLETED] - See `docs/v0_results.md`.

**Tech Stack:** `NetworkX` (Graph), `Pydantic` (Type Definitions), `OpenAI API` (LLM), `Jupyter Notebook`.

#### **1. Define the Micro-Ontology**

Instead of full OWL, use Python classes to represent the ontology. This allows for easy manipulation in `NetworkX`.

```
from typing import List, Type, Any
from pydantic import BaseModel

# 1. The Type System (Nodes)
class DataType(BaseModel):
    name: str
    schema_def: dict  # JSON Schema or Python Type hint

# 2. The Transformation (Edges)
class Tool(BaseModel):
    name: str
    input_type: str  # e.g., "PDF_File"
    output_type: str # e.g., "Raw_Text"
    constraints: List[str] = []

# 3. The Graph State
# In v0, we just populate this manually with 3-4 nodes.
# Nodes: [PDF_File, Raw_Text, Clean_Text, KG_Triples]
# Edges: PDF->Raw, Raw->Clean
```

#### **2. The Gap Detector (The Planner)**

Write a simple function using `networkx.shortest_path`.

- **Input:** Current State (`Clean_Text`), Goal (`KG_Triples`).
- **Logic:** Check if a path exists.
- **Output:** If no path, return the *missing edge signature*: `Target Tool: Clean_Text -> KG_Triples`.

#### **3. The "Manual" Loop**

1. **Scenario:** Define a task (e.g., "Extract Person entities from this text").
2. **Run Gap Detector:** It should identify the missing tool signature.
3. **Generate Spec:** Use a template:
   * *"You are an architect. We have type A (schema X) and need type B (schema Y). Write a Python function `transform(a: A) -> B`."*
4. **Manual Check:** Copy the LLM output into your notebook, run it on sample data.
5. **Critique:** Did the strict type definition help the LLM write better code than a generic "Please extract entities" prompt?

---

### **Specific "Micro-Ontology" for v0**

Here is the concrete ontology structure to implement to start v0. It uses Python classes to mock OWL concepts.

```
from typing import Dict, List, Optional
import networkx as nx

class TypeNode:
    """Represents a Data Type in the Ontology"""
    def __init__(self, name: str, schema: Dict):
        self.name = name
        self.schema = schema # JSON Schema

class ToolEdge:
    """Represents a Capability (Edge)"""
    def __init__(self, name: str, func_code: str, constraints: List[str]):
        self.name = name
        self.code = func_code
        self.constraints = constraints

class CapabilityGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_type(self, type_node: TypeNode):
        self.graph.add_node(type_node.name, schema=type_node.schema)

    def add_tool(self, input_name: str, output_name: str, tool: ToolEdge):
        self.graph.add_edge(input_name, output_name, tool=tool)

    def find_path(self, start_type: str, end_type: str) -> List[str]:
        try:
            return nx.shortest_path(self.graph, start_type, end_type)
        except nx.NetworkXNoPath:
            return []

    def detect_gap(self, start_type: str, end_type: str):
        # A simple gap detector:
        # If no path exists, we simply propose a direct edge.
        # (Research version would find "bridging" types).
        if not self.find_path(start_type, end_type):
            return {
                "gap": True,
                "source": self.graph.nodes[start_type],
                "target": self.graph.nodes[end_type]
            }
        return {"gap": False}
```

1. **Define the Dataset:** Find 3-4 distinct file types (e.g., a PDF invoice, a CSV log, an HTML profile).
2. **Manual Trace:** Write down the "Ideal Trace" for processing these into a KG.
   * *Step 1:* `PDF -> Text` (Tool: `pdf_to_text`)
   * *Step 2:* `Text -> Entities` (Tool: `extract_entities`)
   * *Step 3:* `Entities -> RDF` (Tool: `dict_to_rdf`)
3. **Run the v0 Code:** Implement the class above, populate it with the types `PDF`, `Text`, `Entities`, `RDF`. Ask the `detect_gap` function to find a path from `PDF` to `RDF`. It should fail. This failure is your **trigger** for the LLM.

This setup helps you master Python graphs and sets the foundation for a more advanced AI system.

---

### **Version 1: The Closed-Loop System**

**Goal:** Automate the cycle. The agent encounters a gap, writes the tool, tests it, and *adds it to the graph* to continue planning.

**Tech Stack:** `LangGraph` (for the control loop), `Docker` (Sandbox), `PyTest`.

#### **1. The Formal Planner**

Replace the simple shortest path with a *State-Space Search*.

- **Forward Search:** From `Current_Type` explore reachable types.
- **Backward Search:** From `Goal_Type` find required inputs.
- **Intersection:** The gap is the bridge between the forward frontier and the backward frontier.

#### **2. The Synthesizer & Sandbox**

You need a safe place to execute generated code.

- **Use `docker` (Python SDK):**
  1. LLM outputs code.
  2. Save to `temp_tool.py`.
  3. Generate a unit test `test_tool.py` based on the *Type Schema* (e.g., if output is `List[str]`, test checks `isinstance(out, list)`).
  4. Run `docker run -v ... python -m pytest test_tool.py`.
  5. **If Pass:** Register tool in `NetworkX`.
  6. **If Fail:** Feed stderr back to LLM (Self-Correction).

#### **3. The Ontology Manager**

- When a tool is registered, it isn't just a Python function. It is a **Node** in your graph.
- **Persistence:** Save the graph to JSON/Pickle.
- **Reuse:** On the *next* run of the loop, the planner sees this new edge and uses it immediately without synthesis.

---

### **Version 2: The Research Rig**

**Goal:** Generate the data required for the paper. This focuses on *metrics* and *baselines*.

**Tech Stack:** `Evaluation Framework` (Custom), `Baseline Agents` (LangChain implementation).

#### **1. The Benchmark (Crucial for DPKM)**

I cannot rely on random "chat" tasks. I need a data-centric benchmark.

- **Dataset:** "KG-Bench-Synthesis" (You might need to curate this).
  - *Input:* A collection of messy files (CSV, PDF, JSON, XML).
  - *Goal:* Produce a specific unified JSON-LD format.
  - *Ground Truth:* The expected JSON-LD structure.

#### **2. Baselines**

1. **ReAct Agent (Vanilla):** Has `python_repl` and `search`. No graph memory.
2. **RAG-Tool Agent:** Stores generated functions in a Vector DB (Chroma). Retrieves top-k tools based on task description similarity.
3. **OntoGenesis (Mine):** Retrieves/Synthesizes tools based on *Graph Topology* and *Type Signatures*.

#### **3. Metrics**

- **Synthesis Efficiency:** `(Tools Synthesized) / (Total Steps)`. Low is better (means high reuse).
- **Type Safety:** `% of executions` that crash due to schema mismatch.
- **Graph Density:** How the connectivity of the ontology grows over $N$ tasks.

---
