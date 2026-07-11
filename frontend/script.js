/* ================================================================
   GrievEase v3.0 - script.js
   Handles: Student Dashboard, Admin Dashboard, Staff Dashboard
   Features: AI predict, Timeline, Comments, Notifications,
             Bulk ops, Analytics Charts, Staff Mgmt, Departments,
             Audit Log, Escalation, SLA countdown, WebSocket
================================================================ */

// API_BASE: set window.__API_BASE__ in index.html for production deployment
// Falls back to localhost:8000 for local development
const API_BASE = window.__API_BASE__ || "http://127.0.0.1:8000";

const COLORS = ["#2563eb","#16a34a","#d97706","#dc2626","#7c3aed","#0891b2","#be185d","#15803d","#c2410c","#1d4ed8"];
const COLORS_ALPHA = ["rgba(37,99,235,.7)","rgba(22,163,74,.7)","rgba(217,119,6,.7)","rgba(220,38,38,.7)","rgba(124,58,237,.7)","rgba(8,145,178,.7)","rgba(190,24,93,.7)","rgba(21,128,61,.7)","rgba(194,65,12,.7)","rgba(29,78,216,.7)"];

const API = {
  studentLogin:   `${API_BASE}/api/users/student/login`,
  adminLogin:     `${API_BASE}/api/users/admin/login`,
  staffLogin:     `${API_BASE}/api/users/staff/login`,
  me:             `${API_BASE}/api/users/me`,
  complaints:     `${API_BASE}/api/complaints/`,
  complaintsJson: `${API_BASE}/api/complaints/json`,
  stats:          `${API_BASE}/api/complaints/stats`,
  analytics:      `${API_BASE}/api/complaints/analytics`,
  clearAll:       `${API_BASE}/api/complaints/clear-all`,
  predict:        `${API_BASE}/api/complaints/predict-category`,
  bulkUpdate:     `${API_BASE}/api/complaints/bulk-update`,
  staff:          `${API_BASE}/api/staff/`,
  staffDashboard: `${API_BASE}/api/staff/dashboard/me`,
  staffComplaints:`${API_BASE}/api/staff/dashboard/complaints`,
  departments:    `${API_BASE}/api/admin/departments`,
  auditLogs:      `${API_BASE}/api/admin/audit-logs`,
  exportCsv:      `${API_BASE}/api/admin/reports/complaints/csv`,
  backup:         `${API_BASE}/api/admin/backup`,
  escalation:     `${API_BASE}/api/admin/run-escalation`,
  notifications:  `${API_BASE}/api/notifications/`,
  notifCount:     `${API_BASE}/api/notifications/unread-count`,
  notifMarkRead:  `${API_BASE}/api/notifications/mark-read`,
};

// Expose on window so staff-dashboard.html overrides can access them
window.API          = API;
window.apiRequest   = apiRequest;
window.getToken     = getToken;
window.getUser      = getUser;
window.setSession   = setSession;
window.showToast    = showToast;
window.fmtDate      = fmtDate;
window.timeAgo      = timeAgo;
window.statusBadge  = statusBadge;
window.priorityBadge= priorityBadge;
window.logout       = logout;

const TOKEN_KEY = "grievease_token";
const USER_KEY  = "grievease_user";

/* ── Session ─────────────────────────────────────────────────── */
function getToken() { return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY); }
function getUser()  {
  try { const u = sessionStorage.getItem(USER_KEY) || localStorage.getItem(USER_KEY); return u ? JSON.parse(u) : null; }
  catch { return null; }
}
function setSession(token, user) {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
function logout(redirect) {
  sessionStorage.clear();
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  window.location.href = redirect;
}

/* ── API ─────────────────────────────────────────────────────── */
async function apiRequest(url, opts = {}) {
  try {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(url, { ...opts, headers });
    if (res.status === 401) {
      const p = window.location.pathname;
      if (!p.includes("login")) {
        showToast("Session expired. Logging out…", "error");
        setTimeout(() => { if (p.includes("admin")) logout("admin-login.html"); else if (p.includes("staff")) logout("staff-login.html"); else logout("student-login.html"); }, 1500);
      }
      return null;
    }
    if (res.status === 204) return null;
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
    }
    return await res.json();
  } catch (e) { console.error("API:", e.message); throw e; }
}

async function apiForm(url, formData) {
  try {
    const token = getToken();
    const res = await fetch(url, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) { const e = await res.json().catch(() => ({ detail: "Error" })); throw new Error(typeof e.detail === "string" ? e.detail : JSON.stringify(e.detail)); }
    return await res.json();
  } catch (e) { console.error("Form API:", e.message); throw e; }
}

/* ── Toast ───────────────────────────────────────────────────── */
function showToast(msg, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

/* ── Status / Priority Badges ────────────────────────────────── */
function statusBadge(s) {
  const cls = { "Pending": "yellow", "Assigned": "secondary", "In Progress": "info", "Escalated": "danger", "Resolved": "success", "Closed": "neutral" };
  return `<span class="badge ${cls[s] || "neutral"}">${s}</span>`;
}
function priorityBadge(p) {
  return `<span class="badge priority-${p}">${p}</span>`;
}
function priorityDot(p) {
  return `<span class="priority-dot ${p}">${p}</span>`;
}
function slaTag(c) {
  if (!c.sla_deadline) return "";
  const diff = new Date(c.sla_deadline) - new Date();
  const days = Math.ceil(diff / 86400000);
  if (c.sla_breached || days < 0) return `<span class="badge danger">SLA Breached</span>`;
  if (days === 0) return `<span class="badge warning">SLA Today</span>`;
  return `<span class="badge info">${days}d left</span>`;
}
function fmtDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}
function timeAgo(d) {
  if (!d) return "";
  const diff = Date.now() - new Date(d).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

/* ── Subcategory Map ─────────────────────────────────────────── */
const SUBCATEGORIES = {
  Academic:       ["Marks/Grades", "Attendance", "Faculty Issue", "Assignment", "Syllabus", "Other"],
  Administration: ["Documents", "Certificate", "Policy Issue", "Office Staff", "Other"],
  Examination:    ["Result", "Re-evaluation", "Hall Ticket", "Supplementary", "Other"],
  Fees:           ["Fee Structure", "Refund", "Scholarship", "Receipt Issue", "Other"],
  Hostel:         ["Room Allotment", "Mess/Food", "Water/Electricity", "Cleanliness", "Warden Issue", "Other"],
  "IT Support":   ["Portal Login", "WiFi/Network", "ERP Issue", "Email", "Hardware", "Other"],
  Infrastructure: ["Classroom", "Furniture", "Projector", "Building Issue", "Parking", "Other"],
  Library:        ["Book Issue", "Fine", "Digital Resources", "Timing", "Other"],
  Security:       ["Lost Item", "Ragging", "Gate Access", "CCTV", "Parking", "Other"],
  Transport:      ["Bus Route", "Bus Timing", "Driver Issue", "Overcrowding", "Other"],
};

/* ── AI Predict (debounced) ──────────────────────────────────── */
let aiTimer = null;
function debounceAiPredict() {
  clearTimeout(aiTimer);
  aiTimer = setTimeout(aiPredict, 900);
}
async function aiPredict() {
  const title = document.getElementById("complaintTitle")?.value || "";
  const desc  = document.getElementById("complaintDescription")?.value || "";
  const text  = `${title} ${desc}`.trim();
  if (text.length < 10) return;
  try {
    const data = await apiRequest(`${API.predict}?text=${encodeURIComponent(text)}`);
    if (!data) return;
    const box  = document.getElementById("aiSuggestionBox");
    const span = document.getElementById("aiSuggestionText");
    if (box && span) {
      span.textContent = `Category: ${data.predicted_category} | Priority: ${data.predicted_priority} | Confidence: ${Math.round((data.confidence || 0.85) * 100)}%`;
      box.hidden = false;
    }
    // Auto-set category dropdown
    const catSel = document.getElementById("complaintCategory");
    if (catSel && !catSel.value) {
      catSel.value = data.predicted_category;
      updateSubcategories(data.predicted_category);
    }
  } catch {}
}

/* ── Subcategory Update ──────────────────────────────────────── */
function updateSubcategories(category) {
  const sel = document.getElementById("complaintSubcategory");
  if (!sel) return;
  sel.innerHTML = '<option value="">— Select subcategory —</option>';
  (SUBCATEGORIES[category] || []).forEach(sub => {
    const opt = document.createElement("option");
    opt.value = sub; opt.textContent = sub;
    sel.appendChild(opt);
  });
}

/* ── Notifications ───────────────────────────────────────────── */
async function loadNotifCount() {
  try {
    const data = await apiRequest(API.notifCount);
    if (!data) return;
    const ids = ["adminNotifCount", "staffNotifCount", "studentNotifCount"];
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) { el.textContent = data.count; el.hidden = data.count === 0; }
    });
  } catch {}
}

