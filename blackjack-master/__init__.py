from flask import Flask, send_from_directory, render_template

app = Flask(__name__, static_folder='static', template_folder='templates')

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route for static files (CSS, JS, images)
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)