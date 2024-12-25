import sqlite3
from flask import Flask, request, jsonify, render_template
import spacy
from spacy.cli import download
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib
import os
import logging
from datetime import datetime, timedelta

app = Flask(__name__)

# Set up logging
logging.basicConfig(filename='/app/chatbot.log', level=logging.INFO)

# Download and load spaCy model
download("en_core_web_sm")
nlp = spacy.load("en_core_web_sm")

# Define the path for storing the model
MODEL_PATH = '/app/intent_pipeline.joblib'

# Function to initialize or load the model
def init_model():
    global intent_pipeline
    if os.path.exists(MODEL_PATH):
        intent_pipeline = joblib.load(MODEL_PATH)
    else:
        # Initialize with expanded sample intents
        training_data = [
            ("I want to book a room", "book_room"),
            ("Can I extend my stay?", "extend_stay"),
            ("What are your room types?", "room_info"),
            ("I need to cancel my booking", "cancel_booking"),
            ("How much does a suite cost?", "room_info"),
            ("I want to change my check-out date", "extend_stay"),
            ("Book a deluxe room for me", "book_room"),
            ("Can you tell me about your rooms?", "room_info"),
            ("I need to extend my stay by 2 nights", "extend_stay"),
            ("Cancel my reservation", "cancel_booking"),
            ("Extend my stay for 3 more nights", "extend_stay"),
            ("I want to stay an extra night", "extend_stay"),
            ("Can I add 2 more nights to my booking?", "extend_stay"),
            ("I need to extend my stay until next Friday", "extend_stay"),
            ("Please extend my stay by one day", "extend_stay"),
            ("I want to book a suite", "book_room"),
            ("What is the price of a deluxe room?", "room_info"),
            ("Can I book a room for 2 nights?", "book_room"),
            ("I need to extend my stay for 5 days", "extend_stay"),
            ("Extend my booking to include the weekend", "extend_stay"),
            ("Can you extend my stay by 4 nights?", "extend_stay"),
            ("I want to extend my stay for another week", "extend_stay"),
            ("Add 3 more nights to my booking", "extend_stay"),
            ("Can I extend my stay to next Monday?", "extend_stay"),
            ("I need to extend my stay for 2 more days", "extend_stay"),
            ("Extend my booking by 1 night", "extend_stay"),
            ("Can you extend my stay for 2 additional nights?", "extend_stay"),
            ("I want to extend my stay until the weekend", "extend_stay")
        ]
        X_train, y_train = zip(*training_data)
        
        intent_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english')),
            ('classifier', LogisticRegression(max_iter=1000))
        ])
        intent_pipeline.fit(X_train, y_train)
        save_model()

# Function to save the model
def save_model():
    joblib.dump(intent_pipeline, MODEL_PATH)

# Function to predict intent
def predict_intent(user_input):
    return intent_pipeline.predict([user_input])[0]

# Function to update the model with new intent
def update_model_with_intent(user_input, intent):
    global intent_pipeline
    X_train, y_train = zip(*intent_pipeline.steps[0][1].vocabulary_.items())
    X_train += (user_input,)
    y_train += (intent,)
    intent_pipeline.fit(X_train, y_train)
    save_model()

# Function to extract entities using spaCy
def extract_entities(text):
    doc = nlp(text)
    entities = {
        'DATE': [],
        'CARDINAL': [],
        'ROOM_TYPE': []
    }
    room_types = [room[0].lower() for room in get_room_options()]
    
    for ent in doc.ents:
        if ent.label_ == 'DATE':
            entities['DATE'].append(ent.text)
        elif ent.label_ == 'CARDINAL':
            entities['CARDINAL'].append(ent.text)
    
    for token in doc:
        if token.text.lower() in room_types:
            entities['ROOM_TYPE'].append(token.text.lower())
    
    return entities

# Function to generate response based on user input and conversation state
def generate_response(user_input, state):
    intent = predict_intent(user_input)
    entities = extract_entities(user_input)
    logging.info(f"Predicted intent: {intent}")
    logging.info(f"Extracted entities: {entities}")
    logging.info(f"Current state: {state}")

    if 'history' not in state:
        state['history'] = []
    state['history'].append(user_input)

    # Check if there's an existing booking
    existing_booking = all(key in state for key in ['room_type', 'check_in', 'check_out', 'guests', 'room_price'])

    if intent == "extend_stay" or "extend" in user_input.lower():
        if existing_booking:
            state["step"] = "extend_stay"
            return (f"Certainly! I'd be happy to help you extend your stay in the {state['room_type']} room. "
                    f"Your current booking is from {state['check_in']} to {state['check_out']}. "
                    "How many additional nights would you like to book?")
        else:
            return "I'd be happy to help you extend your stay, but I couldn't find an existing booking. Could you please provide your current booking details or make a new reservation first?"

    elif state["step"] == "extend_stay":
        if entities['CARDINAL']:
            nights = int(entities['CARDINAL'][0])
            current_checkout = datetime.strptime(state["check_out"], "%d-%m-%Y")
            new_checkout = (current_checkout + timedelta(days=nights)).strftime("%d-%m-%Y")
            additional_price = state["room_price"] * nights
            add_booking(state["user_id"], state["check_out"], new_checkout, state["guests"], state["room_type"], additional_price, is_extension=True)
            state["check_out"] = new_checkout
            return (f"Great! I've extended your stay for {nights} more nights. Your new check-out date will be {new_checkout}, "
                    f"and the additional cost is ${additional_price}. Your total stay is now from {state['check_in']} to {new_checkout}. "
                    "Is there anything else I can help you with?")
        else:
            return "I'm sorry, I didn't catch the number of nights. Could you please tell me how many additional nights you'd like to stay?"

    elif intent == "book_room" or (not existing_booking and state["step"] == "greeting"):
        rooms = get_room_options()
        response = "Great! Here are our available room types:\n\n"
        for room in rooms:
            response += f"• {room[0]}: ${room[1]} per night\n"
        response += "\nWhich type of room would you prefer?"
        state["step"] = "room_selection"
        return response

    elif intent == "room_info":
        rooms = get_room_options()
        response = "Here's information about our room types:\n\n"
        for room in rooms:
            response += f"• {room[0]}: ${room[1]} per night\n"
        return response

    elif existing_booking:
        return (f"Your current booking is a {state['room_type']} room from {state['check_in']} to {state['check_out']} "
                f"for {state['guests']} guests at ${state['room_price']} per night. "
                "How can I assist you further? You can ask to extend your stay or inquire about other services.")

    else:
        return "How can I assist you today? You can ask about booking a room, extending your stay, or inquire about our room types."

# Chatbot route with NLP-based flow and feedback mechanism
@app.route('/chat', methods=['POST'])
def chat():
    user_id = request.remote_addr
    text = request.json.get('text')
    feedback = request.json.get('feedback')
    
    if user_id not in conversation_state:
        conversation_state[user_id] = {"step": "greeting", "check_in": None, "check_out": None, "guests": None, "room_type": None, "room_price": None, "user_id": user_id}
    
    state = conversation_state[user_id]
    
    if feedback is not None:
        response = handle_feedback(feedback, text, state)
    else:
        response = generate_response(text, state)
    
    # Update the conversation state
    state['last_input'] = text
    state['last_response'] = response
    
    logging.info(f"User: {text}")
    logging.info(f"Bot: {response}")
    
    return jsonify({'response': response})

if __name__ == '__main__':
    init_db()
    init_model()
    app.run(debug=True, host='0.0.0.0', port=5001)
