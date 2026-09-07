from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    words = db.relationship('Word', backref='file', cascade='all, delete-orphan', lazy=True)


class Word(db.Model):
    __tablename__ = 'words'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    korean = db.Column(db.String(255), nullable=False)
    russian = db.Column(db.String(255), nullable=False)

    errors = db.relationship('ErrorLog', backref='word', cascade='all, delete-orphan', lazy=True)
    hard_marks = db.relationship('HardWord', backref='word', cascade='all, delete-orphan', lazy=True)


class ErrorLog(db.Model):
    __tablename__ = 'errors'

    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class HardWord(db.Model):
    __tablename__ = 'hard_words'

    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), unique=True, nullable=False)
