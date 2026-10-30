"""Prepara um ZIP para envio manual à pesquisadora. Não envia email."""
from pathlib import Path
import hashlib
import json
from zipfile import ZipFile, ZIP_DEFLATED


def prepare(directory=Path(__file__).resolve().parent):
    directory=Path(directory)
    output=directory/'output'
    files=[
        'fat_analytical_dipirona_2019_2025.csv', 'dicionario_dados.csv',
        'resumo_notificacoes_ano.csv', 'resumo_medicamentos.csv',
        'resumo_eventos_adversos.csv', 'manifesto.json',
    ]
    for name in files:
        if not (output/name).is_file():
            raise FileNotFoundError(f'Gere a base antes de preparar a entrega: {output/name}')
    if not (directory/'LEIA_ME_ISABEL.txt').is_file():
        raise FileNotFoundError('Guia de uso não encontrado.')
    manifest=json.loads((output/'manifesto.json').read_text())
    actual=hashlib.sha256((output/files[0]).read_bytes()).hexdigest()
    if actual!=manifest['sha256_csv']:
        raise ValueError('O CSV difere do manifesto. Execute novamente a geração e revise os resultados.')
    destination=directory/'entrega'
    destination.mkdir(exist_ok=True)
    path=destination/'dipirona_2019_2025_para_isabel.zip'
    with ZipFile(path,'w',compression=ZIP_DEFLATED) as archive:
        for name in files:
            archive.write(output/name,name)
        archive.write(directory/'LEIA_ME_ISABEL.txt','LEIA_ME_ISABEL.txt')
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist())==set(files+['LEIA_ME_ISABEL.txt'])
    print(path)
    return path


if __name__=='__main__':
    prepare()
