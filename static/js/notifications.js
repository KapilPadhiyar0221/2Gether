/**
 * Activity badge. Polls quietly, and only while the tab is actually visible.
 */
import { api } from './api.js';
import { toast } from './ui.js';

const INTERVAL = 45000;

function paintBadge(count) {
  document.querySelectorAll('[data-notif-badge]').forEach((badge) => {
    const isDot = badge.classList.contains('badge--dot');
    badge.textContent = isDot ? '' : String(count);
    badge.classList.toggle('is-hidden', count === 0);
  });
}

export function initNotifications() {
  let timer = null;

  async function poll() {
    if (document.hidden) return;
    try {
      const data = await api.get('/notifications/count/');
      paintBadge(data.count);
    } catch { /* a failed poll is not worth interrupting anyone over */ }
  }

  function start() { stop(); timer = setInterval(poll, INTERVAL); }
  function stop() { if (timer) clearInterval(timer); timer = null; }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
    else { poll(); start(); }
  });
  start();

  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-mark-read]');
    if (!btn) return;
    btn.classList.add('is-busy');
    try {
      await api.post(btn.dataset.markRead);
      document.querySelectorAll('.note.is-unread').forEach((n) => n.classList.remove('is-unread'));
      paintBadge(0);
      btn.remove();
      toast('All caught up', 'success', 2000);
    } catch (err) {
      btn.classList.remove('is-busy');
      toast(err.message, 'error');
    }
  });
}
