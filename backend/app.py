from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import google.generativeai as genai


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


genai.configure(api_key=api_key)


app = Flask(__name__)
CORS(app)


model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            users = json.load(f)
            print("Loaded users:", users)  
            return users
    return {}


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    users = load_users()
    if username in users and users[username] == password:
         return jsonify(status="success")
    return jsonify(status="failure")
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(status="failure", message="Username and password are required.")

    users = load_users()

    if username in users:
        return jsonify(status="failure", message="Username already exists.")

    users[username] = password
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)

    return jsonify(status="success", message="User created successfully.")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    raw_prompt = data.get("prompt", "").strip()

    if not raw_prompt:
        return jsonify({"reply": "⚠️ Please enter a prompt before asking a question."})

    try:
        # Extract domain and query
        domain_line, query_line = raw_prompt.split("\n", 1)
        domain = domain_line.replace("Domain:", "").strip()
        query = query_line.replace("User Query:", "").strip()

        if not query:
            return jsonify({"reply": "⚠️ Please enter a prompt before asking a question."})

        # Ask Gemini: is it *likely* related? (more flexible prompt)
        check_prompt = f"Does this question belong to the domain of {domain}? Just say 'Yes' or 'No'.\nQuestion: {query}"
        check_response = model.generate_content(check_prompt).text.strip().lower()

        if "no" in check_response and "yes" not in check_response:
            return jsonify({"reply": f"⚠️ Your question seems unrelated to the selected domain ({domain}). Please ask a relevant question."})

        # Get full answer
        answer_response = model.generate_content(query).text
        return jsonify({"reply": answer_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    print("✅ Gemini backend running at http://127.0.0.1:5000")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
