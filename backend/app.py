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
    if not info:
        return jsonify({"error": f"La consulta técnica '{query_name}' no existe en la configuración."}), 404

    # Captura el parámetro opcional si la consulta lo requiere (ej. ?param=Mozart)
    param = request.args.get('param')
    resultados = ejecutar_consulta_semantica_musical(query_name, param)

    return jsonify({
        "title": info["title"],
        "description": info["description"],
        "total": len(resultados),
        "resultados": resultados
    }), 200

@app.route('/api/dbpedia', methods=['GET'])
def api_dbpedia():
    artista = request.args.get('nombre')

    if not artista:
        return jsonify({
            "error": "Falta el parámetro nombre"
        }), 400

    resultados = consultar_dbpedia_artistas(artista)

    return jsonify({
        "total": len(resultados),
        "resultados": resultados
    })

@app.route('/api/sparql', methods=['GET'])
def api_sparql():
    texto = request.args.get('texto')

    if not texto:
        return jsonify({
            "error": "Falta el parámetro texto"
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
    consulta_semantica = detectar_consulta_semantica(palabra_clave)
    if nombre_clase:
        resultados = buscar_individuos_por_clase(nombre_clase)
    elif palabra_clave:
        if consulta_semantica:
            resultados = ejecutar_consulta_semantica_musical(
            consulta_semantica
        )
        else:
            resultados = buscar_por_texto(
            palabra_clave
         )
    else:

        return jsonify({
            "error": "Debes proporcionar el parámetro 'texto' o 'clase' en la URL."
        }), 400
        
    return jsonify({
        "total": len(resultados),
        "resultados": resultados
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Backend musical funcionando"}), 200

if __name__ == "__main__":
    print("[Servidor] API lista y escuchando en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)