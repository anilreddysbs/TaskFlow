/* ==========================================
   TASKFLOW FRONTEND APPLICATION CONTROLLER
   ========================================== */

const backendOrigin = window.location.origin;

const api = {
  token: `${backendOrigin}/api/token/`,
  tokenRefresh: `${backendOrigin}/api/token/refresh/`,
  register: `${backendOrigin}/api/register/`,
  me: `${backendOrigin}/api/me/`,
  users: `${backendOrigin}/api/users/`,
  teams: `${backendOrigin}/api/teams/`,
  projects: `${backendOrigin}/api/projects/`,
  tasks: `${backendOrigin}/api/tasks/`,
  comments: `${backendOrigin}/api/comments/`,
};

// Application State
const state = {
  access: localStorage.getItem('tf_access') || null,
  refresh: localStorage.getItem('tf_refresh') || null,
  currentUser: null,
  users: [],
  teams: [],
  projects: [],
  tasks: [],
  comments: [],
  currentTab: 'dashboard',
  selectedTaskId: null,
};

// Cache DOM Elements
const dom = {
  authScreen: document.getElementById('auth-screen'),
  loginForm: document.getElementById('login-form'),
  registerForm: document.getElementById('register-form'),
  loginUsername: document.getElementById('login-username'),
  loginPassword: document.getElementById('login-password'),
  regUsername: document.getElementById('reg-username'),
  regEmail: document.getElementById('reg-email'),
  regFirstname: document.getElementById('reg-firstname'),
  regLastname: document.getElementById('reg-lastname'),
  regPassword: document.getElementById('reg-password'),
  toSignup: document.getElementById('to-signup'),
  toLogin: document.getElementById('to-login'),
  authSubtitle: document.getElementById('auth-subtitle-text'),

  // Sidebar / Header
  navItems: document.querySelectorAll('.nav-item'),
  tabPanels: document.querySelectorAll('.tab-panel'),
  systemStatusText: document.getElementById('system-status-text'),
  statusDot: document.getElementById('status-dot'),
  userDisplayName: document.getElementById('user-display-name'),
  userHandle: document.getElementById('user-handle'),
  userAvatar: document.getElementById('user-avatar'),
  btnSignout: document.getElementById('btn-signout'),
  btnRefresh: document.getElementById('btn-refresh'),
  btnGlobalAddTask: document.getElementById('btn-global-add-task'),
  pageTitle: document.getElementById('page-title'),
  pageSubtitle: document.getElementById('page-subtitle'),

  // Dashboard Tab
  statPending: document.getElementById('stat-pending'),
  statCompleted: document.getElementById('stat-completed'),
  statProjects: document.getElementById('stat-projects'),
  statTeams: document.getElementById('stat-teams'),
  shortcutCreateTeam: document.getElementById('shortcut-create-team'),
  shortcutCreateProject: document.getElementById('shortcut-create-project'),

  // Kanban Board Tab
  filterProject: document.getElementById('filter-project'),
  filterPriority: document.getElementById('filter-priority'),
  searchTask: document.getElementById('search-task'),
  cardsTodo: document.getElementById('cards-todo'),
  cardsInProgress: document.getElementById('cards-in_progress'),
  cardsBlocked: document.getElementById('cards-blocked'),
  cardsDone: document.getElementById('cards-done'),
  countTodo: document.getElementById('count-todo'),
  countInProgress: document.getElementById('count-in_progress'),
  countBlocked: document.getElementById('count-blocked'),
  countDone: document.getElementById('count-done'),

  // Teams & Members Tab
  createTeamForm: document.getElementById('create-team-form'),
  newTeamName: document.getElementById('new-team-name'),
  newTeamDesc: document.getElementById('new-team-desc'),
  addMemberForm: document.getElementById('add-member-form'),
  memberTeamSelect: document.getElementById('member-team-select'),
  memberUserSelect: document.getElementById('member-user-select'),
  teamsDirectory: document.getElementById('teams-directory'),

  // Projects Tab
  createProjectForm: document.getElementById('create-project-form'),
  projTeamSelect: document.getElementById('proj-team-select'),
  newProjName: document.getElementById('new-proj-name'),
  newProjDesc: document.getElementById('new-proj-desc'),
  projectsDirectory: document.getElementById('projects-directory'),

  // Task Details Modal
  taskModal: document.getElementById('task-modal'),
  modalTaskId: document.getElementById('modal-task-id'),
  modalTaskTitle: document.getElementById('modal-task-title'),
  modalTaskDesc: document.getElementById('modal-task-desc'),
  modalTaskStatus: document.getElementById('modal-task-status'),
  modalTaskPriority: document.getElementById('modal-task-priority'),
  modalTaskAssignee: document.getElementById('modal-task-assignee'),
  modalTaskDuedate: document.getElementById('modal-task-duedate'),
  modalBtnClose: document.getElementById('modal-btn-close'),
  modalBtnDelete: document.getElementById('modal-btn-delete'),
  taskModalForm: document.getElementById('task-modal-form'),
  modalCommentsList: document.getElementById('modal-comments-list'),
  addCommentForm: document.getElementById('add-comment-form'),
  newCommentContent: document.getElementById('new-comment-content'),

  // Create Task Modal
  createTaskModal: document.getElementById('create-task-modal'),
  createTaskModalClose: document.getElementById('create-task-modal-close'),
  globalCreateTaskForm: document.getElementById('global-create-task-form'),
  createTaskProject: document.getElementById('create-task-project'),
  createTaskTitle: document.getElementById('create-task-title'),
  createTaskDesc: document.getElementById('create-task-desc'),
  createTaskStatus: document.getElementById('create-task-status'),
  createTaskPriority: document.getElementById('create-task-priority'),
  createTaskAssignee: document.getElementById('create-task-assignee'),
  createTaskDuedate: document.getElementById('create-task-duedate'),

  // Toast container
  toastContainer: document.getElementById('toast-container'),
};

