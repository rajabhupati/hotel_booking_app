import logging
from datetime import datetime, timedelta
from utils import predict_intent,extract_user_id,validate_user_id,validate_date
import spacy
from db import get_room_options, get_booking_details, add_booking,get_room_price
from feedback import handle_feedback, store_feedback, requires_feedback,get_correct_intent_from_feedback
from flask import request


# Load spaCy model
nlp = spacy.load("en_core_web_sm")

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
 

def handle_greeting(state):
    state["step"] = "request_user_id"
    return "Welcome! Please provide your user ID to proceed with your booking or to check your existing booking."

def handle_request_user_id(user_input, state):
    state["user_id"] = user_input
    booking_details = get_booking_details(state["user_id"])
    logging.info(f"Retrieved booking details: {booking_details}")

    if booking_details and len(booking_details) >= 4:
        state.update({
            "room_type": booking_details[0],
            "check_in": booking_details[1],
            "check_out": booking_details[2],
            "room_price": booking_details[3],
            "guest_name": "Guest",
            "existing_booking": True
        })
        state["step"] = "verify_user"
        return f"Hello! How can I assist you today? You can ask to extend your stay or book a new room."
    else:
        state["step"] = "new_booking"
        rooms = get_room_options()
        response = "I couldn't find any existing booking with this user ID. Let's proceed with a new booking. Here are our available room types:\n\n"
        response += "\n".join([f"• {room[0]}: ${room[1]} per night" for room in rooms])
        response += "\n\nWhich type of room would you prefer?"
        return response

def handle_verify_user(intent, state):
    if intent == "book_room":
        state['step'] = 'user_verified'
        return "Thank you for verifying your user ID. How can I assist you with your booking today?"
    elif intent == "extend_stay":
        state['step'] = 'extend_stay'
        return "Certainly! I'd be happy to help you extend your stay. How many additional nights would you like to book?"
    else:
        return "I'm sorry, I didn't understand that. Could you please specify if you want to book a room or extend your stay?"


def handle_new_or_extend(user_input, state):
    if "new" in user_input.lower():
        state["step"] = "new_booking"
        rooms = get_room_options()
        response = "Let's proceed with a new booking. Here are our available room types:\n\n"
        response += "\n".join([f"• {room[0]}: ${room[1]} per night" for room in rooms])
        response += "\n\nWhich type of room would you prefer?"
        return response
    elif "extend" in user_input.lower():
        state["step"] = "extend_stay"
        return (f"Certainly! I'd be happy to help you extend your stay in the {state['room_type']} room. "
                f"Your current booking is from {state['check_in']} to {state['check_out']}. "
                "How many additional nights would you like to book?")
    else:
        return "I'm sorry, I didn't understand that. Would you like to extend your stay or book a new room?"
    
from date_utils import parse_date, validate_date_range, get_date_suggestions

def handle_dates(entities, state):
    dates = entities.get('DATE', [])
    
    if len(dates) == 2:
        check_in = parse_date(dates[0])
        check_out = parse_date(dates[1])
        
        if check_in and check_out and validate_date_range(check_in, check_out):
            state['check_in'] = check_in
            state['check_out'] = check_out
            return f"Great! I've set your check-in date to {check_in} and check-out date to {check_out}. How many guests will be staying?"
        else:
            suggestions = get_date_suggestions(dates[0]) + get_date_suggestions(dates[1])
            return f"I'm sorry, but I couldn't understand the dates you provided. Could you please provide them in the format DD-MM-YYYY? For example: {', '.join(suggestions[:2])}"
    
    elif len(dates) == 1:
        parsed_date = parse_date(dates[0])
        if parsed_date:
            if not state['check_in']:
                state['check_in'] = parsed_date
                return f"I've set your check-in date to {parsed_date}. What's your check-out date?"
            elif not state['check_out']:
                if validate_date_range(state['check_in'], parsed_date):
                    state['check_out'] = parsed_date
                    return f"Great! I've set your check-out date to {parsed_date}. How many guests will be staying?"
                else:
                    return "The check-out date must be after the check-in date. Could you please provide a valid check-out date?"
        else:
            suggestions = get_date_suggestions(dates[0])
            return f"I'm sorry, but I couldn't understand the date you provided. Could you please provide it in the format DD-MM-YYYY? For example: {', '.join(suggestions[:2])}"
    
    return "Could you please provide your check-in and check-out dates in the format DD-MM-YYYY?"

    
