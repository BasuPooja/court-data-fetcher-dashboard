from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file,session, make_response
from .scraper import fetch_case_data
from .database import log_query
from .models import CaseQuery, ParsedCaseDetails
from . import db
from faker import Faker
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime
import random
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from flask import render_template
from sqlalchemy import func
from collections import defaultdict
from xhtml2pdf.default import DEFAULT_FONT
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from jinja2 import StrictUndefined


# Get absolute path to font file
font_path = os.path.join(os.path.dirname(__file__), 'static', 'fonts', 'NotoSansDevanagari-Regular.ttf')
pdfmetrics.registerFont(TTFont('NotoSansDevanagari', font_path))

faker = Faker()

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

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

@main.route('/captcha')
def generate_captcha():
    # Captcha configuration
    characters = string.ascii_uppercase + string.digits
    captcha_text = ''.join(random.choices(characters, k=6))
    session['captcha'] = captcha_text

    # Image settings
    width, height = 180, 60
    background_color = (230, 230, 255)  # Light purple/blue tone
    image = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(image)

    # Font setup
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()

    # Draw border
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(80, 80, 150), width=2)

    # Draw CAPTCHA text with random spacing and colors
    for i, char in enumerate(captcha_text):
        x = 10 + i * 25 + random.randint(-2, 2)
        y = random.randint(5, 15)
        draw.text((x, y), char, font=font, fill=(random.randint(0, 100), 0, random.randint(150, 255)))

    # Add noise - random lines
    for _ in range(8):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(150, 150, 255), width=2)

    # Add noise - random dots
    for _ in range(150):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(150, 255), random.randint(150, 255), random.randint(150, 255)))

    # Apply filter to slightly distort image
    image = image.filter(ImageFilter.GaussianBlur(0.5))

    # Serve image as response
    buffer = BytesIO()
    image.save(buffer, 'PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')

def absolute_path(relative_path):
    return os.path.abspath(os.path.join('app', relative_path))

@main.route('/fetch-case', methods=['GET', 'POST'])
def fetch_case():
    if request.method == 'POST':
        user_captcha = request.form.get('captcha')
        expected_captcha = session.get('captcha')

        if not user_captcha or user_captcha.upper() != expected_captcha:
            flash("❌ Invalid captcha. Please try again.", "danger")
            return redirect(url_for('main.fetch_case'))

        case_type = request.form['case_type']
        case_number = request.form['case_number']
        filing_year = request.form['year']
        court_complex = request.form['court_complex']

        query = {
            "id": random.randint(1000, 9999),
            "case_type": case_type,
            "case_number": case_number,
            "filing_year": filing_year,
            "court_complex": court_complex,
            "state": "Haryana",
            "district": "Faridabad",
            "query_time": datetime.now(),
            "status": "Active"
        }

        details = {
            "registration_number": f"REG-{datetime.now().year}{random.randint(1000,9999)}",
            "registration_date": "01-01-2023",
            "judgment_date": "05-01-2025",
            "petitioner": "John Doe",
            "respondent": "Jane Smith",
            "advocate_name": "A. Advocate",
            "next_hearing_date": "01-09-2025",
            "Remark": "ABC"
        }

        # Add absolute paths for logo and flag
        logo_path = absolute_path('static/media/logo.png')
        flag_path = absolute_path('static/media/flag.png')

        html = render_template(
            'GeneratedReport.html',
            query=query,
            details=details,
            current_date=datetime.now().strftime('%d-%m-%Y'),
            logo_path=logo_path,
            flag_path=flag_path
        )

        pdf_buffer = BytesIO()
        pisa.CreatePDF(html, dest=pdf_buffer)
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, mimetype='application/pdf',
                         download_name=f"Order_Summary_{query['id']}.pdf")

    captcha = generate_captcha()
    return render_template('fetch_case.html', captcha_text=captcha)


@main.route('/new-captcha')
def new_captcha():
    captcha = generate_captcha()
    return captcha

@main.route('/dashboard')
def dashboard():
    selected_year = request.args.get("year", "All")

    available_years_query = db.session.query(
        func.extract('year', CaseQuery.query_time).label('year')
    ).distinct().order_by(func.extract('year', CaseQuery.query_time)).all()

    available_years = [str(row.year) for row in available_years_query if row.year]

    filters = []
    if selected_year != "All":
        try:
            filters.append(func.extract('year', CaseQuery.query_time) == int(selected_year))
        except ValueError:
            selected_year = "All"  # Fallback to avoid crash

    # 1️⃣ Case Queries Over Time
    query_over_time = (
        db.session.query(
            func.to_char(CaseQuery.query_time, 'YYYY-MM').label('month'),
            func.count(CaseQuery.id).label('count')
        )
        .filter(*filters)
        .group_by('month')
        .order_by('month')
        .all()
    )
    months = [row.month for row in query_over_time]
    month_counts = [row.count for row in query_over_time]

    # 2️⃣ Status Distribution
    status_distribution = (
        db.session.query(
            CaseQuery.status,
            func.count(CaseQuery.id).label('count')
        )
        .filter(*filters)
        .group_by(CaseQuery.status)
        .all()
    )
    status_labels = [row.status for row in status_distribution]
    status_data = [row.count for row in status_distribution]

    # 3️⃣ Top 5 Case Types
    top_case_types = (
        db.session.query(
            CaseQuery.case_type,
            func.count(CaseQuery.id).label('count')
        )
        .filter(*filters)
        .group_by(CaseQuery.case_type)
        .order_by(func.count(CaseQuery.id).desc())
        .limit(5)
        .all()
    )
    type_labels = [row.case_type for row in top_case_types]
    type_data = [row.count for row in top_case_types]

    # 4️⃣ Summary Counts
    total_cases = sum(status_data) if status_data else 0
    pending_cases = dict(zip(status_labels, status_data)).get("Pending", 0)
    completed_cases = dict(zip(status_labels, status_data)).get("Completed", 0)
    other_cases = total_cases - pending_cases - completed_cases

    return render_template(
        'dashboard.html',
        selected_year=selected_year or "All",
        available_years=available_years or [],
        total_cases=total_cases or 0,
        pending_cases=pending_cases or 0,
        completed_cases=completed_cases or 0,
        other_cases=other_cases or 0,
        months=months or [],
        month_counts=month_counts or [],
        status_labels=status_labels or [],
        status_data=status_data or [],
        type_labels=type_labels or [],
        type_data=type_data or [],
        time_labels=months or [],
        time_values=month_counts or [],
        pie_labels=status_labels or [],
        pie_values=status_data or [],
        bar_labels=type_labels or [],
        bar_values=type_data or []
    )



