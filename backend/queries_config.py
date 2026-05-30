# Lista de consultas semánticas técnica e histórica.
from motor_semantico import q_obras_complejas_piano, q_autores_periodo_romantico, q_instrumentos_viento_madera, q_instrumentos_cuerda, q_instrumentos_viento, q_instrumentos_percusion, q_obras_romanticas

SEMANTIC_QUERIES = {
    "obras_complejas_piano":
        q_obras_complejas_piano,

    "autores_periodo_romantico":
        q_autores_periodo_romantico,

    "instrumentos_viento_madera":
        q_instrumentos_viento_madera,

    "instrumentos_cuerda":
        q_instrumentos_cuerda,

    "instrumentos_viento":
        q_instrumentos_viento,

    "instrumentos_percusion":
        q_instrumentos_percusion,

    "obras_romanticas":
        q_obras_romanticas,
}

def get_query_info(query_name):
    return SEMANTIC_QUERIES.get(query_name)