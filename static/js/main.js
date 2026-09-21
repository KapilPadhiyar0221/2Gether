/** Entry point. Each module owns one behaviour and binds once, by delegation. */
import { initTheme } from './theme.js';
import { initModals } from './modal.js';
import { initLikes } from './likes.js';
import { initComments } from './comments.js';
import { initFollow } from './follow.js';
import { initComposer } from './composer.js';
import { initFeed } from './feed.js';
import { initSearch, initSearchShortcut } from './search.js';
import { initNotifications } from './notifications.js';
import { initNav, initForms } from './nav.js';
import { toast } from './ui.js';

function flushServerMessages() {
  const node = document.getElementById('server-messages');
  if (!node) return;
  try {
    JSON.parse(node.textContent).forEach(({ text, kind }) => {
      const type = kind.includes('error') ? 'error' : kind.includes('success') ? 'success' : 'info';
      toast(text, type);
    });
  } catch { /* nothing worth surfacing */ }
}

function start() {
  initTheme();
  initNav();
  initModals();
  initFeed();
  initComposer();
  initLikes();
  initComments();
  initFollow();
  initSearch();
  initSearchShortcut();
  initForms();
  if (document.querySelector('[data-notif-badge]')) initNotifications();
  flushServerMessages();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start);
} else {
  start();
}
