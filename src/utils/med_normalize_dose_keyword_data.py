DOSE_METADATA = {
    "desconhecido": {"code": 0, "label": "desconhecido"},
    "milligram (mg)": {"code": 1, "label": "milligram (mg)"},
    "millilitre (mL)": {"code": 2, "label": "millilitre (mL)"},
    "gram (g)": {"code": 3, "label": "gram (g)"},
    "microgram (ug)": {"code": 4, "label": "microgram (ug)"},
    "dosage form ({DF})": {"code": 5, "label": "dosage form ({DF})"},
    "milligram per kilogram (mg/kg)": {"code": 6, "label": "milligram per kilogram (mg/kg)"},
    "milligram per square metre (mg/m2)": {"code": 7, "label": "milligram per square metre (mg/m2)"},
    "international unit ([iU])": {"code": 8, "label": "international unit ([iU])"},
    "drop (1/12 millilitre) ([drp])": {"code": 9, "label": "drop (1/12 millilitre) ([drp])"},
    "milligram per millilitre (mg/mL)": {"code": 10, "label": "milligram per millilitre (mg/mL)"},
    "milligram per decilitre (mg/dL)": {"code": 11, "label": "milligram per decilitre (mg/dL)"},
    "microgram per day (ug/d)": {"code": 12, "label": "microgram per day (ug/d)"},
    "milligram per kilogram per hour (mg/kg/h)": {"code": 13, "label": "milligram per kilogram per hour (mg/kg/h)"},
    "international unit per litre ([iU]/L)": {"code": 14, "label": "international unit per litre ([iU]/L)"},
    "milligram per 24 hour (mg/(24.h))": {"code": 15, "label": "milligram per 24 hour (mg/(24.h))"},
    "gram metre (g.m)": {"code": 16, "label": "gram metre (g.m)"},
    "gram per decilitre (g/dL)": {"code": 17, "label": "gram per decilitre (g/dL)"},
    "total ({total})": {"code": 18, "label": "total ({total})"},
    "metre (m)": {"code": 19, "label": "metre (m)"},
    "per milligram (/mg)": {"code": 20, "label": "per milligram (/mg)"},
    "millilitre per square metre (mL/m2)": {"code": 21, "label": "millilitre per square metre (mL/m2)"},
    "degree Kelvin (K)": {"code": 22, "label": "degree Kelvin (K)"},
    "enzyme unit (U)": {"code": 23, "label": "enzyme unit (U)"},
    "milliequivalent (meq)": {"code": 24, "label": "milliequivalent (meq)"},
    "milli-international unit (m[iU])": {"code": 25, "label": "milli-international unit (m[iU])"},
    "per international unit (/[iU])": {"code": 26, "label": "per international unit (/[iU])"},
    "international unit per kilogram ([iU]/kg)": {"code": 27, "label": "international unit per kilogram ([iU]/kg)"},
    "tablespoon (US) ([tbs_us])": {"code": 28, "label": "tablespoon (US) ([tbs_us])"},
    "milliequivalent per millilitre (meq/mL)": {"code": 29, "label": "milliequivalent per millilitre (meq/mL)"},
    "24 hour (24.h)": {"code": 30, "label": "24 hour (24.h)"},
    "nanogram per millilitre (ng/mL)": {"code": 31, "label": "nanogram per millilitre (ng/mL)"},
    "milligram per hour (mg/h)": {"code": 32, "label": "milligram per hour (mg/h)"},
    "kilo-international unit (k[iU])": {"code": 33, "label": "kilo-international unit (k[iU])"},
    "Maclagan unit ([mclg'U])": {"code": 34, "label": "Maclagan unit ([mclg'U])"},
    "milligram per 12 hour (mg/(12.h))": {"code": 35, "label": "milligram per 12 hour (mg/(12.h))"},
    "per cubic millimetre (/mm3)": {"code": 36, "label": "per cubic millimetre (/mm3)"},
    "microgram per kilogram per minute (ug/kg/min)": {"code": 37, "label": "microgram per kilogram per minute (ug/kg/min)"},
    "per day (/d)": {"code": 38, "label": "per day (/d)"},
    "milligram per kilogram per day (mg/kg/d)": {"code": 39, "label": "milligram per kilogram per day (mg/kg/d)"},
}

