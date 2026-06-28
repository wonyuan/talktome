from flask import Flask, jsonify, request
from flask_cors import CORS  
import cohere
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

api_key = os.getenv('API_KEY')
co = cohere.Client(api_key)

chat_history = []

# The original fine-tuned models and the Classify API were removed by Cohere
# (Sept 2025). Persona behavior is now driven by the system prompt in /chat,
# so every persona maps to the same current base model.
BASE_MODEL = "command-a-03-2025"

persona_models = {
    "Angry Adam": BASE_MODEL,
    "Quiet Quintin": BASE_MODEL,
    "Judgmental Judy": BASE_MODEL,
    "Happy Hannah": BASE_MODEL
}


@app.route('/classify', methods=['POST'])
def classify():
    try:
        data = request.get_json()
        paragraph = data.get("paragraph", "").strip()

        if not paragraph:
            return jsonify({"error": "No paragraph provided!"}), 400

        # The Cohere Classify API was removed (Sept 2025), so classify via Chat:
        # ask the model to pick exactly one persona label.
        labels = list(persona_models.keys())
        classify_prompt = (
            "You are classifying a parent's description of their teenager into one "
            "of these teen personas:\n"
            f"{', '.join(labels)}.\n\n"
            "Respond with ONLY the exact label text, nothing else.\n\n"
            f"Description: {paragraph}"
        )

        response = co.chat(
            model = BASE_MODEL,
            message = classify_prompt,
            temperature = 0
        )

        prediction = response.text.strip()
        # Match the model output back to a known label (tolerate extra text/case).
        classification = next(
            (l for l in labels if l.lower() in prediction.lower()),
            None
        )

        if not classification:
            return jsonify({"error": "Could not classify. Please provide more details."}), 400

        confidence_level = 1.0
        chat_id = persona_models.get(classification)
        if not chat_id:
            return jsonify({"error": f"No model found for classification: {classification}"}), 404

        return jsonify({
            "classification": classification,
            "confidence": confidence_level,
            "persona_model_id": chat_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/refined', methods=['POST'])
def refine():
    data = request.json
    situation = data.get("situation")

    stream = co.chat_stream( 
        model='c4ai-aya-expanse-32b',
        message='BASED ON THIS INFORMATION:'+ situation + "create a single, concise 2-sentence description of a teenager, for example: Hi I am a teenager with ____ and I've been having trouble with _____. Please strictly adhere to the short and concise length.",
        temperature=0.3,
        chat_history=[],
        prompt_truncation='AUTO'
    ) 

    updated_situation = ""

    for event in stream:
        if event.event_type == "text-generation":
        # Concatenate the generated text to the updated_situation variable
            updated_situation += event.text
            print(event.text, end = '')
    
    return{
        "profile_intro": updated_situation
    }

@app.route('/chat', methods=['POST'])
def chat():
    global chat_history
    if request.method == 'POST':
        data = request.json
        classification = data.get("classification")
        situation = data.get("situation")
        user_input = data.get("user_input")

        chat_id = persona_models.get(classification)

        if not chat_id:
            return jsonify({"error": f"No model found for classification: {classification}"}), 400

        message_to_chat = (
            f"You are a teenager with the personality: {classification}. "
            "Your role is to help a parent practice conversations with their child based on the situation they have described. "
            f"Stay in character as '{classification}' throughout the conversation. "
            "React naturally based on your assigned persona's emotions, thoughts, and communication style. "
            "Your goal is to simulate a realistic interaction to help the parent better understand how to communicate with their child. "
            "Let the parent lead the conversation, and only respond as the teenager. "
            "Make sure you are open to change. "
            f"Here is the context of the situation provided by the parent: {situation}"
        )

        if not chat_history:
            chat_history = [{"role": "system", "message": message_to_chat}]

        chat_history.append({"role": "user", "message": user_input})

        response = co.chat(
            model = chat_id,
            message = user_input,
            temperature = 0.3,
            chat_history = chat_history,
            prompt_truncation = 'AUTO'
        )

        bot_response = response.text
        chat_history.append({"role": "Chatbot", "message": bot_response})
        return jsonify({"bot_response": bot_response})
    
@app.route('/evaluation', methods=['POST'])
def evaluation():
    try:
        data = request.json  # ✅ No need to extract "params"
        situation = data.get("scenario")  # ✅ Matches frontend
        chat = data.get("chat_history")  # ✅ Matches frontend

        stream = co.chat_stream( 
            model='c4ai-aya-expanse-32b',
            message = f"Based on this information: {situation}, and this conversation: {chat}. ALWAYS Answer the following: 'what the parent did well', 'areas for improvement', and 'advice for better connection'. Give the heading and a text responses for each topic.",
            temperature=0.3,
            chat_history=[],
            prompt_truncation='AUTO'
        ) 

        # well, improve, connection = "", "", ""
        output = ""

        for event in stream:
            if event.event_type == "text-generation":
                output += event.text
                # print(output, end='')
        
        sections = output.split('**')
        response = {}

        for i in range(1, len(sections), 2):  
            key = sections[i].strip().rstrip(':')  
            value = sections[i + 1].strip() if i + 1 < len(sections) else ""
            key = "".join(c for c in key if c.isalnum() or c.isspace())  
            value = "".join(c for c in value if c.isalnum() or c.isspace() or c in ".,!?")  
            response[key] = value

        print(response)  

        return {
            "Output": response
        }
        # return {
        #     "Output": output
        # }

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
if __name__ == "__main__":
    app.run(debug = True, port = 5001)