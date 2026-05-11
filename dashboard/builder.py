"""
Dashboard Builder
Генерирует standalone HTML-дашборд из JSON-отчёта.
Без внешних CDN. Графики на Canvas. Дизайн: data terminal.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DASHBOARD_DIR


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CmtisEdu · Аналитика</title>
<style>
/* ═══════════════════════════════════════════════════════════════
   CMTIS EDU ANALYTICS TERMINAL
   Data-dense serious interface. No gradients, no rounded toys.
   ═══════════════════════════════════════════════════════════════ */

:root {
  /* Monochrome base */
  --ink-0: #0A0A0B;
  --ink-1: #1A1A1D;
  --ink-2: #252529;
  --ink-3: #3A3A40;
  --ink-4: #5A5A62;
  --ink-5: #8A8A92;
  --ink-6: #B8B8BF;
  --ink-7: #E4E4E7;
  --ink-8: #F4F4F5;
  --ink-9: #FCFCFD;

  /* Accents - sharp and deliberate */
  --acc-primary: #E63946;     /* signal red - alerts, at-risk */
  --acc-success: #0F9960;     /* green - healthy metrics */
  --acc-warn: #D9822B;        /* amber - warnings */
  --acc-info: #1F6FEB;        /* cobalt blue - info */
  --acc-accent: #FFD166;      /* yellow highlight */

  /* Semantic */
  --bg: var(--ink-9);
  --bg-panel: #FFFFFF;
  --bg-sidebar: var(--ink-0);
  --border: #E4E4E7;
  --border-strong: #CECED3;
  --text: var(--ink-1);
  --text-muted: var(--ink-4);
  --text-dim: var(--ink-5);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body {
  background: var(--bg);
  color: var(--text);
  font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  font-feature-settings: 'tnum' on, 'lnum' on, 'ss01' on;
}

body {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
}

/* Import fonts */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Serif:wght@400;500;600&display=swap');

/* ─── SIDEBAR ─── */
.sidebar {
  background: var(--bg-sidebar);
  color: var(--ink-7);
  padding: 24px 0;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  border-right: 1px solid var(--ink-2);
}

.brand {
  padding: 0 24px 24px;
  border-bottom: 1px solid var(--ink-2);
  margin-bottom: 12px;
}
.brand .mark {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.15em;
  color: var(--ink-5);
  text-transform: uppercase;
}
.brand .name {
  font-family: 'IBM Plex Serif', serif;
  font-size: 22px;
  font-weight: 500;
  color: var(--ink-9);
  margin-top: 4px;
  letter-spacing: -0.02em;
}
.brand .sub {
  font-size: 11px;
  color: var(--ink-5);
  margin-top: 2px;
}

.nav-section {
  padding: 16px 0 8px;
}
.nav-label {
  padding: 0 24px 8px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  color: var(--ink-4);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.nav-item {
  display: flex;
  align-items: center;
  padding: 9px 24px;
  color: var(--ink-6);
  cursor: pointer;
  border-left: 2px solid transparent;
  font-size: 13px;
  transition: all 0.12s ease;
  user-select: none;
}
.nav-item:hover { background: var(--ink-1); color: var(--ink-9); }
.nav-item.active {
  background: var(--ink-1);
  color: var(--ink-9);
  border-left-color: var(--acc-accent);
  font-weight: 500;
}
.nav-item .icon {
  width: 18px;
  font-size: 11px;
  margin-right: 10px;
  opacity: 0.6;
  font-family: 'IBM Plex Mono', monospace;
}
.nav-item.active .icon { opacity: 1; color: var(--acc-accent); }

.sidebar-footer {
  margin-top: 32px;
  padding: 16px 24px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: var(--ink-4);
  border-top: 1px solid var(--ink-2);
}
.sidebar-footer .dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--acc-success);
  margin-right: 6px;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ─── MAIN CONTENT ─── */
.main {
  min-width: 0;
  padding: 0;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 32px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}
.topbar .page-title {
  font-family: 'IBM Plex Serif', serif;
  font-size: 22px;
  font-weight: 500;
  letter-spacing: -0.02em;
}
.topbar .meta {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  gap: 16px;
  align-items: center;
}
.topbar .meta .period {
  padding: 4px 10px;
  border: 1px solid var(--border-strong);
  background: var(--ink-8);
}

.content {
  padding: 24px 32px 80px;
}

.view { display: none; animation: slideIn 0.25s ease; }
.view.active { display: block; }
@keyframes slideIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ─── SECTION HEADER ─── */
.section {
  margin-bottom: 36px;
}
.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.section-head h2 {
  font-family: 'IBM Plex Serif', serif;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: -0.01em;
}
.section-head .caption {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* ─── KPI ROW ─── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border: 1px solid var(--border);
  background: var(--bg-panel);
  margin-bottom: 28px;
}
.kpi {
  padding: 20px 24px;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  position: relative;
}
.kpi:nth-child(4n) { border-right: none; }
.kpi:nth-last-child(-n+4) { border-bottom: none; }
.kpi .label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}
.kpi .value {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 32px;
  font-weight: 300;
  letter-spacing: -0.03em;
  color: var(--text);
  line-height: 1;
}
.kpi .value .unit {
  font-size: 14px;
  color: var(--text-dim);
  font-weight: 400;
  margin-left: 2px;
}
.kpi .sub {
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-muted);
}
.kpi .trend {
  position: absolute;
  top: 20px;
  right: 24px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  padding: 2px 6px;
}
.kpi .trend.up { background: #E6F5ED; color: var(--acc-success); }
.kpi .trend.warn { background: #FDF0E1; color: var(--acc-warn); }
.kpi .trend.down { background: #FBE7E9; color: var(--acc-primary); }

/* ─── HERO GRID — большие карточки на главной ─── */
.hero-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 8px;
}
.hero-kpi {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  padding: 22px 22px 20px;
  position: relative;
  border-radius: 2px;
  overflow: hidden;
}
.hero-kpi::before {
  content: '';
  position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: var(--ink-3);
}
.hero-kpi.up::before { background: var(--acc-success); }
.hero-kpi.warn::before { background: var(--acc-warn); }
.hero-icon {
  position: absolute; top: 16px; right: 16px;
  font-size: 24px; opacity: 0.5;
}
.hero-label {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-3);
  margin-bottom: 10px;
}
.hero-value {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 36px;
  font-weight: 600;
  color: var(--ink-1);
  letter-spacing: -0.02em;
  line-height: 1;
  margin-bottom: 10px;
}
.hero-sub {
  font-size: 12px;
  color: var(--ink-2);
  margin-bottom: 2px;
}
.hero-sub2 {
  font-size: 11px;
  color: var(--ink-3);
  font-weight: 500;
}
@media (max-width: 1200px) { .hero-grid { grid-template-columns: repeat(2, 1fr); } }

/* ─── MINI FUNNEL — компактная воронка для главной ─── */
.funnel-mini { padding: 14px 18px; }
.fmini-row {
  display: grid;
  grid-template-columns: 160px 1fr 50px;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
}
.fmini-row:last-child { margin-bottom: 0; }
.fmini-lbl {
  font-size: 12px;
  color: var(--ink-2);
}
.fmini-bar {
  position: relative;
  height: 22px;
  background: var(--bg-base);
  border: 1px solid var(--border);
}
.fmini-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--acc-info), var(--acc-success));
  transition: width 0.3s;
}
.fmini-val {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-1);
}
.fmini-pct {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  color: var(--ink-2);
  text-align: right;
}

/* ─── FUNNEL CONVERSIONS — расширенная воронка с двумя конверсиями ─── */
.fmini-row.with-conv {
  grid-template-columns: 180px 1fr 60px 60px 70px;
  gap: 10px;
}
.fmini-row.with-conv .fmini-pct.step {
  color: var(--acc-info);
}
.fmini-row.with-conv .fmini-pct.drop {
  color: var(--acc-primary);
  font-size: 11px;
}
.fmini-head {
  display: grid;
  grid-template-columns: 180px 1fr 60px 60px 70px;
  gap: 10px;
  padding: 0 18px 8px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-4);
  border-bottom: 1px solid var(--border);
  margin-bottom: 12px;
}
.fmini-head span:nth-child(n+3) { text-align: right; }

/* ─── GAUGE — индикатор общей эффективности ─── */
.gauge-wrap {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 24px;
  align-items: center;
  padding: 20px 18px;
}
@media (max-width: 1100px) {
  .gauge-wrap { grid-template-columns: 1fr; }
}
.gauge {
  position: relative;
  width: 220px;
  height: 130px;
  margin: 0 auto;
}
.gauge-track {
  fill: none;
  stroke: var(--ink-7);
  stroke-width: 18;
  stroke-linecap: round;
}
.gauge-fill {
  fill: none;
  stroke-width: 18;
  stroke-linecap: round;
  transition: stroke-dasharray 0.6s ease;
}
.gauge-fill.high { stroke: var(--acc-success); }
.gauge-fill.medium { stroke: var(--acc-warn); }
.gauge-fill.low { stroke: var(--acc-primary); }
.gauge-value {
  position: absolute;
  bottom: 6px;
  left: 0; right: 0;
  text-align: center;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 36px;
  font-weight: 600;
  color: var(--ink-1);
  letter-spacing: -0.02em;
  line-height: 1;
}
.gauge-label {
  position: absolute;
  bottom: -18px;
  left: 0; right: 0;
  text-align: center;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 500;
}
.gauge-label.high { color: var(--acc-success); }
.gauge-label.medium { color: var(--acc-warn); }
.gauge-label.low { color: var(--acc-primary); }

.eff-components { display: flex; flex-direction: column; gap: 12px; }
.eff-comp-row {
  display: grid;
  grid-template-columns: 130px 1fr 70px;
  gap: 12px;
  align-items: center;
}
.eff-comp-lbl {
  font-size: 12px;
  color: var(--ink-2);
}
.eff-comp-bar {
  position: relative;
  height: 8px;
  background: var(--ink-7);
  border-radius: 1px;
  overflow: hidden;
}
.eff-comp-fill {
  position: absolute; left: 0; top: 0; bottom: 0;
  background: var(--acc-info);
  border-radius: 1px;
}
.eff-comp-fill.activity { background: var(--acc-info); }
.eff-comp-fill.cert { background: var(--acc-success); }
.eff-comp-fill.pass { background: var(--acc-warn); }
.eff-comp-val {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  text-align: right;
  color: var(--ink-2);
}

/* ─── INTERACTIVE FILTER — блок «Динамика сертификатов» ─── */
.filter-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-left: 3px solid var(--acc-info);
  margin-bottom: 28px;
}
.filter-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, #F4F8FF 0%, #FFFFFF 100%);
}
.filter-head h3 {
  font-size: 13px; font-weight: 600;
  display: flex; align-items: center; gap: 8px;
}
.filter-head .filter-badge {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: var(--acc-info);
  color: white;
  padding: 2px 8px;
  border-radius: 2px;
  font-weight: 600;
}
.filter-controls {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  padding: 18px;
  border-bottom: 1px solid var(--border);
  background: var(--ink-9);
}
@media (max-width: 1100px) {
  .filter-controls { grid-template-columns: 1fr; }
}
.fctrl {
  display: flex; flex-direction: column; gap: 6px;
}
.fctrl-lbl {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-4);
  font-weight: 500;
}
.fctrl-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.fctrl input[type="date"],
.fctrl input[type="number"],
.fctrl select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border-strong);
  background: white;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 13px;
  color: var(--ink-1);
  border-radius: 2px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.fctrl input:focus, .fctrl select:focus {
  border-color: var(--acc-info);
  box-shadow: 0 0 0 2px rgba(31, 111, 235, 0.12);
}
.fctrl-hint {
  font-size: 10px;
  color: var(--ink-4);
}
.fctrl-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}
.fctrl-btn {
  background: var(--ink-1);
  color: white;
  border: none;
  padding: 8px 14px;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 2px;
  transition: background 0.15s;
}
.fctrl-btn:hover { background: var(--ink-0); }
.fctrl-btn.secondary {
  background: white;
  color: var(--ink-1);
  border: 1px solid var(--border-strong);
}
.fctrl-btn.secondary:hover { background: var(--ink-8); }

.fctrl-presets { display: flex; gap: 4px; margin-top: 4px; flex-wrap: wrap; }
.fctrl-preset {
  font-size: 11px;
  padding: 4px 10px;
  background: white;
  border: 1px solid var(--border);
  cursor: pointer;
  border-radius: 2px;
  color: var(--ink-2);
  transition: all 0.15s;
}
.fctrl-preset:hover { border-color: var(--acc-info); color: var(--acc-info); }
.fctrl-preset.active {
  background: var(--acc-info);
  color: white;
  border-color: var(--acc-info);
}

.filter-results {
  padding: 18px;
}
.fres-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  margin-bottom: 18px;
  border: 1px solid var(--border);
}
.fres-cell {
  padding: 14px 16px;
  border-right: 1px solid var(--border);
}
.fres-cell:last-child { border-right: none; }
.fres-lbl {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-4);
  margin-bottom: 6px;
}
.fres-val {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 22px;
  font-weight: 600;
  color: var(--ink-1);
  letter-spacing: -0.02em;
}
.fres-sub {
  font-size: 11px;
  color: var(--ink-3);
  margin-top: 2px;
}
.fres-table {
  max-height: 320px;
  overflow-y: auto;
  border: 1px solid var(--border);
}
.fres-table table { width: 100%; border-collapse: collapse; font-size: 13px; }
.fres-table th {
  background: var(--ink-8);
  padding: 8px 12px;
  text-align: left;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-3);
  font-weight: 600;
  position: sticky;
  top: 0;
  border-bottom: 1px solid var(--border);
}
.fres-table th.n { text-align: right; }
.fres-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--ink-2);
}
.fres-table td.n {
  text-align: right;
  font-family: 'IBM Plex Mono', monospace;
  font-variant-numeric: tabular-nums;
}
.fres-table tr:hover { background: var(--ink-9); }
.fres-empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--ink-4);
  font-size: 13px;
}

/* multi-select compact */
.fctrl-multi {
  position: relative;
}
.fctrl-multi-btn {
  width: 100%;
  text-align: left;
  padding: 8px 32px 8px 10px;
  border: 1px solid var(--border-strong);
  background: white;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 13px;
  color: var(--ink-1);
  cursor: pointer;
  border-radius: 2px;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fctrl-multi-btn:hover { border-color: var(--ink-3); }
.fctrl-multi-btn::after {
  content: '▾';
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ink-4);
  font-size: 10px;
}
.fctrl-multi-list {
  position: absolute;
  top: calc(100% + 4px);
  left: 0; right: 0;
  background: white;
  border: 1px solid var(--border-strong);
  max-height: 280px;
  overflow-y: auto;
  z-index: 50;
  display: none;
  border-radius: 2px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.fctrl-multi-list.open { display: block; }
.fctrl-multi-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--ink-8);
}
.fctrl-multi-item:hover { background: var(--ink-9); }
.fctrl-multi-item input[type="checkbox"] { margin: 0; }
.fctrl-multi-item.all {
  background: var(--ink-9);
  font-weight: 600;
}
.fctrl-multi-search {
  padding: 8px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: white;
}
.fctrl-multi-search input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--border);
  font-size: 12px;
  border-radius: 2px;
}

/* ─── ORG ROWS ─── */
.org-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light, #EFEFEF);
  font-size: 13px;
}
.org-row:last-child { border-bottom: none; }
.org-name { color: var(--ink-1); }
.org-count {
  font-family: 'IBM Plex Mono', monospace;
  font-weight: 600;
  color: var(--ink-2);
}
.org-cell {
  font-size: 12px;
  color: var(--ink-2);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ─── PANELS ─── */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 28px; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 28px; }
.grid-2-1 { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 28px; }
.grid-1-2 { display: grid; grid-template-columns: 1fr 2fr; gap: 20px; margin-bottom: 28px; }

.panel {
  background: var(--bg-panel);
  border: 1px solid var(--border);
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
}
.panel-head h3 {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.panel-head .tag {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.panel-body {
  padding: 18px;
}
.panel-body.tight { padding: 0; }

/* ─── CHARTS ─── */
.chart-wrap {
  position: relative;
  width: 100%;
}
canvas { display: block; width: 100% !important; }

.tooltip {
  position: absolute;
  background: var(--ink-0);
  color: var(--ink-9);
  padding: 6px 10px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.1s;
  z-index: 20;
  white-space: nowrap;
}
.tooltip::before {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  margin-left: -4px;
  border: 4px solid transparent;
  border-top-color: var(--ink-0);
}

/* ─── TABLES ─── */
table.dt {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
table.dt thead th {
  background: var(--ink-8);
  color: var(--text-muted);
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border-strong);
  position: sticky;
  top: 0;
}
table.dt tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
table.dt tbody tr:hover { background: var(--ink-8); }
table.dt .n { text-align: right; font-family: 'IBM Plex Mono', monospace; }
table.dt .truncate { max-width: 360px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Metric bar inline */
.bar-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.bar-cell .track {
  flex: 1;
  min-width: 60px;
  height: 4px;
  background: var(--ink-8);
  position: relative;
  overflow: hidden;
}
.bar-cell .fill {
  position: absolute; top: 0; left: 0; height: 100%;
}
.bar-cell .num {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  min-width: 40px;
  text-align: right;
}

.status {
  display: inline-block;
  padding: 2px 6px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.status.good { background: #E6F5ED; color: var(--acc-success); }
.status.warn { background: #FDF0E1; color: var(--acc-warn); }
.status.bad  { background: #FBE7E9; color: var(--acc-primary); }
.status.neutral { background: var(--ink-8); color: var(--text-muted); }

/* Rank badge */
.rank {
  display: inline-block;
  width: 24px; height: 24px;
  line-height: 24px;
  text-align: center;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  background: var(--ink-8);
  color: var(--text-muted);
}
.rank.top-1 { background: #FFF4D1; color: #7A5900; }
.rank.top-2 { background: var(--ink-7); color: var(--ink-2); }
.rank.top-3 { background: #F4DFCE; color: #6D3E1B; }

/* ─── FUNNEL ─── */
.funnel { display: flex; flex-direction: column; gap: 4px; }
.funnel-row {
  display: grid;
  grid-template-columns: 180px 1fr 70px 60px;
  gap: 12px;
  align-items: center;
}
.funnel-row .lbl { font-size: 13px; color: var(--text); }
.funnel-row .bar-outer {
  height: 32px;
  position: relative;
  background: var(--ink-8);
}
.funnel-row .bar-inner {
  height: 100%;
  display: flex;
  align-items: center;
  padding-left: 12px;
  color: white;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  font-weight: 500;
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.funnel-row .pct {
  text-align: right;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px;
  font-weight: 500;
}
.funnel-row .drop {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: var(--text-dim);
  text-align: right;
}

/* ─── HEATMAP ─── */
.heatmap { display: grid; grid-template-columns: 40px repeat(24, 1fr); gap: 2px; }
.heatmap .hlabel { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--text-dim); display: flex; align-items: center; justify-content: flex-end; padding-right: 6px; }
.heatmap .hcell { aspect-ratio: 1; background: var(--ink-8); position: relative; cursor: help; }
.heatmap-header { display: grid; grid-template-columns: 40px repeat(24, 1fr); gap: 2px; margin-bottom: 4px; }
.heatmap-header .h { font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: var(--text-dim); text-align: center; }

/* ─── COHORT TABLE ─── */
.cohort-table { font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
.cohort-table th, .cohort-table td { padding: 8px 10px; text-align: center; border: 1px solid var(--border); }
.cohort-table th { background: var(--ink-8); font-weight: 500; }
.cohort-table .label-cell { text-align: left; background: var(--ink-9); font-weight: 600; }
.cohort-table .val { font-variant-numeric: tabular-nums; }

/* ─── PILL / DISTRIBUTION ─── */
.dist-item {
  display: grid;
  grid-template-columns: 1fr 60px 60px;
  gap: 12px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.dist-item:last-child { border-bottom: none; }
.dist-item .dlabel { font-size: 13px; }
.dist-item .dbar { height: 6px; background: var(--ink-8); position: relative; grid-column: 1 / 4; margin-top: 6px; }
.dist-item .dfill { position: absolute; height: 100%; top: 0; left: 0; }

/* ─── INSIGHTS / CALLOUTS ─── */
.insight {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  padding: 14px 16px;
  background: var(--ink-8);
  border-left: 3px solid var(--acc-info);
  margin-bottom: 14px;
  font-size: 13px;
}
.insight.alert { border-left-color: var(--acc-primary); background: #FEF2F3; }
.insight.warn { border-left-color: var(--acc-warn); background: #FDF7EE; }
.insight.good { border-left-color: var(--acc-success); background: #EDF7F2; }
.insight .mark {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding-top: 2px;
}
.insight .txt { color: var(--text); }
.insight .txt strong { font-weight: 600; }

/* ─── METRICS INLINE ─── */
.mrow {
  display: flex; gap: 24px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  background: var(--ink-9);
}
.mrow .m { flex: 1; }
.mrow .m .l { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.1em; }
.mrow .m .v { font-size: 22px; font-weight: 300; letter-spacing: -0.02em; margin-top: 2px; }
.mrow .m .u { font-size: 11px; color: var(--text-muted); margin-left: 3px; }

.empty { padding: 60px 20px; text-align: center; color: var(--text-dim); font-family: 'IBM Plex Mono', monospace; font-size: 12px; }

/* Focus utilities */
.scroll-y { max-height: 560px; overflow-y: auto; }
.scroll-y::-webkit-scrollbar { width: 6px; }
.scroll-y::-webkit-scrollbar-thumb { background: var(--border-strong); }

/* Responsive */
@media (max-width: 1100px) {
  body { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .kpi:nth-child(2n) { border-right: none; }
  .kpi:nth-child(4n) { border-right: 1px solid var(--border); }
  .grid-2, .grid-3, .grid-2-1, .grid-1-2 { grid-template-columns: 1fr; }
}
</style>
</head>
<body>

<aside class="sidebar">
  <div class="brand">
    <div class="mark">CMTIS · АНАЛИТИКА</div>
    <div class="name">Панель</div>
    <div class="sub">Эффективность обучения</div>
  </div>

  <div class="nav-section">
    <div class="nav-label">Обзор</div>
    <div class="nav-item active" data-view="overview"><span class="icon">01</span>Главная</div>
    <div class="nav-item" data-view="funnel"><span class="icon">02</span>Воронка вовлечения</div>
    <div class="nav-item" data-view="activity"><span class="icon">03</span>Активность</div>
  </div>

  <div class="nav-section">
    <div class="nav-label">Контент</div>
    <div class="nav-item" data-view="courses"><span class="icon">04</span>Курсы</div>
    <div class="nav-item" data-view="assessments"><span class="icon">05</span>Тесты и оценки</div>
    <div class="nav-item" data-view="questions"><span class="icon">06</span>Сложность вопросов</div>
  </div>

  <div class="nav-section">
    <div class="nav-label">Студенты</div>
    <div class="nav-item" data-view="cohorts"><span class="icon">07</span>Когорты</div>
    <div class="nav-item" data-view="engagement"><span class="icon">08</span>Вовлечённость</div>
    <div class="nav-item" data-view="risk"><span class="icon">09</span>Риск отсева</div>
  </div>

  <div class="sidebar-footer">
    <div><span class="dot"></span>Хранилище · АКТИВНО</div>
    <div style="margin-top:6px">Последний ETL: __LAST_ETL__</div>
    <div style="margin-top:2px">Период данных: __PERIOD_START__ → __PERIOD_END__</div>
  </div>
</aside>

<main class="main">
  <div class="topbar">
    <div class="page-title" id="page-title">Главная</div>
    <div class="meta">
      <span>v1.0.0</span>
      <span class="period">__PERIOD_LABEL__</span>
    </div>
  </div>

  <div class="content">
    <div class="view active" id="view-overview"></div>
    <div class="view" id="view-funnel"></div>
    <div class="view" id="view-activity"></div>
    <div class="view" id="view-courses"></div>
    <div class="view" id="view-assessments"></div>
    <div class="view" id="view-questions"></div>
    <div class="view" id="view-cohorts"></div>
    <div class="view" id="view-engagement"></div>
    <div class="view" id="view-risk"></div>
  </div>
</main>

<script>
const D = __DATA_JSON__;

// ═══════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const fmt = n => (n == null || isNaN(n)) ? '—' : Number(n).toLocaleString('ru-RU');
const pct = n => n == null ? '—' : Number(n).toFixed(1) + '%';
const DPR = Math.min(window.devicePixelRatio || 1, 2);

const CLR = {
  ink0: '#0A0A0B', ink1: '#1A1A1D', ink2: '#252529', ink3: '#3A3A40',
  ink4: '#5A5A62', ink5: '#8A8A92', ink6: '#B8B8BF', ink7: '#E4E4E7',
  ink8: '#F4F4F5', ink9: '#FCFCFD',
  primary: '#E63946', success: '#0F9960', warn: '#D9822B',
  info: '#1F6FEB', accent: '#FFD166',
};

function hiDPI(canvas, w, h) {
  canvas.width = w * DPR;
  canvas.height = h * DPR;
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(DPR, DPR);
  ctx.textRendering = 'geometricPrecision';
  return ctx;
}

function tooltip(el, txt, x, y) {
  let t = el.parentElement.querySelector('.tooltip');
  if (!t) {
    t = document.createElement('div');
    t.className = 'tooltip';
    el.parentElement.style.position = 'relative';
    el.parentElement.appendChild(t);
  }
  t.innerHTML = txt;
  t.style.left = (x - t.offsetWidth/2) + 'px';
  t.style.top = (y - 36) + 'px';
  t.style.opacity = 1;
}
function hideTooltip(el) {
  const t = el.parentElement.querySelector('.tooltip');
  if (t) t.style.opacity = 0;
}

function bindRegions(canvas, regions, formatter) {
  canvas.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    let hit = null;
    for (const r of regions) {
      if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) { hit = r; break; }
    }
    if (hit) {
      tooltip(canvas, formatter(hit), hit.x + hit.w/2, hit.y);
      canvas.style.cursor = 'crosshair';
    } else {
      hideTooltip(canvas);
      canvas.style.cursor = 'default';
    }
  });
  canvas.addEventListener('mouseleave', () => hideTooltip(canvas));
}

// ═══════════════════════════════════════════════════════════════
// CHART PRIMITIVES
// ═══════════════════════════════════════════════════════════════

function drawBarV(host, data, opts = {}) {
  const canvas = document.createElement('canvas');
  canvas.setAttribute('height', opts.height || 260);
  host.appendChild(canvas);
  const cw = host.clientWidth;
  const ch = opts.height || 260;
  const ctx = hiDPI(canvas, cw, ch);
  const pad = { t: 14, r: 16, b: 36, l: 42 };
  const w = cw - pad.l - pad.r;
  const h = ch - pad.t - pad.b;
  const max = Math.max(...data.map(d => d.v)) * 1.1 || 1;
  const regions = [];

  // Axis grid
  ctx.strokeStyle = CLR.ink7;
  ctx.lineWidth = 1;
  ctx.font = '10px "IBM Plex Mono", monospace';
  ctx.fillStyle = CLR.ink5;
  for (let i = 0; i <= 4; i++) {
    const v = max / 4 * i;
    const y = pad.t + h - (v / max * h);
    ctx.beginPath();
    ctx.moveTo(pad.l, y + 0.5);
    ctx.lineTo(pad.l + w, y + 0.5);
    ctx.strokeStyle = i === 0 ? CLR.ink3 : CLR.ink8;
    ctx.stroke();
    ctx.textAlign = 'right';
    ctx.fillText(fmt(Math.round(v)), pad.l - 6, y + 3);
  }

  const bw = w / data.length * 0.72;
  const gap = w / data.length * 0.28;

  data.forEach((d, i) => {
    const bh = (d.v / max) * h;
    const x = pad.l + i * (bw + gap) + gap / 2;
    const y = pad.t + h - bh;
    const clr = typeof opts.color === 'function' ? opts.color(d, i) : (opts.color || CLR.ink2);

    ctx.fillStyle = clr;
    ctx.fillRect(x, y, bw, bh);

    // top accent line
    if (opts.accent) {
      ctx.fillStyle = CLR.accent;
      ctx.fillRect(x, y, bw, 2);
    }

    ctx.fillStyle = CLR.ink5;
    ctx.font = '10px "IBM Plex Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(d.label, x + bw / 2, ch - pad.b + 14);

    regions.push({ x, y, w: bw, h: bh, ...d });
  });

  bindRegions(canvas, regions, r => `${r.label}<br>${opts.tooltipPrefix || ''}${fmt(r.v)}${opts.tooltipSuffix || ''}`);
}

function drawBarH(host, data, opts = {}) {
  const canvas = document.createElement('canvas');
  const rowH = opts.rowH || 28;
  const ch = Math.max(200, data.length * (rowH + 4) + 20);
  canvas.setAttribute('height', ch);
  host.appendChild(canvas);
  const cw = host.clientWidth;
  const ctx = hiDPI(canvas, cw, ch);
  const labelW = opts.labelW || 200;
  const pad = { t: 10, r: 70, b: 10, l: labelW + 14 };
  const w = cw - pad.l - pad.r;
  const max = opts.max || Math.max(...data.map(d => d.v)) * 1.05;
  const regions = [];

  data.forEach((d, i) => {
    const y = pad.t + i * (rowH + 4);
    const bw = Math.max(2, (d.v / max) * w);
    const clr = typeof opts.color === 'function' ? opts.color(d, i) : (opts.color || CLR.ink2);

    // Label
    ctx.fillStyle = CLR.ink2;
    ctx.font = '12px "IBM Plex Sans", sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    const label = d.label.length > 32 ? d.label.slice(0, 30) + '…' : d.label;
    ctx.fillText(label, pad.l - 10, y + rowH / 2);

    // Track (lighter)
    ctx.fillStyle = CLR.ink8;
    ctx.fillRect(pad.l, y, w, rowH);

    // Bar
    ctx.fillStyle = clr;
    ctx.fillRect(pad.l, y, bw, rowH);

    // Value
    ctx.fillStyle = CLR.ink2;
    ctx.font = '11px "IBM Plex Mono", monospace';
    ctx.textAlign = 'left';
    const valueText = opts.valueFmt ? opts.valueFmt(d.v) : fmt(d.v);
    ctx.fillText(valueText, pad.l + bw + 6, y + rowH / 2);

    regions.push({ x: pad.l, y, w: bw, h: rowH, ...d });
  });

  bindRegions(canvas, regions, r => `${r.label}<br>${opts.valueFmt ? opts.valueFmt(r.v) : fmt(r.v)}`);
}

function drawLine(host, data, opts = {}) {
  const canvas = document.createElement('canvas');
  canvas.setAttribute('height', opts.height || 240);
  host.appendChild(canvas);
  const cw = host.clientWidth;
  const ch = opts.height || 240;
  const ctx = hiDPI(canvas, cw, ch);
  const pad = { t: 14, r: 20, b: 30, l: 46 };
  const w = cw - pad.l - pad.r;
  const h = ch - pad.t - pad.b;
  const max = Math.max(...data.map(d => d.v)) * 1.1 || 1;
  const regions = [];

  // Grid
  ctx.strokeStyle = CLR.ink8;
  ctx.font = '10px "IBM Plex Mono", monospace';
  for (let i = 0; i <= 4; i++) {
    const v = max / 4 * i;
    const y = pad.t + h - (v / max * h);
    ctx.beginPath();
    ctx.moveTo(pad.l, y + 0.5);
    ctx.lineTo(pad.l + w, y + 0.5);
    ctx.strokeStyle = i === 0 ? CLR.ink3 : CLR.ink8;
    ctx.stroke();
    ctx.fillStyle = CLR.ink5;
    ctx.textAlign = 'right';
    ctx.fillText(fmt(Math.round(v)), pad.l - 6, y + 3);
  }

  // Fill area
  if (data.length > 1) {
    ctx.beginPath();
    data.forEach((d, i) => {
      const x = pad.l + (i / (data.length - 1)) * w;
      const y = pad.t + h - (d.v / max * h);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.lineTo(pad.l + w, pad.t + h);
    ctx.lineTo(pad.l, pad.t + h);
    ctx.closePath();
    ctx.fillStyle = opts.fill || 'rgba(31, 111, 235, 0.08)';
    ctx.fill();

    // Line
    ctx.beginPath();
    data.forEach((d, i) => {
      const x = pad.l + (i / (data.length - 1)) * w;
      const y = pad.t + h - (d.v / max * h);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = opts.stroke || CLR.info;
    ctx.lineWidth = 1.75;
    ctx.stroke();
  }

  // Points + axis labels
  const step = Math.max(1, Math.floor(data.length / 10));
  data.forEach((d, i) => {
    const x = pad.l + (data.length > 1 ? (i / (data.length - 1)) * w : w/2);
    const y = pad.t + h - (d.v / max * h);

    if (i % step === 0 || i === data.length - 1) {
      ctx.fillStyle = CLR.ink5;
      ctx.font = '10px "IBM Plex Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText(d.label, x, ch - pad.b + 14);
    }

    // Small point
    ctx.fillStyle = opts.stroke || CLR.info;
    ctx.beginPath();
    ctx.arc(x, y, 2, 0, Math.PI * 2);
    ctx.fill();

    regions.push({ x: x - 8, y: y - 8, w: 16, h: 16, label: d.label, v: d.v });
  });

  bindRegions(canvas, regions, r => `${r.label}<br>${fmt(r.v)}`);
}

function drawHeatmap(host, matrix, opts = {}) {
  const rows = matrix.length, cols = matrix[0].length;
  const canvas = document.createElement('canvas');
  const ch = opts.height || 180;
  canvas.setAttribute('height', ch);
  host.appendChild(canvas);
  const cw = host.clientWidth;
  const ctx = hiDPI(canvas, cw, ch);
  const pad = { t: 20, r: 10, b: 20, l: 36 };
  const w = cw - pad.l - pad.r;
  const h = ch - pad.t - pad.b;
  const cellW = w / cols;
  const cellH = h / rows;
  const max = Math.max(...matrix.flat()) || 1;
  const dayLabels = opts.rowLabels || ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
  const regions = [];

  // Row labels
  ctx.fillStyle = CLR.ink5;
  ctx.font = '10px "IBM Plex Mono", monospace';
  for (let r = 0; r < rows; r++) {
    ctx.textAlign = 'right';
    ctx.fillText(dayLabels[r], pad.l - 6, pad.t + r * cellH + cellH / 2 + 3);
  }

  // Column labels (hours, every 3)
  for (let c = 0; c < cols; c += 3) {
    ctx.textAlign = 'center';
    ctx.fillText(c, pad.l + c * cellW + cellW / 2, pad.t - 6);
  }

  // Cells
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const v = matrix[r][c];
      const intensity = v / max;
      const x = pad.l + c * cellW;
      const y = pad.t + r * cellH;
      // Сyan-blue ink scale
      const alpha = Math.max(0.04, intensity);
      ctx.fillStyle = `rgba(31, 111, 235, ${alpha})`;
      ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);
      regions.push({ x: x + 1, y: y + 1, w: cellW - 2, h: cellH - 2,
                     label: `${dayLabels[r]} ${c}:00`, v });
    }
  }

  bindRegions(canvas, regions, r => `${r.label} · ${fmt(r.v)} событий`);
}

// ═══════════════════════════════════════════════════════════════
// VIEWS
// ═══════════════════════════════════════════════════════════════

function renderOverview() {
  const K = D.kpis;
  const f = D.funnel;
  const eff = D.overall_effectiveness || null;
  const dau90 = D.dau_90d || [];
  const filter = D.certificates_filter || { courses: [], issues: [], min_date: null, max_date: null };

  // ─── HERO KPI: 4 главные метрики ───
  const heroKpis = [
    {
      label: 'Активных пользователей',
      value: fmt(K.users_with_activity),
      sub: 'из ' + fmt(K.active_users) + ' зарегистрированных',
      sub2: pct(K.engagement_rate) + ' вовлечённости · DAU₃₀ ' + fmt(K.active_last_30d),
      trend: K.engagement_rate > 50 ? 'up' : 'warn',
      icon: '👥'
    },
    {
      label: 'Активных курсов',
      value: fmt(K.total_courses),
      sub: fmt(K.total_enrolments) + ' записей всего',
      sub2: fmt(K.courses_with_certificates) + ' курсов выдают сертификаты',
      trend: null,
      icon: '📚'
    },
    {
      label: 'Получили сертификат',
      value: fmt(K.users_with_certificate),
      sub: '+' + fmt(K.users_with_certificate_7d) + ' за 7 дней',
      sub2: pct(K.certification_rate) + ' от активных пользователей',
      trend: K.certification_rate > 50 ? 'up' : 'warn',
      icon: '🎓'
    },
    {
      label: 'Сертификатов выдано',
      value: fmt(K.certificates_issued),
      sub: '+' + fmt(K.certificates_last_7d) + ' за последние 7 дней',
      sub2: 'всего по платформе',
      trend: K.certificates_last_7d > 0 ? 'up' : null,
      icon: '📜'
    },
  ];

  // ─── ВТОРИЧНЫЕ KPI ───
  const secondaryKpis = [
    ['DAU за 7 дней', fmt(K.active_last_7d), 'недавняя активность'],
    ['DAU за 30 дней', fmt(K.active_last_30d), 'месячная активность'],
    ['Средняя оценка', pct(K.avg_grade_percent), pct(K.grade_pass_rate) + ' доля сдачи'],
    ['Событий в логах', fmt(K.total_events), 'за весь период'],
    ['Попыток тестов', fmt(K.total_quiz_attempts), fmt(K.finished_quiz_attempts) + ' завершено'],
    ['Завершено модулей', fmt(K.total_completions), pct(K.completion_rate) + ' от общего числа'],
  ];

  // ─── ВОРОНКА с конверсией ───
  const funnelRows = f.map((s, i) => {
    const conv = i === 0 ? 100 : (s.count / f[0].count * 100);
    return `
      <div class="fmini-row with-conv">
        <span class="fmini-lbl">${s.stage}</span>
        <div class="fmini-bar">
          <div class="fmini-fill" style="width:${conv}%"></div>
          <span class="fmini-val">${fmt(s.count)}</span>
        </div>
        <span class="fmini-pct step" title="Конверсия со шага N-1">${i === 0 ? '—' : (s.conversion_step.toFixed(0) + '%')}</span>
        <span class="fmini-pct" title="Конверсия от вершины">${s.conversion_total.toFixed(0)}%</span>
        <span class="fmini-pct drop" title="Потеряно на шаге">${i === 0 ? '—' : '−' + fmt(s.drop_off)}</span>
      </div>
    `;
  }).join('');

  // ─── ОРГАНИЗАЦИИ + ТОП КУРСОВ ───
  const orgsHtml = (K.top_organizations || []).map(o => `
    <div class="org-row">
      <span class="org-name" title="${o.organization || ''}">${o.organization || '—'}</span>
      <span class="org-count">${fmt(o.users)}</span>
    </div>
  `).join('') || '<div class="org-row" style="color:var(--ink-3)">данные не заполнены</div>';

  const topByCerts = D.courses
    .filter(c => c.certificates_issued > 0)
    .sort((a, b) => b.certificates_issued - a.certificates_issued)
    .slice(0, 5);

  // ─── РЕНДЕРИНГ HTML ───
  $('#view-overview').innerHTML = `
    <div class="section">
      <div class="section-head">
        <h2>Сводка платформы</h2>
        <span class="caption">Период: ${(K.period_start || '').slice(0,10)} → ${(K.period_end || '').slice(0,10)}</span>
      </div>

      <!-- HERO METRICS -->
      <div class="hero-grid">
        ${heroKpis.map(k => `
          <div class="hero-kpi ${k.trend || ''}">
            <div class="hero-icon">${k.icon}</div>
            <div class="hero-label">${k.label}</div>
            <div class="hero-value">${k.value}</div>
            <div class="hero-sub">${k.sub}</div>
            <div class="hero-sub2">${k.sub2}</div>
          </div>
        `).join('')}
      </div>

      <!-- SECONDARY KPIs -->
      <div class="kpi-grid" style="margin-top:16px">
        ${secondaryKpis.map(k => `
          <div class="kpi">
            <div class="label">${k[0]}</div>
            <div class="value">${k[1]}</div>
            <div class="sub">${k[2]}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- ROW 1: DAU 90 дней (широкая) + общая эффективность -->
    <div class="grid-2-1">
      <div class="panel">
        <div class="panel-head">
          <h3>Динамика DAU за 90 дней</h3>
          <span class="tag">${dau90.length} дней наблюдений</span>
        </div>
        <div class="panel-body"><div id="chart-dau90" class="chart-wrap"></div></div>
      </div>
      <div class="panel">
        <div class="panel-head">
          <h3>Коэффициент эффективности</h3>
          <span class="tag">Все курсы</span>
        </div>
        <div class="panel-body" style="padding:0">
          ${eff ? renderEffectivenessGauge(eff) : '<div style="padding:20px; color:var(--ink-3)">нет данных</div>'}
        </div>
      </div>
    </div>

    <!-- ROW 2: Воронка (расширенная с конверсиями) -->
    <div class="panel" style="margin-bottom:28px">
      <div class="panel-head">
        <h3>Воронка вовлечения</h3>
        <span class="tag">7 этапов · от регистрации до сертификата</span>
      </div>
      <div class="panel-body" style="padding:14px 0 18px">
        <div class="fmini-head">
          <span>Этап</span>
          <span>Размер</span>
          <span>Шаг</span>
          <span>От топа</span>
          <span>Потери</span>
        </div>
        <div class="funnel-mini">
          ${funnelRows}
        </div>
      </div>
    </div>

    <!-- ROW 3: ИНТЕРАКТИВНЫЙ ФИЛЬТР -->
    <div class="filter-panel" id="cert-filter">
      <div class="filter-head">
        <h3>
          <span class="filter-badge">Админ</span>
          Динамика выдачи сертификатов · интерактивный фильтр
        </h3>
        <span class="tag" id="cert-filter-period">${filter.min_date || '—'} → ${filter.max_date || '—'}</span>
      </div>

      <div class="filter-controls">
        <!-- ПЕРИОД -->
        <div class="fctrl">
          <span class="fctrl-lbl">📅 Период</span>
          <div class="fctrl-row">
            <input type="date" id="filter-from" min="${filter.min_date || ''}" max="${filter.max_date || ''}" value="${filter.min_date || ''}">
            <input type="date" id="filter-to" min="${filter.min_date || ''}" max="${filter.max_date || ''}" value="${filter.max_date || ''}">
          </div>
          <div class="fctrl-presets">
            <button class="fctrl-preset" data-preset="7">7д</button>
            <button class="fctrl-preset" data-preset="30">30д</button>
            <button class="fctrl-preset" data-preset="90">90д</button>
            <button class="fctrl-preset active" data-preset="all">Весь период</button>
          </div>
        </div>

        <!-- КУРСЫ -->
        <div class="fctrl">
          <span class="fctrl-lbl">📚 Курсы (${filter.courses.length} шт.)</span>
          <div class="fctrl-multi">
            <button class="fctrl-multi-btn" id="filter-courses-btn">Все курсы</button>
            <div class="fctrl-multi-list" id="filter-courses-list">
              <div class="fctrl-multi-search">
                <input type="text" id="filter-courses-search" placeholder="Поиск по названию…">
              </div>
              <label class="fctrl-multi-item all">
                <input type="checkbox" id="filter-courses-all" checked>
                <span>Все курсы</span>
              </label>
              ${filter.courses.map(c => `
                <label class="fctrl-multi-item" data-name="${(c.course_name || '').toLowerCase()}">
                  <input type="checkbox" class="filter-course-cb" value="${c.course_id}" checked>
                  <span title="${c.course_name || ''}">${(c.course_name || '—').length > 60 ? (c.course_name.slice(0, 60) + '…') : (c.course_name || '—')}
                  <span style="color:var(--ink-4); font-family:'IBM Plex Mono',monospace; font-size:11px"> · ${c.certs_total}</span></span>
                </label>
              `).join('')}
            </div>
          </div>
          <div class="fctrl-hint">Можно выбрать один или несколько курсов</div>
        </div>

        <!-- МИНИМУМ СЕРТИФИКАТОВ -->
        <div class="fctrl">
          <span class="fctrl-lbl">🎯 Минимум сертификатов на курс</span>
          <input type="number" id="filter-min-certs" value="0" min="0" step="1">
          <div class="fctrl-hint">Скрыть курсы с числом сертификатов меньше указанного</div>
          <div class="fctrl-actions">
            <button class="fctrl-btn" id="filter-apply">Применить</button>
            <button class="fctrl-btn secondary" id="filter-reset">Сбросить</button>
          </div>
        </div>
      </div>

      <div class="filter-results" id="filter-results">
        <!-- сюда рендерится результат -->
      </div>
    </div>

    <!-- ROW 4: топ курсов и организаций -->
    <div class="grid-2">
      <div class="panel">
        <div class="panel-head"><h3>Топ курсов по сертификатам</h3><span class="tag">Сертификаты</span></div>
        <div class="panel-body tight">
          ${topByCerts.length ? `
          <table class="ctab" style="margin:0">
            <thead><tr>
              <th style="text-align:left">Курс</th>
              <th style="text-align:right">Студентов</th>
              <th style="text-align:right">Сертификатов</th>
              <th style="text-align:right">Доля</th>
            </tr></thead>
            <tbody>
              ${topByCerts.map(c => `
                <tr>
                  <td title="${c.course_name}">${(c.course_name || '').length > 50 ? (c.course_name.slice(0, 50) + '…') : (c.course_name || '—')}</td>
                  <td class="n">${fmt(c.students)}</td>
                  <td class="n"><b>${fmt(c.certificates_issued)}</b></td>
                  <td class="n">${pct(c.certification_rate)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          ` : '<div style="color:var(--ink-3); padding:14px">сертификатов ещё не выдано</div>'}
        </div>
      </div>
      <div class="panel">
        <div class="panel-head"><h3>Топ организаций</h3><span class="tag">По числу пользователей</span></div>
        <div class="panel-body tight" style="padding:14px">
          ${orgsHtml}
        </div>
      </div>
    </div>

    <!-- ROW 5: активность по месяцам — БЕЗ обрезки года -->
    <div class="panel">
      <div class="panel-head"><h3>Активность по месяцам</h3><span class="tag">События по календарю</span></div>
      <div class="panel-body"><div id="chart-monthly" class="chart-wrap"></div></div>
    </div>
  `;

  // ─── ГРАФИКИ ───

  // Активность по месяцам — формат "MM/YY", чтобы 2025-07 ≠ 2026-07
  drawBarV($('#chart-monthly'),
    D.activity.monthly.map(m => ({
      label: formatMonth(m.month),    // "07/25" вместо "07"
      v: m.events,
      tooltip: m.month + ': ' + fmt(m.events) + ' событий'
    })),
    { color: (d, i) => i === D.activity.monthly.length - 1 ? CLR.accent : CLR.ink2,
      tooltipSuffix: ' событий' });

  // DAU за 90 дней — линейный график с заливкой
  if (dau90.length) {
    drawLine($('#chart-dau90'),
      dau90.map(d => ({
        label: formatDayShort(d.date),  // "MM-DD" но мы хранили date полностью
        v: d.dau,
        tooltip: d.date + ': ' + fmt(d.dau) + ' DAU · ' + fmt(d.events) + ' событий'
      })),
      { stroke: CLR.info, fill: 'rgba(31,111,235,0.10)', height: 240 });
  } else {
    $('#chart-dau90').innerHTML = '<div style="padding:40px; text-align:center; color:var(--ink-3)">недостаточно данных</div>';
  }

  // ─── ИНИЦИАЛИЗАЦИЯ ИНТЕРАКТИВНОГО ФИЛЬТРА ───
  initCertFilter(filter);
}

/* Возвращает SVG-полукруг-индикатор + компоненты */
function renderEffectivenessGauge(eff) {
  const r = 80;
  const cx = 110, cy = 100;
  // Полукруг от (cx-r, cy) до (cx+r, cy) — длина = π·r
  const arc = Math.PI * r;
  const dash = (eff.score / 100) * arc;
  const c = eff.components;
  const cls = eff.category; // 'high' | 'medium' | 'low'

  return `
    <div class="gauge-wrap">
      <div>
        <div class="gauge">
          <svg width="220" height="130" viewBox="0 0 220 130">
            <path class="gauge-track"
              d="M 30 100 A 80 80 0 0 1 190 100"/>
            <path class="gauge-fill ${cls}"
              d="M 30 100 A 80 80 0 0 1 190 100"
              stroke-dasharray="${dash} ${arc}"/>
          </svg>
          <div class="gauge-value">${eff.score.toFixed(1)}</div>
          <div class="gauge-label ${cls}">${eff.label} эффективность</div>
        </div>
        <div style="text-align:center; font-size:11px; color:var(--ink-4); margin-top:30px">
          по ${eff.courses_count} активным курсам
        </div>
      </div>

      <div class="eff-components">
        <div class="eff-comp-row" title="Какая доля записанных вообще заходила">
          <span class="eff-comp-lbl">Активность</span>
          <div class="eff-comp-bar">
            <div class="eff-comp-fill activity" style="width:${(c.activity / c.activity_max * 100).toFixed(0)}%"></div>
          </div>
          <span class="eff-comp-val">${c.activity.toFixed(1)}/${c.activity_max}</span>
        </div>
        <div class="eff-comp-row" title="Доля записанных, получивших сертификат">
          <span class="eff-comp-lbl">Сертификация</span>
          <div class="eff-comp-bar">
            <div class="eff-comp-fill cert" style="width:${(c.certification / c.certification_max * 100).toFixed(0)}%"></div>
          </div>
          <span class="eff-comp-val">${c.certification.toFixed(1)}/${c.certification_max}</span>
        </div>
        <div class="eff-comp-row" title="Средний % сдачи (≥ 70 баллов)">
          <span class="eff-comp-lbl">Успеваемость</span>
          <div class="eff-comp-bar">
            <div class="eff-comp-fill pass" style="width:${(c.pass_rate / c.pass_rate_max * 100).toFixed(0)}%"></div>
          </div>
          <span class="eff-comp-val">${c.pass_rate.toFixed(1)}/${c.pass_rate_max}</span>
        </div>
        <div style="margin-top:6px; padding-top:10px; border-top:1px solid var(--border); font-size:11px; color:var(--ink-3); line-height:1.5">
          ${eff.raw.activity_ratio}% записанных активны ·
          ${eff.raw.avg_certification_rate}% получают сертификат ·
          ${eff.raw.avg_pass_rate}% средняя сдача
        </div>
      </div>
    </div>
  `;
}

/* Преобразует "2025-07" в "07/25" — год не теряется */
function formatMonth(ym) {
  if (!ym || ym.length < 7) return ym || '';
  const yr = ym.slice(2, 4);
  const mo = ym.slice(5, 7);
  return mo + '/' + yr;
}

/* Преобразует "2025-07-15" в "MM-DD" + tooltip с полной датой */
function formatDayShort(d) {
  if (!d || d.length < 10) return d || '';
  return d.slice(5);
}

/* ═══ ИНТЕРАКТИВНЫЙ ФИЛЬТР СЕРТИФИКАТОВ ═══ */
function initCertFilter(filter) {
  if (!filter || !filter.issues) return;

  const $from = $('#filter-from');
  const $to = $('#filter-to');
  const $minCerts = $('#filter-min-certs');
  const $btn = $('#filter-courses-btn');
  const $list = $('#filter-courses-list');
  const $allCb = $('#filter-courses-all');
  const $search = $('#filter-courses-search');
  const courseCbs = () => Array.from(document.querySelectorAll('.filter-course-cb'));
  const $results = $('#filter-results');
  const $apply = $('#filter-apply');
  const $reset = $('#filter-reset');
  const $presets = Array.from(document.querySelectorAll('.fctrl-preset'));

  // Открытие/закрытие dropdown курсов
  $btn.addEventListener('click', (e) => {
    e.stopPropagation();
    $list.classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if (!$list.contains(e.target) && e.target !== $btn) $list.classList.remove('open');
  });

  // Поиск по курсам
  $search.addEventListener('input', () => {
    const q = $search.value.toLowerCase().trim();
    document.querySelectorAll('.fctrl-multi-item:not(.all)').forEach(item => {
      const name = item.dataset.name || '';
      item.style.display = (!q || name.includes(q)) ? '' : 'none';
    });
  });

  // "Все курсы" чекбокс
  $allCb.addEventListener('change', () => {
    courseCbs().forEach(cb => { cb.checked = $allCb.checked; });
    updateCoursesBtnLabel();
  });
  courseCbs().forEach(cb => cb.addEventListener('change', () => {
    const total = courseCbs().length;
    const checked = courseCbs().filter(c => c.checked).length;
    $allCb.checked = (checked === total);
    $allCb.indeterminate = (checked > 0 && checked < total);
    updateCoursesBtnLabel();
  }));

  function updateCoursesBtnLabel() {
    const total = courseCbs().length;
    const checked = courseCbs().filter(c => c.checked).length;
    if (checked === total) $btn.textContent = 'Все курсы (' + total + ')';
    else if (checked === 0) $btn.textContent = 'Не выбрано ни одного курса';
    else if (checked === 1) {
      const cb = courseCbs().find(c => c.checked);
      const lbl = cb.parentNode.querySelector('span').textContent.split('·')[0].trim();
      $btn.textContent = lbl;
    } else $btn.textContent = checked + ' из ' + total + ' выбрано';
  }

  // Пресеты периода
  $presets.forEach(p => p.addEventListener('click', () => {
    $presets.forEach(x => x.classList.remove('active'));
    p.classList.add('active');
    const preset = p.dataset.preset;
    if (preset === 'all') {
      $from.value = filter.min_date;
      $to.value = filter.max_date;
    } else {
      const days = parseInt(preset, 10);
      const end = new Date(filter.max_date);
      const start = new Date(filter.max_date);
      start.setDate(start.getDate() - days + 1);
      $from.value = start.toISOString().slice(0, 10);
      $to.value = filter.max_date;
      // не уйти за границу
      if ($from.value < filter.min_date) $from.value = filter.min_date;
    }
    apply();
  }));

  // Если меняют дату руками — снимаем активный пресет
  [$from, $to].forEach(el => el.addEventListener('change', () => {
    $presets.forEach(x => x.classList.remove('active'));
  }));

  $apply.addEventListener('click', apply);
  $minCerts.addEventListener('change', apply);

  $reset.addEventListener('click', () => {
    $from.value = filter.min_date;
    $to.value = filter.max_date;
    $minCerts.value = 0;
    courseCbs().forEach(cb => cb.checked = true);
    $allCb.checked = true;
    $allCb.indeterminate = false;
    $presets.forEach(x => x.classList.remove('active'));
    document.querySelector('.fctrl-preset[data-preset="all"]').classList.add('active');
    $search.value = '';
    document.querySelectorAll('.fctrl-multi-item:not(.all)').forEach(i => i.style.display = '');
    updateCoursesBtnLabel();
    apply();
  });

  // ─── Главная функция: применить фильтр ───
  function apply() {
    const fromStr = $from.value || filter.min_date;
    const toStr = $to.value || filter.max_date;
    const minCerts = parseInt($minCerts.value || '0', 10) || 0;

    const selected = new Set(courseCbs().filter(c => c.checked).map(c => parseInt(c.value, 10)));

    // Фильтруем выдачи сертификатов
    const filtered = filter.issues.filter(i => {
      if (i.date < fromStr || i.date > toStr) return false;
      if (!selected.has(i.course_id)) return false;
      return true;
    });

    // Группируем по курсам
    const byCourse = new Map();
    filtered.forEach(i => {
      if (!byCourse.has(i.course_id)) byCourse.set(i.course_id, { count: 0, users: new Set(), days: new Set() });
      const v = byCourse.get(i.course_id);
      v.count++;
      v.users.add(i.user_id);
      v.days.add(i.date);
    });

    const courseLookup = new Map(filter.courses.map(c => [c.course_id, c]));

    let courseRows = Array.from(byCourse.entries()).map(([cid, v]) => {
      const c = courseLookup.get(cid) || { course_name: '—' };
      return {
        course_id: cid,
        course_name: c.course_name,
        certs: v.count,
        users: v.users.size,
        days: v.days.size,
      };
    }).filter(r => r.certs >= minCerts);

    courseRows.sort((a, b) => b.certs - a.certs);

    // Динамика по дням (для всех выбранных курсов)
    const byDay = new Map();
    filtered.forEach(i => byDay.set(i.date, (byDay.get(i.date) || 0) + 1));

    // Заполняем нулями пустые даты
    const dayList = [];
    const start = new Date(fromStr), end = new Date(toStr);
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const ds = d.toISOString().slice(0, 10);
      dayList.push({ date: ds, count: byDay.get(ds) || 0 });
    }

    const totalCerts = filtered.length;
    const uniqueUsers = new Set(filtered.map(i => i.user_id)).size;
    const activeDays = byDay.size;
    const activeCourses = byCourse.size;

    // ─── РЕНДЕР РЕЗУЛЬТАТА ───
    if (totalCerts === 0) {
      $results.innerHTML = `
        <div class="fres-summary">
          <div class="fres-cell"><div class="fres-lbl">Сертификатов</div><div class="fres-val">0</div></div>
          <div class="fres-cell"><div class="fres-lbl">Уникальных польз.</div><div class="fres-val">0</div></div>
          <div class="fres-cell"><div class="fres-lbl">Активных курсов</div><div class="fres-val">0</div></div>
          <div class="fres-cell"><div class="fres-lbl">Дней с выдачей</div><div class="fres-val">0</div></div>
        </div>
        <div class="fres-empty">Нет сертификатов, удовлетворяющих условиям фильтра.<br>Попробуйте расширить период или выбрать больше курсов.</div>
      `;
      return;
    }

    const periodDays = Math.round((new Date(toStr) - new Date(fromStr)) / 86400000) + 1;
    const avgPerDay = (totalCerts / periodDays).toFixed(1);

    $results.innerHTML = `
      <div class="fres-summary">
        <div class="fres-cell">
          <div class="fres-lbl">Сертификатов выдано</div>
          <div class="fres-val">${fmt(totalCerts)}</div>
          <div class="fres-sub">в среднем ${avgPerDay}/день</div>
        </div>
        <div class="fres-cell">
          <div class="fres-lbl">Уникальных пользователей</div>
          <div class="fres-val">${fmt(uniqueUsers)}</div>
          <div class="fres-sub">${(totalCerts / uniqueUsers).toFixed(2)} серт./польз.</div>
        </div>
        <div class="fres-cell">
          <div class="fres-lbl">Активных курсов</div>
          <div class="fres-val">${fmt(activeCourses)}</div>
          <div class="fres-sub">из ${selected.size} выбранных</div>
        </div>
        <div class="fres-cell">
          <div class="fres-lbl">Дней с активностью</div>
          <div class="fres-val">${fmt(activeDays)}</div>
          <div class="fres-sub">из ${periodDays} дней периода</div>
        </div>
      </div>

      <div class="grid-2-1" style="margin:0">
        <div class="panel" style="border:1px solid var(--border)">
          <div class="panel-head">
            <h3>Динамика по дням</h3>
            <span class="tag">${fromStr} → ${toStr}</span>
          </div>
          <div class="panel-body"><div id="filter-chart-days" class="chart-wrap"></div></div>
        </div>
        <div class="panel" style="border:1px solid var(--border)">
          <div class="panel-head">
            <h3>По курсам · топ ${Math.min(courseRows.length, 30)}</h3>
            <span class="tag">${courseRows.length} курсов</span>
          </div>
          <div class="fres-table">
            ${courseRows.length ? `
            <table>
              <thead>
                <tr>
                  <th>Курс</th>
                  <th class="n">Серт.</th>
                  <th class="n">Польз.</th>
                  <th class="n">Дней</th>
                </tr>
              </thead>
              <tbody>
                ${courseRows.slice(0, 30).map(r => `
                  <tr>
                    <td title="${r.course_name}">${(r.course_name || '').length > 40 ? (r.course_name.slice(0, 40) + '…') : (r.course_name || '—')}</td>
                    <td class="n"><b>${fmt(r.certs)}</b></td>
                    <td class="n">${fmt(r.users)}</td>
                    <td class="n">${fmt(r.days)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
            ` : '<div class="fres-empty">Нет курсов с минимум ' + minCerts + ' сертификатов в этом периоде.</div>'}
          </div>
        </div>
      </div>
    `;

    // график динамики по дням
    if (dayList.length > 1) {
      drawLine($('#filter-chart-days'),
        dayList.map(d => ({
          label: formatDayShort(d.date),
          v: d.count,
          tooltip: d.date + ': ' + fmt(d.count) + ' серт.'
        })),
        { stroke: CLR.success, fill: 'rgba(15,153,96,0.10)', height: 220 });
    } else if (dayList.length === 1) {
      $('#filter-chart-days').innerHTML = `<div style="padding:30px; text-align:center; font-family:'IBM Plex Mono',monospace; font-size:18px">${dayList[0].date}: <b>${fmt(dayList[0].count)}</b> серт.</div>`;
    }
  }

  // первоначальный рендер
  apply();
}


function renderFunnel() {
  const f = D.funnel;
  const topN = f[0].count || 1;
  const colors = [CLR.ink1, CLR.info, CLR.success, CLR.accent, CLR.warn, CLR.primary];
  const rowsHtml = f.map((r, i) => {
    const widthPct = (r.count / topN) * 100;
    const conversion = i > 0 ? (r.count / f[i - 1].count * 100) : 100;
    const total = (r.count / topN * 100);
    const drop = i > 0 ? (f[i - 1].count - r.count) : 0;
    return `
      <div class="funnel-row">
        <span class="lbl">${r.stage}</span>
        <div class="bar-outer">
          <div class="bar-inner" style="width:${widthPct}%; background:${colors[i] || CLR.ink3}">
            ${r.count.toLocaleString('ru-RU')}
          </div>
        </div>
        <span class="pct">${total.toFixed(1)}%</span>
        <span class="drop">${i > 0 ? '−' + fmt(drop) : '—'}</span>
      </div>
    `;
  }).join('');

  $('#view-funnel').innerHTML = `
    <div class="section">
      <div class="section-head">
        <h2>Воронка вовлечения</h2>
        <span class="caption">Конверсия · ${f[0].count.toLocaleString('ru-RU')} на входе</span>
      </div>
      <div class="panel">
        <div class="mrow">
          <div class="m"><div class="l">Общая конверсия</div>
            <div class="v">${(f[f.length-1].count / f[0].count * 100).toFixed(1)}<span class="u">%</span></div></div>
          <div class="m"><div class="l">Отток №1 → №2</div>
            <div class="v">${fmt(f[0].count - f[1].count)}<span class="u">чел</span></div></div>
          <div class="m"><div class="l">Отток №2 → №3</div>
            <div class="v">${fmt(f[1].count - f[2].count)}<span class="u">чел</span></div></div>
          <div class="m"><div class="l">Доля окончивших</div>
            <div class="v">${(f[5].count / f[1].count * 100).toFixed(1)}<span class="u">%</span></div></div>
        </div>
        <div class="panel-body"><div class="funnel">${rowsHtml}</div></div>
      </div>
    </div>
  `;
}

function renderActivity() {
  $('#view-activity').innerHTML = `
    <div class="section">
      <div class="section-head"><h2>Активность платформы</h2><span class="caption">Временные паттерны</span></div>

      <div class="grid-2-1">
        <div class="panel">
          <div class="panel-head"><h3>Активные пользователи по дням</h3><span class="tag">${D.activity.daily.length} дней</span></div>
          <div class="panel-body"><div id="chart-dau" class="chart-wrap"></div></div>
        </div>
        <div class="panel">
          <div class="panel-head"><h3>По дням недели</h3><span class="tag">События</span></div>
          <div class="panel-body"><div id="chart-weekday" class="chart-wrap"></div></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h3>Тепловая карта: день × час</h3><span class="tag">Интенсивность</span></div>
        <div class="panel-body"><div id="chart-heatmap" class="chart-wrap"></div></div>
      </div>

      <div class="grid-2">
        <div class="panel">
          <div class="panel-head"><h3>По часам суток</h3><span class="tag">Распределение 24ч</span></div>
          <div class="panel-body"><div id="chart-hourly" class="chart-wrap"></div></div>
        </div>
        <div class="panel">
          <div class="panel-head"><h3>Уникальные пользователи по месяцам</h3><span class="tag">По месяцам</span></div>
          <div class="panel-body"><div id="chart-monthly-users" class="chart-wrap"></div></div>
        </div>
      </div>
    </div>
  `;

  drawLine($('#chart-dau'),
    D.activity.daily.map(d => ({
      label: formatDayShort(d.date),
      v: d.dau,
      tooltip: d.date + ': ' + fmt(d.dau) + ' DAU · ' + fmt(d.events) + ' событий'
    })),
    { stroke: CLR.info, fill: 'rgba(31,111,235,0.08)', height: 240 });

  drawBarV($('#chart-weekday'),
    D.activity.weekday.map(d => ({ label: d.day, v: d.events })),
    { color: (d, i) => i >= 5 ? CLR.primary : CLR.ink2, height: 240 });

  drawHeatmap($('#chart-heatmap'), D.activity.heatmap.matrix, { height: 180 });

  drawBarV($('#chart-hourly'),
    D.activity.hourly.map(d => ({ label: String(d.hour), v: d.events })),
    { color: (d, i) => (i >= 9 && i <= 12) ? CLR.accent : CLR.ink2, height: 240 });

  drawBarV($('#chart-monthly-users'),
    D.activity.monthly.map(m => ({
      label: formatMonth(m.month),
      v: m.active_users,
      tooltip: m.month + ': ' + fmt(m.active_users) + ' уникальных'
    })),
    { color: CLR.success, height: 240, tooltipSuffix: ' уникальных' });
}

function renderCourses() {
  const courses = D.courses.filter(c => c.students > 0);

  const tableRows = courses.map(c => {
    const gradeClass = c.avg_grade >= 70 ? 'good' : (c.avg_grade >= 50 ? 'warn' : 'bad');
    const certClass = c.certification_rate >= 50 ? 'good' : (c.certification_rate >= 25 ? 'warn' : 'bad');
    const healthClr = c.health_score >= 70 ? CLR.success : (c.health_score >= 40 ? CLR.warn : CLR.primary);
    return `
      <tr>
        <td class="truncate" title="${c.course_name}">${c.course_name || '—'}</td>
        <td class="n">${fmt(c.students)}</td>
        <td class="n">${fmt(c.active_users)}</td>
        <td class="n">${fmt(c.events)}</td>
        <td class="n">
          <span class="status ${certClass}">${fmt(c.certificates_issued)}</span>
          <span style="color:var(--ink-3); font-size:11px; margin-left:4px">${pct(c.certification_rate)}</span>
        </td>
        <td class="n"><span class="status ${gradeClass}">${pct(c.avg_grade)}</span></td>
        <td class="n">${pct(c.pass_rate)}</td>
        <td>
          <div class="bar-cell">
            <div class="track"><div class="fill" style="width:${c.health_score}%; background:${healthClr}"></div></div>
            <span class="num">${c.health_score}</span>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  $('#view-courses').innerHTML = `
    <div class="section">
      <div class="section-head"><h2>Курсы</h2><span class="caption">${courses.length} активных курсов</span></div>

      <div class="grid-2">
        <div class="panel">
          <div class="panel-head"><h3>Топ курсы — число студентов</h3><span class="tag">Топ 12</span></div>
          <div class="panel-body"><div id="chart-c-students" class="chart-wrap"></div></div>
        </div>
        <div class="panel">
          <div class="panel-head"><h3>Средние оценки по курсам</h3><span class="tag">% от максимума</span></div>
          <div class="panel-body"><div id="chart-c-grades" class="chart-wrap"></div></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head">
          <h3>Полная таблица курсов</h3>
          <span class="tag">${courses.length} строк · ${fmt(courses.reduce((s, c) => s + (c.certificates_issued || 0), 0))} сертификатов всего</span>
        </div>
        <div class="scroll-y">
          <table class="dt">
            <thead>
              <tr><th>Курс</th>
                  <th style="text-align:right">Записано</th>
                  <th style="text-align:right">Активных</th>
                  <th style="text-align:right">События</th>
                  <th style="text-align:right" title="Получили сертификат · % от записанных">Сертификаты</th>
                  <th style="text-align:right">Ср. оценка</th>
                  <th style="text-align:right">Доля сдачи</th>
                  <th>коэффициент эффективности</th></tr>
            </thead>
            <tbody>${tableRows}</tbody>
          </table>
        </div>
      </div>

      <div class="section">
        <div class="section-head"><h2>Состав активностей</h2><span class="caption">Типы модулей</span></div>
        <div class="grid-2">
          <div class="panel">
            <div class="panel-head"><h3>Распределение модулей по типам</h3><span class="tag">Количество</span></div>
            <div class="panel-body"><div id="chart-module-mix" class="chart-wrap"></div></div>
          </div>
          <div class="panel">
            <div class="panel-head"><h3>Индекс здоровья курса · диапазоны</h3><span class="tag">Распределение</span></div>
            <div class="panel-body"><div id="chart-health" class="chart-wrap"></div></div>
          </div>
        </div>
      </div>
    </div>
  `;

  drawBarH($('#chart-c-students'),
    courses.slice(0, 12).map(c => ({ label: c.course_name, v: c.students })),
    { labelW: 220, rowH: 22, color: CLR.ink2 });

  drawBarH($('#chart-c-grades'),
    courses.slice(0, 12).filter(c => c.grade_count > 0)
      .map(c => ({ label: c.course_name, v: c.avg_grade })),
    { labelW: 220, rowH: 22, max: 100,
      color: d => d.v >= 70 ? CLR.success : d.v >= 50 ? CLR.warn : CLR.primary,
      valueFmt: v => pct(v) });

  drawBarV($('#chart-module-mix'),
    D.module_mix.map(m => ({ label: m.module_type, v: m.count })),
    { color: CLR.info });

  // Health histogram
  const bins = [0, 20, 40, 60, 80, 100];
  const binData = bins.slice(0, -1).map((b, i) => ({
    label: `${b}-${bins[i+1]}`,
    v: courses.filter(c => c.health_score >= b && c.health_score < bins[i+1] + 0.01).length,
  }));
  drawBarV($('#chart-health'),
    binData,
    { color: (d, i) => i < 2 ? CLR.primary : i < 3 ? CLR.warn : CLR.success });
}

function renderAssessments() {
  const S = D.quiz_overview.summary;
  const g = D.grade_distribution;
  const dur = D.duration_distribution;

  $('#view-assessments').innerHTML = `
    <div class="section">
      <div class="section-head"><h2>Тесты и оценки</h2><span class="caption">Assessments overview</span></div>

      <div class="panel" style="margin-bottom:24px">
        <div class="mrow">
          <div class="m"><div class="l">Всего попыток</div><div class="v">${fmt(S.total)}</div></div>
          <div class="m"><div class="l">Завершены</div><div class="v">${fmt(S.finished)}<span class="u">/ ${fmt(S.total)}</span></div></div>
          <div class="m"><div class="l">В процессе</div><div class="v">${fmt(S.in_progress)}</div></div>
          <div class="m"><div class="l">Ср. время</div><div class="v">${S.avg_duration_min.toFixed(1)}<span class="u">мин</span></div></div>
          <div class="m"><div class="l">Ср. оценка</div><div class="v">${g.mean ? pct(g.mean) : '—'}</div></div>
        </div>
      </div>

      <div class="grid-2">
        <div class="panel">
          <div class="panel-head"><h3>Распределение оценок</h3><span class="tag">Гистограмма · σ = ${g.std}</span></div>
          <div class="panel-body"><div id="chart-grade-dist" class="chart-wrap"></div></div>
        </div>
        <div class="panel">
          <div class="panel-head"><h3>Время прохождения тестов</h3><span class="tag">Длительность · ср. ${dur.avg} мин</span></div>
          <div class="panel-body"><div id="chart-duration" class="chart-wrap"></div></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h3>Оценки по типам модулей</h3><span class="tag">Эффективность по типам</span></div>
        <div class="panel-body">
          ${D.grades_by_module.map(m => `
            <div class="dist-item">
              <span class="dlabel"><strong>${m.module_type || '—'}</strong> · ${fmt(m.n)} оценок</span>
              <span class="n">${pct(m.avg_grade)}</span>
              <span class="n"><span class="status ${m.pass_rate >= 70 ? 'good' : 'warn'}">сдача ${pct(m.pass_rate)}</span></span>
            </div>
          `).join('')}
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h3>Топ тестов по числу попыток</h3><span class="tag">Топ 15</span></div>
        <div class="panel-body"><div id="chart-quizzes" class="chart-wrap"></div></div>
      </div>
    </div>
  `;

  drawBarV($('#chart-grade-dist'),
    g.bins.map((b, i) => ({ label: b, v: g.counts[i] })),
    { color: (d, i) => {
        if (i < 3) return CLR.primary;
        if (i < 6) return CLR.warn;
        return CLR.success;
      },
      tooltipSuffix: ' оценок' });

  drawBarV($('#chart-duration'),
    dur.bins.map((b, i) => ({ label: b, v: dur.counts[i] })),
    { color: CLR.info });

  drawBarH($('#chart-quizzes'),
    D.quiz_overview.per_quiz.slice(0, 15).map(q => ({
      label: q.quiz_name || `Quiz ${q.quiz_id}`,
      v: q.attempts,
    })),
    { labelW: 240, rowH: 22, color: CLR.ink2 });
}

function renderQuestions() {
  const dd = D.difficulty_distribution;
  const pq = D.problematic_questions || [];
  const qd = D.question_difficulty || [];

  // Strip HTML from question names
  const stripHtml = s => (s || '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();

  const rowsHtml = pq.slice(0, 20).map(q => {
    const cls = q.correct_rate < 30 ? 'bad' : q.correct_rate < 50 ? 'warn' : 'good';
    return `
      <tr>
        <td class="truncate" title="${stripHtml(q.question_name)}">${stripHtml(q.question_name).slice(0, 90) || '—'}</td>
        <td class="n">${q.qtype || '—'}</td>
        <td class="n">${fmt(q.attempts)}</td>
        <td class="n">${fmt(q.unique_users)}</td>
        <td class="n"><span class="status ${cls}">${pct(q.correct_rate)}</span></td>
        <td class="n">${pct(q.giveup_rate)}</td>
      </tr>
    `;
  }).join('');

  $('#view-questions').innerHTML = `
    <div class="section">
      <div class="section-head"><h2>Сложность вопросов</h2><span class="caption">Анализ вопросов · ${qd.length} вопросов</span></div>

      <div class="panel">
        <div class="panel-head"><h3>Распределение по сложности</h3><span class="tag">${dd.total_questions || 0} вопросов</span></div>
        <div class="panel-body"><div id="chart-diff-dist" class="chart-wrap"></div></div>
      </div>

      <div class="panel">
        <div class="panel-head"><h3>Самые проблемные вопросы</h3><span class="tag">Топ-20 по ошибкам</span></div>
        <div class="scroll-y">
          <table class="dt">
            <thead><tr><th>Формулировка</th><th style="text-align:right">Тип</th>
              <th style="text-align:right">Попыток</th><th style="text-align:right">Уник. польз.</th>
              <th style="text-align:right">% верных</th><th style="text-align:right">% сдался</th></tr></thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  drawBarV($('#chart-diff-dist'),
    dd.labels.map((l, i) => ({ label: l.split(' ')[0], v: dd.counts[i] })),
    { color: (d, i) => i === 0 ? CLR.primary : i === 1 ? CLR.warn : i === 4 ? CLR.ink5 : CLR.success });
}

function renderCohorts() {
  const ret = D.cohort_retention;
  const cmp = D.cohort_comparison || [];
  const wr = D.weekly_retention || [];

  // Матрица удержания — таблица
  const periods = ret.max_periods;
  let headCells = '<th style="text-align:left">Когорта</th><th>Размер</th>';
  for (let p = 0; p < periods; p++) headCells += `<th>мес+${p}</th>`;

  const rowsHtml = ret.matrix.map(row => {
    let cells = `<td class="label-cell">${row.cohort}</td><td class="val">${fmt(row.size)}</td>`;
    row.values.forEach(v => {
      const r = v.retention;
      const bg = r === 0 ? 'transparent' : `rgba(15, 153, 96, ${Math.min(0.9, r/100 * 1.2)})`;
      const clr = r > 40 ? '#fff' : CLR.ink2;
      cells += `<td class="val" style="background:${bg}; color:${clr}" title="${v.users} чел · ${r}%">${r > 0 ? r.toFixed(0) : '—'}</td>`;
    });
    return `<tr>${cells}</tr>`;
  }).join('');

  $('#view-cohorts').innerHTML = `
    <div class="section">
      <div class="section-head"><h2>Когортный анализ</h2><span class="caption">${ret.cohorts.length} когорт · ${periods} периодов</span></div>

      <div class="panel" style="margin-bottom:20px">
        <div class="panel-head"><h3>Матрица удержания</h3><span class="tag">% возврата когорты через N месяцев</span></div>
        <div class="panel-body" style="overflow-x:auto">
          <table class="cohort-table" style="width:100%">
            <thead><tr>${headCells}</tr></thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
      </div>

      <div class="grid-2">
        <div class="panel">
          <div class="panel-head"><h3>Удержание по неделям</h3><span class="tag">% активных через N недель</span></div>
          <div class="panel-body"><div id="chart-wr" class="chart-wrap"></div></div>
        </div>
        <div class="panel">
          <div class="panel-head"><h3>Сравнение когорт</h3><span class="tag">Средние показатели</span></div>
          <div class="panel-body" style="padding:0">
            <table class="dt">
              <thead><tr><th>Когорта</th>
                <th style="text-align:right">Польз.</th>
                <th style="text-align:right">Ср. оценка</th>
                <th style="text-align:right">Ср. заверш.</th>
                <th style="text-align:right">Ср. событий</th></tr></thead>
              <tbody>
                ${cmp.map(c => `
                  <tr>
                    <td><strong>${c.cohort}</strong></td>
                    <td class="n">${fmt(c.users)}</td>
                    <td class="n">${pct(c.avg_grade)}</td>
                    <td class="n">${c.avg_completions.toFixed(1)}</td>
                    <td class="n">${fmt(Math.round(c.avg_events))}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  `;

  drawBarV($('#chart-wr'),
    wr.map(w => ({ label: `нед${w.week}`, v: w.retention })),
    { color: (d, i) => i === 0 ? CLR.ink1 : CLR.info, tooltipSuffix: '%' });
}

function renderEngagement() {
  const e = D.engagement;
  const top = e.top_students || [];

  const rowsHtml = top.slice(0, 30).map((s, i) => {
    const cls = i === 0 ? 'top-1' : i === 1 ? 'top-2' : i === 2 ? 'top-3' : '';
    const barClr = s.engagement_score >= 70 ? CLR.success : s.engagement_score >= 40 ? CLR.info : CLR.warn;
    const org = s.organization && s.organization !== 'Физ. лицо' ? s.organization : '';
    return `
      <tr>
        <td><span class="rank ${cls}">${i + 1}</span></td>
        <td><strong>${s.full_name || '—'}</strong></td>
        <td class="org-cell" title="${org}">${org || '<span style="color:var(--ink-3)">—</span>'}</td>
        <td class="n">${fmt(s.events)}</td>
        <td class="n">${fmt(s.active_days)}</td>
        <td class="n">${fmt(s.completions)}</td>
        <td class="n">${fmt(s.quizzes_done)}</td>
        <td class="n">${pct(s.avg_grade)}</td>
        <td>
          <div class="bar-cell">
            <div class="track"><div class="fill" style="width:${s.engagement_score}%; background:${barClr}"></div></div>
            <span class="num">${s.engagement_score}</span>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  $('#view-engagement').innerHTML = `
    <div class="section">
      <div class="section-head"><h2>Вовлечённость студентов</h2><span class="caption">Индекс вовлечённости · ${fmt(e.total_engaged)} активных</span></div>

      <div class="panel" style="margin-bottom:20px">
        <div class="mrow">
          ${e.distribution.map(d => `
            <div class="m">
              <div class="l">${d.class}</div>
              <div class="v">${fmt(d.count)}<span class="u">чел</span></div>
            </div>
          `).join('')}
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h3>Лидеры по индексу вовлечённости</h3><span class="tag">Топ 30</span></div>
        <div class="scroll-y">
          <table class="dt">
            <thead><tr><th>#</th><th>Студент</th>
              <th>Организация</th>
              <th style="text-align:right">События</th>
              <th style="text-align:right">Акт. дней</th>
              <th style="text-align:right">Завершено</th>
              <th style="text-align:right">Тестов</th>
              <th style="text-align:right">Ср. оценка</th>
              <th>Индекс</th></tr></thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

function renderRisk() {
  const r = D.at_risk;
  const active = r.active;
  const students = r.students_at_risk || [];

  const rowsHtml = students.slice(0, 40).map(s => {
    const statusCls = s.risk_status === 'never_active' ? 'bad' :
                      s.risk_status === 'inactive_30d' ? 'bad' : 'warn';
    const statusLbl = s.risk_status === 'never_active' ? 'НЕ ЗАХОДИЛ' :
                      s.risk_status === 'inactive_30d' ? '30+ ДН.' : '14 ДН.';
    const days = s.days_inactive && s.days_inactive > 0 ? fmt(Math.round(s.days_inactive)) : '—';
    const lastActive = s.last_active ? s.last_active.split(' ')[0] : 'никогда';
    const org = s.organization && s.organization !== 'Физ. лицо' ? s.organization : '';
    return `
      <tr>
        <td><strong>${s.full_name || '—'}</strong></td>
        <td class="org-cell" title="${org}">${org || '<span style="color:var(--ink-3)">—</span>'}</td>
        <td style="font-size:12px; color:var(--text-muted)">${s.email || '—'}</td>
        <td class="n">${fmt(s.courses_enrolled)}</td>
        <td class="n"><span class="status ${statusCls}">${statusLbl}</span></td>
        <td class="n">${days}</td>
        <td class="n" style="font-family:'IBM Plex Mono',monospace;font-size:12px">${lastActive}</td>
      </tr>
    `;
  }).join('');

  const total = r.total_enrolled;
  const activeP = (active / total * 100).toFixed(1);
  const warnP = (r.inactive_14d / total * 100).toFixed(1);
  const badP = (r.inactive_30d / total * 100).toFixed(1);
  const neverP = (r.never_active / total * 100).toFixed(1);

  $('#view-risk').innerHTML = `
    <div class="section">
      <div class="section-head"><h2>Риск отсева</h2><span class="caption">Раннее оповещение · ${fmt(total)} записанных</span></div>

      <div class="kpi-grid">
        <div class="kpi">
          <div class="label">Активные</div>
          <div class="value">${fmt(active)}</div>
          <div class="sub">${activeP}% от записанных</div>
          <span class="trend up">АКТИВНЫЕ</span>
        </div>
        <div class="kpi">
          <div class="label">Неактивны 14+ дней</div>
          <div class="value">${fmt(r.inactive_14d)}</div>
          <div class="sub">${warnP}% — внимание</div>
          <span class="trend warn">ВНИМАНИЕ</span>
        </div>
        <div class="kpi">
          <div class="label">Неактивны 30+ дней</div>
          <div class="value">${fmt(r.inactive_30d)}</div>
          <div class="sub">${badP}% — высокий риск</div>
          <span class="trend down">РИСК</span>
        </div>
        <div class="kpi">
          <div class="label">Никогда не заходили</div>
          <div class="value">${fmt(r.never_active)}</div>
          <div class="sub">${neverP}% — онбординг не случился</div>
          <span class="trend down">КРИТИЧНО</span>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h3>Распределение по статусу</h3><span class="tag">Доли</span></div>
        <div class="panel-body">
          <div id="chart-risk-pie" class="chart-wrap"></div>
        </div>
      </div>

      <div class="panel" style="margin-top:20px">
        <div class="panel-head"><h3>Студенты в зоне риска</h3><span class="tag">Приоритетный список</span></div>
        <div class="scroll-y">
          <table class="dt">
            <thead><tr><th>Студент</th>
              <th>Организация</th>
              <th>Email</th>
              <th style="text-align:right">Курсов</th><th style="text-align:right">Статус</th>
              <th style="text-align:right">Дней без активности</th><th style="text-align:right">Последний заход</th></tr></thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  drawBarV($('#chart-risk-pie'),
    [
      { label: 'Активные', v: active },
      { label: '14+ дн', v: r.inactive_14d },
      { label: '30+ дн', v: r.inactive_30d },
      { label: 'Never', v: r.never_active },
    ],
    { color: (d, i) => [CLR.success, CLR.warn, CLR.primary, CLR.ink4][i], height: 200 });
}

// ═══════════════════════════════════════════════════════════════
// ROUTER
// ═══════════════════════════════════════════════════════════════
const VIEWS = {
  overview: { title: 'Главная', render: renderOverview },
  funnel: { title: 'Воронка вовлечения', render: renderFunnel },
  activity: { title: 'Активность платформы', render: renderActivity },
  courses: { title: 'Курсы', render: renderCourses },
  assessments: { title: 'Тесты и оценки', render: renderAssessments },
  questions: { title: 'Сложность вопросов', render: renderQuestions },
  cohorts: { title: 'Когортный анализ', render: renderCohorts },
  engagement: { title: 'Вовлечённость', render: renderEngagement },
  risk: { title: 'Риск отсева', render: renderRisk },
};

const rendered = new Set();
function navigate(key) {
  $$('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.view === key));
  $$('.view').forEach(v => v.classList.toggle('active', v.id === 'view-' + key));
  $('#page-title').textContent = VIEWS[key].title;

  if (!rendered.has(key)) {
    VIEWS[key].render();
    rendered.add(key);
  }
}

$$('.nav-item').forEach(n => {
  n.addEventListener('click', () => navigate(n.dataset.view));
});

// Initial render
renderOverview();
rendered.add('overview');

// Re-render on resize (throttled)
let resizeTO;
window.addEventListener('resize', () => {
  clearTimeout(resizeTO);
  resizeTO = setTimeout(() => {
    rendered.clear();
    const active = $$('.nav-item.active')[0];
    if (active) {
      const key = active.dataset.view;
      // Force re-render
      $('#view-' + key).innerHTML = '';
      VIEWS[key].render();
      rendered.add(key);
    }
  }, 200);
});
</script>
</body>
</html>
"""


def generate(report_path: Path, output_path: Path):
    """Строит HTML-дашборд из JSON-отчёта."""
    with open(report_path, "r", encoding="utf-8") as f:
        data_json = f.read()

    report = json.loads(data_json)

    # Метаданные для шапки
    kpi = report.get("kpis", {})
    period_start = (kpi.get("period_start") or "").split(" ")[0]
    period_end = (kpi.get("period_end") or "").split(" ")[0]
    period_label = f"{period_start} — {period_end}" if period_start else "—"

    from datetime import datetime
    last_etl = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = (HTML_TEMPLATE
            .replace("__DATA_JSON__", data_json)
            .replace("__PERIOD_START__", period_start or "—")
            .replace("__PERIOD_END__", period_end or "—")
            .replace("__PERIOD_LABEL__", period_label)
            .replace("__LAST_ETL__", last_etl))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Дашборд сохранён: {output_path}")
    print(f"Размер: {output_path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    DATA_DIR = Path(__file__).parent.parent / "data"
    generate(DATA_DIR / "report.json", DASHBOARD_DIR / "index.html")
