/**
 * Post composer: autogrow, image preview, character feedback, submit states.
 * Validates the same things the server does, then lets the server decide.
 */
import { api } from './api.js';
import { toast } from './ui.js';
import { close as closeModal } from './modal.js';
import { prependPost } from './feed.js';

const MAX_CHARS = 1000;
const MAX_BYTES = 5 * 1024 * 1024;
const WARN_AT = 0.8;

function autogrow(el) {
  el.style.height = 'auto';
  el.style.height = `${el.scrollHeight}px`;
}

function updateCounter(form) {
  const body = form.querySelector('[data-composer-body]');
  const counter = form.querySelector('[data-counter]');
  const arc = form.querySelector('[data-counter-arc]');
  const text = form.querySelector('[data-counter-text]');
  const used = body.value.length;
  const ratio = used / MAX_CHARS;

  counter.classList.toggle('is-visible', ratio >= 0.5);
  counter.classList.toggle('is-warning', ratio >= WARN_AT && ratio < 1);
  counter.classList.toggle('is-over', ratio >= 1);

  const circumference = 56.5;
  arc.style.strokeDashoffset = String(circumference * (1 - Math.min(ratio, 1)));
  text.textContent = ratio >= WARN_AT ? String(MAX_CHARS - used) : '';
}

function refreshSubmit(form) {
  const body = form.querySelector('[data-composer-body]');
  const file = form.querySelector('[data-composer-file]');
  const submit = form.querySelector('[data-composer-submit]');
  submit.disabled = !body.value.trim() && !file.files.length;
}

function showError(form, message) {
  const el = form.querySelector('[data-composer-error]');
  el.textContent = message;
  el.hidden = !message;
}

function clearImage(form) {
  const file = form.querySelector('[data-composer-file]');
  const preview = form.querySelector('[data-composer-preview]');
  const img = form.querySelector('[data-composer-preview-img]');
  file.value = '';
  if (img.src.startsWith('blob:')) URL.revokeObjectURL(img.src);
  img.removeAttribute('src');
  preview.hidden = true;
  refreshSubmit(form);
}

export function initComposer() {
  document.addEventListener('input', (e) => {
    const body = e.target.closest('[data-composer-body]');
    if (!body) return;
    const form = body.closest('[data-composer]');
    autogrow(body);
    updateCounter(form);
    refreshSubmit(form);
    showError(form, '');
  });

  document.addEventListener('change', (e) => {
    const file = e.target.closest('[data-composer-file]');
    if (!file) return;
    const form = file.closest('[data-composer]');
    const image = file.files[0];
    if (!image) return clearImage(form);

    if (!image.type.startsWith('image/')) {
      showError(form, 'Pick an image file — JPG, PNG, WebP or GIF.');
      return clearImage(form);
    }
    if (image.size > MAX_BYTES) {
      showError(form, `That image is ${(image.size / 1048576).toFixed(1)} MB. Keep it under 5 MB.`);
      return clearImage(form);
    }

    showError(form, '');
    const preview = form.querySelector('[data-composer-preview]');
    const img = form.querySelector('[data-composer-preview-img]');
    if (img.src.startsWith('blob:')) URL.revokeObjectURL(img.src);
    img.src = URL.createObjectURL(image);
    preview.hidden = false;
    refreshSubmit(form);
  });

  document.addEventListener('click', (e) => {
    const clear = e.target.closest('[data-composer-clear]');
    if (clear) clearImage(clear.closest('[data-composer]'));
  });

  // Ctrl/Cmd + Enter posts, the way every editor does it.
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      const body = e.target.closest('[data-composer-body]');
      if (body) body.closest('[data-composer]').requestSubmit();
    }
  });

  document.addEventListener('submit', async (e) => {
    const form = e.target.closest('[data-composer]');
    if (!form) return;
    e.preventDefault();

    const submit = form.querySelector('[data-composer-submit]');
    const body = form.querySelector('[data-composer-body]');
    if (!body.value.trim() && !form.querySelector('[data-composer-file]').files.length) return;

    submit.classList.add('is-busy');
    submit.disabled = true;
    showError(form, '');

    try {
      const data = await api.post(form.action, new FormData(form));
      const placed = prependPost(data.html);

      body.value = '';
      autogrow(body);
      clearImage(form);
      updateCounter(form);
      if (form.classList.contains('composer--modal')) closeModal();
      toast(placed ? 'Posted' : 'Posted — it\u2019s on your profile', 'success', 2600);
    } catch (err) {
      showError(form, err.message);
    } finally {
      submit.classList.remove('is-busy');
      refreshSubmit(form);
    }
  });
}