async function openNotifications() {
  const panel = document.getElementById("notifPanel");
  if (!panel) return;
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) {
    const data = await apiRequest(API.notifications) || [];
    const list = document.getElementById("notifList");
    if (!list) return;
    if (!data.length) { list.innerHTML = '<p class="text-muted" style="padding:1rem">No notifications yet.</p>'; return; }
    list.innerHTML = data.map(n => `
      <div class="notif-item ${n.is_read ? "" : "unread"}">
        <div class="notif-title">${n.title}</div>
        <div class="notif-message">${n.message}</div>
        <div class="notif-time">${timeAgo(n.created_at)}</div>
      </div>`).join("");
  }
}
function closeNotifications() {
  const p = document.getElementById("notifPanel");
  if (p) p.classList.add("hidden");
}
async function markAllRead() {
  await apiRequest(API.notifMarkRead, { method: "POST" });
  loadNotifCount();
  closeNotifications();
  showToast("Notifications marked as read");
}

/* ══════════════════════════════════════════════════════════════
   STUDENT DASHBOARD
══════════════════════════════════════════════════════════════ */
let currentRating = 0;
let currentRatingComplaintId = "";

function initStudentDashboard() {
  const user = getUser();
  if (!user || user.type !== "student") { window.location.href = "student-login.html"; return; }

  document.getElementById("welcomeMessage").textContent = `Welcome, ${user.name}`;
  document.getElementById("studentLogout")?.addEventListener("click", () => logout("student-login.html"));
  document.getElementById("refreshComplaints")?.addEventListener("click", loadStudentComplaints);
  document.getElementById("complaintCategory")?.addEventListener("change", function() { updateSubcategories(this.value); });
  document.getElementById("complaintTitle")?.addEventListener("input", debounceAiPredict);

  // Star rating
  document.querySelectorAll(".star").forEach(star => {
    star.addEventListener("click", () => {
      currentRating = +star.dataset.val;
      document.querySelectorAll(".star").forEach((s, i) => s.classList.toggle("active", i < currentRating));
    });
  });

  document.getElementById("complaintForm")?.addEventListener("submit", submitComplaint);
  loadStudentComplaints();
  loadNotifCount();
  setInterval(loadNotifCount, 30000);
}

async function submitComplaint(e) {
  e.preventDefault();
  const user = getUser();
  const title    = document.getElementById("complaintTitle").value.trim();
  const desc     = document.getElementById("complaintDescription").value.trim();
  const category = document.getElementById("complaintCategory").value;
  const sub      = document.getElementById("complaintSubcategory").value;
  const file     = document.getElementById("complaintFile")?.files[0];

  if (!title || !desc) { showToast("Please fill in title and description", "error"); return; }

  const btn = e.target.querySelector("button[type=submit]");
  btn.disabled = true; btn.textContent = "Submitting…";

  try {
    let result;
    if (file) {
      const fd = new FormData();
      fd.append("student_name", user.name);
      fd.append("student_email", user.email);
      fd.append("admission_number", user.admission_number);
      fd.append("title", title);
      fd.append("description", desc);
      if (category) fd.append("category", category);
      if (sub) fd.append("subcategory", sub);
      fd.append("file", file);
      result = await apiForm(API.complaints, fd);
    } else {
      result = await apiRequest(API.complaintsJson, {
        method: "POST",
        body: JSON.stringify({
          student_name: user.name, student_email: user.email,
          admission_number: user.admission_number,
          title, description: desc, category: category || null, subcategory: sub || null,
        }),
      });
    }
    if (result) {
      showToast(`✅ Complaint ${result.complaint_id} submitted! Category: ${result.category}`, "success");
      e.target.reset();
      document.getElementById("aiSuggestionBox").hidden = true;
      loadStudentComplaints();
    }
  } catch (err) {
    if (err.message.includes("Similar complaint")) {
      document.getElementById("duplicateWarning").hidden = false;
      showToast("⚠️ Similar complaint already exists!", "warning");
    } else {
      showToast(err.message || "Submission failed", "error");
    }
  } finally {
    btn.disabled = false; btn.textContent = "Submit Complaint";
  }
}

async function loadStudentComplaints() {
  try {
    const complaints = await apiRequest(API.complaints) || [];
    const tbody = document.querySelector("#studentComplaintsTable tbody");
    if (!tbody) return;

    // Stats
    const total    = complaints.length;
    const pending  = complaints.filter(c => ["Pending","Assigned","In Progress","Escalated"].includes(c.status)).length;
    const resolved = complaints.filter(c => ["Resolved","Closed"].includes(c.status)).length;
    document.getElementById("totalComplaintsCard").textContent   = total;
    document.getElementById("pendingComplaintsCard").textContent  = pending;
    document.getElementById("resolvedComplaintsCard").textContent = resolved;

    if (!complaints.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="empty">No complaints yet. Submit your first grievance above.</td></tr>';
      return;
    }

    tbody.innerHTML = complaints.map(c => `
      <tr class="status-row-${c.status.replace(' ','')}">
        <td><code style="font-size:.78rem">${c.complaint_id}</code></td>
        <td>${c.title.substring(0, 45)}${c.title.length > 45 ? "…" : ""}</td>
        <td><span class="badge neutral">${c.category}</span></td>
        <td>${priorityDot(c.priority)}</td>
        <td>${statusBadge(c.status)}</td>
        <td>${c.assigned_to || '<span class="text-muted">—</span>'}</td>
        <td>${slaTag(c)}</td>
        <td>${fmtDate(c.created_at)}</td>
        <td>
          <button class="btn-view" onclick="openStudentComplaintModal('${c.complaint_id}')">👁 View</button>
          ${c.status === "Resolved" && !c.rating ? `<button class="btn-rate" onclick="openRating('${c.complaint_id}')">★ Rate</button>` : ""}
          ${c.rating ? `<span class="text-muted" style="font-size:.78rem">★ ${c.rating}/5</span>` : ""}
        </td>
      </tr>`).join("");
  } catch (err) { showToast("Failed to load complaints", "error"); }
}

