import sqlite3
from flask import Flask, request, jsonify, render_template, redirect, url_for
import logging
from db import init_db
from utils import init_model, update_model_with_feedback
from utils import predict_intent
from response import generate_response,validate_user_id
from feedback import handle_feedback, store_feedback, requires_feedback,get_correct_intent_from_feedback
import re

app = Flask(__name__)
app.secret_key = '123'  # Added secret key for flash messages

conversation_state = {}

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[
                        logging.FileHandler("/app/chatbot.log"),
                        logging.StreamHandler()
                    ])

def initialize_user_state():
    return {
        "step": "greeting",
        "check_in": None,
        "check_out": None,
        "guests": None,
        "room_type": None,
        "room_price": None,
        "last_input": None,
        "last_response": None,
        "last_intent": None,
        "last_message": None,
        "history": []
    
    }

def sanitize_message(message):
    # Remove any unwanted characters or codes
    return re.sub(r'[^A-Za-z0-9\s,.!?]', '', message.strip())

@app.route('/clear_history', methods=['POST'])
def clear_history():
    user_id = request.remote_addr
    if user_id in conversation_state:
        conversation_state[user_id]['history'] = []
        return jsonify({'message': 'Chat history cleared successfully'})
    return jsonify({'message': 'No chat history found'})

def initialize():
    try:
        init_db()
        init_model()
        logging.info("Database and model initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database or model: {e}")

initialize()

from flask import Flask, request, jsonify, render_template, redirect, url_for, escape

@app.route('/', methods=['GET', 'POST'])
def home():
    user_id = request.remote_addr
    if user_id not in conversation_state:
        conversation_state[user_id] = initialize_user_state()

    if request.method == 'POST':
        text = request.form.get('user_input')
        text = sanitize_message(text)  # Sanitize user input
        logging.info(f"User input: {text}")  # Log user input

        intent = predict_intent(text)
        conversation_state[user_id]['last_intent'] = intent
        conversation_state[user_id]['last_message'] = text

        logging.info(f"Current state before processing: {conversation_state[user_id]}")  # Log state before processing

        response = generate_response(text, conversation_state[user_id])
        response = sanitize_message(response)  # Sanitize bot response
        logging.info(f"Bot response: {response}")  # Log bot response

        conversation_state[user_id]['last_response'] = response

        # Add the new message and response to the history
        conversation_state[user_id]['history'].append(('User', escape(text)))
        conversation_state[user_id]['history'].append(('Bot', escape(response)))

        logging.info(f"Current state after processing: {conversation_state[user_id]}")  # Log state after processing

    return render_template('index.html', messages=conversation_state[user_id]['history'])

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        text = data.get('text')
        user_id = data.get('user_id')

        logging.info(f"Received chat request from {user_id}: {text}")

        if not user_id:
            user_id = request.remote_addr
            if user_id in conversation_state and 'user_id' in conversation_state[user_id]:
                user_id = conversation_state[user_id]['user_id']
            else:
                logging.info("User ID not provided, requesting user ID.")
                return jsonify({
                    "response": "To book a room or extend your stay, please provide your user ID in the format user_XXX where XXX is a three-digit number.",
                    "requires_user_id": True
                })

        if validate_user_id(text):
            user_id = text
            if user_id not in conversation_state:
                conversation_state[user_id] = initialize_user_state()
            conversation_state[user_id]['user_id'] = user_id
            conversation_state[user_id]['step'] = 'verify_user'
            logging.info(f"User ID validated and stored: {user_id}")
            return jsonify({"response": f"Thank you for providing your user ID: {user_id}. How can I assist you today?", "user_id": user_id})

        if user_id not in conversation_state:
            conversation_state[user_id] = initialize_user_state()

        conversation_state[user_id]['last_message'] = text

        intent, confidence = predict_intent(text)
        logging.info(f"Predicted intent: {intent}, confidence: {confidence}")

        conversation_state[user_id]['last_intent'] = intent

        if 'step' not in conversation_state[user_id]:
            conversation_state[user_id]['step'] = 'greeting'

        logging.info(f"Current state before generating response: {conversation_state[user_id]}")
        response = generate_response(text, conversation_state[user_id])
        logging.info(f"Generated response: {response}")
        logging.info(f"Current state after generating response: {conversation_state[user_id]}")

        # Check if feedback is required
        feedback_needed, feedback_reason = requires_feedback(text)
        if feedback_needed:
            return jsonify({
                "response": response,
                "requires_feedback": True,
                "user_input": text,
                "predicted_intent": intent
            })

        return jsonify({"response": response, "user_id": user_id})

    except Exception as e:
        logging.error(f"Unexpected error in chat route: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

@app.route('/feedback', methods=['POST'])
def feedback():
   return render_template('feedback.html')




@app.route('/detailed_feedback', methods=['GET', 'POST'])
def detailed_feedback():
    user_id = request.remote_addr
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        predicted_intent = request.form.get('predicted_intent')
        correct_intent = request.form.get('correct_intent')
        
        # Sanitize user input
        user_input = sanitize_message(user_input)
        predicted_intent = sanitize_message(predicted_intent)
        correct_intent = sanitize_message(correct_intent)
        
        logging.info(f"Storing feedback: user_input={user_input}, predicted_intent={predicted_intent}, correct_intent={correct_intent}")
        
        store_feedback(user_id, user_input, correct_intent, predicted_intent)
        return "Thank you for your detailed feedback!"
    
    return render_template('feedback.html', 
                           user_input=conversation_state[user_id].get('last_message', ''),
                           predicted_intent=conversation_state[user_id].get('last_intent', ''))

from flask import redirect, url_for

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        user_id = request.remote_addr
        user_input = request.form['user_input']
        predicted_intent = request.form['predicted_intent']
        correct_intent = request.form['correct_intent']
        
        store_feedback(user_id, user_input, correct_intent, predicted_intent)
        update_model_with_feedback()
        
        return redirect(url_for('detailed_feedback'))
    except Exception as e:
        logging.error(f"Error in submit_feedback: {str(e)}")
        return "An error occurred while processing your feedback.", 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
