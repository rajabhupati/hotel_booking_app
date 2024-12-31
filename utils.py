import logging
import re
import os 
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
import numpy as np

# Define the path for storing the model
MODEL_PATH = '/app/intent_pipeline.joblib'

# Initialize the pipeline with TF-IDF and SGDClassifier
intent_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words='english')),
    ('classifier', SGDClassifier(max_iter=1000))
])

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
import logging

# Define the training data
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
    ("I want to extend my stay until the weekend", "extend_stay"),
    ("What amenities do you offer?", "room_info"),
    ("Is breakfast included in the room price?", "room_info"),
    ("Do you have any suites available?", "room_info"),
    ("How much does a single room cost per night?", "room_info"),
    ("Can I cancel my booking without a fee?", "cancel_booking"),
    ("What is your cancellation policy?", "cancel_booking"),
    ("Are pets allowed in the hotel rooms?", "room_info"),
    ("Do you have family rooms available?", "room_info"),
    ("Can I book multiple rooms at once?", "book_room"),
    ("Do you offer discounts for extended stays?", "room_info"),
    ("Is there parking available at the hotel?", "room_info"),
    ("Do you have accessible rooms for disabled guests?", "room_info"),
    ("What is your check-in time?", "room_info"),
    ("When is the check-out deadline?", "room_info"),
    ("Can I request an early check-in?", "room_info"),
    ("Is there free Wi-Fi in all rooms?", "room_info"),
    ("Do you provide airport shuttle services?", "room_info"),
    ("Can I request a room with a view of the city?", "book_room"),
    ("My user ID is ABC123", "user_identification"),
    ("I want to log in", "user_identification"),
    ("Here's my ID: XYZ789", "user_identification"),
    ("Can I provide my user ID?", "user_identification"),
    ("Login to my account", "user_identification")
]

# Separate inputs and labels
X, y = zip(*training_data)

# Create and train the pipeline
intent_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('svm', SVC(kernel='linear', probability=True))
])
intent_pipeline.fit(X, y)

def predict_intent(user_input):
    try:
        intent = intent_pipeline.predict([user_input])[0]
        confidence = max(intent_pipeline.decision_function([user_input])[0])
        return intent, confidence
    except Exception as e:
        logging.error(f"Error predicting intent: {str(e)}")
        return "unknown_intent", 0.0


def update_model_with_feedback():
    X, y = load_training_data()
    if not X or not y:
        logging.info("No training data available.")
        return
    if len(set(y)) < 20:
        logging.warning("Insufficient intent variety for retraining. At least two different intents are required.")
        return
    try:
        current_X, current_y = zip(*training_data)
        X = list(current_X) + X
        y = list(current_y) + y
        tfidf_vectorizer = intent_pipeline.named_steps['tfidf']
        classifier = intent_pipeline.named_steps['classifier']
        X_transformed = tfidf_vectorizer.fit_transform(X)
        classifier.partial_fit(X_transformed, y, classes=np.unique(y))
        intent_pipeline.named_steps['tfidf'] = tfidf_vectorizer
        intent_pipeline.named_steps['classifier'] = classifier
        save_model()
        logging.info(f"Model incrementally updated with {len(X)} training entries.")
    except Exception as e:
        logging.error(f"Error updating model: {str(e)}")

def update_model_with_intent(new_data):
    X, y = load_training_data()
    for text, intent in new_data:
        X.append(text)
        y.append(intent)
    vectorizer, clf = train_model(X, y)
    save_model(vectorizer, clf)

def extract_user_id(user_id):
    pattern = r'^user_\d{3}$'
    return bool(re.match(pattern, user_id))   

def validate_user_id(user_id):
    pattern = r'^user_\d{3}$'
    return bool(re.match(pattern, user_id))

def train_model(X, y):
    vectorizer = TfidfVectorizer(stop_words='english')
    X_vectorized = vectorizer.fit_transform(X)
    model = SGDClassifier(max_iter=1000)
    model.fit(X_vectorized, y)
    return vectorizer, model    

