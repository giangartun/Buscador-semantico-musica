from flask import Flask, request, jsonify
from flask_cors import CORS
from motor_semantico import cargar_y_razonar, buscar_individuos_por_clase, buscar_por_texto

app = Flask(__name__)

# Permite que el Frontend se conecte desde puertos distintos como 3000 o 5173 sin bloqueos de seguridad del navegador
CORS(app)

print("\n--- [Servidor] Iniciando Servidor Backend Semántico ---")
# Precargar la ontología y ejecuta el razonador HermiT una sola vez al levantar el servidor
cargar_y_razonar()

@app.route('/api/buscar', methods=['GET'])
def api_buscar():
    """
    Ruta de la API para buscar elementos de la ontología. 
    Parámetros aceptados por URL:
    - /api/buscar?texto=nombre_a_buscar
    - /api/buscar?clase=NombreClase
    """
    palabra_clave = request.args.get('texto')
    nombre_clase = request.args.get('clase')
    
    # 1. Si el usuario filtra por una clase/categoría estructural
    if nombre_clase:
        resultados = buscar_individuos_por_clase(nombre_clase)
    # 2. Si el usuario escribe texto libre en la barra de búsqueda
    elif palabra_clave:
        resultados = buscar_por_texto(palabra_clave)
    # 3. Si no mandó nada válido
    else:
        return jsonify({
            "error": "Debes proporcionar el parámetro 'texto' o 'clase' en la URL."
        }), 400
        
    # Retornamos los resultados en formato JSON limpio para el Frontend
    return jsonify({
        "total": len(resultados),
        "resultados": resultados
    })

if __name__ == "__main__":
    # Correr el servidor local en el puerto 5000
    print("[Servidor] API lista en http://localhost:5000/api/buscar")
    app.run(host="0.0.0.0", port=5000, debug=False)