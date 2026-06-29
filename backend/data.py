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
    "Judgemental Judy": BASE_MODEL,
    "Happy Hannah": BASE_MODEL
}

# Explicit personality for each persona. Since the dedicated fine-tuned models
# were removed, this is what makes each persona behave distinctly on the shared
# base model.
persona_descriptions = {
    "Angry Adam": (
        "You are hot-tempered and easily frustrated. You snap, raise your voice, "
        "slam things, and get defensive fast. Under the anger you actually feel "
        "overwhelmed and unheard. You soften only when the parent stays calm and "
        "genuinely listens instead of lecturing."
    ),
    "Quiet Quintin": (
        "You are withdrawn and shut down. You give short, one- or two-word answers, "
        "avoid eye contact, and keep your feelings to yourself. You're not rude, "
        "just guarded. You slowly open up if the parent is patient, gentle, and "
        "doesn't pressure or interrogate you."
    ),
    "Judgemental Judy": (
        "You are sharp-tongued and critical. You roll your eyes, talk back, and "
        "judge others (including your parent) with sarcastic, cutting remarks. "
        "Underneath you're insecure and testing whether your parent's love is "
        "conditional. You respond to calm confidence and clear, loving boundaries."
    ),
    "Happy Hannah": (
        "You are usually upbeat and bubbly, but lately something has felt off and "
        "you're masking it with forced cheerfulness. You deflect with jokes and "
        "'I'm fine!' You let your guard down when the parent notices the change "
        "and shows they truly care about what's underneath."
    ),
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

        persona_desc = persona_descriptions.get(classification, "")

        message_to_chat = (
            f"You are role-playing a teenager named '{classification}'. "
            f"Personality: {persona_desc} "
            "Your role is to help a parent practice conversations with their child based on the situation they have described. "
            f"Stay fully in character as '{classification}' throughout the conversation, matching the personality above in tone, word choice, and attitude. "
            "Keep your replies short and realistic, the way a real teenager texts or talks. "
            "Your goal is to simulate a realistic interaction to help the parent better understand how to communicate with their child. "
            "Let the parent lead the conversation, and only respond as the teenager. "
            "Make sure you are open to change if the parent handles the conversation well. "
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
    
EVAL_SECTIONS = [
    "What You Did Well",
    "Areas for Improvement",
    "Advice for Better Connection",
]


def parse_evaluation(text):
    """Split the model output into the three known sections, preserving normal
    punctuation. Robust to markdown (**, ##) and to the headings appearing in
    any order."""
    cleaned = text.replace("**", "").replace("#", "").replace("*", "")
    lowered = cleaned.lower()

    # Find where each heading starts in the text.
    found = []
    for heading in EVAL_SECTIONS:
        pos = lowered.find(heading.lower())
        if pos != -1:
            found.append((pos, heading))
    found.sort()

    result = {}
    for i, (pos, heading) in enumerate(found):
        start = pos + len(heading)
        end = found[i + 1][0] if i + 1 < len(found) else len(cleaned)
        body = cleaned[start:end].strip().lstrip(":").strip()
        result[heading] = body
    return result


@app.route('/evaluation', methods=['POST'])
def evaluation():
    try:
        data = request.json
        situation = data.get("scenario")
        chat = data.get("chat_history")

        prompt = (
            f"A parent practiced a conversation with their teenager.\n\n"
            f"Situation: {situation}\n\n"
            f"Conversation: {chat}\n\n"
            "Give the parent warm, specific, constructive feedback. "
            "Use EXACTLY these three headings, each on its own line, followed by "
            "a short paragraph (2-4 sentences) written directly to the parent as 'you':\n"
            "What You Did Well:\n"
            "Areas for Improvement:\n"
            "Advice for Better Connection:\n"
            "Do not use any markdown, bullet points, or asterisks."
        )

        stream = co.chat_stream(
            model='c4ai-aya-expanse-32b',
            message=prompt,
            temperature=0.3,
            chat_history=[],
            prompt_truncation='AUTO'
        )

        output = ""
        for event in stream:
            if event.event_type == "text-generation":
                output += event.text

        response = parse_evaluation(output)

        # Fallback: if parsing found nothing, return the raw text under one key
        # so the user still sees their feedback.
        if not response:
            response = {"Feedback": output.strip()}

        return {"Output": response}

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
if __name__ == "__main__":
    app.run(debug = True, port = 5001)