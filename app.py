from flask import Flask, render_template, request, redirect, url_for, session
from database import get_scraped_data, store_scraped_data
from scraper import scrape_data

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session['username'] = username
        session['password'] = password  # Store password for scraping
        return redirect(url_for('menu'))
    return render_template('login.html')

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        class_input = request.form['class_name']
        session['class_name'] = class_input  # Store class name for scraping
        return redirect(url_for('scrape'))
    
    username = session['username']
    data = get_scraped_data(username)
    return render_template('menu.html', data=data)

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if 'username' not in session or 'class_name' not in session:
        return redirect(url_for('login'))
    username = session['username']
    password = session['password']
    class_input = session['class_name']
    scraped_data = scrape_data(username, password, class_input)  # Scrape data for the user
    store_scraped_data(username, scraped_data)  # Store the scraped data in the database
    return render_template('result.html', data=scraped_data)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('password', None)
    session.pop('class_name', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)