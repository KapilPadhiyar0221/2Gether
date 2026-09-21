/** Small shared UI helpers: toasts, count bumps, motion preference. */

const ICONS = { success: 'i-check', error: 'i-close', info: 'i-spark' };

export const prefersReducedMotion = () =>
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export function toast(text, kind = 'info', duration = 3600) {
  const host = document.getElementById('toasts');
  if (!host) return;

  const el = document.createElement('div');
  el.className = `toast toast--${kind}`;
  el.innerHTML = `<svg class="icon" viewBox="0 0 24 24"><use href="#${ICONS[kind] || ICONS.info}"/></svg><span></span>`;
  el.querySelector('span').textContent = text;
  host.append(el);

  const remove = () => {
    el.classList.add('is-leaving');
    el.addEventListener('animationend', () => el.remove(), { once: true });
    setTimeout(() => el.remove(), 400);
  };
  const timer = setTimeout(remove, duration);
  el.addEventListener('click', () => { clearTimeout(timer); remove(); });
}

/** Briefly animate a number that just changed, so the change is noticed. */
export function bump(el) {
  if (!el || prefersReducedMotion()) return;
  el.classList.remove('is-bumping');
  void el.offsetWidth; // restart the animation
  el.classList.add('is-bumping');
}

/** Replace innerHTML and run any entrance state the new nodes expect. */
export function setHTML(el, html) {
  el.innerHTML = html;
  return el;
}

export function formatCount(n) {
  if (n < 1000) return String(n);
  if (n < 1000000) return `${(n / 1000).toFixed(n < 10000 ? 1 : 0).replace('.0', '')}k`;
  return `${(n / 1000000).toFixed(1).replace('.0', '')}m`;
}
