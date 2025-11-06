import json
import time
from tool_interface import OntoTool
from openai import OpenAI
from typing import List, Dict

MAX_ITERATION = 10


def invoke(model: str, client: OpenAI, input_list: List[Dict], tools: Dict[str, OntoTool], tools_schema: Dict, max_iteration = MAX_ITERATION, verbose=False) -> str:
    """
    Invoke GPT by providing a set of tools.
    GPT is allows to iterate for a maximum number of times, or until it does not want to invoke tools anymore.
    Then, the GPT result is returned as a string. Note that some tools will modify the associated `EntitiesIndex`.

    Args:
        model (str): The GPT model name, e.g. `"gpt-5"`.
        client (OpenAI): The GPT client.
        input_list (List[Dict]): The LLM prompt, other messages and data for GPT.
        tools (Dict[str, OntoTool]): A map of all tools instances indexed by name.
        tools_schema (Dict): A dictionary that describes the tool and its parameter to be given to GPT.
        max_iteration (int, optional): The number of max iterations. Defaults to MAX_ITERATION.
        verbose (bool, optional): Set it to true to print progresses.

    Returns:
        str: The final GPT response.
    """
    
    idx = 0
    while idx < max_iteration:
        if verbose: print(f"---------------- iteration: {idx+1}.")
        
        # Invoke the LLM with given prompt and tools
        try:
            response = client.responses.create(
                model=model,
                tools=tools_schema,
                input=input_list,
            )
        except Exception as e:
            # In case of error, wait and retry
            print(e)
            time.sleep(15)
            idx += 1
            continue
            
        # Scan LLM response and call tool if required
        made_tool_call = False
        for item in response.output:
            if item.type == "function_call":
                
                made_tool_call = True
                args = json.loads(item.arguments) # Load tool inputs
                result = None
                if item.name in tools.keys():
                    result = tools[item.name].useTool(args) # Invoke the toll
                else:
                    print(f"Unknown tool: {item.name}")
                    
                if verbose: print(f"TOOL CALL: {item.name}({args})")

                # Prepare LLM inputs for the next iteration.
                input_list.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(result if result else "OK")
                })
                

        if not made_tool_call:
            # Model has finished calling tools
            return response.output_text

        # Append model output so next iteration has the conversation context
        input_list += response.output
     
        idx += 1
    
    if verbose: print("\t\t\tResponse not found !!!")
    return None
