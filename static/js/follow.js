/**
 * Follow / unfollow. Every button for the same person on the page updates,
 * so the profile header and the suggestion rail never disagree.
 */
import { api } from './api.js';
import { bump, toast } from './ui.js';

function paintAll(username, following) {
  document.querySelectorAll(`[data-follow][data-username="${CSS.escape(username)}"]`)
    .forEach((btn) => {
      btn.classList.toggle('is-following', following);
      btn.setAttribute('aria-pressed', String(following));
      const label = btn.querySelector('.follow__label');
      if (label) label.textContent = following ? 'Following' : 'Follow';
    });
}

export function initFollow() {
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-follow]');
    if (!btn || btn.classList.contains('is-busy')) return;

    const username = btn.dataset.username;
    const wasFollowing = btn.classList.contains('is-following');

    paintAll(username, !wasFollowing);
    btn.classList.add('is-busy');

    try {
      const data = await api.post(btn.dataset.follow);
      paintAll(username, data.following);

      const stat = document.querySelector(`[data-stat="followers"][data-username="${CSS.escape(username)}"]`);
      if (stat) { stat.textContent = data.followers; bump(stat); }

      toast(data.following ? `Following @${username}` : `Unfollowed @${username}`, 'success', 2200);
    } catch (err) {
      paintAll(username, wasFollowing);
      toast(err.message, 'error');
    } finally {
      btn.classList.remove('is-busy');
    }
  });
}
