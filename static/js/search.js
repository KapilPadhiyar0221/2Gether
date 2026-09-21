/**
 * Live people search: debounced, keyboard-navigable, cancels stale requests,
 * and keeps the address bar in sync so results are shareable and go-back-able.
 */
import { api } from './api.js';
import { toast } from './ui.js';

const DEBOUNCE = 220;

export function initSearch() {
  const form = document.querySelector('[data-search]');
  if (!form) return;

  const input = form.querySelector('[data-search-input]');
  const clear = form.querySelector('[data-search-clear]');
  const results = document.querySelector('[data-search-results]');
  let timer = null;
  let cursor = -1;
  let latest = 0;   // only the newest request is allowed to paint

  async function run(query, { push = true } = {}) {
    clear.hidden = !query;
    const ticket = ++latest;

    form.classList.add('is-loading');
    results.classList.add('is-stale');

    try {
      const data = await api.get(`${form.action}?q=${encodeURIComponent(query)}`);
      if (ticket !== latest) return;   // a newer keystroke already won
      results.innerHTML = data.html;
      cursor = -1;
      if (push) {
        const url = query ? `${form.action}?q=${encodeURIComponent(query)}` : form.action;
        history.replaceState({ q: query }, '', url);
      }
    } catch (err) {
      if (ticket === latest) toast(err.message, 'error');
    } finally {
      if (ticket === latest) {
        form.classList.remove('is-loading');
        results.classList.remove('is-stale');
      }
    }
  }

  input.addEventListener('input', () => {
    clearTimeout(timer);
    const query = input.value.trim();
    timer = setTimeout(() => run(query), DEBOUNCE);
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    clearTimeout(timer);
    run(input.value.trim());
  });

  clear.addEventListener('click', () => {
    input.value = '';
    input.focus();
    run('');
  });

  function moveCursor(step) {
    const items = [...results.querySelectorAll('.person')];
    if (!items.length) return;
    items[cursor]?.classList.remove('is-cursor');
    cursor = (cursor + step + items.length) % items.length;
    items[cursor].classList.add('is-cursor');
    items[cursor].scrollIntoView({ block: 'nearest' });
  }

  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); moveCursor(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); moveCursor(-1); }
    else if (e.key === 'Enter' && cursor > -1) {
      e.preventDefault();
      results.querySelectorAll('.person')[cursor]?.querySelector('.person__link')?.click();
    } else if (e.key === 'Escape' && input.value) {
      e.preventDefault();
      input.value = '';
      run('');
    }
  });
}

/** `/` anywhere jumps to search, the way it does in every tool people use. */
export function initSearchShortcut() {
  document.addEventListener('keydown', (e) => {
    if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
    const tag = document.activeElement?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement?.isContentEditable) return;

    const input = document.querySelector('[data-search-input]');
    if (input) { e.preventDefault(); input.focus(); input.select(); }
    else window.location.href = '/search/';
  });
}
