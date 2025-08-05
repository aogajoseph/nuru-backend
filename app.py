from flask import Flask, request, jsonify
from flask_cors import CORS
from assistant import get_agent_response
import os
import json

app = Flask(__name__)
CORS(app)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_input = data.get("question", "")
    answer = get_agent_response(user_input)
    return jsonify({"response": answer})

@app.route("/config", methods=["GET"])
def get_config():
    try:
        with open("config/nuru_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": "Failed to load configuration", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
