import json
from entities_index import EntitiesIndex
from typing import List, Dict



class OntoTool:
    """
    Base class for all ontology tools used by GPT.
    Each subclass must 
        - implement the GPT tool with a function whose name matches `self.name`.
        - specify the `self.parameters` dictionary that describes the GPT toll and its inputs.
    """

    def __init__(self, entities_index: EntitiesIndex, name: str, description: str, parameters=None):
        """
        Initialise an ontology-related tool for GPT.

        Args:
            entities_index (EntitiesIndex): the current state of the ontology to be manipulated.
            name (str): the tool name for GPT (it is the name of the function invoked by GPT).
            description (str): the tool description that GPT will use to decide when use it.
            parameters (dict, optional): the description of input parameters required by the tool. 
                GPT will use it to decide how to use the tool.
        """
        self.entities_index = entities_index
        self.name = name
        self.description = description
        self.parameters = parameters or {}

        # Retrieve the GPT tool, i.e., a function with a name consistent with `self.name`,
        if not hasattr(self, name):
            raise AttributeError(f"{self.__class__.__name__} must define a method `{name}`.")
        self.function_callback = getattr(self, name)


    def useTool(self, args=None):
        """
        Call the GPT tool with inputs given by the LLM.
        It calls a function with a name consistent with `self.name`.
        Such a call occurs in a try catch that notifies GPT in case of `Exception`. 

        Args:
            args (dict, optional): a dictionary of input parameters given by GPT, with keys specified by `self.parameters`. Defaults to None.

        Returns:
            Data to be given back to GPT.
        """
        try:
            return self.function_callback(args or {})
        except Exception as e:
            error_description = str(e)
            print(error_description)
            return {"results": f"Error: {error_description}"}


    def getToolDescription(self):
        """
        Return the tool description to be given to GPT.
        It uses `self.parameters` to describe the tool and its inputs.

        Returns:
            dict: the tool definition to be given to GPT.
        """
        schema = {"type": "function", "name": self.name, "description": self.description}
        if self.parameters:
            schema["parameters"] = self.parameters
        return schema



class AddClassOntoTool(OntoTool):
    """
    A tool for GPT that adds a new class in the ontology.
    
    A new class is represented as a dictionary with 
     - a class name (i.e., identifier),
     - a list of subclasses,
     - a list of descriptions of the roles of new class.
    """
    
    # JSON dictionary keys for tool's input Parameters.
    P_NAME = EntitiesIndex.P_NAME
    P_SUBCLASS = "subclassOf"
    P_DESCRIPTION = EntitiesIndex.P_DESCRIPTION
    
    def __init__(self, entities_index: EntitiesIndex):
        """
        Initialise this GPT tool with the symbols into the ontology.
        It configures the tools and its required input by setting `self.parameters`.

        Args:
            entities_index (EntitiesIndex): the ontology to work with.
        """
        super().__init__(
            entities_index,
            name="add_class",
            description="Add or update a class in the ontology's TBox.",
            parameters={
                "type": "object",
                "properties": {
                    self.P_NAME: {"type": "string", "description": "Class name (ID)."},
                    self.P_SUBCLASS: {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Superclasses of this class."
                    },
                    self.P_DESCRIPTION: {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Logical roles or meanings."
                    }
                },
                "required": [self.P_NAME],
            },
        )


    def add_class(self, args):
        """
        Tool invoked by GPT to add a new class in the ontology.
        
        It creates a new class or updates the data related to a class, if it already exists.

        Args:
            args (dict): a dictionary with these keys:
            - the new class `name`,
            - `subclassOf`, i.e., a list of parent classes,
            - a list of descriptions of the role of the new class.

        Returns:
            dict: a dictionary with a feedback to GPT.
        """
        
        # Retrieve data from GPT
        name = args[self.P_NAME]
        subclassOf = args.get(self.P_SUBCLASS, [])
        role = args.get(self.P_DESCRIPTION, [])

        if name in self.entities_index.tbox_classes:
            # Update a class with new `subClassOf` and `role` definitions.
            cls = self.entities_index.tbox_classes[name]
            cls[self.P_SUBCLASS] = list(set(cls[self.P_SUBCLASS] + subclassOf))
            cls[self.P_DESCRIPTION] = list(set(cls[self.P_DESCRIPTION] + role))
            
            #print(f"Updating class: {name} with {subclassOf}, {role}.")
            feedback = {"results": "Class `{name}` updated."}
            
        else:
            # Define a new class with `name`, `subClassOf` and `role` definitions.
            self.entities_index.tbox_classes[name] = {
                self.P_NAME: name,
                self.P_SUBCLASS: list(set(subclassOf)),
                self.P_DESCRIPTION: list(set(role)),
            }
            
            #print(f"Adding new class: {name}")
            feedback = {"results": "Class `{name}` created."}

        # Notify GPT with a feedback. 
        return feedback



