/** Accessible modal: focus trap, Escape, scroll lock, restore focus. */

let openModal = null;
let lastFocused = null;

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select, [tabindex]:not([tabindex="-1"])';

export function open(name) {
  const modal = document.querySelector(`[data-modal="${name}"]`);
  if (!modal || openModal) return;

  lastFocused = document.activeElement;
  modal.hidden = false;
  document.body.style.overflow = 'hidden';
  openModal = modal;

  const first = modal.querySelector('textarea, input, button');
  requestAnimationFrame(() => first && first.focus());
}

export function close() {
  if (!openModal) return;
  const modal = openModal;
  openModal = null;
  modal.classList.add('is-closing');

  const finish = () => {
    modal.hidden = true;
    modal.classList.remove('is-closing');
    document.body.style.overflow = '';
    if (lastFocused && lastFocused.isConnected) lastFocused.focus();
  };
  const panel = modal.querySelector('.modal__panel');
  panel.addEventListener('animationend', finish, { once: true });
  setTimeout(finish, 400);
}

export function initModals() {
  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-open-composer]')) { open('composer'); return; }
    if (e.target.closest('[data-modal-close]')) close();
  });

  document.addEventListener('keydown', (e) => {
    if (!openModal) return;

    if (e.key === 'Escape') { e.preventDefault(); close(); return; }

    if (e.key === 'Tab') {
      const items = [...openModal.querySelectorAll(FOCUSABLE)].filter(
        (el) => el.offsetParent !== null
      );
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
}