def handle_extend_stay(entities, state):
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    if entities.get('CARDINAL'):
        cardinal = entities['CARDINAL'][0].lower().strip()
        nights = word_to_num.get(cardinal, cardinal)
        try:
            nights = int(nights)
        except ValueError:
            return "I'm sorry, I didn't catch the number of nights. Could you please tell me how many additional nights you'd like to stay?"

        try:
            current_checkout = datetime.strptime(state["check_out"], "%d-%m-%Y")
            new_checkout = (current_checkout + timedelta(days=nights)).strftime("%d-%m-%Y")
        except ValueError:
            return "There was an error processing the dates. Please try again."

        additional_price = state["room_price"] * nights
        add_booking(state["user_id"], state["check_out"], new_checkout, state["guests"], state["room_type"], additional_price, None, None)
        state["check_out"] = new_checkout
        logging.info(f"Extended stay for {nights} nights. New checkout date: {new_checkout}, Additional price: {additional_price}")
        
        return (f"Great! I've extended your stay for {nights} more nights. Your new check-out date will be {new_checkout}, "
                f"and the additional cost is ${additional_price}. Your total stay is now from {state['check_in']} to {new_checkout}. "
                "Is there anything else I can help you with?")
    else:
        return "I'm sorry, I didn't catch the number of nights. Could you please tell me how many additional nights you'd like to stay?"


def handle_new_booking(entities, state):
    if entities.get('ROOM_TYPE'):
        state["room_type"] = entities['ROOM_TYPE'][0]
        state["step"] = "booking_details"
        return f"You have selected a {state['room_type']} room. Please provide your check-in and check-out dates in DD-MM-YYYY format."
    else:
        return "I'm sorry, I didn't catch the room type. Could you please specify which type of room you would like to book?"

def handle_booking_details(entities, state):
    if entities.get('DATE'):
        if not state.get("check_in"):
            state["check_in"] = entities['DATE'][0]
            return "Got it. Now, please provide your check-out date."
        elif not state.get("check_out"):
            state["check_out"] = entities['DATE'][0]
            state["step"] = "guest_details"
            return "Thank you! How many guests will be staying?"
    else:
        return "I'm sorry, I didn't catch the dates. Could you please provide your check-in and check-out dates?"

def handle_guest_details(entities, state):
    if entities.get('CARDINAL'):
        state["guests"] = int(entities['CARDINAL'][0])
        room_price = get_room_price(state["room_type"])
        total_price = room_price * (datetime.strptime(state["check_out"], "%d-%m-%Y") - datetime.strptime(state["check_in"], "%d-%m-%Y")).days
        state.update({"room_price": room_price})
        state["step"] = "confirm_booking"
        return (f"Thank you! You have booked a {state['room_type']} room from {state['check_in']} to {state['check_out']} "
                f"for {state['guests']} guests. The total price will be ${total_price}. Would you like to confirm the booking?")
    else:
        return "I'm sorry, I didn't catch the number of guests. Could you please provide the number of guests?"

def handle_confirm_booking(user_input, state):
    if "yes" in user_input.lower():
        add_booking(state["user_id"], state["check_in"], state["check_out"], 
                    state["guests"], state["room_type"], 
                    state["room_price"], None, None)
        state["existing_booking"] = True
        return "Your booking has been confirmed! Thank you for choosing our service. Is there anything else I can help you with?"
    else:
        state.clear()
        return "Booking not confirmed. Let's start over. Which type of room would you prefer?"

def handle_room_info():
    rooms = get_room_options()
    response = "Here's information about our room types:\n\n"
    response += "\n".join([f"• {room[0]}: ${room[1]} per night" for room in rooms])
    return response



