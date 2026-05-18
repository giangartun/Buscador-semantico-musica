from flask import Flask, request, jsonify
from flask_cors import CORS
from motor_semantico import cargar_y_razonar, buscar_individuos_por_clase, buscar_por_texto

app = Flask(__name__)
CORS(app)

print("\n--- [Servidor] Iniciando Servidor Backend Semántico ---")
cargar_y_razonar()

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