async function openStudentComplaintModal(complaintId) {
  const c = await apiRequest(`${API.complaints}${complaintId}`);
  if (!c) return;

  document.getElementById("studentModalTitle").textContent = c.complaint_id;

  // Detail grid
  document.getElementById("studentComplaintDetail").innerHTML = `
    <div class="detail-row"><span class="detail-label">ID</span><span class="detail-value">${c.complaint_id}</span></div>
    <div class="detail-row"><span class="detail-label">Status</span><span class="detail-value">${statusBadge(c.status)}</span></div>
    <div class="detail-row"><span class="detail-label">Category</span><span class="detail-value">${c.category}</span></div>
    <div class="detail-row"><span class="detail-label">Priority</span><span class="detail-value">${priorityBadge(c.priority)}</span></div>
    <div class="detail-row"><span class="detail-label">Assigned To</span><span class="detail-value">${c.assigned_to || "—"}</span></div>
    <div class="detail-row"><span class="detail-label">Department</span><span class="detail-value">${c.assigned_department || "—"}</span></div>
    <div class="detail-row full"><span class="detail-label">Title</span><span class="detail-value">${c.title}</span></div>
    <div class="detail-row full"><span class="detail-label">Description</span><span class="detail-value">${c.description}</span></div>
    ${c.admin_remarks ? `<div class="detail-row full"><span class="detail-label">Admin Remarks</span><span class="detail-value">${c.admin_remarks}</span></div>` : ""}
    <div class="detail-row"><span class="detail-label">Submitted</span><span class="detail-value">${fmtDate(c.created_at)}</span></div>
    ${c.resolved_at ? `<div class="detail-row"><span class="detail-label">Resolved</span><span class="detail-value">${fmtDate(c.resolved_at)}</span></div>` : ""}
  `;

  // SLA
  const slaBox = document.getElementById("slaCountdown");
  if (c.sla_deadline) {
    const diff = new Date(c.sla_deadline) - new Date();
    const days = Math.ceil(diff / 86400000);
    const breached = c.sla_breached || days < 0;
    slaBox.className = `sla-box ${breached ? "breached" : "ok"}`;
    slaBox.innerHTML = `<span class="sla-label">⏱ SLA Deadline:</span> <span class="sla-countdown">${breached ? "Breached" : `${days} day(s) remaining`}</span> <span class="text-muted">(${fmtDate(c.sla_deadline)})</span>`;
    slaBox.hidden = false;
  } else { slaBox.hidden = true; }

  // Timeline
  const timeline = await apiRequest(`${API.complaints}${complaintId}/timeline`) || c.timeline || [];
  renderTimeline("studentTimeline", timeline);

  // Comments
  const comments = await apiRequest(`${API.complaints}${complaintId}/comments`) || c.comments || [];
  renderComments("studentComments", comments);
  document.getElementById("studentCommentText").value = "";
  window._studentModalComplaintId = complaintId;

  // Rating section
  const ratingSection = document.getElementById("ratingSection");
  if (c.status === "Resolved" && !c.rating) {
    ratingSection.classList.remove("hidden");
    currentRatingComplaintId = complaintId;
    currentRating = 0;
    document.querySelectorAll(".star").forEach(s => s.classList.remove("active"));
  } else {
    ratingSection.classList.add("hidden");
  }

  document.getElementById("studentComplaintModal").classList.remove("hidden");
}

function closeStudentModal() { document.getElementById("studentComplaintModal").classList.add("hidden"); }

function openRating(complaintId) {
  openStudentComplaintModal(complaintId);
}

async function submitRating() {
  if (!currentRating) { showToast("Please select a star rating", "warning"); return; }
  const feedback = document.getElementById("ratingFeedback")?.value || "";
  try {
    await apiRequest(`${API.complaints}${currentRatingComplaintId}/rate`, {
      method: "POST",
      body: JSON.stringify({ rating: currentRating, rating_feedback: feedback }),
    });
    showToast("✅ Rating submitted! Thank you.", "success");
    document.getElementById("ratingSection").classList.add("hidden");
    loadStudentComplaints();
  } catch (e) { showToast(e.message, "error"); }
}

async function submitStudentComment() {
  const text = document.getElementById("studentCommentText").value.trim();
  if (!text) return;
  const id = window._studentModalComplaintId;
  try {
    await apiRequest(`${API.complaints}${id}/comments`, {
      method: "POST",
      body: JSON.stringify({ comment_text: text, is_internal: false }),
    });
    showToast("Comment posted");
    document.getElementById("studentCommentText").value = "";
    const comments = await apiRequest(`${API.complaints}${id}/comments`) || [];
    renderComments("studentComments", comments);
  } catch (e) { showToast(e.message, "error"); }
}

/* ── Timeline & Comment Renderers ────────────────────────────── */
function renderTimeline(containerId, timeline) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!timeline.length) { el.innerHTML = '<p class="text-muted">No timeline entries yet.</p>'; return; }
  el.innerHTML = timeline.map(t => `
    <div class="timeline-item ${t.event.replace(" ", "-")}">
      <div class="timeline-event">${t.event}</div>
      ${t.description ? `<div class="timeline-desc">${t.description}</div>` : ""}
      <div class="timeline-meta">By ${t.performed_by || "System"} · ${timeAgo(t.created_at)}</div>
    </div>`).join("");
}

function renderComments(containerId, comments) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!comments.length) { el.innerHTML = '<p class="text-muted">No comments yet.</p>'; return; }
  el.innerHTML = comments.map(c => `
    <div class="comment-item ${c.is_internal ? "internal" : ""}">
      <span class="comment-author">${c.author_name}</span>
      <span class="comment-role">${c.author_role}${c.is_internal ? " · 🔒 Internal" : ""}</span>
      <div class="comment-text">${c.comment_text}</div>
      <div class="comment-time">${timeAgo(c.created_at)}</div>
    </div>`).join("");
}

/* ══════════════════════════════════════════════════════════════
   ADMIN DASHBOARD
══════════════════════════════════════════════════════════════ */
let allComplaints = [];
let chartInstances = {};

function initAdminDashboard() {
  const user = getUser();
  if (!user || !["admin","super_admin"].includes(user.type)) { window.location.href = "admin-login.html"; return; }

  document.getElementById("adminLogout")?.addEventListener("click", () => logout("admin-login.html"));
  document.getElementById("refreshAdminComplaints")?.addEventListener("click", loadAdminComplaints);
  document.getElementById("exportCsv")?.addEventListener("click", () => window.open(API.exportCsv + `?token=${getToken()}`, "_blank"));
  document.getElementById("backupDb")?.addEventListener("click", () => window.open(API.backup, "_blank"));
  document.getElementById("clearAllComplaints")?.addEventListener("click", clearAll);
  document.getElementById("loadSampleData")?.addEventListener("click", loadSampleData);
  document.getElementById("runEscalation")?.addEventListener("click", runEscalation);

  // Sidebar nav
  document.querySelectorAll(".nav-link[data-section]").forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
      link.classList.add("active");
      document.getElementById(link.dataset.section)?.scrollIntoView({ behavior: "smooth" });
    });
  });

  loadAdminComplaints();
  loadAnalytics();
  loadStaffTable();
  loadDepartments();
  loadAuditLog();
  loadNotifCount();
  setInterval(loadNotifCount, 30000);
  initWebSocket(user.type, user.id);
}

async function loadAdminComplaints() {
  try {
    allComplaints = await apiRequest(API.complaints) || [];
    const stats = await apiRequest(API.stats);
    if (stats) {
      document.getElementById("totalComplaintsAdmin").textContent     = stats.total;
      document.getElementById("pendingComplaintsAdmin").textContent   = stats.pending;
      document.getElementById("inProgressComplaintsAdmin").textContent= stats.in_progress;
      document.getElementById("resolvedComplaintsAdmin").textContent  = stats.resolved;
      document.getElementById("escalatedComplaintsAdmin").textContent = stats.escalated || 0;
      document.getElementById("closedComplaintsAdmin").textContent    = stats.closed || 0;
    }
    renderAdminTable(allComplaints);
  } catch (e) { showToast("Failed to load complaints", "error"); }
}

function renderAdminTable(complaints) {
  const tbody = document.querySelector("#adminComplaintsTable tbody");
  if (!tbody) return;
  if (!complaints.length) {
    tbody.innerHTML = '<tr><td colspan="11" class="empty">No complaints found.</td></tr>';
    return;
  }
  tbody.innerHTML = complaints.map(c => `
    <tr class="status-row-${c.status.replace(' ','')}">
      <td><input type="checkbox" class="complaint-cb" value="${c.complaint_id}" onchange="updateBulkBar()"/></td>
      <td><code style="font-size:.75rem">${c.complaint_id}</code></td>
      <td>
        <div style="font-weight:600;font-size:.85rem">${c.student_name}</div>
        <div style="font-size:.75rem;color:var(--text3)">${c.student_email}</div>
      </td>
      <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${c.title}">${c.title}</td>
      <td><span class="badge neutral">${c.category}</span></td>
      <td>${priorityBadge(c.priority)}</td>
      <td>${statusBadge(c.status)}</td>
      <td>${c.assigned_to ? `<span style="font-size:.8rem">${c.assigned_to}</span>` : '<span class="text-muted">—</span>'}</td>
      <td>${slaTag(c)}</td>
      <td>${fmtDate(c.created_at)}</td>
      <td>
        <button class="btn ghost small" onclick="openAdminComplaintModal('${c.complaint_id}')">View</button>
      </td>
    </tr>`).join("");
}