def generate_response(user_input, state):
    intent, confidence = predict_intent(user_input)  # Use predict_intent to classify the intent
    entities = extract_entities(user_input)
    logging.info(f"Predicted intent: {intent}, confidence: {confidence}")
    logging.info(f"Extracted entities: {entities}")
    logging.info(f"Current state before processing: {state}")

    # Check if feedback is required
    if handle_feedback_if_required(user_input, state, intent):
        return handle_feedback_if_required(user_input, state, intent)

    # Check if user_id is already in the state
    if 'user_id' not in state:
        return handle_user_id(user_input, state)

    # Handle intents after user_id is verified
    if state['step'] == 'verify_user':
        return handle_verify_user(intent, state)

    if state['step'] == 'user_verified':
        return handle_verified_user_intents(intent, entities, state)

    if state['step'] == 'request_room_type':
        return handle_room_type_request(entities, state)

    if state['step'] == 'confirm_booking':
        return handle_confirm_booking(entities, state)

    if state['step'] == 'booking_details':
        return handle_booking_details(user_input, state)

    if state['step'] == 'extend_stay':
        return handle_extend_stay(entities, state)

    # Handle feedback or other intents
    if intent not in ["book_room", "extend_stay", "room_info"]:
        return "I'm sorry, I didn't understand that. Could you please specify what you need help with?"

    return handle_default_responses(user_input, state, intent, entities)

def handle_feedback_if_required(user_input, state, intent):
    feedback_required, feedback_reason = requires_feedback(user_input)
    if feedback_required:
        correct_intent = get_correct_intent_from_feedback(user_input)
        store_feedback(request.remote_addr, user_input, correct_intent, intent)
        return handle_feedback(feedback_reason, user_input, state)
    return None


def handle_user_id(user_input, state):
    if validate_user_id(user_input):
        state['user_id'] = user_input
        state['step'] = 'user_verified'
        logging.info(f"User ID validated and stored in state: {state['user_id']}")
        return f"Thank you for providing your user ID: {user_input}. How can I assist you today?"
    else:
        logging.info("Invalid user ID provided.")
        return "Please provide a valid user ID in the format user_XXX where XXX is a three-digit number."


def handle_verified_user_intents(intent, entities, state):
    if intent == "book_room":
        state['step'] = 'request_room_type'
        return ("We have the following room types available:\n"
                "1. Standard - $100.0 per night\n"
                "2. Deluxe - $150.0 per night\n"
                "3. Suite - $200.0 per night\n"
                "Please specify which type of room you would like to book.")
    elif intent == "extend_stay":
        state['step'] = 'extend_stay'
        return "Certainly! How many additional nights would you like to book?"
    elif intent == "room_info":
        room_type = entities.get('ROOM_TYPE', [])
        if room_type:
            room_type = room_type[0]  # Assuming only one room type is mentioned
            return f"We have several {room_type} rooms available. Would you like to know more about their features or pricing?"
        else:
            return "Could you please specify the type of room you are interested in?"
    else:
        return "I'm sorry, I didn't understand that. Could you please specify what you need help with?"


def handle_room_type_request(entities, state):
    if 'ROOM_TYPE' in entities and entities['ROOM_TYPE']:
        state['room_type'] = entities['ROOM_TYPE'][0]
        state['step'] = 'confirm_booking'
        return f"You have selected a {state['room_type']} room. Please provide your check-in and check-out dates."
    return "Please specify the type of room you would like to book."


