from flask import Flask, request, jsonify
from flask_cors import CORS
from motor_semantico import (
    cargar_y_razonar, 
    buscar_individuos_por_clase, 
    buscar_por_texto, 
    obtener_clases, 
    obtener_detalle_individuo,
    detectar_consulta_semantica,
    ejecutar_consulta_semantica_musical
)
from queries_config import get_query_info
from consultas_sparql import consultar_por_sparql_local, consultar_dbpedia_artistas

app = Flask(__name__)
CORS(app)

SUPPORTED_LANGS = {"es", "en", "fr"}

MESSAGES = {
    "query_not_found": {
        "es": "La consulta tecnica '{query}' no existe en la configuracion.",
        "en": "The technical query '{query}' does not exist in the configuration.",
        "fr": "La requete technique '{query}' n'existe pas dans la configuration.",
    },
    "missing_param": {
        "es": "Falta el parametro 'param' para esta consulta.",
        "en": "Missing 'param' parameter for this query.",
        "fr": "Le parametre 'param' est requis pour cette requete.",
    },
    "missing_name": {
        "es": "Falta el parametro nombre",
        "en": "Missing 'nombre' parameter",
        "fr": "Parametre 'nombre' manquant",
    },
    "missing_text": {
        "es": "Falta el parametro texto",
        "en": "Missing 'texto' parameter",
        "fr": "Parametre 'texto' manquant",
    },
    "missing_search": {
        "es": "Debes proporcionar el parametro 'texto' o 'clase' en la URL.",
        "en": "You must provide the 'texto' or 'clase' parameter in the URL.",
        "fr": "Vous devez fournir le parametre 'texto' ou 'clase' dans l'URL.",
    },
    "health": {
        "es": "Backend musical funcionando",
        "en": "Music backend is running",
        "fr": "Backend musical en fonctionnement",
    },
}

def get_lang():
    lang = request.args.get("lang", "es").lower()
    return lang if lang in SUPPORTED_LANGS else "es"

def msg(key, lang, **kwargs):
    template = MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get("es", ""))
    return template.format(**kwargs)

print("\n--- [Servidor] Iniciando Servidor Backend Semántico Musical ---")
# Carga inicial de la ontología y ejecución única del razonador
cargar_y_razonar()

@app.route('/api/semantic/<query_name>', methods=['GET'])
def api_semantic_queries(query_name):
    """
    Ruta para ejecutar consultas de lógica técnica e histórica avanzada.
    Permite filtrar por criterios específicos como periodo, dificultad o autor.
    """
    info = get_query_info(query_name)
    lang = get_lang()
    if not info:
        return jsonify({"error": msg("query_not_found", lang, query=query_name)}), 404

    # Captura el parámetro opcional si la consulta lo requiere (ej. ?param=Mozart)
    param = request.args.get('param')

    if info.get("requires_param") and not param:
        return jsonify({"error": msg("missing_param", lang)}), 400

    handler = info.get("handler")
    resultados = handler(param) if info.get("requires_param") else handler()

    return jsonify({
        "title": info["title"],
        "description": info["description"],
        "total": len(resultados),
        "resultados": resultados
    }), 200

@app.route('/api/dbpedia', methods=['GET'])
def api_dbpedia():
    artista = request.args.get('nombre')
    lang = get_lang()

    if not artista:
        return jsonify({
            "error": msg("missing_name", lang)
        }), 400

    resultados = consultar_dbpedia_artistas(artista, lang)

    return jsonify({
        "total": len(resultados),
        "resultados": resultados
    })

@app.route('/api/sparql', methods=['GET'])
def api_sparql():
    texto = request.args.get('texto')
    lang = get_lang()

    if not texto:
        return jsonify({
            "error": msg("missing_text", lang)
        }), 400

    resultados = consultar_por_sparql_local(texto)

    return jsonify({
        "total": len(resultados),
        "resultados": resultados
    })

@app.route('/api/clases', methods=['GET'])
def api_clases():
    clases = obtener_clases()

    return jsonify({
        "total": len(clases),
        "clases": clases
    })

@app.route('/api/buscar', methods=['GET'])
def api_buscar():
    palabra_clave = request.args.get('texto')
    nombre_clase = request.args.get('clase')
    
    resultados = []

    # 1. Caso: Se solicita filtrar estrictamente por clase de la ontología
    if nombre_clase:
        try:
            resultados = buscar_individuos_por_clase(nombre_clase)
        except Exception as e:
            print(f"[Error] Falló la búsqueda por clase '{nombre_clase}': {e}")
            resultados = []

    # 2. Caso: Se solicita búsqueda por texto libre (O procesar consultas semánticas complejas)
    elif palabra_clave:
        consulta_semantica, consulta_param = detectar_consulta_semantica(palabra_clave)
        
        if consulta_semantica:
            resultados = ejecutar_consulta_semantica_musical(
                consulta_semantica,
                consulta_param
            )
        else:
            resultados = buscar_por_texto(palabra_clave)
            
    else:
        return jsonify({
            "error": msg("missing_search", lang)
        }), 400

    # 3. Filtro de intersección esencial: Si mandaron AMBOS parámetros (?texto=...&clase=...)
    # Evita el crash cruzando los resultados de texto sobre la clase seleccionada en memoria segura.
    if palabra_clave and nombre_clase and resultados:
        from motor_semantico import normalize_text
        token = normalize_text(palabra_clave)
        resultados = [r for r in resultados if token in normalize_text(r.get("nombre", "")) or token in normalize_text(r.get("descripcion", ""))]

    return jsonify({
        "total": len(resultados),
        "resultados": resultados
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    lang = get_lang()
    return jsonify({"status": "ok", "message": msg("health", lang)}), 200

if __name__ == "__main__":
    print("[Servidor] API lista y escuchando en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)