import random

from flask import session

from models import ErrorLog, HardWord, Word, db


def get_problem_word_ids(file_id=None):
    """Words that have at least one recorded error or are marked as hard."""
    error_q = db.session.query(Word.id).join(ErrorLog, Word.id == ErrorLog.word_id)
    hard_q = db.session.query(Word.id).join(HardWord, Word.id == HardWord.word_id)
    if file_id is not None:
        error_q = error_q.filter(Word.file_id == file_id)
        hard_q = hard_q.filter(Word.file_id == file_id)
    ids = {row[0] for row in error_q.all()} | {row[0] for row in hard_q.all()}
    return list(ids)


def start_session(mode, scope, word_ids, file_id=None, direction='mixed'):
    word_ids = list(word_ids)
    if mode in ('test', 'dictation'):
        random.shuffle(word_ids)

    session['mode'] = mode
    session['scope'] = scope
    session['file_id'] = file_id
    session['direction'] = direction
    session['queue'] = word_ids
    session['current'] = None
    session['current_direction'] = None
    session['total'] = len(word_ids)
    session['done'] = 0
    session['correct'] = 0


def is_complete():
    return session.get('current') is None and not session.get('queue')


def pop_next_word_id():
    if session.get('current') is not None:
        return session['current']
    queue = session.get('queue', [])
    if not queue:
        session['current'] = None
        return None
    current = queue.pop(0)
    session['queue'] = queue
    session['current'] = current
    return current


def skip_current():
    current = session.get('current')
    if current is not None:
        queue = session.get('queue', [])
        queue.append(current)
        session['queue'] = queue
        session['current'] = None
        session['current_direction'] = None


def resolve_current(correct=None):
    session['done'] = session.get('done', 0) + 1
    if correct:
        session['correct'] = session.get('correct', 0) + 1
    session['current'] = None
    session['current_direction'] = None


def progress():
    total = session.get('total', 0)
    done = session.get('done', 0)
    remaining = max(total - done, 0)
    percent = int(done / total * 100) if total else 100
    return {
        'total': total,
        'done': done,
        'remaining': remaining,
        'percent': percent,
        'correct': session.get('correct', 0),
    }