DOSE_UNIT_SPECS_DATA = [
    {"metadata_key": "milligram (mg)", "aliases": [
        "mg", "milligram", "milligrams", "milligrama", "miligramas", "milligram (mg)", "milligram ( mg )"
    ]},
    {"metadata_key": "millilitre (mL)", "aliases": [
        "ml", "millilitre", "milliliter", "millilitro", "millilitros", "milliliters",
        "millilitre (ml)", "milliliter (ml)"
    ]},
    {"metadata_key": "gram (g)", "aliases": [
        "g", "gram", "grams", "grama", "gramas", "gram (g)"
    ]},
    {"metadata_key": "microgram (ug)", "aliases": [
        "ug", "mcg", "μg", "microgram", "micrograms", "micrograma", "microgramas",
        "microgram (ug)", "microgram (mcg)"
    ]},
    {"metadata_key": "dosage form ({DF})", "aliases": [
        "dosage form", "dosage forms", "{df}", "df", "dosage form ({df})",
        "dosage-form", "dosage_form", "forma farmaceutica", "forma farmaceuticas",
        "forma farmacêutica", "forma farmacêuticas"
    ]},
    {"metadata_key": "milligram per kilogram (mg/kg)", "aliases": [
        "mg/kg", "mg / kg", "milligram per kilogram", "milligram per kg",
        "milligram per kilogram (mg/kg)", "milligram per kilogram ( mg / kg )",
        "milligrama por quilograma", "milligrama por kilogram", "mgkg"
    ]},
    {"metadata_key": "milligram per square metre (mg/m2)", "aliases": [
        "mg/m2", "mg / m2", "mg/m^2", "mg / m^2", "milligram per square metre",
        "milligram per square meter", "milligram per square metre (mg/m2)",
        "milligrama por metro quadrado", "milligram per square meter (mg/m2)"
    ]},
    {"metadata_key": "international unit ([iU])", "aliases": [
        "iu", "u", "international unit", "international units",
        "international unit (iu)", "international unit ([iu])", "international unit ([iU])",
        "unidade internacional", "unidades internacionais"
    ]},
    {"metadata_key": "drop (1/12 millilitre) ([drp])", "aliases": [
        "drop", "drops", "drp", "drop (1/12 millilitre) ([drp])",
        "drop (1/12 milliliter) ([drp])", "gota", "gotas"
    ]},
    {"metadata_key": "milligram per millilitre (mg/mL)", "aliases": [
        "mg/ml", "mg / ml", "mg per ml", "milligram per millilitre",
        "milligram per millilitre (mg/ml)", "milligram per milliliter",
        "milligram per milliliter (mg/ml)"
    ]},
    {"metadata_key": "milligram per decilitre (mg/dL)", "aliases": [
        "mg/dl", "mg / dl", "mg per dl", "milligram per decilitre",
        "milligram per deciliter", "milligram per decilitre (mg/dl)"
    ]},
    {"metadata_key": "microgram per day (ug/d)", "aliases": [
        "ug/d", "ug / d", "ug per d", "ug/day", "microgram per day",
        "microgram per day (ug/d)", "microgram per dia"
    ]},
    {"metadata_key": "milligram per kilogram per hour (mg/kg/h)", "aliases": [
        "mg/kg/h", "mg/kg/hr", "mg / kg / h", "mg / kg / hr",
        "milligram per kilogram per hour", "milligram per kilogram per hour (mg/kg/h)"
    ]},
    {"metadata_key": "international unit per litre ([iU]/L)", "aliases": [
        "iu/l", "iu per l", "iu / l", "international unit per litre",
        "international unit per liter", "international unit per litre ([iu]/l)"
    ]},
    {"metadata_key": "milligram per 24 hour (mg/(24.h))", "aliases": [
        "mg/(24.h)", "mg/(24h)", "mg / (24.h)", "mg / (24 h)", "mg per 24 hour",
        "milligram per 24 hour", "milligram per 24 hour (mg/(24.h))"
    ]},
    {"metadata_key": "gram metre (g.m)", "aliases": [
        "g.m", "g * m", "gram metre", "gram meter", "gram metro", "gram metre (g.m)"
    ]},
    {"metadata_key": "gram per decilitre (g/dL)", "aliases": [
        "g/dl", "g / dl", "gram per decilitre", "gram per deciliter", "gram per decilitre (g/dl)"
    ]},
    {"metadata_key": "total ({total})", "aliases": [
        "total", "total ({total})", "{total}", "total ( {total} )"
    ]},
    {"metadata_key": "metre (m)", "aliases": [
        "m", "metre", "meter", "metro", "metre (m)"
    ]},
    {"metadata_key": "per milligram (/mg)", "aliases": [
        "/mg", "per mg", "per milligram", "per milligram (/mg)"
    ]},
    {"metadata_key": "millilitre per square metre (mL/m2)", "aliases": [
        "ml/m2", "ml / m2", "millilitre per square metre",
        "millilitre per square meter", "millilitre per square metre (ml/m2)"
    ]},
    {"metadata_key": "degree Kelvin (K)", "aliases": [
        "kelvin", "degree kelvin", "k", "degree kelvin (k)"
    ]},
    {"metadata_key": "enzyme unit (U)", "aliases": [
        "u", "enzyme unit", "enzyme unit (u)", "enzyme unit (u )", "enzymatic unit"
    ]},
    {"metadata_key": "milliequivalent (meq)", "aliases": [
        "meq", "milliequivalent", "milliequivalente", "milliequivalentes", "milliequivalent (meq)"
    ]},
    {"metadata_key": "milli-international unit (m[iU])", "aliases": [
        "m[iu]", "milli-international unit", "milli international unit",
        "milli-international unit (m[iu])", "miu"
    ]},
    {"metadata_key": "per international unit (/[iU])", "aliases": [
        "/[iu]", "/ iu", "per international unit", "per international unit (/[iu])"
    ]},
    {"metadata_key": "international unit per kilogram ([iU]/kg)", "aliases": [
        "[iu]/kg", "iu/kg", "international unit per kilogram",
        "international unit per kilogram ([iu]/kg)", "international unit per kilogram ([iu]/ kg)"
    ]},
    {"metadata_key": "tablespoon (US) ([tbs_us])", "aliases": [
        "[tbs_us]", "tablespoon", "tablespoon (us)", "tablespoon (us) ([tbs_us])", "tbsp"
    ]},
    {"metadata_key": "milliequivalent per millilitre (meq/mL)", "aliases": [
        "meq/ml", "meq / ml", "milliequivalent per millilitre", "milliequivalent per milliliter",
        "milliequivalent per millilitre (meq/ml)"
    ]},
    {"metadata_key": "24 hour (24.h)", "aliases": [
        "24.h", "24 h", "24 hour", "24 hour (24.h)", "(24.h)"
    ]},
    {"metadata_key": "nanogram per millilitre (ng/mL)", "aliases": [
        "ng/ml", "ng / ml", "nanogram per millilitre", "nanogram per milliliter",
        "nanogram per millilitre (ng/ml)"
    ]},
    {"metadata_key": "milligram per hour (mg/h)", "aliases": [
        "mg/h", "mg / h", "milligram per hour", "milligram per hora", "milligram per hour (mg/h)"
    ]},
    {"metadata_key": "kilo-international unit (k[iU])", "aliases": [
        "k[iu]", "kilointernational unit", "kilo international unit", "kilo-international unit (k[iu])"
    ]},
    {"metadata_key": "Maclagan unit ([mclg'U])", "aliases": [
        "[mclg'u]", "maclagan unit", "maclagan unit ([mclg'u])"
    ]},
    {"metadata_key": "milligram per 12 hour (mg/(12.h))", "aliases": [
        "mg/(12.h)", "mg/(12h)", "mg / (12.h)", "milligram per 12 hour", "milligram per 12 hour (mg/(12.h))"
    ]},
    {"metadata_key": "per cubic millimetre (/mm3)", "aliases": [
        "/mm3", "per mm3", "per cubic millimetre", "per cubic millimeter", "per cubic millimetre (/mm3)"
    ]},
    {"metadata_key": "microgram per kilogram per minute (ug/kg/min)", "aliases": [
        "ug/kg/min", "ug/kg/minute", "ug / kg / min", "microgram per kilogram per minute",
        "microgram per kilogram per minute (ug/kg/min)"
    ]},
    {"metadata_key": "per day (/d)", "aliases": [
        "/d", "per d", "per dia", "per day", "per day (/d)"
    ]},
    {"metadata_key": "milligram per kilogram per day (mg/kg/d)", "aliases": [
        "mg/kg/d", "mg/kg/day", "mg / kg / d", "milligram per kilogram per day",
        "milligram per kilogram per day (mg/kg/d)"
    ]},
]

UNKNOWN_TOKENS = [
    "desconhecido",
    "desconhecida",
    "nao informado",
    "não informado",
    "nao informada",
    "não informada",
    "não sei",
    "nao sei",
    "nao reportado",
    "não reportado",
    "outro",
    "outros",
    "outras",
    "unknown",
]