/* ==========================================
   TOAST NOTIFICATION ENGINE
   ========================================== */

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = '';
  if (type === 'success') {
    icon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
  } else if (type === 'error') {
    icon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
  } else {
    icon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
  }

  toast.innerHTML = `${icon} <span>${message}</span>`;
  dom.toastContainer.appendChild(toast);

  // Animate slide-out
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/* ==========================================
   API FETCH WRAPPER
   ========================================== */

function authHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (state.access) {
    headers.Authorization = `Bearer ${state.access}`;
  }
  return headers;
}

async function request(url, options = {}) {
  options.headers = { ...options.headers, ...authHeaders() };
  
  try {
    let response = await fetch(url, options);
    
    // Auto token refresh on 401 Unauthorized
    if (response.status === 401 && state.refresh && url !== api.token && url !== api.tokenRefresh) {
      const refreshed = await attemptTokenRefresh();
      if (refreshed) {
        options.headers = { ...options.headers, ...authHeaders() };
        response = await fetch(url, options);
      } else {
        throw new Error("Session expired. Please log in again.");
      }
    }

    if (response.status === 204) return null;

    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw { status: response.status, data };
    }
    return data;
  } catch (error) {
    console.error(`Request to ${url} failed:`, error);
    throw error;
  }
}

async function attemptTokenRefresh() {
  try {
    const response = await fetch(api.tokenRefresh, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: state.refresh }),
    });
    if (!response.ok) {
      clearTokens();
      return false;
    }
    const result = await response.json();
    setTokens(result.access, state.refresh);
    return true;
  } catch (err) {
    clearTokens();
    return false;
  }
}

function setTokens(access, refresh) {
  state.access = access;
  state.refresh = refresh;
  localStorage.setItem('tf_access', access);
  localStorage.setItem('tf_refresh', refresh);
  dom.authScreen.classList.add('hidden');
}

function clearTokens() {
  state.access = null;
  state.refresh = null;
  state.currentUser = null;
  localStorage.removeItem('tf_access');
  localStorage.removeItem('tf_refresh');
  dom.authScreen.classList.remove('hidden');
  updateSystemIndicators('Offline');
}

