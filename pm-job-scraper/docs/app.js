"use strict";

// The workflow copies data/*.json next to this file before publishing.
const JOBS_URL = "./jobs.json";
const COMPANIES_URL = "./companies.json";

const HQ_LABELS = { israel: "ישראל", multinational: "רב-לאומית" };
const ATS_LABELS = {
  greenhouse: "Greenhouse",
  lever: "Lever",
  comeet: "Comeet",
  unknown: "טרם נתמך",
};

let allJobs = [];
let allCompanies = [];

/* ============================ tabs ============================ */

function initTabs() {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const view = btn.dataset.view;
      document.getElementById("view-jobs").hidden = view !== "jobs";
      document.getElementById("view-companies").hidden = view !== "companies";
    });
  });
}

/* ============================ jobs ============================ */

async function loadJobs() {
  try {
    const res = await fetch(JOBS_URL, { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    allJobs = data.jobs || [];
    renderJobStats(data);
    populateCompanyFilter(allJobs);
    renderJobs();
  } catch (err) {
    showError("empty", "לא ניתן לטעון את המשרות (" + err.message + ").");
  }
}

function renderJobStats(data) {
  const companies = new Set(allJobs.map((j) => j.company));
  setText("stat-total", data.count ?? allJobs.length);
  setText("stat-new", data.new_count ?? allJobs.filter((j) => j.is_new).length);
  setText("stat-companies", companies.size);
  setText("stat-updated", formatDate(data.generated_at));
}

function populateCompanyFilter(jobs) {
  const sel = document.getElementById("company-filter");
  [...new Set(jobs.map((j) => j.company))].sort().forEach((c) => {
    sel.appendChild(option(c, c));
  });
}

function renderJobs() {
  const q = val("search").toLowerCase();
  const company = val("company-filter");
  const onlyNew = document.getElementById("only-new").checked;

  const rows = document.getElementById("rows");
  rows.innerHTML = "";

  const filtered = allJobs
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
    tr.appendChild(cell(escapeHtml(j.company), "company"));
    tr.appendChild(cell(escapeHtml(j.title)));
    tr.appendChild(cell(escapeHtml(j.location || "—")));
    tr.appendChild(cell(j.posted_at || "—"));
    tr.appendChild(
      cell(
        j.url
          ? `<a class="apply" href="${encodeURI(j.url)}" target="_blank" rel="noopener">לצפייה ←</a>`
          : ""
      )
    );
    rows.appendChild(tr);
  }
  document.getElementById("empty").hidden = filtered.length > 0;
}

/* ========================== companies ========================== */

async function loadCompanies() {
  try {
    const res = await fetch(COMPANIES_URL, { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    allCompanies = data.companies || [];
    renderCompanyStats(data);
    populateCategoryFilter(allCompanies);
    renderCompanies();
  } catch (err) {
    showError("c-empty", "לא ניתן לטעון את רשימת החברות (" + err.message + ").");
  }
}

function renderCompanyStats(data) {
  const jobs = allCompanies.reduce((s, c) => s + (c.jobs_count || 0), 0);
  setText("c-stat-total", data.count ?? allCompanies.length);
  setText(
    "c-stat-scanned",
    data.scanned_count ?? allCompanies.filter((c) => c.ats && c.ats !== "unknown").length
  );
  setText("c-stat-jobs", jobs);
}

function populateCategoryFilter(companies) {
  const sel = document.getElementById("c-cat-filter");
  [...new Set(companies.map((c) => c.category).filter(Boolean))]
    .sort()
    .forEach((cat) => sel.appendChild(option(cat, cat)));
}

function renderCompanies() {
  const q = val("c-search").toLowerCase();
  const cat = val("c-cat-filter");
  const ats = val("c-ats-filter");
  const onlyHiring = document.getElementById("c-only-hiring").checked;

  const rows = document.getElementById("c-rows");
  rows.innerHTML = "";

  const filtered = allCompanies
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
    // Companies with open jobs first, then alphabetically.
    .sort((a, b) => (b.jobs_count || 0) - (a.jobs_count || 0) || a.name.localeCompare(b.name));

  for (const c of filtered) {
    const tr = document.createElement("tr");

    const nameCell = c.careers_url
      ? `<a class="apply" href="${encodeURI(c.careers_url)}" target="_blank" rel="noopener">${escapeHtml(c.name)}</a>`
      : escapeHtml(c.name);
    tr.appendChild(
      cell(
        `<div class="company">${nameCell}</div>` +
          (c.description ? `<div class="desc">${escapeHtml(c.description)}</div>` : ""),
      )
    );
    tr.appendChild(cell(escapeHtml(c.category || "—")));
    tr.appendChild(cell(HQ_LABELS[c.hq] || escapeHtml(c.hq || "—")));

    const atsKey = c.ats || "unknown";
    const atsCls = c.error ? "err" : atsKey;
    const atsTxt = c.error ? "שגיאת סריקה" : (ATS_LABELS[atsKey] || atsKey);
    tr.appendChild(cell(`<span class="pill ${atsCls}">${escapeHtml(atsTxt)}</span>`));

    const n = c.jobs_count || 0;
    tr.appendChild(cell(`<span class="count-chip${n ? "" : " zero"}">${n}</span>`));

    tr.appendChild(
      cell(
        c.careers_url
          ? `<a class="apply" href="${encodeURI(c.careers_url)}" target="_blank" rel="noopener">קריירה ←</a>`
          : ""
      )
    );
    rows.appendChild(tr);
  }
  document.getElementById("c-empty").hidden = filtered.length > 0;
}

/* ============================ helpers ============================ */

function cell(html, cls) {
  const td = document.createElement("td");
  td.innerHTML = html;
  if (cls) td.className = cls;
  return td;
}

function option(value, text) {
  const opt = document.createElement("option");
  opt.value = value;
  opt.textContent = text;
  return opt;
}

function val(id) {
  return document.getElementById(id).value.trim();
}

function setText(id, v) {
  document.getElementById(id).textContent = v;
}

function showError(emptyId, msg) {
  const el = document.getElementById(emptyId);
  el.hidden = false;
  el.textContent = msg;
}

function formatDate(iso) {
  if (!iso) return "–";
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleString("he-IL", { dateStyle: "short", timeStyle: "short" });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

["search", "company-filter", "only-new"].forEach((id) =>
  document.getElementById(id).addEventListener("input", renderJobs)
);
["c-search", "c-cat-filter", "c-ats-filter", "c-only-hiring"].forEach((id) =>
  document.getElementById(id).addEventListener("input", renderCompanies)
);

initTabs();
loadJobs();
loadCompanies();
