const elements = {
  username: document.getElementById('username'),
  password: document.getElementById('password'),
  loginButton: document.getElementById('login-button'),
  refreshButton: document.getElementById('refresh-button'),
  signoutButton: document.getElementById('signout-button'),
  meButton: document.getElementById('me-button'),
  createTeamButton: document.getElementById('create-team-button'),
  refreshLayout: document.getElementById('refresh-layout'),
  teamName: document.getElementById('team-name'),
  teamDescription: document.getElementById('team-description'),
  teamTableBody: document.getElementById('team-table-body'),
  accessToken: document.getElementById('access-token'),
  refreshToken: document.getElementById('refresh-token'),
  authStatus: document.getElementById('auth-status'),
  serverStatus: document.getElementById('server-status'),
  loginError: document.getElementById('login-error'),
  tokenError: document.getElementById('token-error'),
  meError: document.getElementById('me-error'),
  teamError: document.getElementById('team-error'),
  meId: document.getElementById('me-id'),
  meUsername: document.getElementById('me-username'),
  meEmail: document.getElementById('me-email'),
  meName: document.getElementById('me-name'),
};

const state = {
  access: localStorage.getItem('tf_access') || null,
  refresh: localStorage.getItem('tf_refresh') || null,
};

const backendOrigin = 'http://127.0.0.1:8000';

const api = {
  token: `${backendOrigin}/api/token/`,
  tokenRefresh: `${backendOrigin}/api/token/refresh/`,
  me: `${backendOrigin}/api/me/`,
  teams: `${backendOrigin}/api/teams/`,
};

function updateUI() {
  elements.accessToken.textContent = state.access || 'Not available';
  elements.refreshToken.textContent = state.refresh || 'Not available';
  elements.authStatus.textContent = state.access ? 'Signed in' : 'Signed out';
}

function setTokens(access, refresh) {
  state.access = access;
  state.refresh = refresh;
  localStorage.setItem('tf_access', access);
  localStorage.setItem('tf_refresh', refresh);
  updateUI();
}

function clearTokens() {
  state.access = null;
  state.refresh = null;
  localStorage.removeItem('tf_access');
  localStorage.removeItem('tf_refresh');
  updateUI();
  renderTeams([]);
  clearProfile();
}

function handleError(errorElement, message) {
  errorElement.textContent = message || '';
}

function authHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (state.access) {
    headers.Authorization = `Bearer ${state.access}`;
  }
  return headers;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw { status: response.status, data };
  }
  return data;
}

async function login() {
  handleError(elements.loginError, '');
  handleError(elements.tokenError, '');
  handleError(elements.meError, '');
  handleError(elements.teamError, '');

  const payload = {
    username: elements.username.value.trim(),
    password: elements.password.value.trim(),
  };

  try {
    const result = await fetchJson(api.token, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    setTokens(result.access, result.refresh);
    await loadProfile();
    await loadTeams();
  } catch (error) {
    clearTokens();
    handleError(elements.loginError, error.data?.detail || 'Login failed. Check your credentials.');
  }
}

async function refreshAccessToken() {
  handleError(elements.tokenError, '');
  if (!state.refresh) {
    handleError(elements.tokenError, 'Refresh token required. Please log in first.');
    return;
  }

  try {
    const result = await fetchJson(api.tokenRefresh, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: state.refresh }),
    });
    setTokens(result.access, state.refresh);
  } catch (error) {
    if (error.status === 401 || error.status === 400) {
      handleError(elements.tokenError, 'Refresh token expired or invalid. Please log in again.');
    } else {
      handleError(elements.tokenError, 'Unable to refresh access token.');
    }
  }
}

async function loadProfile() {
  handleError(elements.meError, '');
  if (!state.access) return;

  try {
    const profile = await fetchJson(api.me, {
      method: 'GET',
      headers: authHeaders(),
    });
    elements.meId.textContent = profile.id;
    elements.meUsername.textContent = profile.username;
    elements.meEmail.textContent = profile.email || '—';
    elements.meName.textContent = `${profile.first_name || '–'} ${profile.last_name || ''}`.trim();
  } catch (error) {
    clearProfile();
    if (error.status === 401) {
      clearTokens();
      handleError(elements.meError, 'Session expired. Please log in again.');
      return;
    }
    handleError(elements.meError, 'Unable to load profile. Verify authentication.');
  }
}

function clearProfile() {
  elements.meId.textContent = '—';
  elements.meUsername.textContent = '—';
  elements.meEmail.textContent = '—';
  elements.meName.textContent = '—';
}

function renderTeams(teams) {
  const rows = teams.map(team => {
    const members = team.members?.length ? team.members.length : 0;
    const owner = team.owner?.username || 'Unknown';
    return `
      <tr>
        <td>${team.name}</td>
        <td>${owner}</td>
        <td>${members}</td>
        <td>${team.id}</td>
      </tr>
    `;
  }).join('');

  elements.teamTableBody.innerHTML = rows || '<tr><td colspan="4">No teams found.</td></tr>';
}

async function loadTeams() {
  handleError(elements.teamError, '');
  if (!state.access) return;

  try {
    const teams = await fetchJson(api.teams, {
      method: 'GET',
      headers: authHeaders(),
    });
    renderTeams(teams);
  } catch (error) {
    renderTeams([]);
    if (error.status === 401) {
      clearTokens();
      handleError(elements.teamError, 'Authentication required. Please log in again.');
      return;
    }
    handleError(elements.teamError, 'Unable to load teams. Ensure the session is valid.');
  }
}

async function createTeam() {
  handleError(elements.teamError, '');
  if (!state.access) {
    handleError(elements.teamError, 'Login required to create a team.');
    return;
  }

  const payload = {
    name: elements.teamName.value.trim(),
    description: elements.teamDescription.value.trim(),
  };

  try {
    await fetchJson(api.teams, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    elements.teamName.value = '';
    elements.teamDescription.value = '';
    await loadTeams();
  } catch (error) {
    const detail = error.data?.name || error.data?.detail || 'Unable to create team.';
    handleError(elements.teamError, Array.isArray(detail) ? detail.join(' ') : detail);
  }
}

function signOut() {
  clearTokens();
}

function checkServer() {
  elements.serverStatus.textContent = 'Ready';
}

function initEventListeners() {
  elements.loginButton.addEventListener('click', login);
  elements.refreshButton.addEventListener('click', refreshAccessToken);
  elements.signoutButton.addEventListener('click', signOut);
  elements.meButton.addEventListener('click', loadProfile);
  elements.createTeamButton.addEventListener('click', createTeam);
  elements.refreshLayout.addEventListener('click', () => {
    checkServer();
    loadProfile();
    loadTeams();
  });
}

function init() {
  updateUI();
  checkServer();
  initEventListeners();
  if (state.access) {
    loadProfile();
    loadTeams();
  }
}

init();
