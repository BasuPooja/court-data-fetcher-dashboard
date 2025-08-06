from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from .scraper import fetch_case_data
from .database import log_query
from .models import CaseQuery, ParsedCaseDetails
from . import db
from faker import Faker
import random
from flask import render_template, make_response
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime
from captcha.image import ImageCaptcha
import random
import string
from flask import session



faker = Faker()

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/captcha_image')
def captcha_image():
    # Generate random text
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    session['captcha'] = captcha_text

    image = ImageCaptcha()
    data = image.generate(captcha_text)

    return send_file(data, mimetype='image/png')


# @main.route('/fetch-case', methods=['GET', 'POST'])
# def fetch_case():
#     result = None
#     if request.method == 'POST':
#         case_number = request.form.get('case_number')
#         if case_number:
#             result = fetch_case_data(case_number)
#             log_query(case_number)
#     return render_template('fetch_case.html', result=result)
#

@main.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@main.route('/about-project')
def about_project():
    return render_template('aboutProject.html')

@main.route('/enter_case', methods=['GET', 'POST'])
def enter_case():
    current_year = datetime.now().year
    filing_year = ""

    if request.method == 'POST':
        case_type = request.form['case_type']
        case_number = request.form['case_number']
        filing_year = request.form['filing_year']

        # 1. Insert into CaseQuery
        new_query = CaseQuery(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year
        )
        db.session.add(new_query)
        db.session.commit()

        # 2. Get auto-generated case_id
        case_id = new_query.id

        # 3. Auto-generate data for ParsedCaseDetails
        parsed = ParsedCaseDetails(
            query_id=case_id,
            petitioner=faker.company(),
            respondent=faker.company(),
            filing_date=str(datetime.now().date()),  # or use faker.date()
            advocate_name=f"Adv. {faker.name()}",
            next_hearing_date=faker.date_between(start_date='today', end_date='+30d').strftime('%Y-%m-%d'),
            latest_pdf_link=f"https://example.com/case/{case_id}/latest.pdf"  # dummy link
        )
        db.session.add(parsed)
        db.session.commit()

        message = "Case and parsed details submitted successfully."
        return render_template('addCase.html', message=message, current_year=current_year, filing_year=filing_year)

    return render_template('addCase.html', current_year=current_year, filing_year=filing_year)

def generate_case_number():
    now = datetime.now()
    year_month = now.strftime('%Y%m')
    random_number = random.randint(1000, 9999)
    return f'CASE-{year_month}-{random_number}'

@main.route('/add_case', methods=['GET', 'POST'])
def add_case():
    if request.method == 'POST':
        new_case = CaseQuery(
            case_type=request.form['case_type'],
            case_number=request.form['case_number'],
            filing_year=request.form['filing_year'],
            state=request.form.get('state'),
            district=request.form.get('district'),
            court_complex=request.form.get('court_complex'),
        )
        db.session.add(new_case)
        db.session.commit()
        return redirect(url_for('main.add_parsed_case', query_id=new_case.id))

    generated_case_number = generate_case_number()
    return render_template('addCase.html',
                           current_year=datetime.now().year,
                           case_number=generated_case_number)

def generate_registration_number():
    now = datetime.now()
    year_month = now.strftime('%Y%m')
    random_number = random.randint(1000, 9999)
    return f'REG-{random_number}'

@main.route('/add_parsed_case/<int:query_id>', methods=['GET', 'POST'])
def add_parsed_case(query_id):
    message = None
    if request.method == 'POST':
        parsed = ParsedCaseDetails(
            query_id=query_id,
            registration_number=request.form.get('registration_number'),
            registration_date=request.form.get('registration_date'),
            judgment_date=request.form.get('judgment_date'),
            # petitioner=request.form.get('petitioner'),
            # respondent=request.form.get('respondent'),
            # advocate_name=request.form.get('advocate_name'),
            petitioner = faker.company(),
            respondent = faker.company(),
            advocate_name = faker.name(),
            next_hearing_date=faker.date_between(start_date='today', end_date='+30d').strftime('%Y-%m-%d')
        )
        db.session.add(parsed)
        db.session.commit()
        flash("✅ Parsed case details saved successfully!")
        return redirect(url_for('main.add_case'))  # Redirect to add_case page

    # Always return a response
    generated_registration_number = generate_registration_number()
    return render_template('add_parsed_details.html', query_id=query_id,
                           registration_number=generated_registration_number)
 # adjust import as needed