def handle_confirm_booking(entities, state):
    if 'DATE' in entities:
        dates = entities['DATE']
        logging.info(f"Dates extracted: {dates}")
        if len(dates) == 1:
            if not state.get('check_in'):
                if validate_date(dates[0]):
                    state['check_in'] = dates[0]
                    logging.info(f"Check-in date set: {state['check_in']}")
                    return "Please provide your check-out date."
                else:
                    logging.info("Invalid check-in date provided.")
                    return "The check-in date provided is invalid. Please provide a valid date in DD-MM-YYYY format."
            else:
                if validate_date(dates[0]):
                    state['check_out'] = dates[0]
                    state['step'] = 'booking_details'
                    logging.info(f"Check-out date set: {state['check_out']}")
                    return (f"Your booking details: {state['room_type']} room from {state['check_in']} to {state['check_out']}. "
                            "Please confirm your booking.")
                else:
                    logging.info("Invalid check-out date provided.")
                    return "The check-out date provided is invalid. Please provide a valid date in DD-MM-YYYY format."
        elif len(dates) == 2:
            if validate_date(dates[0]) and validate_date(dates[1]):
                state['check_in'] = dates[0]
                state['check_out'] = dates[1]
                state['step'] = 'booking_details'
                logging.info(f"Check-in and check-out dates set: {state['check_in']} to {state['check_out']}")
                return (f"Your booking details: {state['room_type']} room from {state['check_in']} to {state['check_out']}. "
                        "Please confirm your booking.")
            else:
                logging.info("One or both of the dates provided are invalid.")
                return "One or both of the dates provided are invalid. Please provide valid dates in DD-MM-YYYY format."
    logging.info("No dates provided.")
    return "Please provide both check-in and check-out dates."


def handle_booking_details(user_input, state):
    if user_input.lower() in ["yes", "confirm"]:
        if state.get('check_in') and state.get('check_out'):
            state['step'] = 'booking_confirmed'
            return (f"Thank you! Your booking for a {state['room_type']} room from {state['check_in']} to {state['check_out']} "
                    "has been confirmed. We look forward to your stay!")
        else:
            return "Please provide both check-in and check-out dates to confirm your booking."
    elif "extend" in user_input.lower():
        state['step'] = 'extend_stay'
        return (f"Certainly! I'd be happy to help you extend your stay in the {state['room_type']} room. "
                f"Your current booking is from {state['check_in']} to {state['check_out']}. "
                "How many additional nights would you like to book?")
    else:
        return "Booking not confirmed. Let's start over. Which type of room would you prefer?"



def handle_extend_stay(entities, state):
    if 'CARDINAL' in entities and entities['CARDINAL']:
        additional_nights = entities['CARDINAL'][0]
        # Logic to extend the stay by additional_nights
        return f"Your stay has been extended by {additional_nights} nights. Enjoy your extended stay!"
    else:
        return "Please specify the number of additional nights you would like to book."


def handle_default_responses(user_input, state, intent, entities):
    if 'history' not in state:
        state['history'] = []
    state['history'].append(user_input)

    if 'step' not in state:
        state['step'] = 'greeting'

    if "how are you" in user_input.lower():
        return "I'm good, thank you! How can I help you today?"

    if "good" in user_input.lower() or "satisfied" in user_input.lower():
        return "Thank you for choosing our service! If there's anything else you need, feel free to ask."

    if state["step"] == "greeting":
        return handle_greeting(state)
    elif state["step"] == "request_user_id":
        if validate_user_id(user_input):
            state['user_id'] = user_input
            state['step'] = 'user_verified'
            logging.info(f"User ID validated and stored in state: {state['user_id']}")
            return f"Thank you for providing your user ID: {user_input}. How can I assist you today?"
        else:
            logging.info("Invalid user ID provided.")
            return "Please provide a valid user ID in the format user_XXX where XXX is a three-digit number."
    elif state["step"] == "verify_user":
        return handle_verify_user(intent, state)
    elif state["step"] == "new_or_extend":
        return handle_new_or_extend(user_input, state)
    elif state["step"] == "book_room":
        return handle_new_or_extend(user_input, state)
    elif state["step"] == "extend_stay":
        return handle_extend_stay(entities, state)
    elif state["step"] == "new_booking":
        return handle_new_booking(entities, state)
    elif state["step"] == "booking_details":
        return handle_booking_details(entities, state)
    elif state["step"] == "guest_details":
        return handle_guest_details(entities, state)
    elif state["step"] == "confirm_booking":
        return handle_confirm_booking(user_input, state)
    elif intent == "room_info":
        return handle_room_info()
    elif state.get("existing_booking"):
        return (f"Your current booking is a {state['room_type']} room from {state['check_in']} to {state['check_out']} "
                f"for {state['guests']} guests at ${state['room_price']} per night. "
                "How can I assist you further? You can ask to extend your stay or inquire about other services.")
    else:
        return "How can I assist you today? You can ask about booking a room, extending your stay, or inquire about our room types."