function filterComplaints() {
  const statusF   = document.getElementById("filterStatus")?.value;
  const categoryF = document.getElementById("filterCategory")?.value;
  const priorityF = document.getElementById("filterPriority")?.value;
  const searchF   = document.getElementById("filterSearch")?.value.toLowerCase();

  let filtered = allComplaints;
  if (statusF)   filtered = filtered.filter(c => c.status === statusF);
  if (categoryF) filtered = filtered.filter(c => c.category === categoryF);
  if (priorityF) filtered = filtered.filter(c => c.priority === priorityF);
  if (searchF)   filtered = filtered.filter(c =>
    c.complaint_id.toLowerCase().includes(searchF) ||
    c.student_name.toLowerCase().includes(searchF) ||
    c.title.toLowerCase().includes(searchF) ||
    c.admission_number.toLowerCase().includes(searchF)
  );
  renderAdminTable(filtered);
}

function clearFilters() {
  ["filterStatus","filterCategory","filterPriority","filterSearch"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  renderAdminTable(allComplaints);
}

// Bulk
function toggleSelectAll(cb) {
  document.querySelectorAll(".complaint-cb").forEach(c => c.checked = cb.checked);
  updateBulkBar();
}
function updateBulkBar() {
  const checked = document.querySelectorAll(".complaint-cb:checked");
  const bar = document.getElementById("bulkBar");
  if (!bar) return;
  if (checked.length > 0) {
    bar.classList.remove("hidden");
    document.getElementById("bulkCount").textContent = `${checked.length} selected`;
  } else {
    bar.classList.add("hidden");
  }
}
function clearSelection() {
  document.querySelectorAll(".complaint-cb").forEach(c => c.checked = false);
  const all = document.getElementById("selectAll");
  if (all) all.checked = false;
  const bar = document.getElementById("bulkBar");
  if (bar) bar.classList.add("hidden");
}
async function doBulkUpdate() {
  const ids    = [...document.querySelectorAll(".complaint-cb:checked")].map(c => c.value);
  const status = document.getElementById("bulkStatus").value;
  if (!ids.length || !status) { showToast("Select complaints and a status", "warning"); return; }
  try {
    const result = await apiRequest(API.bulkUpdate, {
      method: "POST",
      body: JSON.stringify({ complaint_ids: ids, new_status: status }),
    });
    showToast(`✅ ${result.updated} complaints updated to "${status}"`, "success");
    clearSelection();
    loadAdminComplaints();
  } catch (e) { showToast(e.message, "error"); }
}

// Admin Complaint Modal
async function openAdminComplaintModal(complaintId) {
  const c = await apiRequest(`${API.complaints}${complaintId}`);
  if (!c) return;

  document.getElementById("adminUpdateComplaintId").value = complaintId;
  document.getElementById("adminUpdateStatus").value   = c.status;
  document.getElementById("adminUpdatePriority").value = c.priority;
  document.getElementById("adminUpdateRemarks").value  = c.admin_remarks || "";
  document.getElementById("adminUpdateNotes").value    = c.internal_notes || "";

  document.getElementById("adminComplaintDetail").innerHTML = `
    <div class="detail-row"><span class="detail-label">ID</span><span class="detail-value">${c.complaint_id}</span></div>
    <div class="detail-row"><span class="detail-label">Status</span><span class="detail-value">${statusBadge(c.status)}</span></div>
    <div class="detail-row"><span class="detail-label">Category</span><span class="detail-value">${c.category}</span></div>
    <div class="detail-row"><span class="detail-label">Priority</span><span class="detail-value">${priorityBadge(c.priority)}</span></div>
    <div class="detail-row"><span class="detail-label">Student</span><span class="detail-value">${c.student_name} (${c.admission_number})</span></div>
    <div class="detail-row"><span class="detail-label">Email</span><span class="detail-value">${c.student_email}</span></div>
    <div class="detail-row full"><span class="detail-label">Title</span><span class="detail-value">${c.title}</span></div>
    <div class="detail-row full"><span class="detail-label">Description</span><span class="detail-value">${c.description}</span></div>
    <div class="detail-row"><span class="detail-label">Department</span><span class="detail-value">${c.assigned_department || "—"}</span></div>
    <div class="detail-row"><span class="detail-label">SLA</span><span class="detail-value">${slaTag(c) || "No SLA"}</span></div>
    ${c.escalation_level ? `<div class="detail-row"><span class="detail-label">Escalation</span><span class="detail-value"><span class="badge danger">Level ${c.escalation_level}</span></span></div>` : ""}
    ${c.rating ? `<div class="detail-row"><span class="detail-label">Student Rating</span><span class="detail-value">${"★".repeat(c.rating)}${"☆".repeat(5-c.rating)} ${c.rating}/5</span></div>` : ""}
    <div class="detail-row"><span class="detail-label">Submitted</span><span class="detail-value">${fmtDate(c.created_at)}</span></div>
  `;

  // Staff dropdown
  const staffSel = document.getElementById("adminAssignStaff");
  if (staffSel) {
    staffSel.innerHTML = '<option value="">— Select staff —</option>';
    const staffList = await apiRequest(API.staff) || [];
    staffList.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = `${s.name} (${s.department})`;
      if (c.assigned_staff_id === s.id) opt.selected = true;
      staffSel.appendChild(opt);
    });
  }

  // Timeline & Comments
  const timeline = await apiRequest(`${API.complaints}${complaintId}/timeline`) || [];
  renderTimeline("adminTimeline", timeline);
  const comments = await apiRequest(`${API.complaints}${complaintId}/comments`) || [];
  renderComments("adminComments", comments);
  document.getElementById("adminCommentText").value = "";
  window._adminModalComplaintId = complaintId;

  document.getElementById("adminComplaintModal").classList.remove("hidden");
}

function closeAdminModal() { document.getElementById("adminComplaintModal").classList.add("hidden"); }

async function submitAdminUpdate() {
  const id       = document.getElementById("adminUpdateComplaintId").value;
  const status   = document.getElementById("adminUpdateStatus").value;
  const priority = document.getElementById("adminUpdatePriority").value;
  const remarks  = document.getElementById("adminUpdateRemarks").value;
  const notes    = document.getElementById("adminUpdateNotes").value;
  const staffSel = document.getElementById("adminAssignStaff");
  const staffId  = staffSel ? parseInt(staffSel.value) || null : null;
  const staffName= staffSel ? staffSel.options[staffSel.selectedIndex]?.text.split(" (")[0] : null;

  try {
    await apiRequest(`${API.complaints}${id}`, {
      method: "PUT",
      body: JSON.stringify({
        status, priority, admin_remarks: remarks, internal_notes: notes,
        assigned_staff_id: staffId,
        assigned_to: staffId ? staffName : undefined,
      }),
    });
    showToast(`✅ Complaint ${id} updated`, "success");
    closeAdminModal();
    loadAdminComplaints();
  } catch (e) { showToast(e.message, "error"); }
}

async function submitAdminComment() {
  const text     = document.getElementById("adminCommentText").value.trim();
  const internal = document.getElementById("adminCommentInternal")?.checked;
  const id       = window._adminModalComplaintId;
  if (!text) return;
  try {
    await apiRequest(`${API.complaints}${id}/comments`, {
      method: "POST",
      body: JSON.stringify({ comment_text: text, is_internal: !!internal }),
    });
    showToast("Comment posted");
    document.getElementById("adminCommentText").value = "";
    const comments = await apiRequest(`${API.complaints}${id}/comments`) || [];
    renderComments("adminComments", comments);
  } catch (e) { showToast(e.message, "error"); }
}

