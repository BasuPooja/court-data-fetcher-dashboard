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
from flask import current_app


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
@main.route('/add_case', methods=['GET', 'POST'])
def add_case():
    generated_case_number = generate_case_number()

    if request.method == 'POST':
        case_type = request.form['case_type']
        case_number = request.form['case_number'] or generated_case_number
        filing_year = request.form['filing_year']
        state = request.form.get('state')
        district = request.form.get('district')
        court_complex = request.form.get('court_complex')

        # ✅ Check for duplicates
        existing_case = CaseQuery.query.filter_by(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year
        ).first()

        if existing_case:
            flash("⚠️ Case already exists in database.", "warning")
            return render_template(
                'addCase.html',
                current_year=datetime.now().year,
                case_number=generated_case_number
            )

        # ✅ Add new case
        new_case = CaseQuery(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year,
            state=state,
            district=district,
            court_complex=court_complex,
            raw_response=request.form.get('raw_response', '')  # optional
        )
        db.session.add(new_case)
        db.session.commit()

        flash("✅ Case added. Please enter parsed details.", "success")
        return redirect(url_for('main.add_parsed_case', query_id=new_case.id))

    return render_template(
        'addCase.html',
        current_year=datetime.now().year,
        case_number=generated_case_number
    )


@main.route('/add_parsed_case/<int:query_id>', methods=['GET', 'POST'])
def add_parsed_case(query_id):
    generated_registration_number = generate_registration_number()

    if request.method == 'POST':
        registration_number = request.form.get('registration_number') or generated_registration_number

        parsed = ParsedCaseDetails(
            query_id=query_id,
            registration_number=registration_number,
            registration_date=request.form.get('registration_date'),
            judgment_date=request.form.get('judgment_date'),
            petitioner=request.form.get('petitioner'),
            respondent=request.form.get('respondent'),
            advocate_name=request.form.get('advocate_name'),
            next_hearing_date=request.form.get('next_hearing_date'),
            Remark=request.form.get('remark')
        )
        db.session.add(parsed)
        db.session.commit()

        flash("✅ Parsed case details saved successfully.", "success")
        return redirect(url_for('main.add_case'))

    return render_template(
        'add_parsed_details.html',
        query_id=query_id,
        registration_number=generated_registration_number
    )


def generate_case_number():
    now = datetime.now()
    year_month = now.strftime('%Y%m')
    random_number = random.randint(1000, 9999)
    return f'CASE-{year_month}-{random_number}'


def generate_registration_number():
    now = datetime.now()
    random_number = random.randint(1000, 9999)
    return f'REG-{random_number}'

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


def create_captcha_text():
    """Generate and store captcha text in session."""
    characters = string.ascii_uppercase + string.digits
    captcha_text = ''.join(random.choices(characters, k=6))
    session['captcha'] = captcha_text
    return captcha_text

@main.route('/captcha')
def captcha_image():
    # Always create a fresh captcha text for each request
    captcha_text = create_captcha_text()

    # Image settings
    width, height = 180, 60
    background_color = (230, 230, 255)
    image = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(image)

    # Font
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()

    # Border
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(80, 80, 150), width=2)

    # CAPTCHA text
    for i, char in enumerate(captcha_text):
        x = 10 + i * 25 + random.randint(-2, 2)
        y = random.randint(5, 15)
        draw.text((x, y), char, font=font,
                  fill=(random.randint(0, 100), 0, random.randint(150, 255)))

    # Noise - lines
    for _ in range(8):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(150, 150, 255), width=2)

    # Noise - dots
    for _ in range(150):
        x, y = random.randint(0, width), random.randint(0, height)
        draw.point((x, y),
                   fill=(random.randint(150, 255),
                         random.randint(150, 255),
                         random.randint(150, 255)))

    # Slight blur
    image = image.filter(ImageFilter.GaussianBlur(0.5))

    buffer = BytesIO()
    image.save(buffer, 'PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')

@main.route('/new-captcha')
def new_captcha():
    create_captcha_text()
    return redirect(url_for('main.fetch_case'))

def absolute_path(relative_path):
    return os.path.abspath(os.path.join(current_app.root_path, relative_path))
