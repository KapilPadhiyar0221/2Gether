/** Theme: light or dark, remembered per browser, follows the system until set. */

const KEY = '2gether:theme';

function apply(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
    btn.setAttribute(
      'aria-label',
      theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'
    );
  });
}

export function initTheme() {
  const media = window.matchMedia('(prefers-color-scheme: dark)');

  // If the person hasn't chosen, keep tracking the system.
  media.addEventListener('change', (e) => {
    if (!localStorage.getItem(KEY)) apply(e.matches ? 'dark' : 'light');
  });

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-theme-toggle]');
    if (!btn) return;
    const next =
      document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    apply(next);
    try { localStorage.setItem(KEY, next); } catch {}
  });

  apply(document.documentElement.getAttribute('data-theme') || 'light');
}