class AddPropertyOntoTool(OntoTool):
    """
    A tool for GPT that adds a new property in the ontology.
    
    A new property is represented as a dictionary with 
     - a property name (i.e., identifier),
     - a list of descriptions of the roles of new property.
    """
    
    # JSON dictionary keys for tool's input Parameters.
    P_NAME = EntitiesIndex.P_NAME
    P_DESCRIPTION = EntitiesIndex.P_DESCRIPTION
    
    def __init__(self, entities_index: EntitiesIndex):
        """
        Initialise this GPT tool with the symbols into the ontology.
        It configures the tools and its required input by setting `self.parameters`.

        Args:
            entities_index (EntitiesIndex): the ontology to work with.
        """
        super().__init__(
            entities_index,
            name="add_property",
            description="Add or update a property in the ontology's TBox.",
            parameters={
                "type": "object",
                "properties": {
                    self.P_NAME: {"type": "string"},
                    self.P_DESCRIPTION: {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Roles or meanings associated with the property."
                    }
                },
                "required": [self.P_NAME],
            },
        )


    def add_property(self, args):
        """
        Tool invoked by GPT to add a new property in the ontology.
        
        It creates a new property or updates the data related to a property, if it already exists.

        Args:
            args (dict): a dictionary with these keys:
            - the new property `name`,
            - a list of descriptions of the `role` of the new property.

        Returns:
            dict: a dictionary with a feedback to GPT.
        """
        
        # Retrieve data from GPT
        name = args[self.P_NAME]
        role = args.get(self.P_DESCRIPTION, [])

        if name in self.entities_index.tbox_prop:
            # Update a property with new `role` definitions.
            prop = self.entities_index.tbox_prop[name]
            prop[self.P_DESCRIPTION] = list(set(prop[self.P_DESCRIPTION] + role))
            
            #print(f"Updating property: {name} with {role}.")
            feedback = {"results": "Property `{name}` updated."}
            
        else:
            # Define a new property with `name` and `role` definitions.
            self.entities_index.tbox_prop[name] = {self.P_NAME: name, self.P_DESCRIPTION: list(set(role))}
            
            # print(f"Add new property: {name}")
            feedback = {"results": "Property `{name}` created."}

        return feedback



class AddIndividualOntoTool(OntoTool):
    """
    A tool for GPT that adds a new individual in the ontology.
    
    A new individual is represented as a dictionary with 
     - an individual name (i.e., identifier),
     - a set of classed in which the individual is classified,
     - a list of relations represented as `[relation, value]`,
     - a list of descriptions of the roles of new individual.
    """
    
    # JSON dictionary keys for tool's input Parameters.
    P_NAME = EntitiesIndex.P_NAME
    P_CLASS = "classes"
    P_PROP = "properties"
    P_DESCRIPTION = EntitiesIndex.P_DESCRIPTION
    
    
    def __init__(self, entities_index: EntitiesIndex):
        """
        Initialise this GPT tool with the symbols into the ontology.
        It configures the tools and its required input by setting `self.parameters`.

        Args:
            entities_index (EntitiesIndex): the ontology to work with.
        """
        super().__init__(
            entities_index,
            name="add_individual",
            description="Add or update an individual in the ontology's ABox.",
            parameters={
                "type": "object",
                "properties": {
                    self.P_NAME: {"type": "string"},
                    self.P_CLASS: {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of class names."
                    },
                    self.P_PROP: {
                        "type": "array",
                        "description": "List of property-value pairs.",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 2
                        }
                    },
                    self.P_DESCRIPTION: {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Logical roles or meanings."
                    }
                },
                "required": [self.P_NAME],
            },
        )


    def add_individual(self, args):
        """
        Tool invoked by GPT to add a new individual in the ontology.
        
        It creates a new individual or updates the data related to an individual, if it already exists.

        Args:
            args (dict): a dictionary with these keys:
            - the new individual `name`,
            - a list of `classes` in which the individual is an instance of,
            - a list of `properties` involving the individual (as a list of `(relation, object)` tuples),
            - a list of descriptions of the `role` of the new property.

        Returns:
            dict: a dictionary with a feedback to GPT.
        """
        
        # Retrieve data from GPT
        name = args[self.P_NAME]
        classes = args.get(self.P_CLASS, [])
        properties = args.get(self.P_PROP, [])
        role = args.get(self.P_DESCRIPTION, [])

        if name in self.entities_index.abox_ind:
            # Update an individual with new `classes` and `properties` definitions.
            indiv = self.entities_index.abox_ind[name]
            indiv[self.P_CLASS] = list(set(indiv[self.P_CLASS] + classes))

            # Merge properties without duplicates
            prop_set = {tuple(p) for p in indiv[self.P_PROP]}
            for p in properties:
                prop_set.add(tuple(p))
            indiv[self.P_PROP] = [list(p) for p in prop_set]
            
            indiv[self.P_DESCRIPTION] = list(set(indiv[self.P_DESCRIPTION] + role))
            
            feedback = {"results": "Individual `{name}` updated."}
            #print(f"Updating individual: {name}, {classes}, {properties}.")

        else:
            # Define a new individual with `name`, `classes` and `properties` definitions.
            self.entities_index.abox_ind[name] = {
                self.P_NAME: name,
                self.P_CLASS: list(set(classes)),
                self.P_PROP: [list(p) for p in set(tuple(x) for x in properties)],
                self.P_DESCRIPTION: list(set(role))
            }
            
            feedback = {"results": "Individual `{name}` created."}
            #print(f"Add a new individual: {name}")

        return feedback