function updateSystemIndicators(status = 'Online') {
  if (status === 'Online') {
    dom.systemStatusText.textContent = 'Connected';
    dom.statusDot.className = 'status-pulse status-online';
  } else {
    dom.systemStatusText.textContent = 'Disconnected';
    dom.statusDot.className = 'status-pulse status-offline';
  }
}

/* ==========================================
   TAB ROUTING SYSTEM
   ========================================== */

function switchTab(tabId) {
  state.currentTab = tabId;
  
  // Update sidebar buttons
  dom.navItems.forEach(btn => {
    if (btn.dataset.tab === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Switch display panels
  dom.tabPanels.forEach(panel => {
    if (panel.id === `tab-${tabId}`) {
      panel.classList.add('active');
    } else {
      panel.classList.remove('active');
    }
  });

  // Update headers
  const titles = {
    dashboard: { title: 'Dashboard Overview', sub: 'Real-time metrics and shortcut configurations.' },
    kanban: { title: 'Kanban Board', sub: 'Sprint backlog task tracking.' },
    teams: { title: 'Teams Directory', sub: 'Collaborator structures and assignments.' },
    projects: { title: 'Projects Scope', sub: 'Active deliverables and feature boundaries.' },
  };

  if (titles[tabId]) {
    dom.pageTitle.textContent = titles[tabId].title;
    dom.pageSubtitle.textContent = titles[tabId].sub;
  }

  // Load relevant data
  syncWorkspaceData();
}

/* ==========================================
   API DATA RETRIEVAL (CRUD)
   ========================================== */

async function loadMe() {
  try {
    const profile = await request(api.me);
    state.currentUser = profile;
    
    // Set headers
    const name = `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || profile.username;
    dom.userDisplayName.textContent = name;
    dom.userHandle.textContent = `@${profile.username}`;
    
    // Get initials for avatar
    const initials = profile.username.substring(0, 2).toUpperCase();
    dom.userAvatar.textContent = initials;
    updateSystemIndicators('Online');
  } catch (error) {
    showToast(error.message || 'Unable to retrieve user session.', 'error');
    clearTokens();
  }
}

async function syncWorkspaceData() {
  if (!state.access) return;

  try {
    // Parallel requests
    const [users, teams, projects, tasks, comments] = await Promise.all([
      request(api.users).catch(() => []),
      request(api.teams).catch(() => []),
      request(api.projects).catch(() => []),
      request(api.tasks).catch(() => []),
      request(api.comments).catch(() => []),
    ]);

    state.users = users;
    state.teams = teams;
    state.projects = projects;
    state.tasks = tasks;
    state.comments = comments;

    // Trigger components refresh
    renderStats();
    populateDropdowns();
    renderTeamsTabContent();
    renderProjectsTabContent();
    renderKanbanBoard();
  } catch (err) {
    console.error("Error syncing data:", err);
  }
}

/* ==========================================
   RENDERERS & INTERACTIVE BUILDERS
   ========================================== */

function renderStats() {
  const pending = state.tasks.filter(t => t.status !== 'DONE').length;
  const completed = state.tasks.filter(t => t.status === 'DONE').length;
  
  dom.statPending.textContent = pending;
  dom.statCompleted.textContent = completed;
  dom.statProjects.textContent = state.projects.length;
  dom.statTeams.textContent = state.teams.length;
}

function populateDropdowns() {
  // Clear lists
  const selects = [
    dom.memberTeamSelect, dom.projTeamSelect, dom.createTaskProject,
    dom.memberUserSelect, dom.createTaskAssignee, dom.modalTaskAssignee,
    dom.filterProject
  ];
  
  selects.forEach(sel => {
    if (!sel) return;
    const isFilter = sel === dom.filterProject;
    sel.innerHTML = isFilter ? '<option value="all">All Projects</option>' : '<option value="">-- Select --</option>';
  });

  // Populate Teams
  state.teams.forEach(t => {
    const opt1 = new Option(t.name, t.id);
    const opt2 = new Option(t.name, t.id);
    dom.memberTeamSelect.add(opt1);
    dom.projTeamSelect.add(opt2);
  });

  // Populate Projects
  state.projects.forEach(p => {
    const opt1 = new Option(p.name, p.id);
    const opt2 = new Option(p.name, p.id);
    dom.createTaskProject.add(opt1);
    dom.filterProject.add(opt2);
  });

  // Populate Users
  state.users.forEach(u => {
    const name = `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.username;
    const opt1 = new Option(`${name} (${u.username})`, u.id);
    const opt2 = new Option(name, u.id);
    const opt3 = new Option(name, u.id);
    
    dom.memberUserSelect.add(opt1);
    dom.createTaskAssignee.add(opt2);
    dom.modalTaskAssignee.add(opt3);
  });
}

// Teams Section
function renderTeamsTabContent() {
  if (state.teams.length === 0) {
    dom.teamsDirectory.innerHTML = '<p class="placeholder-text">No teams registered. Create one to begin!</p>';
    return;
  }

  dom.teamsDirectory.innerHTML = state.teams.map(team => {
    const ownerName = team.owner === state.currentUser?.id ? 'You' : `@${state.users.find(u => u.id === team.owner)?.username || 'user'}`;
    const membersList = team.members && team.members.length > 0
      ? team.members.map(m => `<span class="user-tag">${m.username}</span>`).join('')
      : '<span class="text-dark">No other members</span>';
    
    const projectsCount = state.projects.filter(p => p.team === team.id).length;

    return `
      <div class="item-card">
        <div class="item-card-header">
          <h3>${team.name}</h3>
          <span class="badge badge-accent">ID: ${team.id}</span>
        </div>
        <p class="item-card-desc">${team.description || 'No description provided.'}</p>
        
        <div class="members-badges-row">
          <h4>Team Members</h4>
          <div class="members-usernames">${membersList}</div>
        </div>

        <div class="item-card-meta">
          <div class="meta-pill">Owner: <strong>${ownerName}</strong></div>
          <div class="meta-pill">Active Projects: <strong>${projectsCount}</strong></div>
        </div>
      </div>
    `;
  }).join('');
}

// Projects Section
function renderProjectsTabContent() {
  if (state.projects.length === 0) {
    dom.projectsDirectory.innerHTML = '<p class="placeholder-text">No project scopes active. Create one to populate.</p>';
    return;
  }

  dom.projectsDirectory.innerHTML = state.projects.map(proj => {
    const teamName = state.teams.find(t => t.id === proj.team)?.name || 'Unknown Team';
    const dateStr = new Date(proj.created_at).toLocaleDateString(undefined, { dateStyle: 'medium' });

    return `
      <div class="item-card">
        <div class="item-card-header">
          <h3>${proj.name}</h3>
          <span class="badge badge-todo">Tasks: ${proj.tasks_count || 0}</span>
        </div>
        <p class="item-card-desc">${proj.description || 'No description provided.'}</p>
        <div class="item-card-meta">
          <div class="meta-pill">Team: <strong>${teamName}</strong></div>
          <div class="meta-pill">Created: <strong>${dateStr}</strong></div>
        </div>
      </div>
    `;
  }).join('');
}

// Kanban Board Lane Draw
function renderKanbanBoard() {
  const lanes = {
    TODO: { cards: dom.cardsTodo, count: dom.countTodo, list: [] },
    IN_PROGRESS: { cards: dom.cardsInProgress, count: dom.countInProgress, list: [] },
    BLOCKED: { cards: dom.cardsBlocked, count: dom.countBlocked, list: [] },
    DONE: { cards: dom.cardsDone, count: dom.countDone, list: [] },
  };

  // Get filter states
  const projectFilter = dom.filterProject.value;
  const priorityFilter = dom.filterPriority.value;
  const searchQuery = dom.searchTask.value.toLowerCase().trim();

  // Filter Tasks
  const filteredTasks = state.tasks.filter(task => {
    // Project Match
    if (projectFilter !== 'all' && String(task.project) !== projectFilter) return false;
    
    // Priority Match
    if (priorityFilter !== 'all' && task.priority !== priorityFilter) return false;

    // Search Match
    if (searchQuery) {
      const matchTitle = task.title.toLowerCase().includes(searchQuery);
      const matchDesc = task.description && task.description.toLowerCase().includes(searchQuery);
      if (!matchTitle && !matchDesc) return false;
    }

    return true;
  });

  // Distribute tasks
  filteredTasks.forEach(task => {
    if (lanes[task.status]) {
      lanes[task.status].list.push(task);
    }
  });

  // Draw Lanes
  Object.keys(lanes).forEach(status => {
    const lane = lanes[status];
    lane.count.textContent = lane.list.length;

    if (lane.list.length === 0) {
      lane.cards.innerHTML = '<p class="placeholder-text" style="padding: 16px 0;">Empty</p>';
      return;
    }

    lane.cards.innerHTML = lane.list.map(task => {
      const isOverdue = task.due_date && new Date(task.due_date) < new Date().setHours(0,0,0,0) && task.status !== 'DONE';
      const dueLabel = task.due_date 
        ? `<span class="task-card-due ${isOverdue ? 'overdue' : ''}">
             <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
             ${new Date(task.due_date).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}
           </span>`
        : '<span></span>';
      
      const assigneeUser = state.users.find(u => u.id === task.assigned_to);
      const initials = assigneeUser
        ? assigneeUser.username.substring(0, 2).toUpperCase()
        : '—';

      const assigneeBadge = assigneeUser
        ? `<div class="task-card-assignee-badge assigned" title="Assigned to ${assigneeUser.username}">${initials}</div>`
        : `<div class="task-card-assignee-badge" title="Unassigned">${initials}</div>`;

      return `
        <div class="task-card" onclick="openTaskModal(${task.id})">
          <div class="task-card-header">
            <h4 class="task-card-title">${task.title}</h4>
            <div class="task-card-priority-indicator prio-${task.priority.toLowerCase()}" title="Priority: ${task.priority}"></div>
          </div>
          <p class="task-card-body">${task.description || 'No description added.'}</p>
          <div class="task-card-footer">
            ${dueLabel}
            ${assigneeBadge}
          </div>
        </div>
      `;
    }).join('');
  });
}

/* ==========================================
   TASK ACTIONS MODAL HANDLERS
   ========================================== */

window.openTaskModal = async function(taskId) {
  state.selectedTaskId = taskId;
  const task = state.tasks.find(t => t.id === taskId);
  if (!task) return;

  // Populate Modal Fields
  dom.modalTaskId.textContent = `#TASK-${task.id}`;
  dom.modalTaskTitle.value = task.title;
  dom.modalTaskDesc.value = task.description || '';
  dom.modalTaskStatus.value = task.status;
  dom.modalTaskPriority.value = task.priority;
  dom.modalTaskAssignee.value = task.assigned_to || '';
  dom.modalTaskDuedate.value = task.due_date || '';

  // Show Modal
  dom.taskModal.classList.remove('hidden');

  // Load and render comments
  renderCommentsList(taskId);
};

function closeTaskModal() {
  dom.taskModal.classList.add('hidden');
  state.selectedTaskId = null;
}

function renderCommentsList(taskId) {
  const taskComments = state.comments.filter(c => c.task === taskId);
  
  if (taskComments.length === 0) {
    dom.modalCommentsList.innerHTML = '<p class="no-comments">No discussion threads yet. Add a comment below!</p>';
    return;
  }

  dom.modalCommentsList.innerHTML = taskComments.map(c => {
    const authorName = c.author?.username || 'user';
    const dateStr = new Date(c.created_at).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });

    return `
      <div class="comment-card">
        <div class="comment-author-row">
          <span class="comment-author">@${authorName}</span>
          <span class="comment-date">${dateStr}</span>
        </div>
        <p class="comment-text">${c.content}</p>
      </div>
    `;
  }).join('');
}

