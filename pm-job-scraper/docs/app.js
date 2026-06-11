"use strict";

// The workflow copies data/*.json next to this file before publishing.
const JOBS_URL = "./jobs.json";
const COMPANIES_URL = "./companies.json";
const RUNS_URL = "./runs.json";

const HQ_LABELS = { israel: "ישראל", multinational: "רב-לאומית" };
const ATS_LABELS = {
  greenhouse: "Greenhouse", lever: "Lever", comeet: "Comeet", ashby: "Ashby",
  workday: "Workday", smartrecruiters: "SmartRecruiters", workable: "Workable",
  recruitee: "Recruitee", unknown: "טרם נתמך",
};
const STATUS_LABELS = { ok: "תקין", partial: "חלקי" };

let allJobs = [];
let allCompanies = [];
let currentTrack = "hightech";  // toggled by the track switch
let jobsGeneratedAt = null;

const track = (x) => x.track || "hightech";

/* ===================== tabs + track switch ===================== */

function initTabs() {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const view = btn.dataset.view;
      for (const v of ["jobs", "companies", "runs"]) {
        document.getElementById("view-" + v).hidden = v !== view;
      }
      // the track switch only applies to jobs/companies, not runs
      document.getElementById("track-switch").style.display = view === "runs" ? "none" : "";
    });
  });
}

function initTrackSwitch() {
  document.querySelectorAll(".track-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentTrack = btn.dataset.track;
      document.querySelectorAll(".track-btn").forEach((b) => b.classList.toggle("active", b === btn));
      rebuildCompanyFilter();
      rebuildCategoryFilter();
      renderJobs();
      renderCompanies();
    });
  });
}

/* ============================ jobs ============================ */

async function loadJobs() {
  try {
    const data = await fetchJson(JOBS_URL);
    allJobs = data.jobs || [];
    jobsGeneratedAt = data.generated_at;
    setText("stat-updated", formatDate(jobsGeneratedAt));
    rebuildCompanyFilter();
    renderJobs();
  } catch (err) {
    showError("empty", "לא ניתן לטעון את המשרות (" + err.message + ").");
  }
}

function rebuildCompanyFilter() {
  const sel = document.getElementById("company-filter");
  const cur = sel.value;
  sel.innerHTML = '<option value="">כל החברות</option>';
  const names = [...new Set(allJobs.filter((j) => track(j) === currentTrack).map((j) => j.company))].sort();
  names.forEach((c) => sel.appendChild(option(c, c)));
  sel.value = names.includes(cur) ? cur : "";
}

