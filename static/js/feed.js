/**
 * Feed behaviour: entrance stagger, image reveal, pagination, post menus,
 * deletion and link sharing.
 */
import { api } from './api.js';
import { toast, prefersReducedMotion } from './ui.js';

/** Fade each image in once it has actually decoded. */
function watchImages(scope = document) {
  scope.querySelectorAll('img[data-reveal]:not(.is-watched)').forEach((img) => {
    img.classList.add('is-watched');
    const show = () => img.classList.add('is-revealed');
    if (img.complete && img.naturalWidth) show();
    else img.addEventListener('load', show, { once: true });
    img.addEventListener('error', () => {
      img.closest('.post__media')?.remove();
    }, { once: true });
  });
}

/** Collapse an element out of the flow, so the posts below glide up. */
function collapse(el) {
  if (prefersReducedMotion()) { el.remove(); return; }
  el.style.height = `${el.offsetHeight}px`;
  void el.offsetHeight;             // commit the measured height first
  el.classList.add('is-leaving');
  el.addEventListener('transitionend', () => el.remove(), { once: true });
  setTimeout(() => el.remove(), 600);
}

/** Stagger the first screenful only — after that, posts just appear. */
function staggerFirstScreen() {
  if (prefersReducedMotion()) return;
  document.querySelectorAll('[data-feed]').forEach((feed) => {
    [...feed.children].slice(0, 6).forEach((el, i) => {
      el.style.setProperty('--i', i);
      el.setAttribute('data-reveal-item', '');
    });
  });
}

export function prependPost(html) {
  // Explore excludes your own posts, and someone else's profile isn't yours —
  // dropping it there would show something the page's own query wouldn't.
  const feed = document.querySelector('[data-feed][data-feed-accepts-new]');
  if (!feed) return false;

  feed.querySelector('.empty')?.remove();

  const wrap = document.createElement('div');
  wrap.innerHTML = html.trim();
  const post = wrap.firstElementChild;
  post.classList.add('is-new');
  feed.prepend(post);
  watchImages(post);

  post.scrollIntoView({ block: 'nearest', behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
  return true;
}

function initLoadMore() {
  const region = document.querySelector('[data-loadmore]');
  if (!region) return;

  const btn = region.querySelector('[data-loadmore-btn]');
  const skeleton = region.querySelector('[data-loadmore-skeleton]');
  const end = region.querySelector('[data-loadmore-end]');
  const feed = document.querySelector('[data-feed]');
  let loading = false;

  async function loadNext() {
    const next = region.dataset.next;
    if (!next || loading) return;
    loading = true;
    btn.hidden = true;
    skeleton.hidden = false;

    try {
      const data = await api.get(`${region.dataset.url}page=${next}`);
      feed.insertAdjacentHTML('beforeend', data.html);
      watchImages(feed);
      region.dataset.next = data.has_next ? data.next_page : '';
      btn.hidden = !data.has_next;
      end.hidden = data.has_next;
    } catch (err) {
      toast(err.message, 'error');
      btn.hidden = false;
      btn.textContent = 'Try again';
    } finally {
      skeleton.hidden = true;
      loading = false;
    }
  }

  btn?.addEventListener('click', loadNext);

  // Pre-load just before the reader reaches the end, so scrolling never stalls.
  // Only after they've scrolled at least once — a short feed shouldn't fetch
  // its next page before anyone has looked at the first.
  const sentinel = new IntersectionObserver(
    (entries) => { if (entries[0].isIntersecting) loadNext(); },
    { rootMargin: '600px 0px' }
  );
  window.addEventListener('scroll', () => sentinel.observe(region), { once: true, passive: true });
}

function initPostMenus() {
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('[data-menu-trigger]');
    document.querySelectorAll('[data-menu] .menu__list').forEach((list) => {
      if (!trigger || list !== trigger.nextElementSibling) {
        list.hidden = true;
        list.previousElementSibling?.setAttribute('aria-expanded', 'false');
      }
    });
    if (!trigger) return;
    const list = trigger.nextElementSibling;
    const open = list.hidden;
    list.hidden = !open;
    trigger.setAttribute('aria-expanded', String(open));
  });

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('[data-menu] .menu__list:not([hidden])').forEach((list) => {
      list.hidden = true;
      list.previousElementSibling?.focus();
    });
  });
}

function initDelete() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-delete-post]');
    if (!btn) return;

    // Two-step rather than a browser confirm(): it keeps you in the interface.
    if (btn.dataset.confirm !== '1') {
      btn.dataset.confirm = '1';
      btn.innerHTML = '<svg class="icon" viewBox="0 0 24 24"><use href="#i-trash"/></svg>Tap again to confirm';
      setTimeout(() => {
        if (!btn.isConnected) return;
        delete btn.dataset.confirm;
        btn.innerHTML = '<svg class="icon" viewBox="0 0 24 24"><use href="#i-trash"/></svg>Delete post';
      }, 3500);
      return;
    }

    const post = btn.closest('[data-post]');
    try {
      await api.post(btn.dataset.deletePost);
      collapse(post);
      toast('Post deleted', 'success');
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}

function initShare() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-share]');
    if (!btn) return;
    const url = new URL(btn.dataset.share, window.location.origin).href;

    if (navigator.share) {
      try { await navigator.share({ url, title: '2gether' }); return; } catch { /* dismissed */ }
    }
    try {
      await navigator.clipboard.writeText(url);
      toast('Link copied', 'success', 2000);
    } catch {
      toast('Copy failed. Open the post and copy the address.', 'error');
    }
  });
}

export function initFeed() {
  staggerFirstScreen();
  watchImages();
  initLoadMore();
  initPostMenus();
  initDelete();
  initShare();
}