/* ==========================================
   FORM SUBMISSIONS (API MUTATIONS)
   ========================================== */

// Auth form submissions
dom.loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = dom.loginUsername.value.trim();
  const password = dom.loginPassword.value.trim();

  try {
    const result = await request(api.token, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    setTokens(result.access, result.refresh);
    showToast("Signed in successfully!", "success");
    initWorkspace();
  } catch (error) {
    showToast(error.data?.detail || "Login failed. Check username and password.", "error");
  }
});

dom.registerForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    username: dom.regUsername.value.trim(),
    email: dom.regEmail.value.trim(),
    first_name: dom.regFirstname.value.trim(),
    last_name: dom.regLastname.value.trim(),
    password: dom.regPassword.value.trim(),
  };

  try {
    await request(api.register, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showToast("Account created! Logging in...", "success");
    
    // Auto-login after sign-up
    const result = await request(api.token, {
      method: 'POST',
      body: JSON.stringify({ username: payload.username, password: payload.password }),
    });
    setTokens(result.access, result.refresh);
    initWorkspace();
  } catch (error) {
    const detail = error.data?.username || error.data?.email || error.data?.detail || "Registration failed.";
    showToast(Array.isArray(detail) ? detail.join(' ') : detail, "error");
  }
});

// Create Team Submission
dom.createTeamForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = dom.newTeamName.value.trim();
  const description = dom.newTeamDesc.value.trim();

  try {
    await request(api.teams, {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
    dom.newTeamName.value = '';
    dom.newTeamDesc.value = '';
    showToast("Team initialized successfully!", "success");
    await syncWorkspaceData();
  } catch (error) {
    const detail = error.data?.name || error.data?.detail || "Failed to create team.";
    showToast(Array.isArray(detail) ? detail.join(' ') : detail, "error");
  }
});