@main.route('/generate_order_pdf/<int:query_id>')
def generate_order_pdf(query_id):
    query = CaseQuery.query.get_or_404(query_id)
    details = query.case_detail

    # Render HTML with context
    html = render_template('order_judgment_pdf.html', query=query, details=details, current_date=datetime.now().strftime('%d-%m-%Y'))

    # Create PDF
    pdf_stream = BytesIO()
    pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=pdf_stream)

    response = make_response(pdf_stream.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Judgment_{query.case_number}.pdf'
    return response


# @main.route('/fetch-case', methods=['GET', 'POST'])
# def fetch_case():
#     if request.method == 'POST':
#         case_type = request.form['case_type']
#         case_number = request.form['case_number']
#         filing_year = request.form['year']
#         court_complex = request.form['court_complex']
#
#         # Optionally, validate captcha here if needed
#
#         # Fetch case query & details from DB
#         query = CaseQuery.query.filter_by(
#             case_type=case_type,
#             case_number=case_number,
#             filing_year=filing_year,
#             court_complex=court_complex
#         ).first()
#
#         if not query:
#             return render_template("fetch_case.html", error="No case found.")
#
#         details = ParsedCaseDetails.query.filter_by(query_id=query.id).first()
#
#         if not details:
#             return render_template("fetch_case.html", error="Details not found for this case.")
#
#         # Render the report template
#         current_date = datetime.now().strftime('%d-%m-%Y')
#
#         html = render_template(
#             'GeneratedReport.html',
#             query=query,
#             details=details,
#             current_date=current_date
#         )
#
#         # Generate PDF
#         pdf_buffer = BytesIO()
#         pisa.CreatePDF(html, dest=pdf_buffer)
#         pdf_buffer.seek(0)
#
#         # Option 1: Show inline in browser
#         return send_file(
#             pdf_buffer,
#             mimetype='application/pdf',
#             download_name=f"Order_Summary_{query.id}.pdf"
#         )
#
#         # Option 2 (alternate): Save and redirect to file URL
#         # pdf_path = f"static/pdfs/Order_Summary_{query.id}.pdf"
#         # with open(pdf_path, 'wb') as f:
#         #     pisa.CreatePDF(html, dest=f)
#         # return redirect(url_for('static', filename=f'pdfs/Order_Summary_{query.id}.pdf'))
#
#     # GET request
#     return render_template('fetch_case.html')


# @main.route('/fetch-case', methods=['GET', 'POST'])
# def fetch_case():
#     if request.method == 'POST':
#         user_captcha = request.form.get('captcha')
#         expected_captcha = session.get('captcha')
#
#         if not user_captcha or user_captcha.upper() != expected_captcha:
#             return render_template("fetch_case.html", error="❌ Invalid captcha. Please try again.")
#
#         # Proceed with DB fetch logic
#         case_type = request.form['case_type']
#         case_number = request.form['case_number']
#         filing_year = request.form['year']
#         court_complex = request.form['court_complex']
#
#         query = CaseQuery.query.filter_by(
#             case_type=case_type,
#             case_number=case_number,
#             filing_year=filing_year,
#             court_complex=court_complex
#         ).first()
#
#         if not query:
#             return render_template("fetch_case.html", error="No case found.")
#
#         details = ParsedCaseDetails.query.filter_by(query_id=query.id).first()
#
#         if not details:
#             return render_template("fetch_case.html", error="Details not found for this case.")
#
#         html = render_template(
#             'GeneratedReport.html',
#             query=query,
#             details=details,
#             current_date=datetime.now().strftime('%d-%m-%Y')
#         )
#
#         pdf_buffer = BytesIO()
#         pisa.CreatePDF(html, dest=pdf_buffer)
#         pdf_buffer.seek(0)
#
#         return send_file(
#             pdf_buffer,
#             mimetype='application/pdf',
#             download_name=f"Order_Summary_{query.id}.pdf"
#         )
#
#     return render_template('fetch_case.html')

@main.route('/fetch-case', methods=['GET', 'POST'])
def fetch_case():
    if request.method == 'POST':
        user_captcha = request.form.get('captcha')
        expected_captcha = session.get('captcha')

        if not user_captcha or user_captcha.upper() != expected_captcha:
            return render_template("fetch_case.html", error="❌ Invalid captcha. Please try again.")

        # Proceed with DB fetch logic
        case_type = request.form['case_type']
        case_number = request.form['case_number']
        filing_year = request.form['year']
        court_complex = request.form['court_complex']

        query = CaseQuery.query.filter_by(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year,
            court_complex=court_complex
        ).first()

        if not query:
            return render_template("fetch_case.html", error="No case found.")

        details = ParsedCaseDetails.query.filter_by(query_id=query.id).first()

        if not details:
            return render_template("fetch_case.html", error="Details not found for this case.")

        html = render_template(
            'GeneratedReport.html',
            query=query,
            details=details,
            current_date=datetime.now().strftime('%d-%m-%Y')
        )

        pdf_buffer = BytesIO()
        pisa.CreatePDF(html, dest=pdf_buffer)
        pdf_buffer.seek(0)

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            download_name=f"Order_Summary_{query.id}.pdf"
        )

    return render_template('fetch_case.html')

