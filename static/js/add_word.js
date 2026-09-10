document.addEventListener('DOMContentLoaded', function () {
  const modal = document.getElementById('addWordModal');
  if (!modal) return;

  const step1 = document.getElementById('addWordStep1');
  const step2 = document.getElementById('addWordStep2');
  const nextBtn = document.getElementById('addWordNextBtn');
  const backBtn = document.getElementById('addWordBackBtn');
  const doneBtn = document.getElementById('addWordDoneBtn');
  const koreanInput = document.getElementById('addWordKorean');
  const russianInput = document.getElementById('addWordRussian');

  function showStep1() {
    step1.classList.remove('d-none');
    step2.classList.add('d-none');
    nextBtn.classList.remove('d-none');
    backBtn.classList.add('d-none');
    doneBtn.classList.add('d-none');
    koreanInput.focus();
  }

  function showStep2() {
    step1.classList.add('d-none');
    step2.classList.remove('d-none');
    nextBtn.classList.add('d-none');
    backBtn.classList.remove('d-none');
    doneBtn.classList.remove('d-none');
    russianInput.focus();
  }

  nextBtn.addEventListener('click', function () {
    if (!koreanInput.value.trim()) {
      koreanInput.focus();
      return;
    }
    showStep2();
  });

  backBtn.addEventListener('click', showStep1);

  modal.addEventListener('hidden.bs.modal', function () {
    koreanInput.value = '';
    russianInput.value = '';
    showStep1();
  });
});
