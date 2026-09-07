from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from models import File, Word, db
from parsers import parse_file
from quiz import (
    build_test_question,
    check_dictation_answer,
    check_test_answer,
    get_pool_words,
    is_hard,
    pick_direction,
    record_error,
    toggle_hard,
)
from session_logic import (
    get_problem_word_ids,
    has_history,
    is_complete,
    pop_next_word_id,
    progress,
    push_history,
    resolve_current,
    skip_current,
    start_session,
    undo_last,
)

bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
def index():
    files = File.query.order_by(File.upload_date.desc()).all()
    problem_count = len(get_problem_word_ids())
    return render_template('index.html', files=files, problem_count=problem_count)


@bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')

    uploaded = request.files.get('file')
    if not uploaded or uploaded.filename == '':
        flash('Выберите файл для загрузки', 'danger')
        return redirect(url_for('main.upload'))

    if not allowed_file(uploaded.filename):
        flash('Неподдерживаемый формат файла. Разрешены: .docx, .xlsx, .csv', 'danger')
        return redirect(url_for('main.upload'))

    filename = secure_filename(uploaded.filename)

    try:
        pairs = parse_file(filename, uploaded.stream)
    except Exception as exc:
        flash(f'Ошибка обработки файла: {exc}', 'danger')
        return redirect(url_for('main.upload'))

    new_file = File(name=filename, upload_date=datetime.utcnow())
    db.session.add(new_file)
    db.session.flush()

    for kr, ru in pairs:
        db.session.add(Word(file_id=new_file.id, korean=kr, russian=ru))

    db.session.commit()
    flash(f'Загружено слов: {len(pairs)}', 'success')
    return redirect(url_for('main.file_detail', file_id=new_file.id))


@bp.route('/file/<int:file_id>')
def file_detail(file_id):
    file = File.query.get_or_404(file_id)
    words = Word.query.filter_by(file_id=file_id).order_by(Word.id).all()
    local_problem_count = len(get_problem_word_ids(file_id=file_id))
    return render_template(
        'file_words.html', file=file, words=words, local_problem_count=local_problem_count
    )


@bp.route('/errors')
def errors_mode_select():
    file_id = request.args.get('file_id', type=int)

    if file_id:
        file = File.query.get_or_404(file_id)
        problem_count = len(get_problem_word_ids(file_id=file_id))
        scope = 'file_errors'
    else:
        file = None
        problem_count = len(get_problem_word_ids())
        scope = 'errors'

    if problem_count == 0:
        flash('Проблемных слов не найдено', 'warning')
        return redirect(url_for('main.file_detail', file_id=file_id) if file_id else url_for('main.index'))

    return render_template('errors_select.html', problem_count=problem_count, scope=scope, file=file)


@bp.route('/start-session', methods=['GET', 'POST'])
def start_session_route():
    mode = request.args.get('mode')
    scope = request.args.get('scope')
    file_id = request.args.get('file_id', type=int)
    direction = request.args.get('direction', 'mixed')

    if mode not in ('memorize', 'test', 'dictation'):
        flash('Некорректный режим', 'danger')
        return redirect(url_for('main.index'))

    if scope == 'file':
        file = File.query.get_or_404(file_id)
        word_ids = [w.id for w in Word.query.filter_by(file_id=file.id).order_by(Word.id).all()]
        if not word_ids:
            flash('В этом файле нет слов', 'warning')
            return redirect(url_for('main.file_detail', file_id=file.id))
        start_session(mode, 'file', word_ids, file_id=file.id, direction=direction)

    elif scope == 'file_errors':
        file = File.query.get_or_404(file_id)
        word_ids = get_problem_word_ids(file_id=file.id)
        if not word_ids:
            flash('В этом файле нет проблемных слов', 'warning')
            return redirect(url_for('main.file_detail', file_id=file.id))
        start_session(mode, 'file_errors', word_ids, file_id=file.id, direction=direction)

    elif scope == 'errors':
        word_ids = get_problem_word_ids()
        if not word_ids:
            flash('Список проблемных слов пуст', 'warning')
            return redirect(url_for('main.index'))
        start_session(mode, 'errors', word_ids, file_id=None, direction=direction)

    else:
        flash('Некорректная область слов', 'danger')
        return redirect(url_for('main.index'))

    return redirect(url_for(f'main.session_{mode}'))


def _current_pool():
    scope = session.get('scope')
    file_id = session.get('file_id')
    if scope in ('file', 'file_errors'):
        return get_pool_words(file_id=file_id)
    return get_pool_words()


