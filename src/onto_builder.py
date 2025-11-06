import os
import json
import datetime
from openai import OpenAI
from typing import Dict

from tool_interface import init_onto_tools, AddClassOntoTool, AddIndividualOntoTool, AddPropertyOntoTool, GetClassesOntoTool, GetIndividualsOntoTool, GetPropertiesOntoTool
import prompts
import onto_toolkit
from entities_index import EntitiesIndex

# Set the GPT model to use and remember to set the `OPENAI_API_KEY` environmental variable.
MODEL = "gpt-5"


def make_ontology(client: OpenAI, entities_index: EntitiesIndex) -> Dict:
    """
    Invoke the LLM to generate an OWL ontology form the symbols represented by `EntitiesIndex`.

    Args:
        client (OpenAI): The LLM client.
        entities_index (EntitiesIndex): The symbols and descriptions to be encoded in the OWL ontology.

    Returns:
        str: The RDF/XML definition of an OWL ontology.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompts.make_owl(entities_index)},
            {"role": "user", "content": "Generate the OWL file as specified."}
        ]
    )
    return response


def save_response_to_file(response: Dict, entities_index: EntitiesIndex, log_dir: str) -> None:
    """
    Save the ontology created by the LLM as
     - a json file representing the symbols available in the ontology,
     - an owl file representing the OWL ontology.

    Args:
        response (Dict): The OpenAI response to a request given by `make_ontology()`.
        entities_index (EntitiesIndex): The symbols available in the ontology.
        log_dir (str): The base folder where to save the results. 
    """
    
    # Prepare outcome saving directory
    os.makedirs(os.path.dirname(log_dir), exist_ok=True)

    # Serialize the symbols available in the ontology into a JSON-like file.  
    entities_index_file_path = os.path.join(log_dir, "entities_index.json")
    entities_index.serialize(entities_index_file_path)
    
    # Serialize the OWL ontology as an RDF/XML file.
    ontology_file_path = os.path.join(log_dir, "ontology.owl")    
    with open(ontology_file_path, "w", encoding="utf-8") as f:
        f.write(f"{response.choices[0].message.content}")

    print(f"Response saved to: {log_dir} ")
 
  
  
def main():
    """
    A runnable function that uses GPT to create the ontology. It performs two steps:
        1. Invokes GPT with tools for creating the symbols stored in `EntitiesIndex`.
            - it uses two different type of data sources, each, with a slightly different prompt.
        2. Invokes GPT and provides the symbols previously created and returns an OWL file.
    """
    
    client = OpenAI()
    
    entities_index = EntitiesIndex()
        
    # Defines the tools available to the LLM.
    tools_schema, tools = init_onto_tools(entities_index, [AddClassOntoTool, AddPropertyOntoTool, AddIndividualOntoTool, 
                                                           GetClassesOntoTool, GetPropertiesOntoTool, GetIndividualsOntoTool])
    
    # If necessary, compute `EntitiesIndex`.
    print("\n------------------------ Build From Product Tree ------------------------\n")
    
    # Load structured product data
    with open('data/product_data.json', 'r+') as f:
        product_data = json.load(f)

    # Set the prompt for this type of data
    product_tree_prompt = [
        {
            "role": "system",
            "content": prompts.product_tree_2_onto(product_data)
        },
        {
            "role": "user",
            "content": "Extract the class, individuals and properties to generate the ontology as specified."
        }
    ]
    
    # Invoke the LLM with the specified tools.
    onto_toolkit.invoke(MODEL, client, product_tree_prompt, tools, tools_schema, max_iteration=80, verbose=True)

    print(f"Onto state so far:\n{entities_index}")
    print("-----------------------")
        
    
    print("\n------------------------ Build From Guidelines ------------------------\n")
    # Load unstructured logistic data
    with open('data/logistics.json', 'r+') as f:
        logistic_data = json.load(f)

    # Set the prompt for this type of data
    guidelines_prompt = [
        {
            "role": "system", 
            "content": prompts.paragraph_2_onto(logistic_data)
        },
        {
            "role": "user", 
            "content": "Extract the class, individuals and properties to enrich the ontology as specified."
        },
    ]
    
    # Invoke the LLM with the specified tools.
    onto_toolkit.invoke(MODEL, client, guidelines_prompt, tools, tools_schema, max_iteration=80, verbose=True)
    
    print(f"Onto state so far:\n{entities_index}")
    print("-----------------------")
    
    
    print("\n------------------------ Making Ontology ------------------------\n")
    # Use the LLM to convert symbols in `EntitiesIndex` into an actual OWL ontology.
    response = make_ontology(client, entities_index)
    
    print("-----------------------")
    
    # Save the results.
    log_dir = os.path.join("data/outcomes/", datetime.datetime.now().strftime("%Y%m%d_%H%M%S"), "")
    save_response_to_file(response, entities_index, log_dir)
    #print(response.choices[0].message.content)
    print("-----------------------")
    
    
    
if __name__ == "__main__":
    main()