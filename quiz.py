import random

from models import ErrorLog, HardWord, Word, db


def get_pool_words(file_id=None):
    if file_id is not None:
        return Word.query.filter_by(file_id=file_id).all()
    return Word.query.all()


def pick_direction(session_direction):
    if session_direction == 'mixed':
        return random.choice(['kr_ru', 'ru_kr'])
    return session_direction


def build_options(word, pool, direction):
    if direction == 'kr_ru':
        correct = word.russian
        pool_values = [w.russian for w in pool if w.id != word.id]
    else:
        correct = word.korean
        pool_values = [w.korean for w in pool if w.id != word.id]

    candidates = [v for v in dict.fromkeys(pool_values) if v != correct]
    random.shuffle(candidates)
    options = candidates[:3]

    if len(options) < 3:
        attr = 'russian' if direction == 'kr_ru' else 'korean'
        extra = [getattr(w, attr) for w in Word.query.filter(Word.id != word.id).all()]
        extra = [v for v in dict.fromkeys(extra) if v != correct and v not in options]
        random.shuffle(extra)
        options += extra[:3 - len(options)]

    options.append(correct)
    random.shuffle(options)
    return options


def build_test_question(word, pool, direction):
    prompt = word.korean if direction == 'kr_ru' else word.russian
    options = build_options(word, pool, direction)
    return {
        'word_id': word.id,
        'prompt': prompt,
        'direction': direction,
        'options': options,
    }


def check_test_answer(word, direction, answer):
    correct_value = word.russian if direction == 'kr_ru' else word.korean
    return (answer or '').strip() == correct_value.strip(), correct_value


def check_dictation_answer(word, answer):
    correct_value = word.korean
    return (answer or '').strip() == correct_value.strip(), correct_value


def record_error(word_id):
    db.session.add(ErrorLog(word_id=word_id))
    db.session.commit()


def toggle_hard(word_id):
    existing = HardWord.query.filter_by(word_id=word_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return False
    db.session.add(HardWord(word_id=word_id))
    db.session.commit()
    return True


def is_hard(word_id):
    return HardWord.query.filter_by(word_id=word_id).first() is not None
