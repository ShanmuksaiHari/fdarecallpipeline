"""
The Databricks notebook cannot import src/hazard.py, so it carries its own
copy of the hazard rules. This test fails if the two copies ever disagree.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import hazard

NOTEBOOK = os.path.join(
    os.path.dirname(__file__), "..", "databricks", "fda_recalls_silver.py"
)

SAMPLES = [
    None,
    "",
    "Product contains undeclared milk",
    "Label does not declare soy",
    "Peanuts not declared on label",
    "Ingredient statement does not list wheat",
    "Contaminated with Listeria monocytogenes",
    "Possible Salmonella contamination",
    "Risk of E. coli contamination",
    "May contain pieces of metal",
    "Possible plastic fragments",
    "Contains foreign material",
    "Undeclared milk and possible Salmonella contamination",
    "Product recalled due to mislabeling",
]


def load_notebook_function():
    tree = ast.parse(open(NOTEBOOK).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "categorize_hazard":
            namespace = {}
            exec(compile(ast.Module([node], []), NOTEBOOK, "exec"), namespace)
            return namespace["categorize_hazard"]
    raise AssertionError("categorize_hazard not found in the notebook")


def test_notebook_and_src_agree():
    notebook_fn = load_notebook_function()
    for text in SAMPLES:
        assert notebook_fn(text) == hazard.categorize_hazard(text), text
