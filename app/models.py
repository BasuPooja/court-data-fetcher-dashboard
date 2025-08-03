from . import db
from datetime import datetime

class CaseQuery(db.Model):
    __tablename__ = 'case_queries'

    id = db.Column(db.Integer, primary_key=True)
    case_type = db.Column(db.String(50), nullable=False)
    case_number = db.Column(db.String(50), nullable=False)
    filing_year = db.Column(db.String(10), nullable=False)

    petitioner = db.Column(db.String(200))
    respondent = db.Column(db.String(200))
    filing_date = db.Column(db.String(50))
    next_hearing_date = db.Column(db.String(50))
    latest_order_url = db.Column(db.String(500))

    raw_html = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Success")  # Optional: Success / Failed

    def __repr__(self):
        return f"<CaseQuery {self.case_type}-{self.case_number}-{self.filing_year}>"
