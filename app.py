from flask import Flask, render_template, request, redirect, url_for, session
from database import get_scraped_data, store_scraped_data
from scraper import scrape_data, scrape_hws

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
        return redirect(url_for('classMenu'))
    return render_template('login.html')

@app.route('/classMenu', methods=['GET', 'POST'])
def classMenu():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        class_input = request.form['class_name']
        session['class_name'] = class_input
        return redirect(url_for('hwMenu'))
    username = session['username']
    data = get_scraped_data(username)
    return render_template('classMenu.html', data=data)

@app.route('/hwMenu', methods=['GET', 'POST'])
def hwMenu():
    if 'username' not in session or 'class_name' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        hw_input=request.form['hw_input']
        session['hw_input'] = hw_input
        return redirect(url_for('scrape'))
    class_input = session['class_name']
    username = session['username']
    scraped_hws = scrape_hws(username, session['password'], class_input)
    session['scraped_hws'] = scraped_hws
    return render_template('hwMenu.html', scraped_hws=scraped_hws)
    
@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if 'hw_input' not in session or 'class_name' not in session or 'hw_input' not in session or 'scraped_hws' not in session:
        return redirect(url_for('hwMenu'))
    username = session['username']
    password = session['password']
    class_input = session['class_name']
    hw_input = session['hw_input']
    scraped_hws = session['scraped_hws']
    scraped_data = scrape_data(username, password, class_input, scraped_hws, hw_input)
    store_scraped_data(username, scraped_data)
    return render_template('result.html', data=scraped_data)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('password', None)
    session.pop('class_name', None)
    session.pop('hw_input', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)