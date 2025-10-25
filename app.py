from flask import Flask, render_template

# Create the Flask app
app = Flask(__name__)

# Define a route (home page)
@app.route('/')
def home():
    return "<h1>Welcome to MyBudgetHub 💰</h1><p>Your personal finance dashboard is coming soon!</p>"

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
