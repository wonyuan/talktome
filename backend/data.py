from flask import Flask, jsonify, request
from flask_cors import CORS  
import cohere
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
cors = CORS(app)

api_key = os.getenv('API_KEY')
co = cohere.Client(api_key)

chat_history = []

persona_models = {
    "Angry Adam": "ef9183fe-75a5-4686-b7ff-14fced618013-ft",
    "Quiet Quintin": "ebbfe6bd-0c47-42e6-8afe-949a8bfe9e34-ft",
    "Judgmental Judy": "d5452d1d-d8bd-42d6-a28c-321f79f96572-ft",
    "Happy Hannah": "5340c40f-9e3b-4d16-8d4c-9a1d4495e905-ft"
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
            model=chat_id,
            message=user_input,
            temperature=0.3,
            chat_history=chat_history,
            prompt_truncation='AUTO'
        )

        bot_response = response.text
        chat_history.append({"role": "Chatbot", "message": bot_response})
        return jsonify({"bot_response": bot_response})
    
# want chat history from backend 
    # elif request.method == 'GET':
    #     # Return the current chat history
    #     return jsonify({"chat_history": chat_history})

'''
@app.route('/evaluate', methods=['GET'])
def evaluate():
    global chat_history
    # Get chat history from stored variable 
    # data = request.json
    # chat_history = data.get("chat_history")

    # Evaluate the conversation
    score = evaluate_conversation(chat_history)

    # Reset the history after evaluation
    chat_history = []

    return jsonify({"score": score, "message": "Conversation evaluated and history reset."})
'''

@app.route('/evaluation', methods=['POST'])
def evaluation():
    try:
        response = co.classify(
            model = 'bfc37152-1c6c-4486-84bb-843dd7d9df11-ft',  # MODEL ID HERE
            inputs = [chat_history]
        )

        highest_confidence = max(response.classifications, key = lambda x: x.confidence)
        label_scores = {"one": "10%", "two": "20%", "three": "30%", "four": "40%", "five": "50%", "six": "60%", "seven": "70%", "eight": "80%", "nine": "90%", "ten": "100%",
        }

        label = highest_confidence.prediction  # labels from "one", "two", ..., "ten"
        confidence_level = highest_confidence.confidence

        if confidence_level < 0.25:
            return {"error": "Confidence too low. Please provide more details."}, 400

        return {
            "conversation_rating": label_scores.get(label),
            "confidence": confidence_level
        }

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/classify', methods=['POST'])
def classify():
    try:
        data = request.get_json()
        paragraph = data.get("paragraph", "").strip()

        if not paragraph:
            return jsonify({"error": "No paragraph provided"}), 400

        response = co.classify(
            model='5ae71449-3ae0-488f-a703-eb0275839e8f-ft',
            inputs=[paragraph]
        )

        highest_confidence = max(response.classifications, key=lambda x: x.confidence)
        classification = highest_confidence.prediction
        confidence_level = highest_confidence.confidence

        if confidence_level < 0.25:
            return jsonify({"error": "Confidence too low. Please provide more details."}), 400

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

@app.route('/refined', methods=['GET'])
def refine():
    try:
        situation = request.args.get("situation")
        if not situation:
            return jsonify({"error": "No situation provided"}), 400

        stream = co.chat_stream(
            model='c4ai-aya-expanse-32b',
            message=f'BASED ON THIS INFORMATION: {situation} ...',
            temperature=0.3,
            chat_history=[],
            prompt_truncation='AUTO'
        ) 
        updated_situation = "".join(event.text for event in stream if event.event_type == "text-generation")

        if not updated_situation:
            return jsonify({"error": "No response generated"}), 500

        return jsonify({"profile_intro": updated_situation})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)