// Add member to team
dom.addMemberForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const teamId = dom.memberTeamSelect.value;
  const userId = Number(dom.memberUserSelect.value);

  const team = state.teams.find(t => t.id === Number(teamId));
  if (!team) return;

  // Build members list including existing members + new one
  const existingMemberIds = team.members ? team.members.map(m => m.id) : [];
  if (existingMemberIds.includes(userId)) {
    showToast("User is already in the team.", "info");
    return;
  }

  const payload = {
    member_ids: [...existingMemberIds, userId],
  };

  try {
    await request(`${api.teams}${teamId}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    showToast("Member invited to team!", "success");
    await syncWorkspaceData();
  } catch (error) {
    showToast("Unable to add user to team.", "error");
  }
});

// Create Project Scope
dom.createProjectForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const team = dom.projTeamSelect.value;
  const name = dom.newProjName.value.trim();
  const description = dom.newProjDesc.value.trim();

  try {
    await request(api.projects, {
      method: 'POST',
      body: JSON.stringify({ team, name, description }),
    });
    dom.newProjName.value = '';
    dom.newProjDesc.value = '';
    showToast("Project scope provisioned!", "success");
    await syncWorkspaceData();
  } catch (error) {
    const detail = error.data?.name || error.data?.detail || "Unable to create project.";
    showToast(Array.isArray(detail) ? detail.join(' ') : detail, "error");
  }
});

// Task Detail Edit Submit
dom.taskModalForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!state.selectedTaskId) return;

  const payload = {
    title: dom.modalTaskTitle.value.trim(),
    description: dom.modalTaskDesc.value.trim(),
    status: dom.modalTaskStatus.value,
    priority: dom.modalTaskPriority.value,
    assigned_to: dom.modalTaskAssignee.value ? Number(dom.modalTaskAssignee.value) : null,
    due_date: dom.modalTaskDuedate.value || null,
  };

  try {
    await request(`${api.tasks}${state.selectedTaskId}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    showToast("Task updated!", "success");
    closeTaskModal();
    await syncWorkspaceData();
  } catch (error) {
    const detail = error.data?.title || error.data?.due_date || error.data?.detail || "Unable to save task edits.";
    showToast(Array.isArray(detail) ? detail.join(' ') : detail, "error");
  }
});

