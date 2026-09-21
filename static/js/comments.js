/**
 * Comment threads: expand on demand, load once, post and delete in place.
 */
import { api } from './api.js';
import { bump, formatCount, toast } from './ui.js';

async function loadThread(post, thread) {
  const list = thread.querySelector('[data-thread-list]');
  const toggle = post.querySelector('[data-comments-toggle]');
  try {
    const data = await api.get(toggle.dataset.commentsUrl);
    list.innerHTML = data.html;
    thread.dataset.loaded = '1';
  } catch (err) {
    list.innerHTML = `<p class="thread__empty">${err.message}</p>`;
  }
}

function updateCount(post, count) {
  const el = post.querySelector('[data-comment-count]');
  if (!el) return;
  el.textContent = formatCount(count);
  bump(el);
}

export function initComments() {
  // Open / close a thread.
  document.addEventListener('click', (e) => {
    const toggle = e.target.closest('[data-comments-toggle]');
    if (!toggle) return;

    const post = toggle.closest('[data-post]');
    const thread = post.querySelector('[data-thread]');
    const isOpen = !thread.hidden;

    if (isOpen) {
      thread.hidden = true;
      toggle.setAttribute('aria-expanded', 'false');
      return;
    }

    thread.hidden = false;
    thread.classList.add('is-opening');
    thread.addEventListener('animationend', () => thread.classList.remove('is-opening'), { once: true });
    toggle.setAttribute('aria-expanded', 'true');

    if (!thread.dataset.loaded) loadThread(post, thread);
  });

  // The reply button only wakes up when there's something to send.
  document.addEventListener('input', (e) => {
    const input = e.target.closest('[data-reply-input]');
    if (!input) return;
    const submit = input.closest('[data-reply]').querySelector('[data-reply-submit]');
    submit.disabled = input.value.trim().length === 0;
  });

  // Post a comment.
  document.addEventListener('submit', async (e) => {
    const form = e.target.closest('[data-reply]');
    if (!form) return;
    e.preventDefault();

    const input = form.querySelector('[data-reply-input]');
    const submit = form.querySelector('[data-reply-submit]');
    const body = input.value.trim();
    if (!body) return;

    submit.disabled = true;
    submit.classList.add('is-busy');

    try {
      const data = await api.post(form.action, { body });
      const post = form.closest('[data-post]');
      const list = post.querySelector('[data-thread-list]');
      list.querySelector('.thread__empty')?.remove();
      list.querySelector('.skeleton-thread')?.remove();

      const wrap = document.createElement('div');
      wrap.innerHTML = data.html.trim();
      const node = wrap.firstElementChild;
      node.classList.add('is-new');
      list.append(node);

      input.value = '';
      updateCount(post, data.count);
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      submit.classList.remove('is-busy');
      submit.disabled = input.value.trim().length === 0;
    }
  });

  // Delete a comment.
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-delete-comment]');
    if (!btn) return;

    const comment = btn.closest('[data-comment]');
    const post = btn.closest('[data-post]');
    comment.classList.add('is-leaving');

    try {
      const data = await api.post(btn.dataset.deleteComment);
      comment.addEventListener('animationend', () => comment.remove(), { once: true });
      setTimeout(() => comment.remove(), 300);
      if (post) updateCount(post, data.count);
      toast('Comment deleted', 'success');
    } catch (err) {
      comment.classList.remove('is-leaving');
      toast(err.message, 'error');
    }
  });
}
