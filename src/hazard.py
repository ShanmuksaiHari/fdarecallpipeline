def is_allergen_recall(reason_text):
    text = reason_text.lower()
    if "undeclared" in text or "does not declare" in text or "do not declare" in text or "not declared" in text or "does not list" in text:
        return True
    return False


def is_pathogen_recall(reason_text):
    text = reason_text.lower()
    pathogens = ["salmonella", "listeria", "botulinum", "e. coli", "cyclospora", "patulin", "giardia", "norovirus"]
    if any(p in text for p in pathogens):
        return True
    return False


def is_foreign_material_recall(reason_text):
    text = reason_text.lower()
    if "foreign object" in text or "foreign material" in text or "metal" in text or "plastic" in text or "glass" in text:
        return True
    return False


def categorize_hazard(reason_text):
    if is_allergen_recall(reason_text):
        return "allergen"
    if is_pathogen_recall(reason_text):
        return "pathogen"
    if is_foreign_material_recall(reason_text):
        return "foreign_material"
    return "other"
