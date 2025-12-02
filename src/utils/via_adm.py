import pandas as pd
from unidecode import unidecode

def normalizar_via_administracao(value) -> str:
    """
    Normaliza a via de administração para os códigos:
      Implant, Inhal, Instill, N, O, P, R, SL, TD, V
    ou 'desconhecido'.
    """

    # ---------- 1) Pré-tratamento / missing ----------
    if pd.isna(value):
        return "desconhecido"

    s = unidecode(str(value)).strip().lower()
    s = " ".join(s.split())

    # atalhos óbvios de missing
    short_unknown = {
        "none", "nan", "na", "n/a",
        "ni", "n.i.", "n/i", "n.i", "nf", "nq",
        "unk", "unknown",
        "sem informacao", "sem informacao.",
        "sem informacao de via", "sem informacoes",
        "nao se aplica", "não se aplica",
        "route of administration not applicable",
        "nao identificado", "não identificado",
        "sem informacao de administracao",
    }
    if s == "" or s in short_unknown:
        return "desconhecido"

    # unknown / outra / não informado / E2B
    if any(
        k in s
        for k in (
            "unknown",
            "desconhecid",      # desconhecido / desconhecida
            "deconhecido",
            "descohecido",
            "rota desconhecida",
            "via desconhecida",
            "e2b r2 code: 065",  # unknown
            "e2b r2 code: 050",  # other
            "nao informado",
            "não informado",
            "nao informada",
            "não informada",
            "nao infomado",
            "nao infomada",
            "nao perguntado",
            "não perguntado",
            "nao questionado",
            "não questionado",
            "nao relatad",
            "não relatad",
            "nao reportad",
            "não reportad",
            "nao aplicavel",
            "não aplicavel",
            "nao especificado a via de administracao",
            "via de administracao nao informada",
            "via de administracao nao especificada",
            "via de administracao do paciente - outra",
            "route of administration not applicable",
            "rota desconhecida",
        )
    ):
        return "desconhecido"

    # exposições, não administração clássica
    if any(
        k in s
        for k in (
            "transplacent",          # transplacental, transplacentaria, etc.
            "transmam",              # transmammary, transmamaria
            "via leite materno",
            "exposicao pelo leite",
            "exposição pelo leite",
            "leite materno",
            "uso do paciente",
            "uso proprio do paciente",
            "product taken by father",
            "product taken by male partner",
            "medicamento utilizado pela mae",
            "medicamento utilizado pelo pai",
        )
    ):
        return "desconhecido"

    # ---------- 2) Combinações oral + parenteral: prioriza P ----------
    # se texto fala de algo oral + venoso/subcutâneo/etc, vamos classificar como P
    has_oral = "oral" in s or "via oral" in s or s in {"vo", "v.o", "v.o.", "vo,"}
    has_parenteral_token = any(
        k in s
        for k in (
            "intraven", "venos", "endoven", "enoven", "intaven",
            "intramus", "subcut", "s.c", "hipodermoclise",
            "epidural", "peridural", "raquid", "subaracnoid",
        )
    )
    if has_oral and has_parenteral_token:
        return "P"
    if any(k in s for k in ("transplacent", "transmam")):
        return "P"

    # ---------- 3) Inalação / respiratória (Inhal) ----------
    inhal_keywords = (
        "inhal",            # inhalation
        "inala",            # inalação, inalatorio, inalatoria
        "aerosol", "aerossol",
        "respiratoria", "respiratória",
        "respiracao inalat", "respiracao inalat",
        "uso inalatorio", "uso inalatório",
        "via inalat", "inalador",
        "oral inhalation", "oral inhalation",
        "uso inalatorio oral",
        "uso inalatorio por via oral",
        "uso inalatorio (oral)",
        "inalatorio oral", "inalatorio via oral",
        "respiratory (inhalation)",
    )
    if any(k in s for k in inhal_keywords):
        return "Inhal"

    # ---------- 4) Sublingual / bucal / oromucosa (SL) ----------
    if (
        s in {"sl", "s.l", "s.l.", "s l", "sublingually"}
        or any(k in s for k in ("sublingual", "buccal", "bucal", "oromuc"))
    ):
        return "SL"

    # ---------- 5) Nasal (N) ----------
    # cuidado para não pegar nasoENTERAL (enteral/sonda)
    if (
        "nasal" in s
        or "via nasal" in s
        or "nasal use" in s
        or "usado no nariz" in s
        or "vick inalado no nariz" in s
    ):
        # se é claramente nasogastrica / nasoenteral => cai depois em O
        if not any(k in s for k in ("nasogastr", "nasoenter", "nasoent", "nasoduodenal")):
            return "N"

    # ---------- 6) Vaginal (V) ----------
    if "vaginal" in s or "intravaginal" in s or "uso vaginal" in s:
        return "V"

    # ---------- 7) Oftálmica / ocular / otológica / auricular (Instill) ----------
    if any(
        k in s
        for k in (
            "oftalm",        # oftalmica, oftalmico, oftalmologica...
            "ophthalm",      # ophthalmic
            "colirio", "colírio",
            "ocular", "uso ocular", "topico ocular", "tópico ocular",
            "otolog", "otologic", "otológico", "otologica",
            "auricul", "auricular",
            "otologic", "otological",
        )
    ):
        return "Instill"

    # ---------- 8) Retal (R) ----------
    if "retal" in s or "rectal" in s or s in {"v.r", "v.r.", "via retal", "via retal"}:
        return "R"

    # ---------- 9) Cutânea / tópica / dermatológica / transdérmica (TD) ----------
    if any(
        k in s
        for k in (
            "cutanea", "cutaneo", "cutâneo", "cutaneous",
            "uso cutaneo", "uso cutâneo",
            "uso topico", "uso tópico",
            "topico", "tópico", "topical",
            "dermatolog", "couro cabeludo",
            "percutan",     # percutanea
            "transderm", "tranderm", "trasderm", "transcutanea",
            "iontophoresis",
        )
    ):
        return "TD"

    # ---------- 10) Implante / intra-uterino (Implant) ----------
    if any(
        k in s
        for k in (
            "implant",
            "intra uterin", "intra-uterin",
            "intrauterin",
        )
    ):
        return "Implant"

    # ---------- 11) ORAL / ENTERAL / SONDA (O) ----------
    # enteral / gastrica / nasogastrica / nasoenteral / sonda etc.
    enteral_keywords = (
        "enteral", "gastroenter", "gastroent", "gastrostom", "gastrostomia",
        "sonda", "sne", "gtt",             # sonda / sonda nasoenteral / sonda GTT
        "nasogastr", "nasogástr", "orogastr", "oroenter", "nasoduodenal",
        "nasoenter", "nasoent",
        "jejunostom", "jejunostomia",
        "gastric use", "via gastrica", "via gástrica",
        "gastrostom", "gastro", "gastrostomia",
        "nasoenteric tube", "nasogastric tube",
    )
    if any(k in s for k in enteral_keywords):
        return "O"

    # oral puro (sem sublingual/oromucosa, sem inalação – já tratados acima)
    if ("oral" in s or s in {"vo", "v.o", "v.o.", "vo,", "orla", "0ral", "oal", "via ora"}) and not any(
        k in s for k in ("sublingual", "buccal", "bucal", "oromuc")
    ):
        return "O"

    # ---------- 12) Parenteral (P) ----------
    # engloba: IV/EV, IM, SC, hipodermoclise, intra-arterial, intratecal, epidural, raqui etc.
    parenteral_keywords = (
        # venoso / endovenoso / intravenoso com N variações
        "intraven", "intaven", "intraveno", "venos", "endoven", "enoven",
        "endven", "envoven", "endove", "endo venos",
        "iv ", " iv", "i.v", "i.v.", "iv.", " iv-", " iv/", "iv infusao", "iv infusao",
        "ev ", " ev", "e.v", "e.v.", "ev.", "ev-", "evb", "evi",
        # musculo / subcutâneo
        "intramus", "intra musc", "intra-muscular",
        " i.m", "i.m ", "i.m.", " im ", "im ", "im/",
        "subcut", "sub cut", "sub-cut", "s.c", "s.c.", "sc ", " sc", "sc.",
        "hipodermoclise", "hipoder",
        "subderm", "subdérm",
        "subaracnoid", "subaracnoide", "subaracnóide",
        # injeção / infusão
        "injetavel", "injetável", "inetavel", "inejtavel",
        "injection", "injecao", "injeção", "injecao nao especificada",
        "infusao", "infusão", "infusion",
        "gotejamento", "drip", "bolus", "bomba de infusao", "bomba de infusão",
        # neuraxial / intra-meningea / intratecal
        "epidural", "peridural", "raquid", "raqui", "espinhal",
        "intratec", "intrathec", "intramenin", "intrarraquid",
        "punçao lombar", "puncao lombar", "punção lombar",
        # intra-arterial / intracard / etc.
        "intracard", "intracoron", "intra-arterial", "intra arterial", "intraarterial",
        "intraperiton", "intracavitar", "intracavern", "intrapericard", "intravesic",
        # outros parenterais
        "hemodial", "hemodiálise", "extracorpore", "extracorpora",
        "cateter venoso", "acesso venoso", "acesso periferico",
        "port-cath", "porth cath", "cvc-ti",
        "intravitre", "intravitreal", "intra vitrea",
        "intralesion", "infiltracao", "infiltração",
        "intrapericardial", "intravesical",
        "parenteral", "e2b r2 code: 051 - parenteral",
    )
    if any(k in s for k in parenteral_keywords):
        return "P"

    if s in {"iv", "i.v", "i.v.", "iv.", "|v", " vi", "vd"}:
        return "P"
    if s in {"ev", "e.v", "e.v.", "ev.", "ve"}:
        return "P"
    if s in {"im", "i.m", "i m"}:
        return "P"
    if s in {"sc", "s.c", "s.c."}:
        return "P"

    # ---------- 13) fallback ----------
    # Ex.: transplacental / transmammary / extracorporea etc. que não queremos mapear para via clássica
    return "desconhecido"
