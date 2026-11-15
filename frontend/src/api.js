export function readSession() {
  try { return JSON.parse(sessionStorage.getItem('campus.session')); }
  catch { return null; }
}

export async function api(path, method = 'GET', data) {
  const token = readSession()?.token;
  const response = await fetch('/api/' + path, {
    method,
    headers: {'Content-Type': 'application/json', ...(token && {Authorization: 'Bearer ' + token})},
    body: data === undefined ? undefined : JSON.stringify(data)
  });
  if (response.status === 204) return;
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401 && token && path !== 'login') {
      sessionStorage.removeItem('campus.session');
      window.location.assign('/signin');
    }
    throw new Error(Array.isArray(result.detail) ? result.detail.map(x => x.msg).join('. ') : result.detail || 'Request failed.');
  }
  return result;
}

export const money = paise => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', minimumFractionDigits: 0, maximumFractionDigits: 2
}).format(paise / 100);
