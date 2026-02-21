from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, JSON
from datetime import datetime
from app.models.base import Base


class StockInfo(Base):
    __tablename__ = "stock_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100))
    market = Column(String(10))  # CN, US, HK
    sector = Column(String(100))
    industry = Column(String(100))
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockDaily(Base):
    __tablename__ = "stock_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)

    __table_args__ = ({"sqlite_autoincrement": True},)


class FinancialStatement(Base):
    __tablename__ = "financial_statement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    report_date = Column(Date, nullable=False)
    statement_type = Column(String(20))  # income, balance, cashflow
    data = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)


class AnalysisRecord(Base):
    __tablename__ = "analysis_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(100))
    market = Column(String(10))
    analysis_date = Column(DateTime, default=datetime.utcnow)
    fundamental_score = Column(Float)
    technical_score = Column(Float)
    sentiment_score = Column(Float)
    composite_score = Column(Float)
    verdict = Column(String(20))  # strong_buy, buy, hold, sell, strong_sell
    ai_provider = Column(String(20))
    fundamental_detail = Column(JSON)
    technical_detail = Column(JSON)
    sentiment_detail = Column(JSON)
    ai_synthesis = Column(JSON)
