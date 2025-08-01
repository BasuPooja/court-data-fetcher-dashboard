from flask import Blueprint, render_template, request
from .scraper import fetch_case_data
from .database import log_query

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        case_number = request.form.get('case_number')
        if case_number:
            result = fetch_case_data(case_number)
            log_query(case_number)
    return render_template('index.html', result=result)

@main.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
