import os
import json
from openai import OpenAI
from rdflib import Graph
import prompts
import onto_toolkit
from tool_interface import init_onto_tools, GetEntitiesOntoTool, QueryOntoTool
from entities_index import EntitiesIndex


# The data generate by the LLM to be used for answer user's questions.
BASE_PATH = "data/outcomes/20251105_185955/"
ENTITIES_INDEX_PATH = os.path.join(BASE_PATH,"entities_index.json")
OWL_ONTO_PATH = os.path.join(BASE_PATH, "ontology.owl")

# Set the GPT model to use and remember to set the `OPENAI_API_KEY` environmental variable.
MODEL = "gpt-5"


def load_owl(file_path):
    """
    Load an OWL (RDF/XML) file into an RDF graph, which is returned.
    """
    g = Graph()
    g.parse(file_path, format="xml")  # RDF/XML format
    print(f"Loaded {len(g)} triples from {file_path}")
    return g


def main():
    """
    A runnable script that loads the ontology created by `onto_builder.py` and poses user's questions to the LLM,
    which answers based on SPARQL queries. The questions are stored in hte `test.json` file.
    """
    
    client = OpenAI()
    
    # Load an EntitiesIndex previously created by the LLM
    entities_index = EntitiesIndex.fromFile(ENTITIES_INDEX_PATH)
    # Get the tools available to the LLM
    tools_schema, tools = init_onto_tools(entities_index, [GetEntitiesOntoTool, QueryOntoTool])
    
    # Load the ontology
    graph = load_owl(OWL_ONTO_PATH)
    # Make the query tool work with the loaded ontology
    tools[QueryOntoTool.T_NAME].setOntology(graph)

    # Load the user's questions.
    print("\n------------------------ User's Questions ------------------------\n")
    with open('data/test.json', 'r+') as f:
        questions = json.load(f)
    
    # Make the LLM answer for all user's questions.
    question_cnt = 1
    for q in questions:
        
        # Prepare prompt
        prompt = [{
            "role": "system",
            "content": prompts.explore_onto()
        },{
            "role": "user",
            "content": q["query"]
        }]
        
        # Invoke GPT with the specified tools
        outcome = onto_toolkit.invoke(MODEL, client, prompt, tools, tools_schema, verbose=False, max_iteration=20)
        
        # Print outcomes
        print('======================================')
        print(f"Asking question {question_cnt}: `{q["query"]}` (expected response: `{q["expected"]}`)")
        print(f"Response:\n{outcome}")
        print('======================================')
        question_cnt += 1
    
    print("Test done")

if __name__ == "__main__":
    main()