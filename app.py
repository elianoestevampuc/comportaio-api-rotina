from flask_openapi3 import OpenAPI, Info, Tag
from flask import redirect
from urllib.parse import unquote
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta

from model import Session, RotinaDia
from logger import logger
from schemas import *
from flask_cors import CORS

info = Info(title="Comporta.io API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

# definindo tags
home_tag = Tag(name="Documentação", description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
rotinadia_tag = Tag(name="Rotina Dia", description="Adição, visualização e remoção de rotina dia à base.")


@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação.
    """
    return redirect('/openapi')


@app.post('/rotinadia', tags=[rotinadia_tag],
          responses={"200": RotinaDiaSchema, "404": ErrorSchema})
def add_rotinadia(form: RotinaDiaSchema):
    """Adiciona uma nova rotina dia à uma pessoa.

    Retorna uma representação das pessoas e rotinas padrao associados.
    """
    print("Adiciona uma nova rotina dia à uma pessoa.");
    print("form.data_execucao", form);

    logger.debug(f"Adicionando rotinas dia a pessoa #{form.id_pessoa}")
    # criando conexão com a base
    session = Session()
    
    # Verificar se a rotina dia já existe
    # Parametros: hora, id_evento, id_pessoa e data_execucao
    rotina_dia = session.query(RotinaDia).filter(RotinaDia.hora == form.hora , 
                                                RotinaDia.id_pessoa == form.id_pessoa , 
                                                RotinaDia.id_evento == form.id_evento ,
                                                extract('day', RotinaDia.data_execucao) == form.data_execucao.day ,
                                                extract('month', RotinaDia.data_execucao) == form.data_execucao.month ,
                                                extract('year', RotinaDia.data_execucao) == form.data_execucao.year).first()

    if not rotina_dia:
        # criando a rotina dia
        rotina_dia = RotinaDia(form.hora, form.id_evento, form.id_pessoa, form.executou, form.data_execucao)
        # adicionando a rotina padrão a pessoa
        session.add(rotina_dia)
    else:
        rotina_dia.executou = form.executou
        session.merge(rotina_dia)

    session.commit()
    logger.debug(f"Adicionado rotina dia a pessoa #{form.id_pessoa}")

    # retorna a representação de rotina_dia
    return apresenta_rotinadia(rotina_dia), 200


@app.delete('/rotinadia', tags=[rotinadia_tag],
            responses={"200": RotinaDiaDelSchema, "404": ErrorSchema})
def del_rotinadia(query: RotinaDiaBuscaIdSchema):
    """Deleta uma rotina dia a partir do id.

    Retorna uma mensagem de confirmação da remoção.
    """
    rotinadia_id = query.id
    logger.debug(f"Deletando dados sobre rotina dia #{rotinadia_id}")
    # criando conexão com a base
    session = Session()
    # fazendo a remoção
    count = session.query(RotinaDia).filter(RotinaDia.id == rotinadia_id).delete()
    session.commit()

    if count:
        # retorna a representação da mensagem de confirmação
        logger.debug(f"Deletado rotina dia #{rotinadia_id}")
        return {"mesage": "Rotina Dia removido", "id": rotinadia_id}
    else:
        # se a rotina padrão não foi encontrado
        error_msg = "Rotina Dia não encontrada na base :/"
        logger.warning(f"Erro ao deletar rotina dia #'{rotinadia_id}', {error_msg}")
        return {"mesage": error_msg}, 404


@app.post('/rotinasdia', tags=[rotinadia_tag],
         responses={"200": ListagemRotinasDiaSchema, "404": ErrorSchema})
def get_rotinasdia(form: RotinaDiaBuscaPessoaDiaExecucaoSchema):
    """Recupera todas as rotinas dia a partir do id da pessoa e data de execução.

    Retorna uma representação da listagem de rotinas dia.
    """
    logger.debug(f"Coletando pessoas ")
    # criando conexão com a base
    session = Session()
    id_pessoa = form.id_pessoa
    # fazendo a busca
    rotinasdia = session.query(RotinaDia).filter(RotinaDia.id_pessoa == id_pessoa,
                                                extract('day', RotinaDia.data_execucao) == form.data_execucao.day ,
                                                extract('month', RotinaDia.data_execucao) == form.data_execucao.month ,
                                                extract('year', RotinaDia.data_execucao) == form.data_execucao.year).all()

    if not rotinasdia:
        # se não há rotinas cadastradas
        return {"rotinasdia": []}, 200
    else:
        logger.debug(f"%d rotinas econtrados" % len(rotinasdia))
        # retorna a representação de rotinas
        #print(rotinasdia)
        return apresenta_rotinasdia(rotinasdia), 200
    

@app.post('/rotinasdia-data', tags=[rotinadia_tag],
         responses={"200": ListagemRotinasDiaSchema, "404": ErrorSchema})
def get_ultimasrotinasdia(form: RotinaDiaBuscaPessoaDiaExecucaoSchema):
    """Recupera todas as rotinas dia a partir do id da pessoa e data de execução maior igual a data informada.

    Retorna uma representação da listagem de rotinas dia.
    """
    logger.debug(f"Coletando pessoas ")
    # criando conexão com a base
    session = Session()
    id_pessoa = form.id_pessoa
    # fazendo a busca
    rotinasdia = session.query(RotinaDia).filter(RotinaDia.id_pessoa == id_pessoa,
                                                RotinaDia.data_execucao >= form.data_execucao).all()

    if not rotinasdia:
        # se não há rotinas cadastradas
        return {"rotinasdia": []}, 200
    else:
        logger.debug(f"%d rotinas econtrados" % len(rotinasdia))
        # retorna a representação de rotinas
        #print(rotinasdia)
        return apresenta_rotinasdia(rotinasdia), 200    


@app.post('/rotinadia-passado', tags=[rotinadia_tag],
          responses={"200": RotinaDiaSchema, "404": ErrorSchema})
def add_rotinadia_passado(form: RotinaDiaSchema):
    """Adiciona uma nova rotina dia à uma pessoa.

    Retorna uma representação das pessoas e rotinas padrao associados.
    """

    logger.debug(f"Adicionando rotinas dia a pessoa #{form.id_pessoa}")
    # criando conexão com a base
    session = Session()

    td = timedelta(1)
    data_atual = form.data_execucao - td
    rotinasDia = []
    for numero in range(7):
        rotina_dia = RotinaDia(form.hora, form.id_evento, form.id_pessoa, 1, data_atual)
        print(">> rotina_dia", rotina_dia)
        rotinasDia.append(rotina_dia)
        data_atual = data_atual - td

    session.add_all(rotinasDia)

    session.commit()
    logger.debug(f"Adicionado rotina dia a pessoa #{form.id_pessoa}")

    # retorna a representação de rotina_dia
    return apresenta_rotinadia(rotina_dia), 200
