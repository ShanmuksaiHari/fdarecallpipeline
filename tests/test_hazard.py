import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hazard import (
    categorize_hazard,
    is_allergen_recall,
    is_foreign_material_recall,
    is_pathogen_recall,
)


# --- allergen ---

def test_allergen_undeclared_milk():
    assert is_allergen_recall("Product contains undeclared milk")


def test_allergen_does_not_declare():
    assert is_allergen_recall("Label does not declare soy")


def test_allergen_not_declared_phrasing():
    assert is_allergen_recall("Peanuts not declared on label")


def test_allergen_does_not_list():
    assert is_allergen_recall("Ingredient statement does not list wheat")


# --- pathogen ---

def test_pathogen_salmonella():
    assert is_pathogen_recall("Product may be contaminated with Salmonella")


def test_pathogen_listeria():
    assert is_pathogen_recall("Potential Listeria monocytogenes contamination")


def test_pathogen_e_coli():
    assert is_pathogen_recall("Risk of E. coli contamination")


def test_pathogen_is_case_insensitive():
    assert is_pathogen_recall("SALMONELLA risk identified")


# --- foreign material ---

def test_foreign_material_metal():
    assert is_foreign_material_recall("Product may contain pieces of metal")


def test_foreign_material_plastic():
    assert is_foreign_material_recall("Possible plastic fragments in product")


def test_foreign_material_glass():
    assert is_foreign_material_recall("Product may contain glass")


# --- categorize_hazard: full routing ---

def test_categorize_allergen():
    assert categorize_hazard("Contains undeclared egg") == "allergen"


def test_categorize_pathogen():
    assert categorize_hazard("Contaminated with Listeria") == "pathogen"


def test_categorize_foreign_material():
    assert categorize_hazard("Contains foreign material - metal") == "foreign_material"


def test_categorize_other_fallback():
    assert categorize_hazard("Product recalled due to mislabeling") == "other"


def test_categorize_empty_string():
    assert categorize_hazard("") == "other"


def test_categorize_precedence_allergen_before_pathogen():
    # Known limitation: if a reason mentions both an undeclared allergen
    # and a pathogen, it is labeled allergen because that rule runs first.
    # This test pins that behavior so a change to it is deliberate.
    text = "Undeclared milk and possible Salmonella contamination"
    assert categorize_hazard(text) == "allergen"


def test_categorize_none_is_other():
    assert categorize_hazard(None) == "other"
