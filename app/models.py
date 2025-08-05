from datetime import datetime
from . import db

class CaseQuery(db.Model):
    __tablename__ = 'case_queries'
    id = db.Column(db.Integer, primary_key=True)
    case_type = db.Column(db.String(20), nullable=False)
    case_number = db.Column(db.String(20), nullable=False)
    filing_year = db.Column(db.String(10), nullable=False)
    query_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Pending")

    # One-to-One or One-to-Many relation to ParsedCaseDetails (Optional)
    parsed_details = db.relationship('ParsedCaseDetails', backref='query', uselist=False)
    raw_response = db.relationship('RawResponse', backref='query', uselist=False)

class ParsedCaseDetails(db.Model):
    __tablename__ = 'parsed_case_details'
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('case_queries.id'))

    petitioner = db.Column(db.String(100))
    respondent = db.Column(db.String(100))
    filing_date = db.Column(db.String(20))
    next_hearing_date = db.Column(db.String(20))
    latest_pdf_link = db.Column(db.String(255))

class RawResponse(db.Model):
    __tablename__ = 'raw_responses'
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('case_queries.id'))
    html_content = db.Column(db.Text)  # Storing entire HTML response
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
