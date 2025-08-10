from datetime import datetime
from . import db

class CaseQuery(db.Model):
    __tablename__ = 'case_queries'

    id = db.Column(db.Integer, primary_key=True)
    case_type = db.Column(db.String(50), nullable=False)
    case_number = db.Column(db.String(50), nullable=False)
    filing_year = db.Column(db.String(10), nullable=False)

    state = db.Column(db.String(100))
    district = db.Column(db.String(100))
    court_complex = db.Column(db.String(150))

    query_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Pending")
    raw_response = db.Column(db.Text, nullable=True)  # store raw HTML or JSON from scraper

    # ✅ New field to store the latest PDF link (Requirement #2)
    latest_pdf_link = db.Column(db.String(300), nullable=True)

    # Relationship to parsed details
    case_detail = db.relationship('ParsedCaseDetails', backref='query', uselist=False)


class ParsedCaseDetails(db.Model):
    __tablename__ = 'parsed_case_details'

    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('case_queries.id'), nullable=False)

    registration_number = db.Column(db.String(50))
    registration_date = db.Column(db.String(20))
    judgment_date = db.Column(db.String(20))

    petitioner = db.Column(db.String(200))
    respondent = db.Column(db.String(200))
    advocate_name = db.Column(db.String(200))
    next_hearing_date = db.Column(db.String(20))

    remark = db.Column(db.Text, nullable=True)  # lowercase for Python convention

    # ✅ If you want to store multiple order/judgment PDF links later
    order_pdf_link = db.Column(db.String(300), nullable=True)

