import logging
import spacy
import datetime
import re
from utils import  extract_user_id, validate_user_id
# Load spaCy model for NLP tasks
nlp = spacy.load("en_core_web_sm")

def handle_feedback(feedback, text, state):
    if feedback.lower() == "positive":
        return "Thank you for your positive feedback! We're glad you had a great experience."
    elif feedback.lower() == "negative":
        return "I'm sorry to hear that you had a negative experience. Could you please provide more details so we can improve?"
    elif feedback.lower() == "neutral":
        return "Thank you for your feedback! If you have any suggestions for improvement, please let us know."
    else:
        return "Thank you for your feedback! We appreciate your input."

def store_feedback(user_ip, user_input, correct_intent, predicted_intent):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_entry = f"{timestamp}\t{user_ip}\t{user_input}\t{correct_intent}\t{predicted_intent}\n"
    try:
        with open('feedback.txt', 'a') as f:
            f.write(feedback_entry)
        logging.info(f"Feedback stored successfully: {feedback_entry}")
    except Exception as e:
        logging.error(f"Error storing feedback: {e}")

def requires_feedback(text):
    feedback_indicators = [
        "not correct", "wrong", "meant", "not what I wanted", "change that",
        "incorrect", "didn't mean", "not right", "no", "never said",
        "misunderstood", "please fix", "not what I expected", "this is wrong",
        "isn't what I wanted", "not correct", "didn't understand",
        "not what I asked", "not helping", "isn't useful", "try again",
        "doesn't make sense", "don't think you got that", "misinterpreted",
        "not right at all", "off track", "not even close", "not getting it",
        "completely wrong", "need to clarify", "confused", "mistaken",
        "error", "mistake", "incorrect", "inaccurate", "not quite right"
    ]

    pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, feedback_indicators)) + r')\b', re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return True, match.group()

    negative_words = ["hate", "dislike", "angry", "frustrated", "disappointed",
                      "annoyed", "upset", "irritated", "dissatisfied", "unhappy"]
    word_count = Counter(word.lower() for word in text.split())
    negative_count = sum(word_count[word] for word in negative_words)
    if negative_count >= 2:
        return True, "negative sentiment"

    if '?' in text or '!' in text:
        return True, "punctuation"

    return False, None


import datetime


def store_feedback(user_ip, user_input, correct_intent, predicted_intent):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_entry = f"{timestamp}\t{user_ip}\t{user_input}\t{correct_intent}\t{predicted_intent}\n"
    
    try:
        with open('feedback.txt', 'a') as f:
            f.write(feedback_entry)
        logging.info(f"Feedback stored successfully: {feedback_entry}")
    except Exception as e:
        logging.error(f"Error storing feedback: {e}")

def update_training_data():
    feedback_data = []
    with open('feedback.txt', 'r') as f:
        for line in f:
            user_id, text, feedback, predicted_intent = line.strip().split('\t')
            if feedback.lower() != predicted_intent:
                feedback_data.append((text, feedback))
    
    return feedback_data

def get_correct_intent_from_feedback(feedback):
    # Use spaCy to process the feedback text
    doc = nlp(feedback)
    
    # Define a list of known intents
    known_intents = ["book_room", "extend_stay", "room_info", "cancel_booking"]
    
    # Extract potential intents from the feedback
    for token in doc:
        if token.text.lower() in known_intents:
            return token.text.lower()
    
    # If no known intent is found, return a default intent
    return "unknown_intent"



import re
from collections import Counter




def handle_user_identification(text, state):
    user_id = extract_user_id(text)
    
    if user_id and validate_user_id(user_id):
        state['user_id'] = user_id
        return f"Thank you for providing your user ID: {user_id}. How can I assist you today?"
    else:
        return "Please provide your user ID in the format 'user_XXX' where XXX is a three-digit number."