class GetClassesOntoTool(OntoTool):
    """
    A tool for GPT that returns all the classes added so far in the ontology (see `AddClassOntoTool`). 
    """
    
    def __init__(self, entities_index: EntitiesIndex):
        """
        Initialise and configure this GPT tool with the symbols into the ontology.

        Args:
            entities_index (EntitiesIndex): the ontology to work with.
        """
        super().__init__(entities_index, "get_classes", "Return all ontology classes.")


    def get_classes(self, _args=None):
        """
        The function invoked by GPT, which does not take any input parameters and returns
        the list of classes based on `entities_index.tbox_classes`

        Args:
            _args (dict, optional): Inputs parameters are not considered.

        Returns:
            dict: the classes added so far in the ontology with the relate data.
        """
        return json.dumps(self.entities_index.tbox_classes, indent=2)



class GetPropertiesOntoTool(OntoTool):
    """
    A tool for GPT that returns all the properties added so far in the ontology (see `AddPropertyOntoTool`). 
    """
    
    def __init__(self, entities_index: EntitiesIndex):
        """
        Initialise and configure this GPT tool with the symbols into the ontology.

        Args:
            entities_index (EntitiesIndex): the ontology to work with.
        """
        super().__init__(entities_index, "get_properties", "Return all ontology properties.")


    def get_properties(self, _args=None):
        """
        The function invoked by GPT, which does not take any input parameters and returns
        the list of properties based on `entities_index.tbox_prop`

        Args:
            _args (dict, optional): Inputs parameters are not considered.

        Returns:
            dict: the properties added so far in the ontology with the relate data.
        """
        return json.dumps(self.entities_index.tbox_prop, indent=2)



class GetIndividualsOntoTool(OntoTool):
    """
    A tool for GPT that returns all the individuals added so far in the ontology (see `AddIndividualOntoTool`). 
    """
    
    def __init__(self, entities_index: EntitiesIndex):
        """
        Initialise and configure this GPT tool with the symbols into the ontology.

        Args:
            entities_index (EntitiesIndex): the ontology to work with.
        """
        super().__init__(entities_index, "get_individuals", "Return all ontology individuals.")

    def get_individuals(self, _args=None):
        """
        The function invoked by GPT, which does not take any input parameters and returns
        the list of individuals based on `entities_index.abox_ind`

        Args:
            _args (dict, optional): Inputs parameters are not considered.

        Returns:
            dict: the individuals added so far in the ontology with the relate data.
        """
        return json.dumps(self.entities_index.abox_ind, indent=2)



class QueryOntoTool(OntoTool):
    """
    A tool for GPT that runs a SPARQL given by the LLM, and returns the results. 
    """
    
    # JSON dictionary keys for tool's input Parameters.
    P_QUERY = "query_text"
    
    # The tool name, it should mack the function name
    T_NAME = "query_ontology"
    
    def __init__(self, entities_index: EntitiesIndex):
        """
        Initialise and configure this GPT tool with the symbols into the ontology.
        Be sure to call `setOntology` before to use the tool.

        Args:
            entities_index (EntitiesIndex): the ontology to work with.
        """
        super().__init__(
            entities_index=entities_index,
            name=self.T_NAME,
            description="Get the result of a SPARQL query (as a json string) computed against the ontology.",
            parameters={
                "type": "object",
                "properties": {
                    self.P_QUERY: {"type": "string"},
                },
                "required": [self.P_QUERY],
            },
        )


    def setOntology(self, graph):
        """
        Sets the OWL ontology where SPARQL queries will be performed.  
        
        Args:
            graph (Graph): the OWL ontology opened with rdflib.
        """
        
        self.ontology = graph


    def query_ontology(self, args):
        """
        Run a given SPARQL query against the ontology and return the results.

        Args:
            args (dict): a dictionary with the `query_text` key, which contains the query to run. 

        Returns:
            list: of RDF triples found trough the query.
        """
        # Get GPT inputs
        query_text = args[self.P_QUERY]
        
        # Run SPARQL query
        results = self.ontology.query(query_text)
        outcomes = []
        for row in results:
            outcomes.append(str(row))
        return json.dumps(outcomes)



