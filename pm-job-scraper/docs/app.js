"use strict";

// The workflow copies data/jobs.json next to this file before publishing.
const DATA_URL = "./jobs.json";

let allJobs = [];

async function load() {
  try {
    const res = await fetch(DATA_URL, { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    allJobs = data.jobs || [];
    renderStats(data);
    populateCompanies(allJobs);
    render();
  } catch (err) {
    document.getElementById("empty").hidden = false;
    document.getElementById("empty").textContent =
      "לא ניתן לטעון את הנתונים (" + err.message + ").";
  }
}

function renderStats(data) {
  const companies = new Set(allJobs.map((j) => j.company));
  setText("stat-total", data.count ?? allJobs.length);
  setText("stat-new", data.new_count ?? allJobs.filter((j) => j.is_new).length);
  setText("stat-companies", companies.size);
  setText("stat-updated", formatDate(data.generated_at));
}

function populateCompanies(jobs) {
  const sel = document.getElementById("company-filter");
  [...new Set(jobs.map((j) => j.company))].sort().forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    sel.appendChild(opt);
  });
}

function render() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const company = document.getElementById("company-filter").value;
  const onlyNew = document.getElementById("only-new").checked;

  const rows = document.getElementById("rows");
  rows.innerHTML = "";

  const filtered = allJobs.filter((j) => {
    if (onlyNew && !j.is_new) return false;
    if (company && j.company !== company) return false;
    if (q) {
      const hay = (j.title + " " + j.company + " " + j.location).toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  // New jobs first, then alphabetical by company.
  filtered.sort((a, b) =>
    (b.is_new - a.is_new) || a.company.localeCompare(b.company)
  );

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

function cell(html, cls) {
  const td = document.createElement("td");
  td.innerHTML = html;
  if (cls) td.className = cls;
  return td;
}

function setText(id, val) {
  document.getElementById(id).textContent = val;
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
  document.getElementById(id).addEventListener("input", render)
);

load();
