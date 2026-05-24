from flask import Flask, request, jsonify
from flask_cors import CORS
from motor_semantico import cargar_y_razonar, buscar_individuos_por_clase, buscar_por_texto, obtener_clases, obtener_detalle_individuo
from consultas_sparql import consultar_por_sparql_local, consultar_dbpedia_artistas

app = Flask(__name__)
CORS(app)

print("\n--- [Servidor] Iniciando Servidor Backend Semántico ---")
cargar_y_razonar()

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
    
    if nombre_clase:
        resultados = buscar_individuos_por_clase(nombre_clase)
    elif palabra_clave:
        resultados = buscar_por_texto(palabra_clave)
    else:
        return jsonify({
            "error": "Debes proporcionar el parámetro 'texto' o 'clase' en la URL."
        }), 400
        
    return jsonify({
        "total": len(resultados),
        "resultados": resultados
    })

# ===== AGREGAR ESTA RUTA =====
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Backend funcionando"}), 200
# ==============================

if __name__ == "__main__":
    print("[Servidor] API lista en http://localhost:5000/api/buscar")
    app.run(host="0.0.0.0", port=5000, debug=False)