// Analytics
async function loadAnalytics() {
  try {
    const data = await apiRequest(API.analytics);
    if (!data) return;

    // KPI row
    const kpiEl = document.getElementById("analyticsKpis");
    if (kpiEl) {
      kpiEl.innerHTML = `
        <div class="kpi-card"><div class="kpi-value">${data.resolution_rate}%</div><div class="kpi-label">Resolution Rate</div></div>
        <div class="kpi-card"><div class="kpi-value">${data.avg_resolution_days}d</div><div class="kpi-label">Avg Resolution Time</div></div>
        <div class="kpi-card"><div class="kpi-value">${data.avg_rating || "N/A"}</div><div class="kpi-label">Avg Student Rating</div></div>
        <div class="kpi-card"><div class="kpi-value">${data.sla_breached}</div><div class="kpi-label">SLA Breached</div></div>
        <div class="kpi-card"><div class="kpi-value">${data.escalated}</div><div class="kpi-label">Escalated</div></div>
      `;
    }

    renderChart("categoryChart", "doughnut",
      data.by_category.map(d => d.category),
      data.by_category.map(d => d.count),
      "Complaints by Category"
    );
    renderChart("statusChart", "pie",
      data.by_status.map(d => d.status),
      data.by_status.map(d => d.count),
      "Complaints by Status"
    );
    renderChart("priorityChart", "bar",
      data.by_priority.map(d => d.priority),
      data.by_priority.map(d => d.count),
      "Complaints by Priority"
    );
    renderChart("monthlyChart", "line",
      data.monthly_trend.map(d => d.month),
      data.monthly_trend.map(d => d.count),
      "Monthly Trend"
    );
    if (data.department_performance?.length) {
      renderChart("deptChart", "bar",
        data.department_performance.map(d => d.department),
        data.department_performance.map(d => d.total),
        "Dept Total", {
          datasets2: [{ label: "Resolved", data: data.department_performance.map(d => d.resolved), backgroundColor: "rgba(22,163,74,.7)" }]
        }
      );
    }
    if (data.staff_performance?.length) {
      renderChart("staffPerfChart", "bar",
        data.staff_performance.map(d => d.staff),
        data.staff_performance.map(d => d.total),
        "Staff Total"
      );
    }
  } catch (e) { console.error("Analytics:", e); }
}


function renderChart(canvasId, type, labels, data, label, extra = {}) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  if (chartInstances[canvasId]) { chartInstances[canvasId].destroy(); }
  const bgColors = type === "line" ? "rgba(37,99,235,.15)" : type === "bar" ? COLORS_ALPHA : COLORS;
  const bdColors = type === "line" ? "#2563eb" : COLORS;
  const datasets = [{
    label, data,
    backgroundColor: bgColors,
    borderColor: bdColors,
    borderWidth: type === "bar" ? 0 : 2,
    borderRadius: type === "bar" ? 4 : 0,
    fill: type === "line", tension: .4,
    ...(extra.dataset1 || {})
  }];
  if (extra.datasets2) datasets.push(...extra.datasets2);
  chartInstances[canvasId] = new Chart(canvas, {
    type,
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { position: "bottom", labels: { font: { size: 11 } } } },
      scales: ["bar","line"].includes(type) ? { y: { beginAtZero: true, ticks: { stepSize: 1 } } } : undefined,
    }
  });
}

// Staff Management
async function loadStaffTable() {
  const tbody = document.querySelector("#staffTable tbody");
  if (!tbody) return;
  try {
    const staff = await apiRequest(API.staff + "?active_only=false") || [];
    if (!staff.length) { tbody.innerHTML = '<tr><td colspan="8" class="empty">No staff yet. Add staff to enable auto-assignment.</td></tr>'; return; }
    tbody.innerHTML = staff.map(s => `
      <tr>
        <td>${s.id}</td>
        <td><strong>${s.name}</strong></td>
        <td>${s.email}</td>
        <td><span class="badge neutral">${s.department}</span></td>
        <td>${s.designation || "—"}</td>
        <td>${s.phone || "—"}</td>
        <td>${s.is_active ? '<span class="badge success">Active</span>' : '<span class="badge neutral">Inactive</span>'}</td>
        <td>
          <button class="btn-danger-sm" onclick="deactivateStaff(${s.id},'${s.name}')">Deactivate</button>
        </td>
      </tr>`).join("");
  } catch (e) { tbody.innerHTML = '<tr><td colspan="8" class="empty">Failed to load staff.</td></tr>'; }
}

function openAddStaffModal()  { document.getElementById("addStaffModal").classList.remove("hidden"); }
function closeAddStaffModal() { document.getElementById("addStaffModal").classList.add("hidden"); }

async function submitAddStaff() {
  const name        = document.getElementById("newStaffName").value.trim();
  const email       = document.getElementById("newStaffEmail").value.trim();
  const password    = document.getElementById("newStaffPassword").value;
  const department  = document.getElementById("newStaffDepartment").value;
  const designation = document.getElementById("newStaffDesignation").value;
  const phone       = document.getElementById("newStaffPhone").value;
  if (!name || !email || !password || !department) { showToast("Please fill in all required fields", "warning"); return; }
  try {
    await apiRequest(API.staff, {
      method: "POST",
      body: JSON.stringify({ name, email, password, department, designation, phone }),
    });
    showToast("✅ Staff added successfully", "success");
    closeAddStaffModal();
    loadStaffTable();
  } catch (e) { showToast(e.message, "error"); }
}

async function deactivateStaff(id, name) {
  if (!confirm(`Deactivate staff member: ${name}?`)) return;
  try {
    await apiRequest(`${API.staff}${id}`, { method: "DELETE" });
    showToast(`${name} deactivated`, "success");
    loadStaffTable();
  } catch (e) { showToast(e.message, "error"); }
}

// Departments
async function loadDepartments() {
  const grid = document.getElementById("deptGrid");
  if (!grid) return;
  try {
    const depts = await apiRequest(API.departments) || [];
    if (!depts.length) { grid.innerHTML = '<p class="empty">No departments loaded.</p>'; return; }
    grid.innerHTML = depts.map(d => `
      <div class="dept-card">
        <div class="dept-name">${d.name}</div>
        <div class="dept-category">Handles: ${d.handles_category || "—"}</div>
        <div class="dept-head">👤 ${d.head_name || "No head assigned"}</div>
        ${d.head_email ? `<div style="font-size:.78rem;color:var(--text3)">${d.head_email}</div>` : ""}
        <div style="margin-top:.5rem">${d.is_active ? '<span class="badge success">Active</span>' : '<span class="badge neutral">Inactive</span>'}</div>
      </div>`).join("");
  } catch { grid.innerHTML = '<p class="empty">Failed to load departments.</p>'; }
}

// Audit Log
async function loadAuditLog() {
  const tbody = document.querySelector("#auditTable tbody");
  if (!tbody) return;
  try {
    const logs = await apiRequest(API.auditLogs) || [];
    if (!logs.length) { tbody.innerHTML = '<tr><td colspan="6" class="empty">No audit entries yet.</td></tr>'; return; }
    tbody.innerHTML = logs.map(l => `
      <tr>
        <td style="white-space:nowrap;font-size:.78rem">${fmtDate(l.created_at)}</td>
        <td><span class="badge neutral">${l.action}</span></td>
        <td>${l.performed_by}</td>
        <td><span class="badge info">${l.performed_by_role}</span></td>
        <td>${l.target_type ? `${l.target_type}: ${l.target_id}` : "—"}</td>
        <td style="font-size:.78rem;max-width:200px;overflow:hidden;text-overflow:ellipsis">${l.details || "—"}</td>
      </tr>`).join("");
  } catch { tbody.innerHTML = '<tr><td colspan="6" class="empty">Failed to load audit log.</td></tr>'; }
}

// Escalation
async function runEscalation() {
  const btn = document.getElementById("runEscalation");
  if (btn) { btn.disabled = true; btn.textContent = "Running…"; }
  try {
    const result = await apiRequest(API.escalation, { method: "POST" });
    showToast(`✅ Escalation complete: ${result.total_escalated} complaints escalated`, "success");
    loadAdminComplaints();
  } catch (e) { showToast(e.message, "error"); }
  finally { if (btn) { btn.disabled = false; btn.textContent = "⚡ Run Escalation"; } }
}

// Clear All
async function clearAll() {
  if (!confirm("Delete ALL complaints? This cannot be undone.")) return;
  try {
    await apiRequest(API.clearAll, { method: "DELETE" });
    showToast("All complaints deleted", "success");
    loadAdminComplaints();
  } catch (e) { showToast(e.message, "error"); }
}

