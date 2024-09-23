# Hotel Booking Chatbot

This project is a Flask-based hotel booking chatbot that allows users to select room types, input booking details, and store the data in an SQLite database. The application is fully Dockerized for easy deployment.

## Features

- **Room Selection**: Users can select different room types (Standard, Deluxe, Suite) with varying prices.
- **Booking Details**: Users can input check-in and check-out dates and the number of guests.
- **SQLite Database**: All booking details are stored in an SQLite database.
- **Docker Support**: The application is containerized using Docker for easy setup and deployment.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://www.docker.com/get-started)


## Getting Started

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/your-username/hotel-booking-chatbot.git
cd hotel-booking-chatbot


2. Build the Docker Image
Next, build the Docker image for the Flask application:

docker build -t hotelbooking:latest .


This command will create a Docker image named hotelbooking based on the Dockerfile.

3. Run the Docker Container using the following command
docker run -p 5001:5000 hotelbooking
To run the Flask application in a Docker container:

This will start the Flask app inside the container and expose it on port 5000.
 You can access the chatbot at http://localhost:5000.


Application Flow

The bot will first ask the user to select a room type from available options (Standard, Deluxe, Suite) and display the respective price.
After room selection, the bot will ask for the check-in date, check-out date, and the number of guests.
Once all details are entered, the bot will confirm the booking and store the information in an SQLite database.

Example Flow :

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


Dependencies

The following Python packages are used:

Flask: The web framework used to build the chatbot.
nltk: For natural language processing tasks like tokenizing user input.
SQLite3: A lightweight database to store booking information.

Database

The application uses an SQLite database to store booking details, such as the user's selected room type, check-in and check-out dates, and the number of guests. The database is created automatically the first time the Docker container is run.


You can view the App UI [here](https://raw.githubusercontent.com/your-username/hotel_booking_app/main/Hotel Booking Chatbot.html).