class GetEntitiesOntoTool(OntoTool):
    """
    A tool for GPT that return entities name and description from the ontology.
    Entities can be of type `classes`, `properties`, and `individuals`.
    This tools does not return the semantic definition of the entities.
    """
    
    # The name of tool's input properties, which are booleans.
    P_ENTITIES_CLASS = "classes"
    P_ENTITIES_PROPERTY = "properties"
    P_ENTITIES_INDIVIDUAL = "individuals"
    
    
    def __init__(self, entities_index: EntitiesIndex):
        """
        Initialise and configure this GPT tool with the symbols into the ontology.

        Args:
            entities_index (EntitiesIndex): the ontology to work with.
        """
        super().__init__(
            entities_index=entities_index,
            name="get_entities",
            description="Get a dictionary of entities in the ontology by selecting the requested type among: `classes`, `properties` and `individuals`.",
            parameters={
                "type": "object",
                "properties": {
                    self.P_ENTITIES_CLASS: {
                        "type": "boolean",
                        "description": "Set True to include `classes`.",
                    },
                    self.P_ENTITIES_PROPERTY: {
                        "type": "boolean",
                        "description": "Set True to include `properties`.",
                    },
                    self.P_ENTITIES_INDIVIDUAL: {
                        "type": "boolean",
                        "description": "Set True to include `individuals`.",
                    }
                },
                "required": [self.P_ENTITIES_CLASS, self.P_ENTITIES_PROPERTY, self.P_ENTITIES_INDIVIDUAL],
            },
        )


    def get_entities(self, args):
        """
        Tool invoked by GPT to get entities names and description from the ontology.
        It does not provide the semantic definition of entities.
        
        Args:
            args (dict): a dictionary with these keys:
            - `classes`: bool. True if the classes should be added to the output entities dictionary,
            - `properties`: bool. True if the properties should be added to the output entities dictionary,
            - `individuals`: bool. True if the individuals should be added to the output entities dictionary,

        Returns:
            dict: a dictionary as `{"classes":{"name1":["role1"], ...}, "properties":{"name1":["role1"], ...}, "individuals": {"name1":["role1"], ...}}`.
            With a false input parameter, the relate object in the returned value would not appear.
        """
        
        # Get GPT inputs
        should_include_classes = args[self.P_ENTITIES_CLASS]
        should_include_properties = args[self.P_ENTITIES_PROPERTY]
        should_include_individuals = args[self.P_ENTITIES_INDIVIDUAL]
        
        # Retrieve the required entities from the ontology.
        out = {}
        if should_include_classes:
            classes_entities = self.entities_index.getClassEntities()
            out[self.P_ENTITIES_CLASS] = classes_entities
            
        if should_include_properties:
            properties_entities = self.entities_index.getPropertyEntities()
            out[self.P_ENTITIES_PROPERTY] = properties_entities
            
        if should_include_individuals:
            individuals_entities = self.entities_index.getIndividualEntities()
            out[self.P_ENTITIES_INDIVIDUAL] = individuals_entities
            
        return out
            
            

def _build_tools_map(entities_index: EntitiesIndex, onto_tools: List[OntoTool] = None) -> Dict[str, OntoTool]:
    """
    Instantiates the specified tools and returns a map of tools indexed by name.

    Args:
        entities_index (EntitiesIndex): the symbols into the ontology to work with.
        onto_tools (List[OntoTool], optional): List of class that implement `OntoTool`. 
            Defaults is None, which instantiate all the implemented classes that derive from `OntoTool`.

    Returns:
        Dict[str, OntoTool]: A dictionary as `{"tool_name": tool_instance}`.
    """
    tools = {}
    if onto_tools is None:
        onto_tools = OntoTool.__subclasses__()
    for cls in onto_tools:
        tool = cls(entities_index)
        tools[tool.name] = tool
    return tools



