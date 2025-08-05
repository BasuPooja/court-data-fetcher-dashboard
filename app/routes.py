from flask import Blueprint, render_template, request, redirect, url_for, flash
from .scraper import fetch_case_data
from .database import log_query
from .models import CaseQuery
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')


@main.route('/fetch-case', methods=['GET', 'POST'])
def fetch_case():
    result = None
    if request.method == 'POST':
        case_number = request.form.get('case_number')
        if case_number:
            result = fetch_case_data(case_number)
            log_query(case_number)
    return render_template('fetch_case.html', result=result)


@main.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@main.route('/about-project')
def about_project():
    return render_template('aboutProject.html')


@main.route('/enter_case', methods=['GET', 'POST'])
def enter_case():
    if request.method == 'POST':
        case_type = request.form['case_type']
        case_number = request.form['case_number']
        filing_year = request.form['filing_year']

        # Create CaseQuery entry
        new_query = CaseQuery(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year
        )
        db.session.add(new_query)
        db.session.commit()

        message = "Case details submitted successfully."
        return render_template('addCase.html', message=message)

    return render_template('addCase.html')
