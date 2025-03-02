from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from database import get_scraped_data, store_scraped_data, store_meetings, get_meetings
from scraper import scrape_data, scrape_hws, post_homework, get_list_msg
import csv
import os
import pytz
from datetime import datetime
from werkzeug.utils import secure_filename
from io import StringIO

app = Flask(__name__, static_folder='static')
app.secret_key = 'my_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session['username'] = username
        session['password'] = password  #store password for scraping
        return redirect(url_for('classMenu'))
    return render_template('login.html')

@app.route('/classMenu', methods=['GET', 'POST'])
def classMenu():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        class_input = request.form['class_name']
        session['class_name'] = class_input
        return redirect(url_for('optionsMenu'))
    username = session['username']
    data = get_scraped_data(username)
    return render_template('classMenu.html', data=data)

@app.route('/optionsMenu')
def optionsMenu():
    if 'username' not in session or 'class_name' not in session:
        return redirect(url_for('login'))
    return render_template('optionsMenu.html')

@app.route('/postHW', methods=['GET', 'POST'])
def postHW():
    if 'username' not in session or 'class_name' not in session:
        return redirect(url_for('login'))
    message = None
    username = session['username']
    password = session['password']
    class_name = session['class_name']
    if request.method == 'POST':
        class_type = request.form['class_type']
        hw_description = request.form['hw_description']
        post_homework(username, password, class_name, class_type)
        message = "Homework successfully posted!"
    return render_template('postHW.html', message=message)

@app.route('/hwMenu', methods=['GET', 'POST'])
def hwMenu():
    if 'username' not in session or 'class_name' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        hw_input = request.form['hw_input']
        session['hw_input'] = hw_input
        return redirect(url_for('scrape'))
    class_input = session['class_name']
    username = session['username']
    scraped_hws = scrape_hws(username, session['password'], class_input)
    session['scraped_hws'] = scraped_hws
    return render_template('hwMenu.html', scraped_hws=scraped_hws)

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if 'hw_input' not in session or 'class_name' not in session or 'scraped_hws' not in session:
        return redirect(url_for('hwMenu'))
    username = session['username']
    password = session['password']
    class_input = session['class_name']
    hw_input = session['hw_input']
    scraped_hws = session['scraped_hws']
    scraped_data = scrape_data(username, password, class_input, scraped_hws, hw_input)
    store_scraped_data(username, scraped_data)
    return render_template('result.html', data=scraped_data)

@app.route('/print_data', methods=['POST'])
def print_data():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 403
    username = session['username']
    data = get_scraped_data(username)
    if not data:
        return jsonify({'status': 'error', 'message': 'No data found'}), 404
    result_string = get_list_msg(data)
    return jsonify({'status': 'success', 'message': result_string}), 200

@app.route('/get_class_meetings')
def get_class_meetings():
    meetings = get_meetings()  #get meetings from the database
    user_timezone = request.args.get('timezone', 'UTC')
    for meeting in meetings:
        start = datetime.fromisoformat(meeting['start'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(meeting['end'].replace('Z', '+00:00'))
        start = start.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(user_timezone))
        end = end.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(user_timezone))
        meeting['start'] = start.isoformat()
        meeting['end'] = end.isoformat()
    return jsonify(meetings)

@app.route('/import_csv', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        meetings = []
        with open(file_path, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                meetings.append({
                    'title': row['title'],
                    'start': row['start'],
                    'end': row['end']
                })
        store_meetings(meetings)
        return jsonify({'message': 'CSV imported successfully'}), 200
    return jsonify({'message': 'Invalid file type'}), 400

@app.route('/import_file', methods=['POST'])
def import_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file and (file.filename.endswith('.csv') or file.filename.endswith('.txt')):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        meetings = []
        with open(file_path, 'r') as file_content:
            content = file_content.read()
            
        if ',' in content.split('\n')[0]:  # Assume CSV if first line contains commas
            reader = csv.DictReader(StringIO(content))
        else:  # Assume TXT otherwise
            lines = content.strip().split('\n')
            reader = [dict(zip(['title', 'start', 'end'], line.strip().split('\t'))) for line in lines[1:]]  # Skip header
        
        for row in reader:
            start = datetime.fromisoformat(row['start'])
            end = datetime.fromisoformat(row['end'])
            meetings.append({
                'title': row['title'],
                'start': start.isoformat(),
                'end': end.isoformat()
            })
        store_meetings(meetings)
        return jsonify({'message': 'File imported successfully'}), 200
    return jsonify({'message': 'Invalid file type'}), 400

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('password', None)
    session.pop('class_name', None)
    session.pop('hw_input', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)