// Sample Data
async function loadSampleData() {
  const SAMPLES = [
    { name: "Aarav Sharma",   email: "aarav@test.com",   admn: "2024CS001", title: "Marks not updated in portal",          desc: "My semester 4 marks are not showing in the ERP portal even after 2 weeks of result declaration.",    category: "Academic",       priority: "High"   },
    { name: "Priya Singh",    email: "priya@test.com",   admn: "2024EC002", title: "Hostel mess food quality very poor",   desc: "The mess food quality has been very bad for the past 2 weeks. Unhygienic and undercooked items.",        category: "Hostel",         priority: "High"   },
    { name: "Rahul Verma",    email: "rahul@test.com",   admn: "2024ME003", title: "College bus always late by 45 min",   desc: "Bus route 3 from Sector 12 is always 30-45 minutes late every morning causing us to miss first class.",  category: "Transport",      priority: "Medium" },
    { name: "Sneha Patel",    email: "sneha@test.com",   admn: "2024CS004", title: "Unable to login to student portal",   desc: "Getting invalid credentials error on ERP portal. Password reset link not working via email.",            category: "IT Support",     priority: "High"   },
    { name: "Arjun Kumar",    email: "arjun@test.com",   admn: "2024CE005", title: "Classroom projector not working",     desc: "The projector in Room 205 block B has been broken for 3 weeks. Teachers unable to teach properly.",      category: "Infrastructure", priority: "Medium" },
    { name: "Kavya Nair",     email: "kavya@test.com",   admn: "2024IT006", title: "Fee receipt not generated",          desc: "I paid my semester fee on 15th Jan but no receipt was generated. Showing pending in portal.",           category: "Fees",           priority: "High"   },
    { name: "Rohan Gupta",    email: "rohan@test.com",   admn: "2024CS007", title: "Re-evaluation result not updated",   desc: "Applied for re-evaluation in December. Result still not updated after 6 weeks.",                       category: "Examination",    priority: "High"   },
    { name: "Ananya Joshi",   email: "ananya@test.com",  admn: "2024EC008", title: "Reference books not available",      desc: "Required reference books for 5th semester not available in library. Request to procure urgently.",     category: "Library",        priority: "Low"    },
    { name: "Vikram Yadav",   email: "vikram@test.com",  admn: "2024ME009", title: "Lost laptop in campus",             desc: "My laptop was stolen from the mechanical engineering lab. Need CCTV footage review urgently.",           category: "Security",       priority: "Critical"},
    { name: "Pooja Sharma",   email: "pooja@test.com",   admn: "2024CS010", title: "Bonafide certificate pending 3 wks",desc: "Applied for bonafide certificate 3 weeks ago for bank loan. Still not issued from admin office.",      category: "Administration", priority: "Medium" },
  ];

  let success = 0;
  for (const s of SAMPLES) {
    try {
      await apiRequest(API.complaintsJson, {
        method: "POST",
        body: JSON.stringify({
          student_name: s.name, student_email: s.email, admission_number: s.admn,
          title: s.title, description: s.desc, category: s.category, priority: s.priority,
        }),
      });
      success++;
    } catch {}
  }
  showToast(`✅ ${success} sample complaints loaded`, "success");
  loadAdminComplaints();
  loadAnalytics();
}

/* ══════════════════════════════════════════════════════════════
   STAFF DASHBOARD
══════════════════════════════════════════════════════════════ */
function initStaffDashboard() {
  const user = getUser();
  if (!user || user.type !== "staff") { window.location.href = "staff-login.html"; return; }

  document.getElementById("staffLogout")?.addEventListener("click", () => logout("staff-login.html"));
  document.getElementById("refreshStaffComplaints")?.addEventListener("click", loadStaffComplaints);
  document.getElementById("staffWelcome").textContent     = `Welcome, ${user.name}`;
  document.getElementById("staffNameSidebar").textContent = user.name;
  document.getElementById("staffDeptSidebar").textContent = user.department || "";
  document.getElementById("staffDeptHeader").textContent  = `Department: ${user.department || ""}`;

  loadStaffDashboard();
  loadStaffComplaints();
  loadNotifCount();
  setInterval(loadNotifCount, 30000);
  initWebSocket("staff", user.id);
}

async function loadStaffDashboard() {
  try {
    const data = await apiRequest(API.staffDashboard);
    if (!data) return;
    const s = data.stats;
    document.getElementById("staffTotal").textContent      = s.total;
    document.getElementById("staffPending").textContent    = s.pending;
    document.getElementById("staffInProgress").textContent = s.in_progress;
    document.getElementById("staffResolved").textContent   = s.resolved;
    document.getElementById("staffEscalated").textContent  = s.escalated;
  } catch {}
}

async function loadStaffComplaints() {
  const tbody = document.querySelector("#staffComplaintsTable tbody");
  if (!tbody) return;
  try {
    const complaints = await apiRequest(API.staffComplaints) || [];
    if (!complaints.length) { tbody.innerHTML = '<tr><td colspan="9" class="empty">No complaints assigned yet.</td></tr>'; return; }
    tbody.innerHTML = complaints.map(c => `
      <tr class="status-row-${c.status.replace(' ','')}">
        <td><code style="font-size:.75rem">${c.complaint_id}</code></td>
        <td>
          <div style="font-weight:600;font-size:.85rem">${c.student_name}</div>
          <div style="font-size:.75rem;color:var(--text3)">${c.admission_number}</div>
        </td>
        <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c.title}</td>
        <td><span class="badge neutral">${c.category}</span></td>
        <td>${priorityBadge(c.priority)}</td>
        <td>${statusBadge(c.status)}</td>
        <td>${slaTag(c)}</td>
        <td>${fmtDate(c.created_at)}</td>
        <td><button class="btn-update" onclick="openStaffComplaintModal('${c.complaint_id}')">✏️ Update</button></td>
      </tr>`).join("");
  } catch (e) { tbody.innerHTML = '<tr><td colspan="9" class="empty">Failed to load complaints.</td></tr>'; }
}

async function openStaffComplaintModal(complaintId) {
  const c = await apiRequest(`${API.complaints}${complaintId}`);
  if (!c) return;

  document.getElementById("staffUpdateComplaintId").value = complaintId;
  document.getElementById("staffUpdateStatus").value  = c.status;
  document.getElementById("staffUpdateRemarks").value = c.admin_remarks || "";
  document.getElementById("staffUpdateNotes").value   = c.internal_notes || "";

  document.getElementById("staffComplaintDetail").innerHTML = `
    <div class="detail-row"><span class="detail-label">ID</span><span class="detail-value">${c.complaint_id}</span></div>
    <div class="detail-row"><span class="detail-label">Status</span><span class="detail-value">${statusBadge(c.status)}</span></div>
    <div class="detail-row"><span class="detail-label">Category</span><span class="detail-value">${c.category}</span></div>
    <div class="detail-row"><span class="detail-label">Priority</span><span class="detail-value">${priorityBadge(c.priority)}</span></div>
    <div class="detail-row full"><span class="detail-label">Title</span><span class="detail-value">${c.title}</span></div>
    <div class="detail-row full"><span class="detail-label">Description</span><span class="detail-value">${c.description}</span></div>
    <div class="detail-row full"><span class="detail-label">Student</span><span class="detail-value">${c.student_name} — ${c.student_email}</span></div>
    <div class="detail-row"><span class="detail-label">SLA</span><span class="detail-value">${slaTag(c) || "No SLA"}</span></div>
    <div class="detail-row"><span class="detail-label">Submitted</span><span class="detail-value">${fmtDate(c.created_at)}</span></div>
  `;

  const timeline = await apiRequest(`${API.complaints}${complaintId}/timeline`) || [];
  renderTimeline("staffTimeline", timeline);
  const comments = await apiRequest(`${API.complaints}${complaintId}/comments`) || [];
  renderComments("staffComments", comments);
  document.getElementById("staffCommentText").value = "";
  window._staffModalComplaintId = complaintId;

  document.getElementById("staffUpdateModal").classList.remove("hidden");
}

function closeStaffModal() { document.getElementById("staffUpdateModal").classList.add("hidden"); }

async function submitStaffUpdate() {
  const id     = document.getElementById("staffUpdateComplaintId").value;
  const status = document.getElementById("staffUpdateStatus").value;
  const remarks= document.getElementById("staffUpdateRemarks").value;
  const notes  = document.getElementById("staffUpdateNotes").value;
  try {
    await apiRequest(`${API.complaints}${id}`, {
      method: "PUT",
      body: JSON.stringify({ status, admin_remarks: remarks, internal_notes: notes }),
    });
    showToast(`✅ Complaint ${id} updated to "${status}"`, "success");
    closeStaffModal();
    loadStaffComplaints();
    loadStaffDashboard();
  } catch (e) { showToast(e.message, "error"); }
}

