import sys
import os

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from ontology.graph import CapabilityGraph

def main():
    print("OntoGenesis v0.1")
    graph = CapabilityGraph()
    print("Graph initialized.")

if __name__ == "__main__":
    main()
