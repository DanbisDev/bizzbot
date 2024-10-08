import requests
from flask import Flask, render_template, request, send_from_directory, jsonify
from bizzbot_scraper import get_csv_and_save
import os
app = Flask(__name__)

# Define the route for the main page
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/502', methods=['GET'])
def error_page():
    requests.get('intuitive-kindness.railway.internal:4444')
    return render_template('502.html')

# Handle 502 error
@app.errorhandler(502)
def bad_gateway_error(e):
    requests.get('intuitive-kindness.railway.internal:4444')
    return render_template('502.html'), 502

# Route to serve the file for download
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(directory='static', path=filename, as_attachment=True)

@app.route('/receive_html', methods=['POST'])
def receive_html():
    data = request.json
    html_content = data.get('html_content')

    # Process the HTML as needed (e.g., parse it with BeautifulSoup)
    if html_content:
        print("Received HTML content successfully.")
        # You can now parse and process the HTML using BeautifulSoup or save it
        return jsonify({"status": "success", "message": "HTML received and processed."})
    else:
        return jsonify({"status": "error", "message": "No HTML content received."}), 400


# Route to handle the form submission and return the download link
@app.route('/generate_link', methods=['POST'])
def generate_link():
    data = request.json
    get_csv_and_save(data['input'])
    filename = 'bizzbot_scrape.csv'  # You can change this to any file you want to serve
    download_link = f"/download/{filename}"
    return jsonify({"link": download_link})


if __name__ == '__main__':
    from waitress import serve

    port = 8080;
    serve(app, host="0.0.0.0", port=port)
    print("Now serving")
