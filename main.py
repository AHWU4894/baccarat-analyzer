from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder='.')

history = []

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"history": history})

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json() or {}
    res = data.get('result')
    if res in ['B', 'P', 'T']:
        history.append(res)
    return jsonify({"history": history})

@app.route('/reset', methods=['POST'])
def reset():
    global history
    history = []
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