def init_onto_tools(entities_index: EntitiesIndex, onto_tools: List[OntoTool] = None):
    """
    Initialize a set of tools for GPT. It returns two lists with the tool schema 
    for GPT and relative tool instances.

    Args:
        entities_index (EntitiesIndex): the symbols into the ontology to work with.
        onto_tools (List[OntoTool], optional): A list of tools, e.g., `[AddClassOntoTool, GetClassesOntoTool]`.
            Defaults is None, which instantiate all the implemented classes that derive from `OntoTool`.

    Returns:
        (list, list): two lists with corresponding indexes that represents 
            1. the tool description and parameter schema for GPT.
            2. the tool instance that will be invoked by GPT.
    """
    tools = _build_tools_map(entities_index, onto_tools)
    tools_json_schema = [tool.getToolDescription() for tool in tools.values()]
    return tools_json_schema, tools




#if __name__ == "__main__":
#    tools_test()

def tools_test():
    """
    A debugging function that runs all tools without using GPT.
    """
    
    print("=== Ontology Tools Demo (Add & Update Test Cases) ===")
    state = EntitiesIndex()
    _, tools = init_onto_tools(state)

    # ----------------------------------------------------
    # CLASSES
    # ----------------------------------------------------
    print("\n[1] ADDING CLASS: Person")
    tools["add_class"].useTool({
        "name": "Person",
        "subclassOf": ["Mammal"],
        "role": ["agent"]
    })
    print(tools["get_classes"].useTool())

    print("\n[2] UPDATING CLASS: Person (add new subclass and roles)")
    tools["add_class"].useTool({
        "name": "Person",
        "subclassOf": ["LivingBeing"],
        "role": ["human", "rational"]
    })
    print(tools["get_classes"].useTool())

    print("\n[3] ADDING CLASS: Student")
    tools["add_class"].useTool({
        "name": "Student",
        "subclassOf": ["Person"],
        "role": ["learner"]
    })
    print(tools["get_classes"].useTool())

    print("\n[4] UPDATING CLASS: Student (add role ‘enrolled’)")
    tools["add_class"].useTool({
        "name": "Student",
        "subclassOf": ["Person"],
        "role": ["learner", "enrolled"]
    })
    print(tools["get_classes"].useTool())

    # ----------------------------------------------------
    # PROPERTIES
    # ----------------------------------------------------
    print("\n[5] ADDING PROPERTY: hasAge")
    tools["add_property"].useTool({
        "name": "hasAge",
        "role": ["numeric", "temporal"]
    })
    print(tools["get_properties"].useTool())

    print("\n[6] UPDATING PROPERTY: hasAge (add new roles)")
    tools["add_property"].useTool({
        "name": "hasAge",
        "role": ["personal_info", "demographic"]
    })
    print(tools["get_properties"].useTool())

    print("\n[7] ADDING PROPERTY: hasName")
    tools["add_property"].useTool({
        "name": "hasName",
        "role": ["identifier"]
    })
    print(tools["get_properties"].useTool())

    print("\n[8] UPDATING PROPERTY: hasName (add new role ‘label’)")
    tools["add_property"].useTool({
        "name": "hasName",
        "role": ["label"]
    })
    print(tools["get_properties"].useTool())

    # ----------------------------------------------------
    # INDIVIDUALS
    # ----------------------------------------------------
    print("\n[9] ADDING INDIVIDUAL: Alice")
    tools["add_individual"].useTool({
        "name": "Alice",
        "classes": ["Person", "Student"],
        "properties": [["hasAge", "23"], ["hasName", "Alice Johnson"]]
    })
    print(tools["get_individuals"].useTool())

    print("\n[10] UPDATING INDIVIDUAL: Alice (add class + new properties)")
    tools["add_individual"].useTool({
        "name": "Alice",
        "classes": ["Scholar"],
        "properties": [["hasHobby", "Reading"], ["hasAge", "23"], ["hasStatus", "Active"]]
    })
    print(tools["get_individuals"].useTool())

    print("\n[11] ADDING INDIVIDUAL: Bob")
    tools["add_individual"].useTool({
        "name": "Bob",
        "classes": ["Person"],
        "properties": [["hasAge", "30"], ["hasName", "Bob Smith"]]
    })
    print(tools["get_individuals"].useTool())

    print("\n[12] UPDATING INDIVIDUAL: Bob (add new property + extra class)")
    tools["add_individual"].useTool({
        "name": "Bob",
        "classes": ["Employee"],
        "properties": [["hasJob", "Engineer"], ["hasStatus", "Active"]]
    })
    print(tools["get_individuals"].useTool())

    print("\n=== All Add/Update Test Cases Executed Successfully ===")
