"""Wind-farm outage energy-loss estimator - Streamlit GUI.

Run:  streamlit run app.py
All modelling logic lives in src/; this file only handles interaction and display.
"""
from __future__ import annotations

import glob
import io
import os
import urllib.parse
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src import data_loader as dl
from src import data_validation as dv
from src import feature_engineering as fe
from src import model_training as mt
from src import outage_detection as od
from src import pipeline as pl
from src import reporting as rp
from src import user_guide as ug
from src.energy_calculation import totals
from src.model_evaluation import errors_by_speed_bin, energy_deviation
from src.power_curve import PowerCurve, PowerCurveError

ROOT = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(ROOT, "sample_data")

# ---------------------------------------------------------------- look & feel (light, minimal)
# Chart colours keep their meaning everywhere: blue = measured, orange = reconstructed, green = references.
C_OBS = "#2a78d6"
C_PRED = "#eb6834"
C_REF = "#1baf7a"
C_BAND = "rgba(235,104,52,0.16)"
C_OUTAGE = "rgba(100,116,139,0.10)"
INK = "#1F2937"
MUTED = "#6B7280"
GRID = "#EEF0F3"
AXIS = "#D1D5DB"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]

st.set_page_config(page_title="Outage Energy-Loss Estimator", page_icon="🌬️", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container {padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1280px;}
header[data-testid="stHeader"] {background: transparent;}
h1 {font-size: 1.65rem !important; font-weight: 700 !important; letter-spacing: -0.015em;
    color: #111827 !important; padding-bottom: 0 !important;}
.app-sub {color:#6B7280; font-size:.98rem; margin:.15rem 0 .9rem 0; max-width: 820px;}

/* progress stepper */
.stepper {display:flex; align-items:center; gap:.4rem; flex-wrap:wrap; margin:.2rem 0 1.1rem 0;}
.stp {display:flex; align-items:center; gap:.45rem; padding:.28rem .8rem .28rem .32rem; border-radius:999px;
      border:1px solid #E5E7EB; background:#FFFFFF; font-size:.84rem; color:#6B7280; white-space:nowrap;}
.stp .n {width:1.35rem; height:1.35rem; border-radius:50%; display:inline-flex; align-items:center;
         justify-content:center; font-size:.74rem; font-weight:700; background:#F3F4F6; color:#6B7280;}
.stp.done {color:#065F46; border-color:#D1FAE5; background:#F0FDF4;}
.stp.done .n {background:#10B981; color:#FFFFFF;}
.stp.now {color:#1E40AF; border-color:#BFDBFE; background:#EFF6FF; font-weight:600;}
.stp.now .n {background:#2563EB; color:#FFFFFF;}
.stp-sep {width:14px; height:1px; background:#E5E7EB;}

/* cards */
.kpi {background:#FFFFFF; border:1px solid #E5E7EB; border-radius:12px; padding:1rem 1.15rem; height:100%;}
.kpi .l {color:#6B7280; font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em;}
.kpi .v {font-size:1.5rem; font-weight:700; color:#111827; margin-top:.3rem; line-height:1.2;}
.kpi .s {color:#6B7280; font-size:.84rem; margin-top:.25rem; line-height:1.35;}
.kpi.accent {background:#EFF6FF; border-color:#BFDBFE;}
.kpi.accent .v {color:#1D4ED8; font-size:1.75rem;}

/* headings, notes */
.sec {margin:1.8rem 0 .55rem 0;}
.sec .t {font-size:1.08rem; font-weight:700; color:#111827;}
.sec .d {font-size:.9rem; color:#6B7280; margin-top:.1rem;}
.ctitle {font-size:.9rem; font-weight:600; color:#374151; margin:.5rem 0 -.35rem 0;}
.note {background:#F8FAFC; border:1px solid #EEF0F3; border-radius:10px; padding:.7rem .95rem;
       color:#4B5563; font-size:.9rem; line-height:1.45;}
.next {margin-top:2rem; padding:.8rem 1.05rem; border-radius:10px; border:1px dashed #CBD5E1;
       color:#475569; font-size:.92rem; background:#FBFCFE;}
.next b {color:#1E40AF;}
.check {display:flex; flex-direction:column; gap:.4rem; margin:.2rem 0 1rem 0;}
.ci {font-size:.93rem; color:#374151;}
.ci .ok {color:#059669; font-weight:700;} .ci .no {color:#DC2626; font-weight:700;} .ci .wa {color:#D97706; font-weight:700;}
.empty {text-align:center; padding:3.2rem 1rem; border:1px dashed #E5E7EB; border-radius:14px;
        color:#6B7280; background:#FCFCFD; margin-top:.5rem;}
.empty .t {font-size:1.05rem; font-weight:600; color:#374151; margin-bottom:.35rem;}
.welcome {display:grid; grid-template-columns:repeat(3, 1fr); gap:1rem; margin:1rem 0 1.4rem 0;}
.wc {border:1px solid #E5E7EB; border-radius:12px; padding:1.1rem 1.2rem; background:#FFFFFF;}
.wc .n {font-size:.75rem; font-weight:700; color:#2563EB; letter-spacing:.06em; text-transform:uppercase;}
.wc .t {font-size:1.02rem; font-weight:650; color:#111827; margin:.25rem 0 .2rem 0;}
.wc .d {font-size:.88rem; color:#6B7280; line-height:1.4;}
@media (max-width: 800px) {.welcome {grid-template-columns:1fr;}}

/* tabs, expanders, sidebar */
div[data-baseweb="tab-list"] {gap:.15rem; border-bottom:1px solid #E5E7EB;}
button[data-baseweb="tab"] {padding:.55rem .95rem;}
button[data-baseweb="tab"] p {font-size:.95rem; font-weight:500;}
div[data-testid="stExpander"] details {border-color:#EEF0F3; border-radius:10px; background:#FFFFFF;}
div[data-testid="stExpander"] summary p {font-weight:600; color:#374151; font-size:.93rem;}
section[data-testid="stSidebar"] .brand {font-size:1.08rem; font-weight:700; color:#111827; margin-bottom:.1rem;}
section[data-testid="stSidebar"] .side-h {font-size:.72rem; font-weight:700; color:#6B7280;
     text-transform:uppercase; letter-spacing:.07em; margin:1.1rem 0 .3rem 0;}
</style>""", unsafe_allow_html=True)


def layout(fig, h=360, ytitle=None):
    """Clean light chart style. Titles are written above the chart (see `chart`), so legends never collide."""
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=36, b=8), title=None,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(size=12, color="#374151"),
                      legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom", bgcolor="rgba(0,0,0,0)",
                                  font=dict(size=12, color="#4B5563")),
                      hovermode="x unified",
                      hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E5E7EB", font=dict(color=INK)))
    fig.update_xaxes(showgrid=False, linecolor=AXIS, tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=AXIS, tickfont=dict(color=MUTED),
                     title_font=dict(color=MUTED), title=ytitle)
    return fig


def chart(fig, title=None, where=None):
    where = where or st
    if title:
        where.markdown(f'<div class="ctitle">{title}</div>', unsafe_allow_html=True)
    where.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def kpi(col, label, value, sub="", accent=False):
    col.markdown(f'<div class="kpi{" accent" if accent else ""}"><div class="l">{label}</div>'
                 f'<div class="v">{value}</div><div class="s">{sub}</div></div>', unsafe_allow_html=True)


def section(title, desc=None, where=None):
    (where or st).markdown(f'<div class="sec"><div class="t">{title}</div>'
                           + (f'<div class="d">{desc}</div>' if desc else "") + "</div>", unsafe_allow_html=True)


def note(text, where=None):
    (where or st).markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)


def next_step(text, where=None):
    (where or st).markdown(f'<div class="next">→ <b>Next:</b> {text}</div>', unsafe_allow_html=True)


def empty_state(title, text):
    st.markdown(f'<div class="empty"><div class="t">{title}</div>{text}</div>', unsafe_allow_html=True)


def help_box(prefix, label="How to use this tab"):
    body = ug.section(prefix)
    if body:
        with st.expander(label, expanded=False, icon=":material/help_outline:"):
            st.markdown(body)


def fmt(x, nd=0, unit=""):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    return f"{x:,.{nd}f}{unit}"


def stepper(done, now):
    names = ["Load data", "Confirm outage", "Review model", "Read energy loss", "Validate", "Export"]
    parts = []
    for i, nm in enumerate(names, start=1):
        cls = "done" if i in done else ("now" if i == now else "")
        mark = "✓" if i in done else str(i)
        parts.append(f'<div class="stp {cls}"><span class="n">{mark}</span>{nm}</div>')
    return '<div class="stepper">' + '<div class="stp-sep"></div>'.join(parts) + "</div>"


ss = st.session_state
ss.setdefault("results", None)
ss.setdefault("backtests", None)

# ---------------------------------------------------------------- sidebar: inputs
with st.sidebar:
    st.markdown('<div class="brand">🌬️ Energy-Loss Estimator</div>', unsafe_allow_html=True)
    st.caption("Reconstructs missing turbine wind speeds from other wind parks and estimates the lost energy.")
    st.markdown('<div class="side-h">Data</div>', unsafe_allow_html=True)
    source = st.radio("Data source", ["Demo data (hackathon sample)", "Upload my files"], index=0)
    ts_files, pc_files = [], []
    if source.startswith("Demo"):
        ts_files = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(SAMPLE_DIR, "*_data.*")))]
        pc_files = [(os.path.basename(f), f) for f in sorted(glob.glob(os.path.join(SAMPLE_DIR, "*_power_curve.*")))]
        st.caption(f"✓ {len(ts_files)} turbine files and {len(pc_files)} power curves loaded.")
    else:
        up = st.file_uploader("Wind data (one CSV per turbine, or one combined CSV)", type=["csv", "xlsx", "xls"],
                              accept_multiple_files=True)
        upc = st.file_uploader("Power curve(s) of the target turbine(s)", type=["csv", "xlsx", "xls"],
                               accept_multiple_files=True)
        ts_files = [(f.name, f.getvalue()) for f in (up or [])]
        pc_files = [(f.name, f.getvalue()) for f in (upc or [])]
    st.markdown('<div class="side-h">Options</div>', unsafe_allow_html=True)
    pc_unit = st.selectbox("Power-curve unit", ["kW", "MW", "W"], index=0,
                           help="The unit of the power column in the power-curve files.")
    zero_rule = st.checkbox("Treat sensor-fault zero records as missing", value=True,
                            help="Rows where wind speed, direction AND temperature are all exactly 0 are sensor "
                                 "faults, not calm wind. They are treated as missing.")
    st.markdown('<div class="side-h">Help</div>', unsafe_allow_html=True)
    with st.expander("What do these settings mean?"):
        st.markdown(ug.section("The sidebar"))
    st.caption("Work through the tabs from left to right: ① data → ② outage → ③ model → ④ energy → "
               "⑤ validation → ⑥ export. The 📖 tab holds the full user guide.")


def _src(obj):
    return io.BytesIO(obj) if isinstance(obj, (bytes, bytearray)) else obj


st.title("Wind-turbine outage: energy-yield loss estimator")
st.markdown('<div class="app-sub">Learn how wind at the affected turbine relates to turbines in other wind parks, '
            'reconstruct the missing wind speeds, and convert them to energy with the power curve.</div>',
            unsafe_allow_html=True)

if not ts_files:
    st.markdown("""
<div class="welcome">
 <div class="wc"><div class="n">Step 1</div><div class="t">Add your data</div>
  <div class="d">Upload the wind data of all turbines and the power curves of the affected ones in the sidebar
  — or switch to <b>Demo data</b> to try the tool.</div></div>
 <div class="wc"><div class="n">Step 2</div><div class="t">Confirm the outage</div>
  <div class="d">The tool finds the missing period itself. Check it, adjust if needed, and run the analysis.</div></div>
 <div class="wc"><div class="n">Step 3</div><div class="t">Read and share</div>
  <div class="d">See the estimated energy loss, check its accuracy, and download the report and insurance
  e-mail.</div></div>
</div>""", unsafe_allow_html=True)
    st.info("⬅ Choose **Demo data** or upload wind-data files in the sidebar to start.")
    section("Quick start")
    st.markdown(ug.section("Quick start"))
    with st.expander("📖 Full user guide"):
        st.markdown(ug.full_text())
    st.stop()

stepper_box = st.empty()
tabs = st.tabs(["① Data", "② Outage", "③ Model", "④ Wind & energy", "⑤ Validation", "⑥ Report & export",
                "📖 User guide"])

# ---------------------------------------------------------------- 📖 user guide (rendered first so it always works)
with tabs[6]:
    g1, g2 = st.columns([3, 1])
    g1.caption("Everything about the tool in one place. Each tab also has a *How to use this tab* box at the top.")
    g2.download_button("⬇ Download guide (Markdown)", ug.full_text().encode(), "USER_GUIDE.md", "text/markdown",
                       width="stretch")
    sec = ug.sections()
    jump = st.selectbox("Jump to section", ["Show everything"] + list(sec))
    if jump == "Show everything":
        st.markdown(ug.full_text())
    else:
        st.markdown(f"## {jump}\n\n{sec[jump]}")

# ---------------------------------------------------------------- ① data
with tabs[0]:
    help_box("Tab ①")
    kpi_area = st.container()
    select_area = st.container()
    overview_area = st.container()

    raw_tables = {}
    try:
        for name, obj in ts_files:
            raw_tables[name] = dl.read_table(_src(obj), name)
    except dl.DataLoadError as e:
        st.error(str(e))
        st.stop()

    # column mapping, grouped by schema (shown at the bottom: only needed for unusual files)
    schemas = {}
    for name, df in raw_tables.items():
        schemas.setdefault(tuple(df.columns), []).append(name)
    mappings, mapping_ok = {}, True
    any_problem = any(any(c not in dl.suggest_mapping(cols)[0] for c in dl.REQUIRED) for cols in schemas)
    with st.expander("Column mapping", expanded=any_problem):
        st.caption("Columns were recognised automatically. Check them, or fix any that are marked as needed.")
        for k, (cols, names) in enumerate(schemas.items()):
            sugg, amb = dl.suggest_mapping(cols)
            st.markdown(f"**{len(names)} file(s)** with columns: `{', '.join(map(str, cols))}`")
            mcols = st.columns(4)
            mp = {}
            for i, canon in enumerate(["timestamp", "wind_speed", "turbine", "wind_direction", "ambient_temperature",
                                       "air_pressure", "wind_speed_stddev", "test_set"]):
                opts = ["— not available —"] + list(cols)
                default = opts.index(sugg[canon]) if canon in sugg else 0
                req = canon in dl.REQUIRED
                label = canon.replace("_", " ") + (" *" if req else "")
                if canon in amb:
                    label += " ⚠ ambiguous"
                choice = mcols[i % 4].selectbox(label, opts, index=default, key=f"map{k}_{canon}")
                if choice != opts[0]:
                    mp[canon] = choice
            if any(c not in mp for c in dl.REQUIRED):
                st.error("Map the required columns (*) to continue.")
                mapping_ok = False
            for n in names:
                mappings[n] = mp
    if not mapping_ok:
        st.stop()

    @st.cache_data(show_spinner="Reading and checking data…")
    def load_and_prepare(file_items, maps, zero_rule_):
        log = dl.LoadLog()
        data = dl.load_timeseries_files([(n, _src(o)) for n, o in file_items], maps, log)
        return dv.prepare(data, zero_rule_), log.messages

    try:
        prep, load_msgs = load_and_prepare(tuple(ts_files), mappings, zero_rule)
    except (dl.DataLoadError, ValueError) as e:
        st.error(str(e))
        st.stop()

    curves, curve_errors = {}, []
    if pc_files:
        try:
            raw_curves = dl.load_power_curves([(n, _src(o)) for n, o in pc_files], pc_unit)
            for t, cdf in raw_curves.items():
                try:
                    curves[t] = PowerCurve.from_frame(cdf, t)
                except PowerCurveError as e:
                    curve_errors.append(str(e))
        except dl.DataLoadError as e:
            curve_errors.append(str(e))

    turbines = list(prep.wide["wind_speed"].columns)
    s = prep.summary
    with kpi_area:
        c1, c2, c3, c4 = st.columns(4)
        kpi(c1, "Turbines", len(turbines), f"{s['park'].nunique()} wind park(s)")
        kpi(c2, "Period", f"{(prep.wide['wind_speed'].index[-1] - prep.wide['wind_speed'].index[0]).days + 1} days",
            f"{prep.wide['wind_speed'].index[0]:%d %b %Y} – {prep.wide['wind_speed'].index[-1]:%d %b %Y}")
        kpi(c3, "Sampling interval", f"{int(prep.freq / pd.Timedelta(minutes=1))} min", "inferred from timestamps")
        kpi(c4, "Power curves", len(curves), ", ".join(curves) or "none uploaded")

    with select_area:
        section("Choose the turbines", "The affected turbines (targets) and the turbines in other wind parks used "
                                       "to fill their gap (references).")
        default_targets = [t for t in turbines if t in curves] or turbines[:1]
        cA, cB = st.columns([1, 2], gap="large")
        targets = cA.multiselect("Target turbine(s)", turbines, default=default_targets,
                                 help="Turbines whose missing wind speeds are reconstructed. Each needs a power curve.")
        if not targets:
            st.warning("Select at least one target turbine.")
            st.stop()
        elig_sets, enforced_all = [], True
        for t in targets:
            e, enf = pl.eligible_references(turbines, t)
            elig_sets.append(set(e) - set(targets))
            enforced_all &= enf
        eligible = sorted(set.intersection(*elig_sets)) if elig_sets else []
        refs = cB.multiselect("Reference turbines", eligible, default=eligible)
        if enforced_all:
            cB.caption(f"Only turbines from **other wind parks** are offered (park = leading letters of the name). "
                       f"Eligible: {', '.join(eligible) or 'none'}.")
        else:
            cB.warning("Wind-park membership could not be read from the turbine names. Please make sure every "
                       "selected reference is in a **different** wind park than the targets.")
        auto_refs = cB.checkbox("Let the tool pick the best subset of references automatically", value=False,
                                help="Greedy forward selection: references are added one by one while they improve "
                                     "the cross-validated error by at least 0.5%.")
        missing_curves = [t for t in targets if t not in curves]
        if missing_curves:
            st.error(f"No valid power curve for: {', '.join(missing_curves)}. Upload one per target turbine.")
        for msg in curve_errors:
            st.error(msg)
        if not refs:
            st.warning("Select at least one reference turbine.")

    with overview_area:
        section("Dataset summary", "One row per turbine. 'constant (not measured)' marks a filled-in placeholder "
                                   "(e.g. O-park air pressure); such variables are never used as predictors.")
        st.dataframe(s.style.format({"wind speed missing %": "{:.2f}", "mean wind speed (m/s)": "{:.2f}"}),
                     hide_index=True, width="stretch")
        q = prep.log.to_frame()
        if len(q) or load_msgs:
            with st.expander(f"Data-quality actions ({len(q)})", expanded=False):
                for lvl, m in load_msgs:
                    (st.warning if lvl == "warning" else st.info)(m)
                st.dataframe(q, hide_index=True, width="stretch")
        if curves:
            with st.expander("Power curves as interpreted"):
                fig = go.Figure()
                for i, (t, c) in enumerate(curves.items()):
                    fig.add_trace(go.Scatter(x=c.wind_speed, y=c.power_kw, name=t, mode="lines+markers",
                                             line=dict(width=2, color=SERIES[i % 8]), marker=dict(size=5)))
                chart(layout(fig, 300, ytitle="kW").update_xaxes(title="wind speed (m/s)"))
                st.dataframe(pd.DataFrame([c.describe() for c in curves.values()]), hide_index=True,
                             width="stretch")

ready_data = bool(targets) and bool(refs) and not missing_curves
ready = ready_data
ws_wide = prep.wide["wind_speed"]
idx = ws_wide.index

with tabs[0]:
    if ready_data:
        next_step("open <b>② Outage</b> to confirm the outage period and run the analysis.")

# ---------------------------------------------------------------- ② outage
with tabs[1]:
    help_box("Tab ②")
    period_area = st.container()
    adv = st.expander("Advanced analysis settings")
    run_area = st.container()

    with adv:
        a1, a2 = st.columns(2, gap="large")
        block_thr = a1.number_input("Minimum length of a missing *block* (intervals)", 2, 1000, 6,
                                    help="Shorter gaps are treated as isolated missing values, not as an outage.")
        scope = a1.radio("Training data", ["Only data before the outage (challenge setting)",
                                           "All measured data outside the outage (before and after)"], index=0,
                         help="After-the-fact claims often have data after the outage too; using it can help, "
                              "but the challenge specifies historical data before the outage.")
        group_mode = a1.radio("Input features", ["Automatic (validated forward selection)", "Choose manually"])
        man_groups = None
        if group_mode.startswith("Choose"):
            man_groups = a1.multiselect("Feature groups", fe.ALL_GROUPS, default=["wind_speed", "smoothed"],
                                        format_func=lambda g: fe.GROUP_LABELS[g])
        models = a2.multiselect("Candidate models", mt.CANDIDATES, default=mt.CANDIDATES)
        tol = a2.slider("Tolerance for 'equivalent' accuracy (%)", 0.0, 10.0, 2.0, 0.5,
                        help="Models within this % of the best CV RMSE are treated as equally accurate; "
                             "the simplest of them is selected.") / 100
        above = a2.radio("Wind above the end of the power curve", ["hold last power value", "assume shutdown (0 kW)"])
    cfg = pl.Config(training_scope="before_outage" if scope.startswith("Only") else "outside_outage",
                    feature_groups=man_groups if man_groups else "auto",
                    models=models or ["Ridge Regression"], tolerance=tol, auto_references=auto_refs,
                    above_policy="hold_last" if above.startswith("hold") else "zero")

    with period_area:
        run_tables, sugg = [], []
        for t in targets:
            st_, en_, runs = od.suggest_outage(ws_wide[t], ws_wide, refs, prep.freq, block_thr)
            runs = runs.assign(turbine=t)
            run_tables.append(runs)
            if st_ is not None:
                sugg.append((st_, en_))
        runs_all = pd.concat(run_tables, ignore_index=True) if run_tables else pd.DataFrame()
        section("Outage period", "Detected automatically from the missing target data — adjust it if you know the "
                                 "actual times.")
        if sugg:
            s0 = min(x[0] for x in sugg)
            e0 = max(x[1] for x in sugg)
            st.success(f"Detected outage: **{s0:%a %d %b %Y %H:%M} → {e0:%a %d %b %Y %H:%M}** "
                       f"({int((e0 - s0) / prep.freq) + 1} intervals). You can adjust it below.")
        else:
            s0, e0 = idx[-1] - pd.Timedelta(days=1), idx[-1]
            st.warning("No block of missing target data was found. Set the outage period manually.")

        c1, c2, c3, c4 = st.columns(4)
        sd = c1.date_input("Outage start date", s0.date(), min_value=idx[0].date(), max_value=idx[-1].date())
        stt = c2.time_input("start time", s0.time(), step=prep.freq.to_pytimedelta())
        ed = c3.date_input("Outage end date", e0.date(), min_value=idx[0].date(), max_value=idx[-1].date())
        ett = c4.time_input("end time (last interval)", e0.time(), step=prep.freq.to_pytimedelta())
        o_start, o_end = pd.Timestamp(datetime.combine(sd, stt)), pd.Timestamp(datetime.combine(ed, ett))
        period_ok = o_end >= o_start
        if not period_ok:
            st.error("The end must be after the start.")
            ready = False
        n_out = int(od.outage_mask(idx, o_start, o_end).sum())

        # timeline: availability strip + target wind
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.35, 0.65], vertical_spacing=0.05)
        show = targets + refs
        avail = ws_wide[show].notna().astype(float).replace(0, np.nan)
        for i, t in enumerate(show):
            col_t = C_OBS if t in targets else C_REF
            fig.add_trace(go.Scattergl(x=idx, y=np.where(avail[t].notna(), t, None), mode="lines",
                                       line=dict(width=5, color=col_t), opacity=.55, connectgaps=False,
                                       name=t, showlegend=False, hoverinfo="skip"), row=1, col=1)
        for i, t in enumerate(targets):
            fig.add_trace(go.Scattergl(x=idx, y=ws_wide[t], mode="lines", name=f"{t} measured",
                                       line=dict(width=1, color=SERIES[i % 8])), row=2, col=1)
        fig.add_vrect(x0=o_start, x1=o_end + prep.freq, fillcolor="rgba(235,104,52,.16)", line_width=0,
                      row=1, col=1)
        fig.add_vrect(x0=o_start, x1=o_end + prep.freq, fillcolor="rgba(235,104,52,.16)", line_width=0,
                      annotation_text="outage", annotation_position="top left",
                      annotation_font=dict(color=MUTED, size=11), row=2, col=1)
        layout(fig, 440)
        fig.update_yaxes(title="wind (m/s)", row=2, col=1)
        fig.update_yaxes(title="data present", row=1, col=1, showgrid=False)
        chart(fig, "Data timeline")
        st.caption("Top: a bar where a turbine has wind measurements (gaps = missing; blue = targets, green = references). Bottom: measured target "
                   "wind speed. Shaded: selected outage.")

        cc1, cc2 = st.columns(2, gap="large")
        any_ref = None
        with cc1:
            st.markdown('<div class="ctitle">Reference data during the selected outage</div>',
                        unsafe_allow_html=True)
            st.write("")
            if refs:
                ra = od.reference_availability(ws_wide, refs, o_start, o_end)
                st.dataframe(ra, hide_index=True, width="stretch")
                any_ref = ra.attrs["any_reference_%"]
        with cc2:
            st.markdown('<div class="ctitle">Missing-data runs in the target turbine(s)</div>',
                        unsafe_allow_html=True)
            st.write("")
            if not runs_all.empty:
                view = runs_all[runs_all["kind"] == "block"]
                st.dataframe(view, hide_index=True, width="stretch")
                n_iso = int((runs_all["kind"] == "isolated").sum())
                st.caption(f"Plus {n_iso} short isolated gap(s). Gaps outside the outage stay missing and are "
                           "excluded from training — they are never treated as zero wind.")
        st.write("")
        note("A missing measurement is <b>not</b> proof the turbine stopped. The energy estimate assumes the turbine "
             "would have run normally on its power curve during the selected period.")

    with run_area:
        section("Ready to run?", "A quick check before the analysis starts (about 20 s per turbine).")

        def _ci(ok, text, warn=False):
            cls, mark = ("ok", "✓") if ok else (("wa", "!") if warn else ("no", "✕"))
            return f'<div class="ci"><span class="{cls}">{mark}</span>&nbsp; {text}</div>'

        items = [
            _ci(bool(targets) and not missing_curves,
                f"Target turbine(s): {', '.join(targets)}" + ("" if not missing_curves else
                                                              f" — power curve missing for {', '.join(missing_curves)}")),
            _ci(bool(refs), f"Reference turbines: {', '.join(refs)}" if refs else "No reference turbine selected"),
            _ci(period_ok and n_out > 0,
                f"Outage period: {n_out} intervals ({n_out * prep.freq / pd.Timedelta(hours=1):,.1f} h)"
                if period_ok else "Outage period: the end is before the start"),
        ]
        if any_ref is not None:
            items.append(_ci(any_ref >= 99, f"Reference data available for {any_ref:.1f}% of the outage",
                             warn=any_ref < 99))
        st.markdown('<div class="check">' + "".join(items) + "</div>", unsafe_allow_html=True)

        run = st.button("✅ Confirm outage and run analysis", type="primary", disabled=not ready, width="stretch")
        if run:
            results, errs = [], []
            prog = st.progress(0.0, "Starting…")
            for i, t in enumerate(targets):
                prog.progress(i / len(targets), f"Analysing {t}: validating models (this takes ~20 s per turbine)…")
                try:
                    r_refs = [r for r in refs if r in pl.eligible_references(turbines, t)[0] or not enforced_all]
                    results.append(pl.run_target(prep, t, r_refs, o_start, o_end, curves[t], cfg))
                except Exception as e:  # show actionable message, keep other turbines
                    errs.append(f"{t}: {e}")
            prog.empty()
            ss.results, ss.backtests, ss.run_errors = results, None, errs
            ss.run_sig = (tuple(targets), tuple(refs), o_start, o_end)
        if ss.get("run_errors"):
            for e in ss.run_errors:
                st.error(e)
        if ss.results:
            st.success("Analysis complete — see tabs ③ Model and ④ Wind & energy.")
            next_step("open <b>④ Wind & energy</b> for the estimated energy loss, or <b>③ Model</b> to see how "
                      "it was calculated.")

for _tb, _pre in zip(tabs[2:6], ["Tab ③", "Tab ④", "Tab ⑤", "Tab ⑥"]):
    with _tb:
        help_box(_pre)

results = ss.results
stale = bool(results) and ss.get("run_sig") != (tuple(targets), tuple(refs), o_start, o_end)
if stale:
    for tb in tabs[2:6]:
        with tb:
            st.warning("Inputs changed since the last run. Press **Confirm outage and run analysis** in tab ② "
                       "to update. Results below belong to the previous run.")


def need_results(tab):
    with tab:
        if not results:
            empty_state("No results yet",
                        "Run the analysis in tab <b>② Outage</b> first — it takes about 20 seconds per turbine.")
            return False
    return True


# ---------------------------------------------------------------- ③ model
if need_results(tabs[2]):
    with tabs[2]:
        sel = st.radio("Turbine", [r.target for r in results], horizontal=True, key="model_t")
        r = next(x for x in results if x.target == sel)
        note(f"<b>The prediction problem.</b> During the outage <b>{r.target}</b> has no wind measurements, but its "
             f"reference turbines (<b>{', '.join(r.refs)}</b>) do. We learn, from periods when both were measured, "
             f"how the wind at {r.target} relates to the wind at the references, then apply that relationship "
             "during the outage.")
        st.write("")
        row = r.comparison.set_index("model").loc[r.selected_model]
        c1, c2, c3, c4 = st.columns(4)
        kpi(c1, "Selected model", r.selected_model, mt.MODEL_INFO[r.selected_model]["complexity"] + " complexity")
        kpi(c2, "CV RMSE", fmt(row["CV RMSE (m/s)"], 2, " m/s"), "typical 10-min error")
        kpi(c3, "CV MAE", fmt(row["CV MAE (m/s)"], 2, " m/s"), "average absolute error")
        base = r.comparison.set_index("model").loc["Mean (no-skill baseline)", "CV RMSE (m/s)"]
        kpi(c4, "Skill vs. no-skill", fmt(100 * (1 - row["CV RMSE (m/s)"] / base), 0, " %"),
            "RMSE reduction vs. always predicting the mean")
        st.write("")
        st.markdown(f"**What it does:** {mt.MODEL_INFO[r.selected_model]['plain']}  \n"
                    f"**Why it was chosen:** {r.selection_reason}  \n"
                    "**Inputs used:** " + "; ".join(fe.GROUP_LABELS[g] for g in r.groups) + ".")

        section("Model comparison", "All models are scored on exactly the same validation timestamps. "
                                    "The selected row is bold.")
        tbl = r.comparison.copy()
        st.dataframe(tbl.style.format({c: "{:.3f}" for c in tbl.columns if tbl[c].dtype.kind == "f"})
                     .apply(lambda s_: ["font-weight:700" if v else "" for v in tbl["selected"]], axis=0),
                     hide_index=True, width="stretch")
        st.caption("**RMSE** penalises large errors, **MAE** is the average error, **R²** is the share of wind "
                   "variation explained. Selection rule: models within the tolerance of the best RMSE count as "
                   "equally accurate and the simplest one wins; a tree model must also beat Ridge in most folds.")

        section("Errors and uncertainty", "Out-of-fold predictions only — the model never saw these intervals.")
        o = r.oof
        g1, g2, g3 = st.columns(3)
        f1 = go.Figure(go.Scattergl(x=o["actual"], y=o["predicted"], mode="markers",
                                    marker=dict(size=4, color=C_OBS, opacity=.35), name="interval"))
        mx = float(np.nanmax(o[["actual", "predicted"]].to_numpy()))
        f1.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines", line=dict(color=MUTED, dash="dot", width=1),
                                name="perfect"))
        chart(layout(f1, 320, "predicted (m/s)").update_xaxes(title="measured (m/s)")
              .update_layout(hovermode="closest", showlegend=False), "Predicted vs. measured (validation)", g1)
        f2 = go.Figure(go.Histogram(x=o["error"], nbinsx=50, marker=dict(color=C_PRED), name="errors"))
        chart(layout(f2, 320, "count").update_xaxes(title="predicted − measured (m/s)")
              .update_layout(showlegend=False, hovermode="closest"), "Error distribution", g2)
        eb = r.errors_by_bin
        f3 = go.Figure()
        f3.add_trace(go.Bar(x=eb["bin"].astype(str), y=eb["RMSE (m/s)"], name="RMSE", marker_color=C_OBS))
        f3.add_trace(go.Bar(x=eb["bin"].astype(str), y=eb["bias (m/s)"], name="bias", marker_color=C_PRED))
        chart(layout(f3, 320, "m/s").update_layout(barmode="group"), "Error by measured wind speed", g3)
        st.caption("These errors are used for the empirical 80% bands in tab ④. Historical errors do not "
                   "guarantee future accuracy.")

        with st.expander("Validation details — how the inputs were chosen and how the model was tested"):
            cL, cR = st.columns(2, gap="large")
            with cL:
                st.markdown("**How the inputs were chosen** (forward selection, ≥1% CV improvement needed)")
                st.dataframe(r.group_log.style.format({"CV RMSE (m/s)": "{:.4f}"}), hide_index=True,
                             width="stretch")
                if not r.ref_selection_log.empty:
                    st.markdown("**Automatic reference selection**")
                    st.dataframe(r.ref_selection_log, hide_index=True, width="stretch")
            with cR:
                st.markdown("**Validation design**")
                si = r.split_info
                st.markdown(f"- Training data: {si['training intervals']:,} intervals ({si['training period']})\n"
                            f"- {len(si['CV folds'])} rolling-origin folds — train on the past, validate on the next "
                            f"block, {si['embargo']} embargo between them\n"
                            f"- Final holdout (scored once, after selection): {si['holdout']}")
                folds = pd.DataFrame(si["CV folds"], columns=["trained on", "validated on"])
                folds["RMSE selected (m/s)"] = si["fold RMSE (selected)"]
                st.dataframe(folds.style.format({"RMSE selected (m/s)": "{:.3f}"}), hide_index=True,
                             width="stretch")
            if not r.holdout.empty:
                st.markdown("**Final holdout — independent check after selection** (not used to choose)")
                st.dataframe(r.holdout.style.format({c: "{:.3f}" for c in ["RMSE (m/s)", "MAE (m/s)", "Bias (m/s)",
                                                                            "R²"]}),
                             hide_index=True, width="stretch")
        if r.coefficients is not None:
            with st.expander("Model weights (linear model — fully transparent)"):
                st.caption("Coefficient = change in predicted target wind (m/s) per unit change of the input. "
                           "Standardised weight = importance when all inputs are on the same scale.")
                st.dataframe(r.coefficients.style.format({"coefficient": "{:.4f}", "standardised weight": "{:.3f}"}),
                             hide_index=True, width="stretch")
        with st.expander("Feature definitions"):
            st.dataframe(r.feature_descriptions, hide_index=True, width="stretch")
        with st.expander("Limitations"):
            st.markdown(
                "- The relationship between parks is learned from a limited history; weather situations not seen "
                "in training (e.g. unusual wind directions or storms) may be predicted less accurately.\n"
                "- Predictions are 'regression to the mean': short peaks and lulls are smoothed.\n"
                "- Reference values shortly after a timestamp are used (centred smoothing); this is fine for an "
                "after-the-fact claim but would not suit real-time forecasting.\n"
                "- The empirical 80% band assumes future errors look like past validation errors.")
        next_step("open <b>④ Wind & energy</b> for the estimated energy loss.")

# ---------------------------------------------------------------- ④ wind & energy
if need_results(tabs[3]):
    with tabs[3]:
        tot = sum(r.energy_kwh for r in results)
        lo = sum(r.energy_band["P10 (kWh)"] for r in results)
        hi = sum(r.energy_band["P90 (kWh)"] for r in results)
        r0 = results[0]
        c1, c2, c3, c4 = st.columns(4)
        kpi(c1, "Estimated energy-yield loss", fmt(tot / 1000, 1, " MWh"), f"{fmt(tot)} kWh, all target turbines",
            accent=True)
        kpi(c2, "Indicative range", f"{fmt(lo / 1000, 1)} – {fmt(hi / 1000, 1)} MWh",
            "sum of per-turbine empirical 80% bands")
        hrs = len(r0.outage_table) * r0.freq / pd.Timedelta(hours=1)
        kpi(c3, "Outage duration", f"{hrs:,.1f} h", f"{r0.outage_start:%d %b %H:%M} – {r0.outage_end:%d %b %H:%M}")
        cap = sum(r.curve.rated_kw for r in results) * hrs
        kpi(c4, "Equivalent full-load", f"{100 * tot / cap:,.1f} %" if cap else "n/a",
            "of max power-curve output over the outage")

        section("Per turbine")
        et = totals({r.target: r.energy_kwh for r in results})
        et["P10 (kWh)"] = [r.energy_band["P10 (kWh)"] for r in results] + [lo]
        et["P90 (kWh)"] = [r.energy_band["P90 (kWh)"] for r in results] + [hi]
        et["mean predicted wind (m/s)"] = [f"{r.outage_table['predicted_ws'].mean():.2f}" for r in results] + [""]
        et["intervals reconstructed"] = [f"{r.energy_band['intervals reconstructed']}/{r.energy_band['intervals in outage']}"
                                         for r in results] + [""]
        st.dataframe(et.style.format({"energy (kWh)": "{:,.0f}", "P10 (kWh)": "{:,.0f}", "P90 (kWh)": "{:,.0f}"}, na_rep=""),
                     hide_index=True, width="stretch")

        section("Wind speed — measured and reconstructed",
                "Blue = measured, orange = reconstructed, light band = likely range, green = reference mean.")
        cs1, cs2 = st.columns([2, 3], gap="large")
        sel = cs1.radio("Turbine", [r.target for r in results], horizontal=True, key="energy_t")
        r = next(x for x in results if x.target == sel)
        pad = cs2.slider("Context shown around the outage (days)", 0, 14, 3)
        w0, w1 = r.outage_start - pd.Timedelta(days=pad), r.outage_end + pd.Timedelta(days=pad)
        sv = r.series[(r.series["timestamp"] >= w0) & (r.series["timestamp"] <= w1)]
        fig = go.Figure()
        ot = sv[sv["source"].isin(["reconstructed", "unpredictable"])]
        fig.add_trace(go.Scatter(x=ot["timestamp"], y=ot["p90_ws"], line=dict(width=0), showlegend=False,
                                 hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=ot["timestamp"], y=ot["p10_ws"], fill="tonexty", fillcolor=C_BAND,
                                 line=dict(width=0), name="empirical 80% band"))
        refmean = ws_wide.loc[(idx >= w0) & (idx <= w1), r.refs].mean(axis=1)
        fig.add_trace(go.Scatter(x=refmean.index, y=refmean, name="reference mean (measured)",
                                 line=dict(width=1, color=C_REF), opacity=.7))
        fig.add_trace(go.Scatter(x=sv["timestamp"], y=sv["observed_ws"], name=f"{r.target} measured",
                                 line=dict(width=1.5, color=C_OBS)))
        fig.add_trace(go.Scatter(x=ot["timestamp"], y=ot["predicted_ws"], name=f"{r.target} reconstructed",
                                 line=dict(width=2, color=C_PRED)))
        fig.add_vrect(x0=r.outage_start, x1=r.outage_end + r.freq, fillcolor=C_OUTAGE, line_width=0,
                      annotation_text="outage", annotation_position="top left",
                      annotation_font=dict(color=MUTED, size=11))
        chart(layout(fig, 400, "wind speed (m/s)"))

        cL, cR = st.columns(2, gap="large")
        fp = go.Figure()
        fp.add_trace(go.Scatter(x=r.curve.wind_speed, y=r.curve.power_kw, name="power curve",
                                line=dict(color="#9CA3AF", width=2)))
        o_ = r.outage_table
        fp.add_trace(go.Scattergl(x=o_["predicted_ws"], y=o_["expected_power_kw"], mode="markers",
                                  name="outage intervals", marker=dict(size=6, color=C_PRED, opacity=.5)))
        chart(layout(fp, 340, "kW").update_xaxes(title="wind speed (m/s)").update_layout(hovermode="closest"),
              f"{r.target} power curve and reconstructed operating points", cL)
        fe_ = go.Figure()
        fe_.add_trace(go.Scatter(x=o_["timestamp"], y=o_["expected_power_kw"], name="expected power (kW)",
                                 line=dict(color=C_PRED, width=1.5), fill="tozeroy",
                                 fillcolor="rgba(235,104,52,.10)"))
        chart(layout(fe_, 340, "kW").update_layout(showlegend=False), "Expected power during the outage", cR)

        section("Lost energy over time")
        gran = st.radio("Resolution", ["per hour", "per day"], horizontal=True, index=1)
        cB1, cB2 = st.columns(2, gap="large")
        fb = go.Figure()
        for i, rr in enumerate(results):
            d = rr.hourly_energy if gran == "per hour" else rr.daily_energy
            fb.add_trace(go.Bar(x=d["timestamp"], y=d["energy (kWh)"], name=rr.target,
                                marker=dict(color=SERIES[i % 8], line=dict(width=1, color="white"))))
        fb.update_layout(barmode="stack")
        chart(layout(fb, 320, "kWh"), f"Energy {gran}", cB1)
        fc = go.Figure()
        for i, rr in enumerate(results):
            o2 = rr.outage_table
            fc.add_trace(go.Scatter(x=o2["timestamp"], y=np.nancumsum(o2["interval_energy_kwh"]) / 1000,
                                    name=rr.target, line=dict(width=2, color=SERIES[i % 8])))
        chart(layout(fc, 320, "MWh"), "Cumulative estimated loss", cB2)

        section("10-minute results", f"Reconstructed values for {r.target}. The flags column marks intervals that "
                                     "need attention.")
        show_cols = ["timestamp", "source", "predicted_ws", "p10_ws", "p90_ws", "expected_power_kw",
                     "interval_energy_kwh", "flags", "power_flag"]
        st.dataframe(r.outage_table[show_cols].style.format(
            {"predicted_ws": "{:.2f}", "p10_ws": "{:.2f}", "p90_ws": "{:.2f}", "expected_power_kw": "{:,.0f}",
             "interval_energy_kwh": "{:,.1f}"}), hide_index=True, width="stretch", height=280)
        st.download_button("⬇ Download outage predictions (CSV, all turbines)", rp.predictions_csv(results),
                           "outage_predictions.csv", "text/csv")
        with st.expander("How the energy is calculated, and assumptions", expanded=False):
            st.markdown("Each reconstructed **wind speed** (m/s) is converted to **expected power** (kW) by linear "
                        "interpolation of the power curve. Each value is a 10-minute average, so **energy** per "
                        "interval = power × 10/60 h (kWh). The **estimated energy-yield loss** is the sum over the "
                        "outage.\n\n" + "\n".join(f"- {a}" for a in rp.ASSUMPTIONS))
            for w in r.warnings:
                st.warning(w)
        next_step("open <b>⑤ Validation</b> to prove the accuracy, or <b>⑥ Report & export</b> to download the "
                  "results.")

# ---------------------------------------------------------------- ⑤ validation
if need_results(tabs[4]):
    with tabs[4]:
        note("The real outage has no measurements to compare with. To show how well the method works, we "
             "<b>hide a period where the truth is known</b>, run exactly the same procedure (including model "
             "selection), and compare. Power is compared via the power curve, because measured electrical "
             "output is not in the data.")
        t0 = results[0].target
        test_rows = prep.wide["test_set"][t0] & ws_wide[t0].notna()
        if test_rows.any():
            d0, d1 = test_rows[test_rows].index.min(), test_rows[test_rows].index.max()
            period_hint = f"Default period = the data's marked test period with measurements ({d0:%d %b} – {d1:%d %b})."
        else:
            d1 = results[0].outage_start - prep.freq
            d0 = d1 - pd.Timedelta(days=3) + prep.freq
            period_hint = "Default period = the 3 days just before the outage."
        section("Back-test period", period_hint)
        c1, c2, c3 = st.columns([1, 1, 1], vertical_alignment="bottom")
        b0 = c1.date_input("Back-test from", d0.date(), key="bt0")
        b1 = c2.date_input("to (inclusive)", d1.date(), key="bt1")
        bs = pd.Timestamp(b0)
        be = pd.Timestamp(b1) + pd.Timedelta(days=1) - prep.freq
        overlap = (bs <= results[0].outage_end) and (be >= results[0].outage_start)
        if overlap:
            st.warning("The back-test period overlaps the outage, where no measurements exist.")
        if c3.button("▶ Run back-test", type="primary", width="stretch"):
            bts, errs = [], []
            prog = st.progress(0.0)
            for i, r in enumerate(results):
                prog.progress(i / len(results), f"Back-testing {r.target}…")
                try:
                    bts.append(pl.backtest(prep, r.target, r.refs, bs, be, r.curve, r.config))
                except Exception as e:
                    errs.append(f"{r.target}: {e}")
            prog.empty()
            ss.backtests = bts
            for e in errs:
                st.error(e)
        bts = ss.backtests
        if bts:
            rows = []
            for b in bts:
                rows.append({"turbine": b.target, "model": b.result.selected_model,
                             "wind RMSE (m/s)": b.wind["RMSE (m/s)"], "wind MAE (m/s)": b.wind["MAE (m/s)"],
                             "wind bias (m/s)": b.wind["Bias (m/s)"], "R²": b.wind["R²"],
                             "power RMSE (kW)": b.power["RMSE (kW)"], "power MAE (kW)": b.power["MAE (kW)"],
                             "predicted energy (kWh)": b.energy["predicted energy (kWh)"],
                             "energy from measured wind (kWh)": b.energy["reference energy (kWh)"],
                             "energy deviation (%)": b.energy["deviation (%)"],
                             "inside 80% band": b.band_hit, "intervals": b.wind["n"]})
            allc = pd.concat([b.compare for b in bts])
            allc = allc[allc["actual_ws"].notna() & allc["predicted_ws"].notna()]
            h = prep.freq / pd.Timedelta(hours=1)
            ed = energy_deviation(float(allc["expected_power_kw"].sum() * h), float(allc["actual_power_kw"].sum() * h))
            section("Accuracy, all target turbines")
            c1, c2, c3, c4, c5 = st.columns(5)
            err_ws = allc["predicted_ws"] - allc["actual_ws"]
            err_p = allc["expected_power_kw"] - allc["actual_power_kw"]
            kpi(c1, "Wind RMSE", fmt(float(np.sqrt((err_ws ** 2).mean())), 2, " m/s"), "all targets")
            kpi(c2, "Wind MAE", fmt(float(err_ws.abs().mean()), 2, " m/s"), "all targets")
            kpi(c3, "Power RMSE", fmt(float(np.sqrt((err_p ** 2).mean())), 0, " kW"), "via power curve")
            kpi(c4, "Power MAE", fmt(float(err_p.abs().mean()), 0, " kW"), "via power curve")
            kpi(c5, "Summed energy deviation", fmt(ed["deviation (%)"], 1, " %"),
                f"{fmt(ed['difference (kWh)'])} kWh", accent=True)
            section("Per turbine")
            bt_df = pd.DataFrame(rows)
            st.dataframe(bt_df.style.format({c: "{:,.3f}" if "m/s" in c or c == "R²" else "{:,.0f}"
                                             for c in bt_df.columns if bt_df[c].dtype.kind == "f"}
                                            | {"energy deviation (%)": "{:+.2f}"}),
                         hide_index=True, width="stretch")
            section("Reconstructed vs. measured")
            sel = st.radio("Turbine", [b.target for b in bts], horizontal=True, key="bt_t")
            b = next(x for x in bts if x.target == sel)
            cmp_ = b.compare
            f = go.Figure()
            f.add_trace(go.Scatter(x=cmp_["timestamp"], y=cmp_["p90_ws"], line=dict(width=0), showlegend=False,
                                   hoverinfo="skip"))
            f.add_trace(go.Scatter(x=cmp_["timestamp"], y=cmp_["p10_ws"], fill="tonexty", fillcolor=C_BAND,
                                   line=dict(width=0), name="empirical 80% band"))
            f.add_trace(go.Scatter(x=cmp_["timestamp"], y=cmp_["actual_ws"], name="measured (hidden from model)",
                                   line=dict(color=C_OBS, width=1.5)))
            f.add_trace(go.Scatter(x=cmp_["timestamp"], y=cmp_["predicted_ws"], name="reconstructed",
                                   line=dict(color=C_PRED, width=2)))
            chart(layout(f, 380, "m/s"), f"{b.target}: reconstructed vs. measured wind")
            band_cov = float(((cmp_["actual_ws"] >= cmp_["p10_ws"]) & (cmp_["actual_ws"] <= cmp_["p90_ws"]))
                             [cmp_["actual_ws"].notna()].mean() * 100)
            st.caption(f"{band_cov:.0f}% of measured values fall inside the empirical 80% band (target: ~80%). "
                       + " ".join(b.notes))
            g1, g2, g3 = st.columns(3)
            fs_ = go.Figure(go.Scattergl(x=cmp_["actual_power_kw"], y=cmp_["expected_power_kw"], mode="markers",
                                         marker=dict(size=4, color=C_OBS, opacity=.4)))
            mxp = b.result.curve.rated_kw
            fs_.add_trace(go.Scatter(x=[0, mxp], y=[0, mxp], mode="lines", line=dict(color=MUTED, dash="dot")))
            chart(layout(fs_, 320, "predicted (kW)").update_xaxes(title="from measured wind (kW)")
                  .update_layout(showlegend=False, hovermode="closest"), "Power: predicted vs. from measured wind", g1)
            ebb = errors_by_speed_bin(cmp_["actual_ws"], cmp_["predicted_ws"])
            fbin = go.Figure([go.Bar(x=ebb["bin"].astype(str), y=ebb["RMSE (m/s)"], name="RMSE", marker_color=C_OBS),
                              go.Bar(x=ebb["bin"].astype(str), y=ebb["bias (m/s)"], name="bias", marker_color=C_PRED)])
            chart(layout(fbin, 320, "m/s").update_layout(barmode="group"), "Wind error by measured speed", g2)
            fe2 = go.Figure(go.Bar(x=["from measured wind", "reconstructed"],
                                   y=[b.energy["reference energy (kWh)"] / 1000, b.energy["predicted energy (kWh)"] / 1000],
                                   marker_color=[C_OBS, C_PRED], text=[fmt(b.energy["reference energy (kWh)"] / 1000, 1),
                                                                       fmt(b.energy["predicted energy (kWh)"] / 1000, 1)],
                                   textposition="outside"))
            chart(layout(fe2, 320, "MWh").update_layout(showlegend=False), "Energy over back-test period", g3)
            if b.wind["n"] < int(pd.Timedelta(days=1) / prep.freq):
                st.warning("Fewer than one day of comparison data — metrics are not representative.")
            next_step("open <b>⑥ Report & export</b> — the back-test is now included in the report and metrics.")
        else:
            st.write("")
            empty_state("Back-test not run yet", "Press <b>Run back-test</b> (about 20 s per turbine).")

# ---------------------------------------------------------------- ⑥ export
if need_results(tabs[5]):
    with tabs[5]:
        section("Downloads", "Everything you need to document or submit the result.")
        c1, c2, c3 = st.columns(3)
        c1.download_button("⬇ Predictions, power & energy (CSV)", rp.predictions_csv(results),
                           "outage_predictions.csv", "text/csv", width="stretch")
        c2.download_button("⬇ Model comparison & validation metrics (CSV)", rp.metrics_csv(results, ss.backtests),
                           "model_metrics.csv", "text/csv", width="stretch")
        report = rp.engineering_report(results, ss.backtests, prep.log.to_frame())
        c3.download_button("⬇ Engineering report (Markdown)", report.encode(), "engineering_report.md",
                           "text/markdown", width="stretch")
        if not ss.backtests:
            st.caption("Tip: run the back-test in tab ⑤ to include it in the report and metrics.")
        with st.expander("Preview engineering report"):
            st.markdown(report)

        section("Insurance notification e-mail", "Written automatically from the results. Edit freely — nothing "
                                                 "is sent automatically.")
        e1, e2, e3 = st.columns(3)
        park = e1.text_input("Wind farm name", "Wind farm T")
        rec = e2.text_input("Recipient (salutation)", "")
        snd = e3.text_input("Your name / company", "")
        subject, body = rp.insurance_email(results, park, rec, snd)
        st.text_input("Subject", subject)
        body_edit = st.text_area("Body (editable)", body, height=420)
        mailto = "mailto:?subject=" + urllib.parse.quote(subject) + "&body=" + urllib.parse.quote(body_edit)
        d1, d2 = st.columns(2)
        d1.link_button("✉ Open in my e-mail program", mailto, width="stretch")
        d2.download_button("⬇ Download e-mail text", f"Subject: {subject}\n\n{body_edit}".encode(),
                           "insurance_email.txt", "text/plain", width="stretch")
        st.caption("Attach the report and the predictions CSV before sending.")

# ---------------------------------------------------------------- progress stepper (filled last, shown on top)
done = set()
if ready:
    done.add(1)
if results and not stale:
    done |= {2, 3, 4}
if ss.backtests and not stale:
    done.add(5)
now = next((i for i in range(1, 7) if i not in done), 6)
stepper_box.markdown(stepper(done, now), unsafe_allow_html=True)