function renderJobs() {
  const trackJobs = allJobs.filter((j) => track(j) === currentTrack);
  setText("stat-total", trackJobs.length);
  setText("stat-new", trackJobs.filter((j) => j.is_new).length);
  setText("stat-companies", new Set(trackJobs.map((j) => j.company)).size);

  const q = val("search").toLowerCase();
  const company = val("company-filter");
  const onlyNew = document.getElementById("only-new").checked;
  const rows = document.getElementById("rows");
  rows.innerHTML = "";

  const filtered = trackJobs
    .filter((j) => {
      if (onlyNew && !j.is_new) return false;
      if (company && j.company !== company) return false;
      if (q) {
        const hay = (j.title + " " + j.company + " " + j.location).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    })
    .sort((a, b) => (b.is_new - a.is_new) || a.company.localeCompare(b.company));

  for (const j of filtered) {
    const tr = document.createElement("tr");
    if (j.is_new) tr.className = "new";
    tr.appendChild(cell(j.is_new ? '<span class="badge">חדש</span>' : ""));
    tr.appendChild(cell(escapeHtml(j.company), "company", "חברה"));
    tr.appendChild(cell(escapeHtml(j.title), "", "תפקיד"));
    tr.appendChild(cell(escapeHtml(j.location || "—"), "", "מיקום"));
    tr.appendChild(cell(j.posted_at || "—", "", "פורסם"));
    tr.appendChild(cell(j.url
      ? `<a class="apply" href="${encodeURI(j.url)}" target="_blank" rel="noopener">לצפייה ←</a>` : ""));
    rows.appendChild(tr);
  }
  document.getElementById("empty").hidden = filtered.length > 0;
}

/* ========================== companies ========================== */

async function loadCompanies() {
  try {
    const data = await fetchJson(COMPANIES_URL);
    allCompanies = data.companies || [];
    rebuildCategoryFilter();
    renderCompanies();
  } catch (err) {
    showError("c-empty", "לא ניתן לטעון את רשימת החברות (" + err.message + ").");
  }
}

function rebuildCategoryFilter() {
  const sel = document.getElementById("c-cat-filter");
  const cur = sel.value;
  sel.innerHTML = '<option value="">כל התחומים</option>';
  const cats = [...new Set(allCompanies.filter((c) => track(c) === currentTrack)
    .map((c) => c.category).filter(Boolean))].sort();
  cats.forEach((cat) => sel.appendChild(option(cat, cat)));
  sel.value = cats.includes(cur) ? cur : "";
}

function renderCompanies() {
  const trackCos = allCompanies.filter((c) => track(c) === currentTrack);
  setText("c-stat-total", trackCos.length);
  setText("c-stat-scanned", trackCos.filter((c) => c.ats && c.ats !== "unknown").length);
  setText("c-stat-jobs", trackCos.reduce((s, c) => s + (c.jobs_count || 0), 0));

  const q = val("c-search").toLowerCase();
  const cat = val("c-cat-filter");
  const ats = val("c-ats-filter");
  const onlyHiring = document.getElementById("c-only-hiring").checked;
  const rows = document.getElementById("c-rows");
  rows.innerHTML = "";

  const filtered = trackCos
    .filter((c) => {
      if (onlyHiring && !(c.jobs_count > 0)) return false;
      if (cat && c.category !== cat) return false;
      if (ats && (c.ats || "unknown") !== ats) return false;
      if (q) {
        const hay = (c.name + " " + (c.description || "") + " " + (c.category || "")).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    })
    .sort((a, b) => (b.jobs_count || 0) - (a.jobs_count || 0) || a.name.localeCompare(b.name));

  for (const c of filtered) {
    const tr = document.createElement("tr");
    const nameCell = c.careers_url
      ? `<a class="apply" href="${encodeURI(c.careers_url)}" target="_blank" rel="noopener">${escapeHtml(c.name)}</a>`
      : escapeHtml(c.name);
    tr.appendChild(cell(
      `<div class="company">${nameCell}</div>` +
      (c.description ? `<div class="desc">${escapeHtml(c.description)}</div>` : ""),
      "", "חברה"));
    tr.appendChild(cell(escapeHtml(c.category || "—"), "", "תחום"));
    tr.appendChild(cell(HQ_LABELS[c.hq] || escapeHtml(c.hq || "—"), "", "מטה"));
    const atsKey = c.ats || "unknown";
    const atsCls = c.error ? "err" : atsKey;
    const atsTxt = c.error ? "שגיאת סריקה" : (ATS_LABELS[atsKey] || atsKey);
    tr.appendChild(cell(`<span class="pill ${atsCls}">${escapeHtml(atsTxt)}</span>`, "", "פלטפורמה"));
    const n = c.jobs_count || 0;
    tr.appendChild(cell(`<span class="count-chip${n ? "" : " zero"}">${n}</span>`, "", "משרות"));
    tr.appendChild(cell(c.careers_url
      ? `<a class="apply" href="${encodeURI(c.careers_url)}" target="_blank" rel="noopener">קריירה ←</a>` : ""));
    rows.appendChild(tr);
  }
  document.getElementById("c-empty").hidden = filtered.length > 0;
}

/* ============================ runs ============================ */

async function loadRuns() {
  try {
    const data = await fetchJson(RUNS_URL);
    const runs = data.runs || [];
    const last = runs[0];
    setText("r-stat-last", last ? formatDate(last.finished_at) : "–");
    setText("r-stat-status", last ? (STATUS_LABELS[last.status] || last.status) : "–");
    setText("r-stat-count", runs.length);

    const rows = document.getElementById("r-rows");
    rows.innerHTML = "";
    for (const r of runs) {
      const tr = document.createElement("tr");
      const statusTxt = STATUS_LABELS[r.status] || r.status;
      tr.appendChild(cell(formatDate(r.finished_at), "", "מתי"));
      tr.appendChild(cell(`<span class="pill ${r.status === "ok" ? "ok" : "partial"}">${statusTxt}</span>`, "", "סטטוס"));
      tr.appendChild(cell(String(r.jobs ?? "—"), "", "משרות"));
      tr.appendChild(cell(String(r.new ?? 0), "", "חדשות"));
      tr.appendChild(cell(`${r.scanned ?? "—"}/${r.companies ?? "—"}`, "", "נסרקו"));
      const errHtml = (r.errors
        ? `<span style="color:var(--err)">${r.errors}</span>` +
          (r.error_companies && r.error_companies.length
            ? `<div class="errlist">${escapeHtml(r.error_companies.join(", "))}</div>` : "")
        : "0");
      tr.appendChild(cell(errHtml, "", "שגיאות"));
      rows.appendChild(tr);
    }
    document.getElementById("r-empty").hidden = runs.length > 0;
  } catch (err) {
    showError("r-empty", "אין עדיין היסטוריית ריצות (" + err.message + ").");
  }
}

/* ============================ helpers ============================ */

async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

function cell(html, cls, label) {
  const td = document.createElement("td");
  td.innerHTML = html;
  if (cls) td.className = cls;
  if (label) td.dataset.label = label;
  return td;
}

function option(value, text) {
  const opt = document.createElement("option");
  opt.value = value; opt.textContent = text;
  return opt;
}

function val(id) { return document.getElementById(id).value.trim(); }
function setText(id, v) { document.getElementById(id).textContent = v; }

function showError(emptyId, msg) {
  const el = document.getElementById(emptyId);
  el.hidden = false; el.textContent = msg;
}

function formatDate(iso) {
  if (!iso) return "–";
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleString("he-IL", { dateStyle: "short", timeStyle: "short" });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

["search", "company-filter", "only-new"].forEach((id) =>
  document.getElementById(id).addEventListener("input", renderJobs));
["c-search", "c-cat-filter", "c-ats-filter", "c-only-hiring"].forEach((id) =>
  document.getElementById(id).addEventListener("input", renderCompanies));

initTabs();
initTrackSwitch();
loadJobs();
loadCompanies();
loadRuns();
