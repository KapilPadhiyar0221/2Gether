/**
 * One place that talks to Django. Everything goes through here so CSRF,
 * error shape and network failure are handled identically everywhere.
 */

export function csrfToken() {
  const input = document.querySelector('#csrf-holder [name="csrfmiddlewaretoken"]');
  return input ? input.value : '';
}

export class RequestError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'RequestError';
    this.status = status;
  }
}

async function request(url, options = {}) {
  let response;
  try {
    response = await fetch(url, {
      credentials: 'same-origin',
      ...options,
      headers: {
        'X-Requested-With': 'fetch',
        'X-CSRFToken': csrfToken(),
        ...(options.headers || {}),
      },
    });
  } catch {
    // Offline, DNS, aborted — never a Django traceback.
    throw new RequestError("Can't reach the server. Check your connection.", 0);
  }

  let data = null;
  const type = response.headers.get('content-type') || '';
  if (type.includes('application/json')) {
    data = await response.json().catch(() => null);
  }

  if (!response.ok) {
    const message =
      (data && data.error) ||
      (response.status === 403 ? "You don't have permission to do that." : null) ||
      (response.status === 404 ? "That's already gone." : null) ||
      'Something went wrong. Try again.';
    throw new RequestError(message, response.status);
  }
  return data;
}

export const api = {
  get: (url) => request(url),
  post: (url, body) =>
    request(url, {
      method: 'POST',
      body: body instanceof FormData ? body : new URLSearchParams(body || {}),
    }),
};
