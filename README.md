# Hotel Booking Chatbot

This project implements an advanced Flask-based hotel booking chatbot using machine learning for intent classification. The chatbot allows users to book rooms, extend stays, get room information, cancel bookings, and more. The application is fully Dockerized for easy deployment and includes a feedback system for continuous improvement.

## Features

- **Intent Classification**: Uses machine learning (TF-IDF and SVM) to understand user intents
- **Room Booking**: Users can select different room types (Standard, Deluxe, Suite) with varying prices
- **Stay Extension**: Allows users to extend their current bookings
- **Room Information**: Provides details about room types, amenities, and prices
- **Booking Cancellation**: Enables users to cancel their existing bookings
- **User Identification**: Implements a user ID system for personalized interactions
- **Feedback System**: Collects user feedback to improve the chatbot's performance
- **SQLite Database**: Stores booking details, conversation history, and user data
- **Docker Support**: The application is containerized for easy setup and deployment

## Prerequisites

Before you begin, ensure you have the following installed:
- [Docker](https://www.docker.com/get-started)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/hotel-booking-chatbot.git
cd hotel-booking-chatbot
```

### 2. Build the Docker Image

```bash
docker build --no-cache -t hotel_booking_app .
```

### 3. Run the Docker Container

```bash
docker run -d -p 5001:5001 -v /Users/<id>/Downloads/hotel_booking_app-main:/app hotel_booking_app
```

This command runs the Flask app inside the container, exposes it on port 5001, and mounts the local directory to the container for easy development.

## Application Flow

1. The chatbot greets the user and asks for their user ID
2. Once identified, the user can interact with the chatbot using natural language
3. The chatbot classifies the user's intent and responds accordingly:
   - Booking a room
   - Extending a stay
   - Requesting room information
   - Cancelling a booking
4. The chatbot handles the entire conversation flow, asking for necessary details when required
5. All interactions are logged, and the system collects feedback for continuous improvement

## Example Flow

Bot: We have the following room options available: 
Standard: $100 per night, Deluxe: $150 per night, Suite: $200 per night.
Please select a room type.

You: Deluxe

Bot: You selected Deluxe for $150 per night. When would you like to check in? Please provide a valid date (e.g., 23-09-2024).

You: 23-09-2024

Bot: Got it! Now, what is your check-out date?

You: 25-09-2024

Bot: How many guests will be staying?

You: 2

Bot: Thank you! Your room is booked from 23-09-2024 to 25-09-2024 for 2 guests in a Deluxe room at $150 per night.

## Dependencies

- Flask: Web framework for the chatbot interface
- scikit-learn: For machine learning-based intent classification
- spaCy: For advanced natural language processing tasks
- SQLite3: Lightweight database for storing booking information and conversation history
- NLTK: For natural language processing tasks like tokenizing user input

## Database

The application uses an SQLite database to store:
- Booking details (room type, check-in/out dates, number of guests)
- User information
- Conversation history
- Feedback data for model improvement

## Feedback and Model Improvement

The chatbot includes a feedback system that:
- Collects user feedback on the chatbot's responses
- Stores this feedback for analysis
- Periodically retrains the intent classification model to improve accuracy

## Development and Debugging

- Logs are stored in `/app/chatbot.log` for debugging purposes
- The `-v` flag in the Docker run command allows for real-time code changes without rebuilding the image

## Security Considerations

- User inputs are sanitized to prevent potential security vulnerabilities
- The chatbot implements a basic user identification system

## Future Improvements

- Integration with external APIs for real-time data (e.g., room availability)
- Multi-language support
- Voice interface integration
- Deployment to cloud platforms for scalability

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

