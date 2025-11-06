import json
from typing import Dict, List, Self


class EntitiesIndex:
    """
    Represents the state of an ontology while the LLM is building it.
    
    It includes lists of classes, properties and individuals returned by the *getter* tools of `tools_interface`.
    In particular it provides: 
     - `tbox_classes`: `{"AZ493": {"name": "AZ493", "subclassOf": ["HeadPhones"], "role": ["A product class description."]},...}`.
     - `tbox_prop`: `{"hasID": {"name": "hasID", "role": ["Identifier of a product (literal).",...]},...}`.
     - `abox_ind`: `{"Yellow": {"name": "Yellow", "role": ["the root class",..], "classes": ["Color",...], "properties": [["hasValue", "#FFFF00"], ...]},...}`.
    
    It also provides methods to serialize and deserialize data into file.
    """
    
    # The dictionary keys to represent the ID and brief comment of an entity in the ontology. These are also used in th tools definitions.
    P_NAME = "name"
    P_DESCRIPTION = "role"
    
    def __init__(self):
        """
        Initialize an empty EntitiesIndex.
        """
        self.tbox_classes: Dict[str, Dict] = {}
        self.tbox_prop: Dict[str, Dict] = {}
        self.abox_ind: Dict[str, Dict] = {}
    

    def serialize(self, filepath: str) -> None:
        """
        Save the current EntitiesIndex to a JSON file.

        Args:
            filepath (str): Path to the JSON file where the EntitiesIndex will be saved.
        """
        data = {
            "tbox_classes": self.tbox_classes,
            "tbox_prop": self.tbox_prop,
            "abox_ind": self.abox_ind
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"EntitiesIndex serialized to {filepath}")


    def deserialize(self, filepath: str) -> None:
        """
        Load `self` EntitiesIndex data from a JSON file.

        Args:
            filepath (str): Path to the JSON file containing the EntitiesIndex data.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.tbox_classes = data.get("tbox_classes", {})
        self.tbox_prop = data.get("tbox_prop", {})
        self.abox_ind = data.get("abox_ind", {})
        print(f"EntitiesIndex deserialized from {filepath}")
    
    
    def getClassEntities(self) -> Dict[str, List[str]]: 
        """
        Return all the classes in the ontology represented only by their name and very brief descriptions.
        It does not return the class definition.

        Returns:
            Dict[str, List[str]]: a dictionary as `{"class_name": ["description1", "description2",...], ...}`
        """
        out = {}
        for c in self.tbox_classes.values():
            out[c[self.P_NAME]] = c[self.P_DESCRIPTION]
        return out
   
    
    def getPropertyEntities(self) -> Dict[str, List[str]]: 
        """
        Return all the properties in the ontology represented only by their name and very brief descriptions.
        It does not return the properties definition.

        Returns:
            Dict[str, List[str]]: a dictionary as `{"property_name": ["description1", "description2",...], ...}`
        """
        out = {}
        for p in self.tbox_prop.values():
            out[p[self.P_NAME]] = p[self.P_DESCRIPTION]
        return out
   
    
    def getIndividualEntities(self) -> Dict[str, List[str]]: 
        """
        Return all the individuals in the ontology represented only by their name and very brief descriptions.
        It does not return the individuals definition.

        Returns:
            Dict[str, List[str]]: a dictionary as `{"individual_name": ["description1", "description2",...], ...}`
        """
        out = {}
        for p in self.tbox_prop.values():
            out[p[self.P_NAME]] = p[self.P_DESCRIPTION]
        return out
        
        
    def __str__(self):
        """
        Return a formatted string representation of the ontology state.
        """
        return f"\t ***** Classes:\n {self.tbox_classes}\n\t ***** Properties:\n {self.tbox_prop}\n\t ***** Individuals:\n {self.abox_ind}\n"
    
    
    @staticmethod
    def fromFile(filepath: str) -> Self:
        """
        Create and return an new EntitiesIndex instance from a JSON file.

        Args:
            filepath (str): Path to the JSON file containing the EntitiesIndex data.

        Returns:
            EntitiesIndex: A new EntitiesIndex instance populated with data from the file.
        """
        entities_index = EntitiesIndex()
        entities_index.deserialize(filepath)
        return entities_index
