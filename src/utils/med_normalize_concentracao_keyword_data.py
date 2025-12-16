CONCENTRACAO_METADATA = {
    "desconhecido": {"code": 0, "label": "desconhecido"},
    "milligram (mg)": {"code": 1, "label": "milligram (mg)"},
    "gram (g)": {"code": 2, "label": "gram (g)"},
    "microgram (ug)": {"code": 3, "label": "microgram (ug)"},
    "millilitre (mL)": {"code": 4, "label": "millilitre (mL)"},
    "percent (%)": {"code": 5, "label": "percent (%)"},
    "milligram per millilitre (mg/mL)": {"code": 6, "label": "milligram per millilitre (mg/mL)"},
    "milligram per milligram (mg/mg)": {"code": 7, "label": "milligram per milligram (mg/mg)"},
    "milligram per gram (mg/g)": {"code": 8, "label": "milligram per gram (mg/g)"},
    "gram per millilitre (g/mL)": {"code": 9, "label": "gram per millilitre (g/mL)"},
}

UNIT_SPECS_DATA = [
    {
        "metadata_key": "milligram (mg)",
        "aliases": [
            "mg",
            "milligram",
            "milligrams",
            "milligrama",
            "miligramas",
        ],
    },
    {
        "metadata_key": "gram (g)",
        "aliases": ["g", "gram", "grams", "grama", "gramas"],
    },
    {
        "metadata_key": "microgram (ug)",
        "aliases": [
            "ug",
            "mcg",
            "μg",
            "microgram",
            "micrograms",
            "micrograma",
            "microgramas",
        ],
    },
    {
        "metadata_key": "millilitre (mL)",
        "aliases": [
            "ml",
            "millilitre",
            "millilitro",
            "mililitro",
            "millilitros",
            "mililitros",
        ],
    },
    {
        "metadata_key": "percent (%)",
        "aliases": ["%", "percent", "porcento", "percentual"],
    },
    {
        "metadata_key": "milligram per millilitre (mg/mL)",
        "aliases": [
            "mg/ml",
            "mg/mL",
            "mgpor ml",
            "mg por ml",
            "mgperml",
        ],
    },
    {
        "metadata_key": "milligram per milligram (mg/mg)",
        "aliases": ["mg/mg"],
    },
    {
        "metadata_key": "milligram per gram (mg/g)",
        "aliases": ["mg/g"],
    },
    {
        "metadata_key": "gram per millilitre (g/mL)",
        "aliases": ["g/ml", "g/mL"],
    },
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