async function submitStaffComment() {
  const text     = document.getElementById("staffCommentText").value.trim();
  const internal = document.getElementById("staffCommentInternal")?.checked;
  const id       = window._staffModalComplaintId;
  if (!text) return;
  try {
    await apiRequest(`${API.complaints}${id}/comments`, {
      method: "POST",
      body: JSON.stringify({ comment_text: text, is_internal: !!internal }),
    });
    showToast("Comment posted");
    document.getElementById("staffCommentText").value = "";
    const comments = await apiRequest(`${API.complaints}${id}/comments`) || [];
    renderComments("staffComments", comments);
  } catch (e) { showToast(e.message, "error"); }
}

/* ── WebSocket ───────────────────────────────────────────────── */
function initWebSocket(userType, userId) {
  try {
    const ws = new WebSocket(`ws://127.0.0.1:8000/ws/${userType}/${userId}`);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "notification") {
          showToast(`🔔 ${data.message}`, "info");
          loadNotifCount();
        }
      } catch {}
    };
    ws.onclose = () => setTimeout(() => initWebSocket(userType, userId), 5000);
  } catch {}
}

/* ── Router ──────────────────────────────────────────────────── */
const page = window.location.pathname;

if (page.includes("student-dashboard")) {
  document.addEventListener("DOMContentLoaded", initStudentDashboard);
} else if (page.includes("admin-dashboard")) {
  document.addEventListener("DOMContentLoaded", initAdminDashboard);
} else if (page.includes("staff-dashboard")) {
  document.addEventListener("DOMContentLoaded", initStaffDashboard);
}

/* ── Login page helpers ─────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {

  /* ---------- SESSION GUARD ON LOGIN PAGES ---------- */
  // Prevents old tokens from wrong portals causing redirect confusion
  (function sessionGuard() {
    const p   = window.location.pathname;
    const tok = getToken();
    const usr = getUser();
    if (!p.includes("login")) return;
    if (!tok || !usr) return;

    // Same portal already logged in — redirect to dashboard
    if (p.includes("student-login") && usr.type === "student") {
      window.location.href = "student-dashboard.html"; return;
    }
    if (p.includes("staff-login") && usr.type === "staff") {
      window.location.href = "staff-dashboard.html"; return;
    }
    if (p.includes("admin-login") && (usr.type === "admin" || usr.type === "super_admin")) {
      window.location.href = "admin-dashboard.html"; return;
    }

    // Wrong portal token — clear it so login page works clean
    sessionStorage.removeItem("grievease_token");
    sessionStorage.removeItem("grievease_user");
    localStorage.removeItem("grievease_token");
    localStorage.removeItem("grievease_user");
  })();

  /* ---------- STUDENT LOGIN ---------- */
  const sForm = document.getElementById("studentLoginForm");
  if (sForm) {
    sForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name  = (document.getElementById("studentName")?.value  || "").trim();
      const email = (document.getElementById("studentEmail")?.value || "").trim();
      const admn  = (document.getElementById("studentAdmission")?.value || "").trim();
      const errEl = document.getElementById("studentLoginError");
      const btn   = document.getElementById("studentLoginBtn");
      if (errEl) errEl.style.display = "none";
      if (!name || !email || !admn) {
        if (errEl) { errEl.textContent = "❌ Please fill in all three fields."; errEl.style.display = "block"; }
        return;
      }
      if (btn) { btn.disabled = true; btn.textContent = "Logging in…"; }
      try {
        const res = await fetch("http://127.0.0.1:8000/api/users/student/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, admission_number: admn }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(typeof err.detail === "string" ? err.detail : "Login failed");
        }
        const data = await res.json();
        const me = await fetch("http://127.0.0.1:8000/api/users/me", {
          headers: { "Authorization": "Bearer " + data.access_token }
        }).then(r => r.json()).catch(() => ({}));
        const user = { id: me.id, type: "student", name: me.name || name, email: me.email || email, admission_number: me.admission_number || admn };
        sessionStorage.setItem("grievease_token", data.access_token);
        sessionStorage.setItem("grievease_user", JSON.stringify(user));
        localStorage.setItem("grievease_token", data.access_token);
        localStorage.setItem("grievease_user", JSON.stringify(user));
        window.location.href = "student-dashboard.html";
      } catch (err) {
        const msg = err.message.includes("fetch") ? "❌ Cannot connect to server. Is it running on port 8000?" : "❌ " + err.message;
        if (errEl) { errEl.textContent = msg; errEl.style.display = "block"; }
        else alert(msg);
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "Login to Student Portal"; }
      }
    });
  }

  /* ---------- ADMIN LOGIN ---------- */
  const aForm = document.getElementById("adminLoginForm");
  if (aForm) {
    aForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = (document.getElementById("adminUsername")?.value || "").trim();
      const password =  document.getElementById("adminPassword")?.value || "";
      const errEl    = document.getElementById("adminLoginError");
      const btn      = document.getElementById("adminLoginBtn");
      if (errEl) errEl.style.display = "none";
      if (!username || !password) {
        if (errEl) { errEl.textContent = "❌ Enter username and password."; errEl.style.display = "block"; }
        return;
      }
      if (btn) { btn.disabled = true; btn.textContent = "Logging in…"; }
      try {
        const res = await fetch("http://127.0.0.1:8000/api/users/admin/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });
        if (!res.ok) throw new Error("Invalid username or password");
        const data = await res.json();
        const user = { type: data.user_role || "admin", name: username };
        sessionStorage.setItem("grievease_token", data.access_token);
        sessionStorage.setItem("grievease_user", JSON.stringify(user));
        localStorage.setItem("grievease_token", data.access_token);
        localStorage.setItem("grievease_user", JSON.stringify(user));
        window.location.href = "admin-dashboard.html";
      } catch (err) {
        const msg = err.message.includes("fetch") ? "❌ Cannot connect to server. Is it running on port 8000?" : "❌ " + err.message;
        if (errEl) { errEl.textContent = msg; errEl.style.display = "block"; }
        else alert(msg);
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "Login to Admin Panel"; }
      }
    });
  }

  /* ---------- STAFF LOGIN ---------- */
  const sfForm = document.getElementById("staffLoginForm");
  if (sfForm) {
    sfForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email    = (document.getElementById("staffEmail")?.value    || "").trim();
      const password =  document.getElementById("staffPassword")?.value || "";
      const errEl    = document.getElementById("staffLoginError");
      const btn      = document.getElementById("staffLoginBtn");
      if (errEl) errEl.style.display = "none";
      if (!email || !password) {
        if (errEl) { errEl.textContent = "❌ Enter email and password."; errEl.style.display = "block"; }
        return;
      }
      if (btn) { btn.disabled = true; btn.textContent = "Logging in…"; }
      try {
        const res = await fetch("http://127.0.0.1:8000/api/users/staff/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) throw new Error("Invalid email or password");
        const data = await res.json();
        const me = await fetch("http://127.0.0.1:8000/api/users/me", {
          headers: { "Authorization": "Bearer " + data.access_token }
        }).then(r => r.json()).catch(() => ({}));
        const user = { ...me, type: "staff" };
        sessionStorage.setItem("grievease_token", data.access_token);
        sessionStorage.setItem("grievease_user", JSON.stringify(user));
        localStorage.setItem("grievease_token", data.access_token);
        localStorage.setItem("grievease_user", JSON.stringify(user));
        window.location.href = "staff-dashboard.html";
      } catch (err) {
        const msg = err.message.includes("fetch") ? "❌ Cannot connect to server. Is it running on port 8000?" : "❌ " + err.message;
        if (errEl) { errEl.textContent = msg; errEl.style.display = "block"; }
        else alert(msg);
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "Login to Staff Portal"; }
      }
    });
  }

  /* ---------- GUEST ACCESS ---------- */
  document.getElementById("guestAccess")?.addEventListener("click", async () => {
    const errEl = document.getElementById("studentLoginError");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/users/student/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Guest User", email: "guest@demo.com", admission_number: "GUEST2024" }),
      });
      if (!res.ok) throw new Error("Guest login failed");
      const data = await res.json();
      const user = { type: "student", name: "Guest User", email: "guest@demo.com", admission_number: "GUEST2024" };
      sessionStorage.setItem("grievease_token", data.access_token);
      sessionStorage.setItem("grievease_user", JSON.stringify(user));
      localStorage.setItem("grievease_token", data.access_token);
      localStorage.setItem("grievease_user", JSON.stringify(user));
      window.location.href = "student-dashboard.html";
    } catch (err) {
      if (errEl) { errEl.textContent = "❌ Guest login failed. Check server."; errEl.style.display = "block"; }
    }
  });

  /* ---------- LANDING PAGE STATS ---------- */
  const landingTotal    = document.getElementById("landingTotal");
  const landingResolved = document.getElementById("landingResolved");
  if (landingTotal || landingResolved) {
    fetch("http://127.0.0.1:8000/api/complaints/stats")
      .then(r => r.json())
      .then(d => {
        if (landingTotal)    landingTotal.textContent    = d.total    || 0;
        if (landingResolved) landingResolved.textContent = d.resolved || 0;
      }).catch(() => {
        if (landingTotal)    landingTotal.textContent    = "—";
        if (landingResolved) landingResolved.textContent = "—";
      });
  }

  /* ---------- CHATBOT + DARK MODE INIT ---------- */
  if (typeof initChatbot   === "function") initChatbot();
  if (typeof initDarkMode  === "function") initDarkMode();

});
/* ══════════════════════════════════════════════════════════════
   CHATBOT WIDGET — AI Assistant
   Predict category → Suggest solution → Offer to submit complaint
══════════════════════════════════════════════════════════════ */

