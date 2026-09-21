/**
 * Mobile chrome: the top bar gets out of the way going down and comes back
 * the instant you scroll up. Desktop is untouched.
 */
export function initNav() {
  const topbar = document.querySelector('[data-topbar]');
  if (!topbar) return;

  let lastY = window.scrollY;
  let ticking = false;

  function update() {
    const y = window.scrollY;
    topbar.classList.toggle('is-stuck', y > 4);

    const goingDown = y > lastY;
    const pastHeader = y > 120;
    topbar.classList.toggle('is-hidden', goingDown && pastHeader);

    lastY = y;
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(update);
  }, { passive: true });

  update();
}

/** Small progressive touches for forms that still post normally. */
export function initForms() {
  document.querySelectorAll('[data-validate]').forEach((form) => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn && form.checkValidity()) btn.classList.add('is-busy');
    });
  });

  // Live bio counter on the edit-profile form.
  const bio = document.querySelector('#id_bio');
  const readout = document.querySelector('[data-bio-count]');
  if (bio && readout) {
    const paint = () => { readout.textContent = `${bio.value.length}/180`; };
    bio.addEventListener('input', paint);
    paint();
  }

  // Avatar preview before upload.
  const avatarInput = document.querySelector('[data-avatar-input]');
  const avatarPreview = document.querySelector('[data-avatar-preview]');
  if (avatarInput && avatarPreview) {
    avatarInput.addEventListener('change', () => {
      const file = avatarInput.files[0];
      if (!file) return;
      if (avatarPreview.src?.startsWith('blob:')) URL.revokeObjectURL(avatarPreview.src);
      avatarPreview.src = URL.createObjectURL(file);
      avatarPreview.hidden = false;
    });
  }
}