#
# @main.route('/fetch-case', methods=['GET', 'POST'])
# def fetch_case():
#     if request.method == 'POST':
#         # 1. Validate Captcha
#         user_captcha = request.form.get('captcha')
#         expected_captcha = session.get('captcha')
#
#         if not user_captcha or user_captcha.strip().upper() != expected_captcha:
#             flash("❌ Invalid captcha. Please try again.", "danger")
#
#             # Create a new captcha without wiping the form
#             create_captcha_text()
#
#             # Pass back entered values so they stay in the form
#             return render_template(
#                 'fetch_case.html',
#                 form_data={
#                     'case_type': request.form.get('case_type', ''),
#                     'case_number': request.form.get('case_number', ''),
#                     'year': request.form.get('year', ''),
#                     'court_complex': request.form.get('court_complex', '')
#                 }
#             )
#
#         # 2. Read form fields
#         case_type = request.form['case_type'].strip()
#         case_number = request.form['case_number'].strip()
#         filing_year = request.form['year'].strip()
#         court_complex = request.form['court_complex'].strip()
#
#         # 3. Fetch query
#         query_obj = CaseQuery.query.filter_by(
#             case_type=case_type,
#             case_number=case_number,
#             filing_year=filing_year
#         ).first()
#
#         if not query_obj:
#             flash("⚠️ No matching case found in database.", "warning")
#             return redirect(url_for('main.fetch_case'))
#
#         # 4. Fetch details
#         details_obj = db.session.query(ParsedCaseDetails).filter(
#             ParsedCaseDetails.query_id == query_obj.id
#         ).first()
#
#         query_data = {
#             "id": query_obj.id,
#             "case_type": query_obj.case_type,
#             "case_number": query_obj.case_number,
#             "filing_year": query_obj.filing_year,
#             "court_complex": query_obj.court_complex,
#             "state": query_obj.state,
#             "district": query_obj.district,
#             "query_time": query_obj.query_time,
#             "status": query_obj.status
#         }
#
#         details_data = {}
#         if details_obj:
#             details_data = {
#                 "registration_number": details_obj.registration_number,
#                 "registration_date": details_obj.registration_date,
#                 "judgment_date": details_obj.judgment_date,
#                 "petitioner": details_obj.petitioner,
#                 "respondent": details_obj.respondent,
#                 "advocate_name": details_obj.advocate_name,
#                 "next_hearing_date": details_obj.next_hearing_date,
#                 "Remark": details_obj.Remark
#             }
#
#         # 5. Paths for PDF (absolute)
#         logo_abs_path = absolute_path('static/media/logo.png')
#         flag_abs_path = absolute_path('static/media/flag.png')
#
#         # 6. PDF absolute save path
#         pdf_filename = f"Order_Summary_{query_data['id']}.pdf"
#         pdf_dir = absolute_path('static/reports')
#         os.makedirs(pdf_dir, exist_ok=True)
#         pdf_abs_path = os.path.join(pdf_dir, pdf_filename)
#
#         # 7. HTML for PDF (no download link in PDF)
#         html_for_pdf = render_template(
#             'GeneratedReport.html',
#             query=query_data,
#             details=details_data,
#             current_date=datetime.now().strftime('%d-%m-%Y %H:%M'),
#             logo_path=logo_abs_path,
#             flag_path=flag_abs_path,
#             pdf_url=None,
#             auto_open_pdf = False
#         )
#
#         with open(pdf_abs_path, "wb") as f:
#             pisa.CreatePDF(html_for_pdf, dest=f)
#
#         # 8. Browser URL for the saved PDF
#         pdf_url = url_for("static", filename=f"reports/{pdf_filename}")
#
#         # 9. Render preview with working link
#         return render_template(
#             "GeneratedReport.html",
#             query=query_data,
#             details=details_data,
#             current_date=datetime.now().strftime('%d-%m-%Y %H:%M'),
#             logo_path=url_for('static', filename='media/logo.png'),
#             flag_path=url_for('static', filename='media/flag.png'),
#             pdf_url=pdf_url,
#             auto_open_pdf=True
#         )
#
#     return render_template('fetch_case.html', form_data={})

