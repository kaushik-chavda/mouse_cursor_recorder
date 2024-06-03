
# Mouse Tracker Web Application

## Introduction
Mouse Tracker is a web application that tracks mouse movements and captures images from a webcam when the left mouse button is pressed. The captured data is saved to a SQLite database and can be viewed in the browser.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/mouse-tracker.git
    ```
2. Navigate to the project directory:
    ```bash
   cd mouse-tracker
    ```
3. Install the dependencies:
    ```
   pip install -r requirements.txt
   ```

## Installation

1. Start the Flask server:

   ```bash
   python app.py
    ```
   
2. Open a web browser and go to http://localhost:5000/ to access the application.
3. Move the mouse and click the left mouse button to track movements and capture images.
4. To view the captured images, go to http://localhost:5000/images.


## Requirements
- Python 3.10
- Flask
- Flask-SocketIO
- OpenCV
- SQLite
