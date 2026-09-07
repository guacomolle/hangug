function initQuiz(config) {
  const promptEl = document.getElementById('prompt');
  const feedbackEl = document.getElementById('feedback');
  const skipBtn = document.getElementById('skip-btn');
  const nextBtn = document.getElementById('next-btn');
  const progressWrap = document.getElementById('progress-wrap');

  const optionsEl = document.getElementById('options');
  const dictationForm = document.getElementById('dictation-form');
  const answerInput = document.getElementById('answer-input');
  const submitBtn = document.getElementById('submit-btn');

  const dirKrRuBtn = document.getElementById('dir-kr-ru');
  const dirRuKrBtn = document.getElementById('dir-ru-kr');

  let answered = false;
  let currentWordId = null;

  function renderProgress(progress) {
    progressWrap.innerHTML = `
      <div class="mb-4">
        <div class="d-flex justify-content-between small text-secondary mb-1">
          <span>${progress.done} / ${progress.total}</span>
          <span>${progress.remaining} осталось</span>
        </div>
        <div class="progress" role="progressbar" style="height: 8px;">
          <div class="progress-bar bg-info" style="width: ${progress.percent}%;"></div>
        </div>
      </div>`;
  }

  function setAnswering(enabled) {
    answered = !enabled;
    if (config.mode === 'test' && optionsEl) {
      optionsEl.querySelectorAll('button').forEach((b) => (b.disabled = !enabled));
    } else if (answerInput) {
      answerInput.disabled = !enabled;
      submitBtn.disabled = !enabled;
    }
    skipBtn.disabled = !enabled;
    nextBtn.classList.toggle('d-none', enabled);
  }

  async function loadQuestion() {
    feedbackEl.textContent = '';
    feedbackEl.className = 'mt-3 fw-semibold';

    const res = await fetch(config.questionUrl);
    const data = await res.json();
    renderProgress(data.progress);

    if (data.complete) {
      window.location.href = config.completeUrl;
      return;
    }

    currentWordId = data.question.word_id;
    promptEl.textContent = data.question.prompt;

    if (config.mode === 'test') {
      optionsEl.innerHTML = '';
      data.question.options.forEach((opt) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-outline-light text-start';
        btn.textContent = opt;
        btn.addEventListener('click', () => submitAnswer(opt, btn));
        optionsEl.appendChild(btn);
      });
    } else if (answerInput) {
      answerInput.value = '';
      answerInput.focus();
    }

    setAnswering(true);
  }

  async function submitAnswer(answerValue, clickedBtn) {
    if (answered) return;
    const res = await fetch(config.answerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ word_id: currentWordId, answer: answerValue }),
    });
    const data = await res.json();
    setAnswering(false);
    renderProgress(data.progress);

    if (data.correct) {
      feedbackEl.textContent = 'Верно!';
      feedbackEl.classList.add('text-success');
      if (clickedBtn) clickedBtn.classList.add('btn-success');
    } else {
      feedbackEl.textContent = `Неверно. Правильный ответ: ${data.correct_answer}`;
      feedbackEl.classList.add('text-danger');
      if (clickedBtn) clickedBtn.classList.add('btn-danger');
    }

    if (config.mode === 'test' && optionsEl) {
      optionsEl.querySelectorAll('button').forEach((b) => {
        if (b.textContent === data.correct_answer) b.classList.add('btn-success');
      });
    }
  }

  skipBtn.addEventListener('click', async () => {
    if (skipBtn.disabled) return;
    await fetch(config.skipUrl, { method: 'POST' });
    loadQuestion();
  });

  nextBtn.addEventListener('click', loadQuestion);

  if (dictationForm) {
    dictationForm.addEventListener('submit', (e) => {
      e.preventDefault();
      if (answered) return;
      submitAnswer(answerInput.value);
    });
  }

  if (dirKrRuBtn) {
    dirKrRuBtn.addEventListener('click', async () => {
      await fetch(config.directionUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: 'kr_ru' }),
      });
    });
  }
  if (dirRuKrBtn) {
    dirRuKrBtn.addEventListener('click', async () => {
      await fetch(config.directionUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: 'ru_kr' }),
      });
    });
  }

  loadQuestion();
}
