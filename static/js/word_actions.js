document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.delete-word-form').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!window.confirm('Удалить это слово? История ошибок и отметка сложности тоже будут удалены.')) {
        event.preventDefault();
      }
    });
  });
});
