/**
 * Like / unlike.
 * The UI flips the moment you press; if the server disagrees we put it back
 * and say so. No page reload, no waiting on the network to feel responsive.
 */
import { api } from './api.js';
import { bump, formatCount, prefersReducedMotion, toast } from './ui.js';

function paint(btn, liked, count) {
  btn.classList.toggle('is-on', liked);
  btn.setAttribute('aria-pressed', String(liked));
  const countEl = btn.querySelector('[data-like-count]');
  if (countEl) {
    countEl.textContent = formatCount(count);
    bump(countEl);
  }
}

export function initLikes() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-like]');
    if (!btn || btn.dataset.busy) return;

    const countEl = btn.querySelector('[data-like-count]');
    const wasLiked = btn.classList.contains('is-on');
    const wasCount = parseInt(btn.dataset.raw || countEl?.textContent || '0', 10) || 0;

    // Optimistic flip.
    const nextCount = wasLiked ? Math.max(0, wasCount - 1) : wasCount + 1;
    btn.dataset.raw = nextCount;
    paint(btn, !wasLiked, nextCount);

    if (!wasLiked && !prefersReducedMotion()) {
      btn.classList.add('is-animating');
      setTimeout(() => btn.classList.remove('is-animating'), 480);
    }

    btn.dataset.busy = '1';
    try {
      const data = await api.post(btn.dataset.like);
      btn.dataset.raw = data.count;
      paint(btn, data.liked, data.count);
    } catch (err) {
      btn.dataset.raw = wasCount;
      paint(btn, wasLiked, wasCount);
      toast(err.message, 'error');
    } finally {
      delete btn.dataset.busy;
    }
  });
}
