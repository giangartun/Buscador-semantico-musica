# Lista de consultas semánticas técnica e histórica.

SEMANTIC_QUERIES = {
    "obras_complejas_piano": {
        "title": "Obras Maestras de Alta Dificultad para Piano",
        "description": "Muestra composiciones complejas (ideales para Chopin o Beethoven) que requieren piano."
    },
    "autores_periodo_romantico": {
        "title": "Compositores del Romanticismo",
        "description": "Lista a los autores clásicos catalogados dentro del periodo romántico."
    },
    "instrumentos_viento_madera": {
        "title": "Registro de Viento-Madera",
        "description": "Filtra los instrumentos clasificados técnicamente bajo la familia acústica de viento-madera."
    },
    "obras_por_autor": {
        "title": "Catálogo de Obras por Compositor",
        "description": "Busca dinámicamente las piezas musicales creadas por un autor específico (ej. Mozart)."
    }
}

def get_query_info(query_name):
    return SEMANTIC_QUERIES.get(query_name)