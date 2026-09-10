document.addEventListener('DOMContentLoaded', function () {
  const modal = document.getElementById('renameModal');
  if (!modal) return;

  const input = document.getElementById('renameInput');
  const form = document.getElementById('renameForm');

  modal.addEventListener('show.bs.modal', function (event) {
    const btn = event.relatedTarget;
    if (!btn) return;
    const fileId = btn.getAttribute('data-file-id');
    const fileName = btn.getAttribute('data-file-name');
    input.value = fileName || '';
    form.action = '/file/' + fileId + '/rename';
  });
});
