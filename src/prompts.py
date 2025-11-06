# The generic prompt to describe an OWL ontology.
GENERIC_ONTO_PROMPT = f"""\
## Context
You are an **OWL-DL ontology expert**. Build an ontology from the data below.

An ontology consists of:
- **TBox**
  - **Classes**: group individuals (∈); may have subclasses (⊑).
  - **Properties**: link individuals or individuals to literals as tuples:  
    `(subject, property, object)` or `(subject, property, literal)`.  
    Prefer linking individuals over literals.

- **ABox**
  - **Individuals**: belong to classes and have properties with other individuals or literals.
  - **Literals**: are data primitives (e.g., str, int, etc.).

Each class, property, and individual name is a unique identifier.

## Task
From the provided data:

1. Define relevant **classes**.  
2. Define **properties** linking data.  
3. Define **individuals** with their classes and properties.  

Unify equivalent terms (e.g., `Kg` = `kg`, `MiniSplit` = `Mini Split`).  
Do **not** omit any data.
"""


# The prompt describing of how to extract information from the `product_data.json` file (given as input parameter).
def product_tree_2_onto(product_data) -> str:
    return f"""\
{GENERIC_ONTO_PROMPT}

## Scenario
The data describes a **product taxonomy** and its features.

- **Classes**: represent product categories (e.g., `Retaining Walls`).  
  All should be subclasses of a top-l.
- **Properties**: represent product features (e.g., `Block weight (kg)`, `Color`).  
  Generalize similar features for consistency across products.
- **Individuals**: represent specific products (tree leaves with an `ID`),  
  each classified under its category and linked to its features.

The ontology should be derived from the following JSON-like product tree:
```{product_data}```
"""



# The prompt describing of how to extract information from the `logistics.json` file (given as input parameter).
def paragraph_2_onto(paragraphs) -> str:
    return f"""\
{GENERIC_ONTO_PROMPT}

## Scenario
The data contains **logistics details** about products already defined as ontology individuals.

- **Classes**: logistics concepts, all subclasses of **`Logistic`**.  
- **Properties**: link **Product** individuals with logistics-related individuals or literals (e.g., cost, location, storage time, weight, arrangement).  
- **Individuals/Literals**: represent logistics metrics extracted from the data.

Focus on defining new **properties**; derive related classes and individuals where needed.  
Ensure the ontology supports reasoning between products and logistics entities.

**Examples**  
- `(MiniEcoRing, averageStorageTimeDay, 10)` → `MiniEcoRing ∈ Product`  
- `(GrecCurb100, dailyStorageCostEuro, 1.25)` → `GrecCurb100 ∈ Product`  
- `(Warehouse, hasSector, SectorA)`, `(SectorA, produces, EcoRing)` → `SectorA ∈ Logistic`, `EcoRing ∈ RetainingWalls ⊑ Product`

Use the following text to infer ontology elements:
```{paragraphs}```.
"""



# The prompt describing of how to extract an OWl file from the an `EntitiesIndex` object (given as input parameter).
def make_owl(entities_index) -> str:
    return f"""\
## Scenario
Use the following information to build a complete **OWL ontology** (RDF/XML format) compatible with **Protégé**.
To unify terms, use symmetric properties to link equivalent individuals (e.g., `describedAlsoBy(WavePave, WavePave_1074)`, `describedAlsoBy(EcoRing, EcoRing_2298)`, etc.).

Include:
1. **Classes** with their names, descriptive roles, and subclasses.
2. **Properties** with their names and roles.
3. **Individuals** with their names, classifications, properties, roles.

### Input Data
- **Classes**  
  ```{entities_index.tbox_classes}```
  
- **Property**
  ```{entities_index.tbox_prop}```
  
- **Individual**
  ```{entities_index.abox_ind}```
"""


# The prompt describing of how to response to user's questions.
def explore_onto():
    return """\
Using the ontology's semantic representation:

- Create **SPARQL queries** to explore the ontology data and answer the user's question.  
- Provide only the query and its result — **do not propose other actions**.  
- Briefly explain the query used in a **concise** manner.
"""
