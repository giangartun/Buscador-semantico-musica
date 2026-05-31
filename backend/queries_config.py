# Lista de consultas semánticas técnica e histórica.
from motor_semantico import (
    q_autores_periodo_romantico,
    q_instrumentos_cuerda,
    q_instrumentos_percusion,
    q_instrumentos_viento,
    q_instrumentos_viento_madera,
    q_obras_complejas_piano,
    q_obras_por_autor,
    q_obras_romanticas,
)

SEMANTIC_QUERIES = {
    "obras_complejas_piano": {
        "title": "Obras complejas para piano",
        "description": "Obras con complejidad tecnica alta y ejecutadas en piano.",
        "handler": q_obras_complejas_piano,
        "requires_param": False,
    },
    "autores_periodo_romantico": {
        "title": "Autores del periodo romantico",
        "description": "Individuos asociados al periodo romantico en la ontologia.",
        "handler": q_autores_periodo_romantico,
        "requires_param": False,
    },
    "instrumentos_viento_madera": {
        "title": "Instrumentos de viento madera",
        "description": "Instrumentos que pertenecen a la familia de viento madera.",
        "handler": q_instrumentos_viento_madera,
        "requires_param": False,
    },
    "instrumentos_cuerda": {
        "title": "Instrumentos de cuerda",
        "description": "Instrumentos que pertenecen a la familia de cuerda.",
        "handler": q_instrumentos_cuerda,
        "requires_param": False,
    },
    "instrumentos_viento": {
        "title": "Instrumentos de viento",
        "description": "Instrumentos que pertenecen a la familia de viento.",
        "handler": q_instrumentos_viento,
        "requires_param": False,
    },
    "instrumentos_percusion": {
        "title": "Instrumentos de percusion",
        "description": "Instrumentos que pertenecen a la familia de percusion.",
        "handler": q_instrumentos_percusion,
        "requires_param": False,
    },
    "obras_romanticas": {
        "title": "Obras romanticas",
        "description": "Obras vinculadas al periodo romantico.",
        "handler": q_obras_romanticas,
        "requires_param": False,
    },
    "obras_por_autor": {
        "title": "Obras por autor",
        "description": "Obras filtradas por el autor indicado.",
        "handler": q_obras_por_autor,
        "requires_param": True,
    },
}

def get_query_info(query_name):
    return SEMANTIC_QUERIES.get(query_name)