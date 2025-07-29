from flask import Flask, request, jsonify
from flask_cors import CORS
from assistant import get_agent_response  # your logic

app = Flask(__name__)
CORS(app)  # allow cross-origin calls from React

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_input = data.get("question", "")
    answer = get_agent_response(user_input)
    return jsonify({"response": answer})

if __name__ == "__main__":
    app.run(port=5000)