// Task Deletion
dom.modalBtnDelete.addEventListener('click', async () => {
  if (!state.selectedTaskId || !confirm("Are you sure you want to delete this task?")) return;

  try {
    await request(`${api.tasks}${state.selectedTaskId}/`, {
      method: 'DELETE',
    });
    showToast("Task deleted.", "info");
    closeTaskModal();
    await syncWorkspaceData();
  } catch (error) {
    showToast("Unable to delete task.", "error");
  }
});

// Create Comment
dom.addCommentForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!state.selectedTaskId) return;

  const content = dom.newCommentContent.value.trim();

  try {
    const newComment = await request(api.comments, {
      method: 'POST',
      body: JSON.stringify({ task: state.selectedTaskId, content }),
    });
    dom.newCommentContent.value = '';
    showToast("Comment posted!", "success");
    
    // Optimistically push comment to local state
    state.comments.push(newComment);
    renderCommentsList(state.selectedTaskId);
  } catch (error) {
    showToast("Failed to post comment.", "error");
  }
});

// Global Create Task
dom.globalCreateTaskForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    project: dom.createTaskProject.value,
    title: dom.createTaskTitle.value.trim(),
    description: dom.createTaskDesc.value.trim(),
    status: dom.createTaskStatus.value,
    priority: dom.createTaskPriority.value,
    assigned_to: dom.createTaskAssignee.value ? Number(dom.createTaskAssignee.value) : null,
    due_date: dom.createTaskDuedate.value || null,
  };

  try {
    await request(api.tasks, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    
    // Clear Form & Close Modal
    dom.globalCreateTaskForm.reset();
    dom.createTaskModal.classList.add('hidden');
    showToast("Task created successfully!", "success");
    await syncWorkspaceData();
  } catch (error) {
    const detail = error.data?.title || error.data?.due_date || error.data?.detail || "Unable to create task.";
    showToast(Array.isArray(detail) ? detail.join(' ') : detail, "error");
  }
});