# ---- Memorize (server-rendered, no JS required) ----

@bp.route('/session/memorize')
def session_memorize():
    if session.get('mode') != 'memorize':
        return redirect(url_for('main.index'))
    if is_complete():
        return redirect(url_for('main.session_complete'))
    word_id = pop_next_word_id()
    word = Word.query.get_or_404(word_id)
    return render_template(
        'memorize.html', word=word, hard=is_hard(word.id), progress=progress(), has_history=has_history()
    )


@bp.route('/session/memorize/next', methods=['POST'])
def session_memorize_next():
    word_id = session.get('current')
    if word_id is not None:
        push_history(word_id, 'next')
    resolve_current()
    if is_complete():
        return redirect(url_for('main.session_complete'))
    return redirect(url_for('main.session_memorize'))


@bp.route('/session/memorize/skip', methods=['POST'])
def session_memorize_skip():
    word_id = session.get('current')
    if word_id is not None:
        push_history(word_id, 'skip')
    skip_current()
    return redirect(url_for('main.session_memorize'))


@bp.route('/session/memorize/back', methods=['POST'])
def session_memorize_back():
    undo_last()
    return redirect(url_for('main.session_memorize'))


@bp.route('/session/memorize/star', methods=['POST'])
def session_memorize_star():
    word_id = session.get('current')
    if word_id:
        toggle_hard(word_id)
    return redirect(url_for('main.session_memorize'))


# ---- Test / Dictation (JS-driven) ----

@bp.route('/session/test')
def session_test():
    if session.get('mode') != 'test':
        return redirect(url_for('main.index'))
    if is_complete():
        return redirect(url_for('main.session_complete'))
    return render_template('test.html', progress=progress(), direction=session.get('direction'))


@bp.route('/session/dictation')
def session_dictation():
    if session.get('mode') != 'dictation':
        return redirect(url_for('main.index'))
    if is_complete():
        return redirect(url_for('main.session_complete'))
    return render_template('dictation.html', progress=progress())


@bp.route('/session/complete')
def session_complete():
    mode = session.get('mode')
    scope = session.get('scope')
    file_id = session.get('file_id')
    direction = session.get('direction', 'mixed')
    summary = progress()
    return render_template(
        'session_complete.html', mode=mode, scope=scope, file_id=file_id, direction=direction, summary=summary
    )


# ---- JSON API for test & dictation ----

@bp.route('/api/session/question')
def api_question():
    mode = session.get('mode')
    if mode not in ('test', 'dictation'):
        return jsonify({'error': 'no active session'}), 400

    if is_complete():
        return jsonify({'complete': True, 'progress': progress()})

    word_id = pop_next_word_id()
    word = Word.query.get_or_404(word_id)

    if mode == 'test':
        direction = session.get('current_direction')
        if not direction:
            direction = pick_direction(session.get('direction', 'mixed'))
            session['current_direction'] = direction
        pool = _current_pool()
        question = build_test_question(word, pool, direction)
        return jsonify({'complete': False, 'question': question, 'progress': progress()})

    return jsonify({
        'complete': False,
        'question': {'word_id': word.id, 'prompt': word.russian},
        'progress': progress(),
    })


@bp.route('/api/session/answer', methods=['POST'])
def api_answer():
    mode = session.get('mode')
    data = request.get_json(force=True, silent=True) or {}
    word_id = session.get('current')

    if mode not in ('test', 'dictation') or word_id is None:
        return jsonify({'error': 'no active question'}), 400

    word = Word.query.get_or_404(word_id)
    answer = data.get('answer', '')

    if mode == 'test':
        direction = session.get('current_direction', 'kr_ru')
        correct, correct_value = check_test_answer(word, direction, answer)
    else:
        correct, correct_value = check_dictation_answer(word, answer)

    if not correct:
        record_error(word.id)

    resolve_current(correct=correct)

    return jsonify({
        'correct': correct,
        'correct_answer': correct_value,
        'progress': progress(),
        'complete': is_complete(),
    })


@bp.route('/api/session/skip', methods=['POST'])
def api_skip():
    skip_current()
    return jsonify({'progress': progress()})


@bp.route('/api/session/direction', methods=['POST'])
def api_direction():
    data = request.get_json(force=True, silent=True) or {}
    new_direction = data.get('direction')
    if new_direction in ('kr_ru', 'ru_kr'):
        session['direction'] = new_direction
        session['current_direction'] = None
    return jsonify({'direction': session.get('direction')})