@main.route('/case-list')
def case_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # cases per page

    pagination = CaseQuery.query.order_by(CaseQuery.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    cases = pagination.items

    return render_template('case_list.html', cases=cases, pagination=pagination)


@main.route('/fetch-case', methods=['GET', 'POST'])
def fetch_case():
    if request.method == 'POST':
        # 1️⃣ Validate Captcha
        user_captcha = request.form.get('captcha')
        expected_captcha = session.get('captcha')

        form_data = {
            'court_complex': request.form.get('court_complex', ''),
            'case_type': request.form.get('case_type', ''),
            'case_number': request.form.get('case_number', ''),
            'year': request.form.get('year', '')
        }

        if not user_captcha or user_captcha.strip().upper() != expected_captcha:
            flash("❌ Invalid captcha. Please try again.", "danger")
            create_captcha_text()
            return render_template('fetch_case.html', form_data=form_data)

        # 2️⃣ Read form inputs
        case_type = form_data['case_type'].strip()
        case_number = form_data['case_number'].strip()
        filing_year = form_data['year'].strip()
        court_complex = form_data['court_complex'].strip()

        # 3️⃣ Search in DB
        query_obj = CaseQuery.query.filter_by(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year
        ).first()

        details_obj = None

        if not query_obj:
            # 4️⃣ Scrape if not found
            scraped_result = fetch_case_data(case_type, case_number, filing_year, court_complex)
            if not scraped_result:
                flash("⚠️ Case not found online or site unavailable.", "warning")
                return render_template('fetch_case.html', form_data=form_data)

            # 5️⃣ Save query
            query_obj = CaseQuery(
                case_type=case_type,
                case_number=case_number,
                filing_year=filing_year,
                court_complex=court_complex,
                status=scraped_result.get("status", "Pending"),
                raw_response=scraped_result.get("raw_html", "")
            )
            db.session.add(query_obj)
            db.session.commit()

            # 6️⃣ Save details
            details_obj = ParsedCaseDetails(
                query_id=query_obj.id,
                registration_number=scraped_result.get("registration_number"),
                registration_date=scraped_result.get("registration_date"),
                judgment_date=scraped_result.get("judgment_date"),
                petitioner=scraped_result.get("petitioner"),
                respondent=scraped_result.get("respondent"),
                advocate_name=scraped_result.get("advocate_name"),
                next_hearing_date=scraped_result.get("next_hearing_date"),
                Remark=scraped_result.get("remark")
            )
            db.session.add(details_obj)
            db.session.commit()
        else:
            # 7️⃣ Fetch existing details
            details_obj = db.session.query(ParsedCaseDetails).filter_by(query_id=query_obj.id).first()

        # 8️⃣ Prepare details_data
        details_data = {
            "registration_number": details_obj.registration_number if details_obj else "",
            "registration_date": details_obj.registration_date if details_obj else "",
            "judgment_date": details_obj.judgment_date if details_obj else "",
            "petitioner": details_obj.petitioner if details_obj else "",
            "respondent": details_obj.respondent if details_obj else "",
            "advocate_name": details_obj.advocate_name if details_obj else "",
            "next_hearing_date": details_obj.next_hearing_date if details_obj else "",
            "Remark": details_obj.Remark if details_obj else ""
        }

        # 🔔 Registration number missing?
        if not details_data["registration_number"]:
            flash("⚠️ Registration number not available for this case.", "warning")

        # 9️⃣ Prepare query_data
        query_data = {
            "id": query_obj.id,
            "case_type": query_obj.case_type,
            "case_number": query_obj.case_number,
            "filing_year": query_obj.filing_year,
            "court_complex": query_obj.court_complex,
            "state": query_obj.state,
            "district": query_obj.district,
            "query_time": query_obj.query_time,
            "status": query_obj.status
        }

        # 🔟 Generate PDF
        logo_abs_path = absolute_path('static/media/logo.png')
        flag_abs_path = absolute_path('static/media/flag.png')

        pdf_filename = f"Order_Summary_{query_data['id']}.pdf"
        pdf_dir = absolute_path('static/reports')
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_abs_path = os.path.join(pdf_dir, pdf_filename)

        html_for_pdf = render_template(
            'GeneratedReport.html',
            query=query_data,
            details=details_data,
            current_date=datetime.now().strftime('%d-%m-%Y %H:%M'),
            logo_path=logo_abs_path,
            flag_path=flag_abs_path,
            pdf_url=None,
            auto_open_pdf=False
        )

        with open(pdf_abs_path, "wb") as f:
            pisa.CreatePDF(html_for_pdf.encode('utf-8'), dest=f)

        pdf_url = url_for("static", filename=f"reports/{pdf_filename}")

        return render_template(
            "GeneratedReport.html",
            query=query_data,
            details=details_data,
            current_date=datetime.now().strftime('%d-%m-%Y %H:%M'),
            logo_path=url_for('static', filename='media/logo.png'),
            flag_path=url_for('static', filename='media/flag.png'),
            pdf_url=pdf_url,
            auto_open_pdf=True
        )

    return render_template('fetch_case.html', form_data={})