function initChatbot() {
  const root = document.getElementById("chatbot-root");
  if (!root) return;

  root.innerHTML = `
    <div class="chatbot-widget" id="chatbotWidget">
      <div class="chatbot-header">
        <h4>🤖 GrievEase AI Assistant</h4>
        <button class="chatbot-toggle" onclick="toggleChatbot()">—</button>
      </div>
      <div class="chatbot-body">
        <div class="chatbot-log" id="chatbotLog">
          <div class="chatbot-message bot">Hi! Describe your issue and I'll predict its category, priority, and help you submit a complaint.</div>
        </div>
        <div class="chatbot-input">
          <input type="text" id="chatbotInput" placeholder="Describe your issue…" onkeydown="if(event.key==='Enter') chatbotSend()"/>
          <button onclick="chatbotSend()">Send</button>
        </div>
      </div>
    </div>`;
}

function toggleChatbot() {
  const w = document.getElementById("chatbotWidget");
  if (!w) return;
  w.classList.toggle("collapsed");
  const btn = w.querySelector(".chatbot-toggle");
  btn.textContent = w.classList.contains("collapsed") ? "💬" : "—";
}

function chatbotAppend(text, role) {
  const log = document.getElementById("chatbotLog");
  if (!log) return;
  const div = document.createElement("div");
  div.className = `chatbot-message ${role}`;
  div.innerHTML = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

let _chatbotLastPrediction = null;

async function chatbotSend() {
  const input = document.getElementById("chatbotInput");
  if (!input || !input.value.trim()) return;
  const text = input.value.trim();
  input.value = "";
  chatbotAppend(text, "user");

  // Check if user is trying to submit
  if (_chatbotLastPrediction && /yes|submit|file|okay|ok|haan|ha$/i.test(text)) {
    const user = getUser();
    if (!user || user.type !== "student") {
      chatbotAppend("Please <a href='student-login.html'>login as student</a> to submit a complaint.", "bot");
      return;
    }
    try {
      const result = await apiRequest(API.complaintsJson, {
        method: "POST",
        body: JSON.stringify({
          student_name: user.name,
          student_email: user.email,
          admission_number: user.admission_number,
          title: _chatbotLastPrediction.title,
          description: _chatbotLastPrediction.text,
          category: _chatbotLastPrediction.category,
          priority: _chatbotLastPrediction.priority,
        }),
      });
      if (result) {
        chatbotAppend(`✅ Complaint submitted! ID: <strong>${result.complaint_id}</strong><br>Category: ${result.category} | Priority: ${result.priority}`, "bot");
        _chatbotLastPrediction = null;
        if (typeof loadStudentComplaints === "function") loadStudentComplaints();
      }
    } catch (e) {
      chatbotAppend(`❌ Could not submit: ${e.message}`, "bot");
    }
    return;
  }

  if (text.length < 5) { chatbotAppend("Please describe your issue in more detail.", "bot"); return; }

  try {
    const token = getToken();
    if (!token) { chatbotAppend("Please <a href='student-login.html'>login</a> to use the AI assistant.", "bot"); return; }
    const data = await apiRequest(`${API.predict}?text=${encodeURIComponent(text)}`);
    if (!data) return;

    const solutions = {
      "Academic":       "Contact your faculty or academic coordinator. Bring your student ID and course registration slip.",
      "Administration": "Visit the admin office during working hours (9 AM–4 PM). Carry all original documents.",
      "Examination":    "Contact the examination cell directly. Bring your enrollment number and hall ticket.",
      "Fees":           "Visit the accounts department with your payment receipt/screenshot.",
      "Hostel":         "Contact the hostel warden directly. For urgent issues, contact the Dean of Student Affairs.",
      "IT Support":     "Try clearing browser cache and cookies first. Then raise ticket with IT helpdesk.",
      "Infrastructure": "Report to the maintenance department. Mark as urgent if it's a safety issue.",
      "Library":        "Speak with the librarian directly. Bring your library card and complaint in writing.",
      "Security":       "Contact security office immediately. For ragging, contact anti-ragging committee directly.",
      "Transport":      "Contact transport department. Keep your bus pass and route number ready.",
    };

    const suggestion = solutions[data.predicted_category] || "Contact the relevant department with proper documentation.";
    _chatbotLastPrediction = { text, title: text.substring(0, 80), category: data.predicted_category, priority: data.predicted_priority };

    chatbotAppend(`
      <strong>🔍 Analysis:</strong><br>
      Category: <strong>${data.predicted_category}</strong> | Priority: <strong>${data.predicted_priority}</strong><br>
      Confidence: ${Math.round((data.confidence || 0.9) * 100)}%<br><br>
      <strong>💡 Suggestion:</strong> ${suggestion}<br><br>
      <em>Type <strong>"yes"</strong> to auto-submit this as a complaint.</em>
    `, "bot");
  } catch (e) {
    chatbotAppend("Sorry, AI assistant is unavailable right now. Please submit complaint directly.", "bot");
  }
}

/* ── Dark Mode ─────────────────────────────────────────────── */
function initDarkMode() {
  const savedTheme = localStorage.getItem("grievease_theme") || "light";
  if (savedTheme === "dark") document.body.classList.add("dark-mode");

  // Add toggle button if a toggle element exists
  const toggleEl = document.getElementById("darkModeToggle");
  if (toggleEl) {
    toggleEl.textContent = savedTheme === "dark" ? "☀️" : "🌙";
    toggleEl.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      const isDark = document.body.classList.contains("dark-mode");
      localStorage.setItem("grievease_theme", isDark ? "dark" : "light");
      toggleEl.textContent = isDark ? "☀️" : "🌙";
    });
  }
}

/* ── Guest Login ───────────────────────────────────────────── */

/* ── Print complaint (admin) ───────────────────────────────── */
function printComplaint(complaintId) {
  const modal = document.getElementById("adminComplaintModal") || document.getElementById("staffUpdateModal");
  if (!modal) return;
  const content = modal.querySelector(".modal-body")?.innerHTML || "";
  const win = window.open("", "_blank");
  win.document.write(`<!DOCTYPE html><html><head><title>Complaint ${complaintId}</title>
    <style>body{font-family:Arial,sans-serif;padding:20px;font-size:13px}
    .detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px}
    .detail-label{font-weight:700;font-size:11px;text-transform:uppercase;color:#666}
    .timeline-item{border-left:3px solid #2563eb;padding:6px 12px;margin:6px 0;font-size:12px}
    .badge{padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700}
    .hidden,.modal-actions,.comment-form,.update-form,.rating-section{display:none!important}
    h4{margin:12px 0 6px}
    </style></head><body>
    <h2>GrievEase — Complaint ${complaintId}</h2>
    <p style="color:#666;font-size:11px">Printed on ${new Date().toLocaleString()}</p>
    ${content}
    </body></html>`);
  win.document.close();
  win.print();
}