def save_model():
    joblib.dump(intent_pipeline, MODEL_PATH)

def load_training_data():
    training_data = []
    try:
        with open('feedback.txt', 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 5:
                    timestamp, user_ip, user_input, correct_intent, predicted_intent = parts
                    if correct_intent != predicted_intent:
                        training_data.append((user_input, correct_intent))
    except FileNotFoundError:
        logging.warning("feedback.txt not found. No feedback data to process.")
    
    if not training_data:
        default_data = [
            ("I want to book a room", "book_room"),
            ("Can I extend my stay?", "extend_stay"),
            ("What are your room types?", "room_info"),
            ("I need to cancel my booking", "cancel_booking")
        ]
        training_data.extend(default_data)
    
    X, y = zip(*training_data)
    return list(X), list(y)

def init_model():
    global intent_pipeline
    if os.path.exists(MODEL_PATH):
        intent_pipeline = joblib.load(MODEL_PATH)
    else:
        training_data = [
            # book_room intent
            ("I want to book a room", "book_room"),
            ("Can I reserve a suite for next week?", "book_room"),
            ("Book a deluxe room for me", "book_room"),
            ("I'd like to make a reservation for a standard room", "book_room"),
            ("How can I book a room for this weekend?", "book_room"),
            ("I need to reserve a room for two nights", "book_room"),
            ("Can you help me book a family room?", "book_room"),
            ("I want to book a room with ocean view", "book_room"),
            ("Is it possible to book a room for next month?", "book_room"),
            ("I'd like to make a booking for a group of 5", "book_room"),
            ("Can I book a room with a king-size bed?", "book_room"),
            ("I need to reserve a wheelchair accessible room", "book_room"),
            ("How do I book a room for a long-term stay?", "book_room"),
            ("I want to book a honeymoon suite", "book_room"),
            ("Can I make a reservation for New Year's Eve?", "book_room"),
            ("I'd like to book a room with a balcony", "book_room"),
            ("How can I reserve a room for a business trip?", "book_room"),
            ("I need to book a room near the conference center", "book_room"),
            ("Can I reserve a room with a kitchenette?", "book_room"),
            ("I want to book a penthouse suite", "book_room"),

            # extend_stay intent
            ("Can I extend my stay?", "extend_stay"),
            ("I want to change my check-out date", "extend_stay"),
            ("I need to extend my stay by 2 nights", "extend_stay"),
            ("Extend my stay for 3 more nights", "extend_stay"),
            ("I want to stay an extra night", "extend_stay"),
            ("Can I add 2 more nights to my booking?", "extend_stay"),
            ("I need to extend my stay until next Friday", "extend_stay"),
            ("Please extend my stay by one day", "extend_stay"),
            ("I need to extend my stay for 5 days", "extend_stay"),
            ("Extend my booking to include the weekend", "extend_stay"),
            ("Can you extend my stay by 4 nights?", "extend_stay"),
            ("I want to extend my stay for another week", "extend_stay"),
            ("Add 3 more nights to my booking", "extend_stay"),
            ("Can I extend my stay to next Monday?", "extend_stay"),
            ("I need to extend my stay for 2 more days", "extend_stay"),
            ("Extend my booking by 1 night", "extend_stay"),
            ("Can you extend my stay for 2 additional nights?", "extend_stay"),
            ("I want to extend my stay until the weekend", "extend_stay"),
            ("Is it possible to stay for an extra week?", "extend_stay"),
            ("Can I prolong my stay by a few more days?", "extend_stay"),

            # room_info intent
            ("What are your room types?", "room_info"),
            ("How much does a suite cost?", "room_info"),
            ("Can you tell me about your rooms?", "room_info"),
            ("What is the price of a deluxe room?", "room_info"),
            ("What amenities do you offer?", "room_info"),
            ("Is breakfast included in the room price?", "room_info"),
            ("Do you have any suites available?", "room_info"),
            ("How much does a single room cost per night?", "room_info"),
            ("Are pets allowed in the hotel rooms?", "room_info"),
            ("Do you have family rooms available?", "room_info"),
            ("Do you offer discounts for extended stays?", "room_info"),
            ("Is there parking available at the hotel?", "room_info"),
            ("Do you have accessible rooms for disabled guests?", "room_info"),
            ("What is your check-in time?", "room_info"),
            ("When is the check-out deadline?", "room_info"),
            ("Can I request an early check-in?", "room_info"),
            ("Is there free Wi-Fi in all rooms?", "room_info"),
            ("Do you provide airport shuttle services?", "room_info"),
            ("What's included in the minibar?", "room_info"),
            ("Do you have rooms with a jacuzzi?", "room_info"),

            # cancel_booking intent
            ("I need to cancel my booking", "cancel_booking"),
            ("Cancel my reservation", "cancel_booking"),
            ("Can I cancel my booking without a fee?", "cancel_booking"),
            ("What is your cancellation policy?", "cancel_booking"),
            ("How do I cancel my reservation?", "cancel_booking"),
            ("I want to cancel my room booking", "cancel_booking"),
            ("Is it possible to cancel my stay?", "cancel_booking"),
            ("Can you help me cancel my reservation?", "cancel_booking"),
            ("I need to cancel due to an emergency", "cancel_booking"),
            ("What's the deadline for cancelling my booking?", "cancel_booking"),
            ("How much will it cost to cancel my reservation?", "cancel_booking"),
            ("Can I get a refund if I cancel now?", "cancel_booking"),
            ("I want to cancel one of my room bookings", "cancel_booking"),
            ("Is there a cancellation fee?", "cancel_booking"),
            ("Can I cancel my booking and rebook for different dates?", "cancel_booking"),
            ("How do I cancel a group reservation?", "cancel_booking"),
            ("I need to cancel due to flight changes", "cancel_booking"),
            ("What happens if I cancel my non-refundable booking?", "cancel_booking"),
            ("Can I cancel my booking online?", "cancel_booking"),
            ("I want to cancel and book with a different hotel", "cancel_booking"),

            # user_identification intent
            ("My user ID is ABC123", "user_identification"),
            ("I want to log in", "user_identification"),
            ("Here's my ID: XYZ789", "user_identification"),
            ("Can I provide my user ID?", "user_identification"),
            ("Login to my account", "user_identification"),
            ("How do I access my booking details?", "user_identification"),
            ("I need to retrieve my user ID", "user_identification"),
            ("Can you look up my reservation with my ID?", "user_identification"),
            ("I forgot my user ID, how can I find it?", "user_identification"),
            ("Is my user ID the same as my booking number?", "user_identification"),
            ("Do I need to create an account to book a room?", "user_identification"),
            ("Can I use my email as my user ID?", "user_identification"),
            ("How do I reset my password?", "user_identification"),
            ("I'm having trouble logging in", "user_identification"),
            ("Can you send my user ID to my email?", "user_identification"),
            ("Where can I find my user ID on the website?", "user_identification"),
            ("Is there a guest login option?", "user_identification"),
            ("Do I need to log in to view my booking?", "user_identification"),
            ("Can I change my user ID?", "user_identification"),
            ("How do I create a new user account?", "user_identification")
        ]
        
        X_train, y_train = zip(*training_data)
        
        intent_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english')),
            ('classifier', SVC(kernel='linear', probability=True, max_iter=1000))
        ])
        
        intent_pipeline.fit(X_train, y_train)
        save_model()


def scheduled_retraining():
    logging.info("Starting scheduled model retraining...")
    update_model_with_feedback()
    logging.info("Scheduled model retraining completed.")


import datetime

def validate_date(date_text):
    try:
        datetime.datetime.strptime(date_text, '%d-%m-%Y')
        return True
    except ValueError:
        return False    
