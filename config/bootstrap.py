import sys
from pathlib import Path


def add_src_to_sys_path(markers=(".project-root", "README.md", ".git")):
    """
    Adiciona <root>/src ao sys.path. Procura marcadores a partir do cwd e do
    diretório deste arquivo, para funcionar em notebooks mesmo com cwd fora da
    raiz do projeto.
    """
    start_points = [Path().resolve()]
    
    # Tenta obter __file__ de várias formas (funciona com %run em notebooks)
    try:
        # Este arquivo está em config/, então o projeto root é o parent do config/
        config_dir = Path(__file__).resolve().parent
        project_root = config_dir.parent
        start_points.insert(0, project_root)  # Prioriza o caminho do arquivo
        start_points.append(config_dir)
    except NameError:
        pass

    seen = set()
    for start in start_points:
        for parent in [start] + list(start.parents):
            if parent in seen:
                continue
            seen.add(parent)
            if any((parent / marker).exists() for marker in markers):
                src_path = parent / "src"
                if src_path.exists() and str(src_path) not in sys.path:
                    sys.path.insert(0, str(src_path))
                return parent
    raise FileNotFoundError("Could not find project root to add src to sys.path.")


add_src_to_sys_path()