/* ==========================================
   EVENT LISTENERS & BINDERS
   ========================================== */

function initEventListeners() {
  // Navigation tabs
  dom.navItems.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Auth screen toggle
  dom.toSignup.addEventListener('click', (e) => {
    e.preventDefault();
    dom.loginForm.classList.add('hidden');
    dom.registerForm.classList.remove('hidden');
    dom.authSubtitle.textContent = 'Join the team workspace today';
  });

  dom.toLogin.addEventListener('click', (e) => {
    e.preventDefault();
    dom.registerForm.classList.add('hidden');
    dom.loginForm.classList.remove('hidden');
    dom.authSubtitle.textContent = 'Log in to your professional workspace';
  });

  // Session Control
  dom.btnSignout.addEventListener('click', () => {
    clearTokens();
    showToast("Signed out.", "info");
  });

  // Action Buttons
  dom.btnRefresh.addEventListener('click', async () => {
    showToast("Syncing data...", "info");
    await syncWorkspaceData();
    showToast("Workspace synchronized.", "success");
  });

  dom.btnGlobalAddTask.addEventListener('click', () => {
    dom.createTaskModal.classList.remove('hidden');
  });

  dom.createTaskModalClose.addEventListener('click', () => {
    dom.createTaskModal.classList.add('hidden');
  });

  dom.modalBtnClose.addEventListener('click', closeTaskModal);

  // Filters search/dropdowns on Kanban tab
  dom.filterProject.addEventListener('change', renderKanbanBoard);
  dom.filterPriority.addEventListener('change', renderKanbanBoard);
  dom.searchTask.addEventListener('input', renderKanbanBoard);

  // Shortcut redirections on dashboard
  dom.shortcutCreateTeam.addEventListener('click', () => switchTab('teams'));
  dom.shortcutCreateProject.addEventListener('click', () => switchTab('projects'));
}

/* ==========================================
   INITIALIZATION
   ========================================== */

async function initWorkspace() {
  await loadMe();
  await syncWorkspaceData();
}

function init() {
  initEventListeners();
  if (state.access) {
    initWorkspace();
  } else {
    clearTokens();
  }
}

// Boot
init();
