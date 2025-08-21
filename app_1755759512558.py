# app.py — single Flask app serving static dashboard + stats API + CSV append API
# Expected layout:
#   C:\Users\Colin\Desktop\Server\app.py
#   C:\Users\Colin\Desktop\Server\lab_dashboard_tools\   (index.html, tools_*.html, assets/)
#   C:\Users\Colin\Desktop\Server\data\                  (created automatically)

from flask import Flask, send_from_directory, request, jsonify, redirect, url_for, Response
from flask_cors import CORS
import os, csv, pathlib, threading, datetime, json

import pandas as pd
import numpy as np
import scipy.stats as stats

import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import scikit_posthocs as sp
# safe quoting for formula column names

# ---- Configure paths ----
ROOT     = r"C:\Users\Colin\Desktop\Server"
TOOLS    = os.path.join(ROOT, "lab_dashboard_tools")
ASSETS   = os.path.join(TOOLS, "assets")
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---- App ----
app = Flask(__name__, static_folder=None)
CORS(app)

# ----------------- Static pages -----------------
@app.route("/")
def root():
    # go straight to the dashboard index
    return redirect(url_for("serve_tools", path="index.html"))

@app.route("/lab/<path:path>")
def serve_tools(path):
    return send_from_directory(TOOLS, path)

@app.route("/lab/assets/<path:path>")
def serve_assets(path):
    return send_from_directory(ASSETS, path)

# ----------------- Health -----------------
@app.get("/health")
def health():
    return jsonify(status="ok")

# ----------------- Helpers -----------------
def descriptives(df, group_col, value_col):
    g = (df.groupby(group_col)[value_col]
           .agg(['mean', 'std', 'count'])
           .rename(columns={'count': 'n'}))
    g['sem'] = g['std'] / np.sqrt(g['n'].clip(lower=1))
    g['ci95_lo'] = g['mean'] - 1.96 * g['sem']
    g['ci95_hi'] = g['mean'] + 1.96 * g['sem']
    # return group label as a column named consistently:
    g = g.reset_index().rename(columns={group_col: "Group"})
    return g

def json_error(msg, code=400, **extra):
    out = {"ok": False, "error": msg}
    if extra:
        out.update(extra)
    return jsonify(out), code

# ----------------- Stats API -----------------
# POST multipart/form-data with:
#   file  -> CSV file
#   group -> column name for groups (categorical)
#   value -> column name for numeric response
#   test  -> one of: ttest | anova | kruskal
@app.post("/run_stats")
def run_stats():
    # 1) Inputs
    f = request.files.get("file", None)
    group_col = (request.form.get("group") or "").strip()
    value_col = (request.form.get("value") or "").strip()
    test = (request.form.get("test") or "").strip().lower()

    if f is None:
        return json_error("No CSV uploaded.")
    if not group_col or not value_col or not test:
        return json_error("Missing group/value/test parameters.",
                          params=list(request.form.keys()))

    # 2) Load CSV
    try:
        df = pd.read_csv(f)
    except Exception as e:
        return json_error("Could not read CSV.", detail=str(e))

    # 3) Validate columns
    if group_col not in df.columns or value_col not in df.columns:
        return json_error("Column not found in CSV.",
                          columns=df.columns.tolist(),
                          group_requested=group_col,
                          value_requested=value_col)

    # coerce numeric for value column
    df = df[[group_col, value_col]].copy()
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[value_col])

    # 4) Basic structure
    groups = df[group_col].dropna().unique().tolist()
    n_by_group = df.groupby(group_col)[value_col].size().to_dict()

    out = {
        "ok": True,
        "groups": groups,
        "n_by_group": n_by_group,
        "descriptives": descriptives(df, group_col, value_col).to_dict(orient="records"),
        "requested_test": test
    }

    # 5) Tests
    try:
        if test == "ttest":
            if len(groups) != 2:
                return json_error("t-test requires exactly 2 groups.", groups=groups)
            g1 = df[df[group_col] == groups[0]][value_col].astype(float)
            g2 = df[df[group_col] == groups[1]][value_col].astype(float)
            t, p = stats.ttest_ind(g1, g2, equal_var=False)  # Welch
            out.update(test="Welch t-test", t=float(t), p=float(p))

        elif test == "anova":
            if len(groups) < 3:
                return json_error("One-way ANOVA requires ≥3 groups.", groups=groups)

            # Safe quoting for arbitrary column names
            model = smf.ols(f"Q('{value_col}') ~ C(Q('{group_col}'))", data=df).fit()
            anova_tbl = sm.stats.anova_lm(model, typ=2)
            out["test"] = "One-way ANOVA"
            out["anova"] = anova_tbl.to_dict()

            # Tukey HSD on raw columns
            tukey = pairwise_tukeyhsd(df[value_col], df[group_col])
            out["tukey"] = str(tukey.summary())

        elif test == "kruskal":
            if len(groups) < 3:
                return json_error("Kruskal–Wallis requires ≥3 groups.", groups=groups)
            samples = [df[df[group_col] == g][value_col].astype(float) for g in groups]
            H, p = stats.kruskal(*samples)
            out.update(test="Kruskal–Wallis", H=float(H), p=float(p))
            dunn = sp.posthoc_dunn(df, val_col=value_col, group_col=group_col, p_adjust="bonferroni")
            out["dunn"] = dunn.to_dict()

        else:
            return json_error("Unknown test. Use: ttest | anova | kruskal.")
    except Exception as e:
        # bubble the detail so you can see parsing errors etc.
        return json_error("Exception during analysis.", detail=str(e), code=500)

    return jsonify(out)

# ---------- Server-side CSV append (generic) ----------
# Whitelisted “tables”
ALLOWED_CSV = {
    "animal_log":   ["date","mouse_id","strain","sex","dob","age_wk","treatment","weight_g","notes"],
    "lab_notebook": ["date","title","experiment_id","project","tags","body_md","links","author","notes"],
    "meeting_notes":["date","title","attendees","project","agenda","decisions","actions","owner","next_meeting"],
}

_csv_lock = threading.Lock()

def _append_row(csv_name: str, row: dict):
    if csv_name not in ALLOWED_CSV:
        raise ValueError(f"Unknown csv_name: {csv_name}")
    cols = ALLOWED_CSV[csv_name]
    cleaned = {c: ("" if row.get(c) is None else str(row.get(c))) for c in cols}
    cleaned["_ts"] = datetime.datetime.now().isoformat(timespec="seconds")
    path = os.path.join(DATA_DIR, f"{csv_name}.csv")
    new_file = not os.path.exists(path)
    with _csv_lock, open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols+["_ts"])
        if new_file:
            w.writeheader()
        w.writerow(cleaned)
    return path

@app.post("/append_csv")
def append_csv():
    """
    Accepts JSON or multipart/form-data.

    JSON:
      {"csv_name":"<key in ALLOWED_CSV>","row":{...}}

    Multipart/form-data:
      csv_name=<...>, row=<json-string>
    """
    try:
        if request.is_json:
            payload = request.get_json(force=True)
        else:
            payload = {
                "csv_name": request.form.get("csv_name"),
                "row": request.form.get("row"),
            }
            if isinstance(payload["row"], str):
                payload["row"] = json.loads(payload["row"])

        csv_name = (payload.get("csv_name") or "").strip()
        row = payload.get("row") or {}
        if not csv_name or not isinstance(row, dict):
            return jsonify({"ok": False, "error": "csv_name and row required"}), 400

        saved = _append_row(csv_name, row)
        rel = os.path.relpath(saved, ROOT)
        return jsonify({"ok": True, "path": rel})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# -------- Utilities: list & download saved CSVs --------
@app.get("/list_data")
def list_data():
    items = []
    for p in pathlib.Path(DATA_DIR).glob("*.csv"):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                n = sum(1 for _ in fh) - 1  # exclude header
                if n < 0: n = 0
        except Exception:
            n = None
        items.append({"name": p.name, "rows": n})
    return jsonify(items)

@app.get("/download_csv")
def download_csv():
    name = request.args.get("name", "")
    if not name.endswith(".csv"):
        return json_error("Specify ?name=<file>.csv")
    path = os.path.join(DATA_DIR, name)
    if not os.path.isfile(path):
        return json_error("File not found", code=404)
    with open(path, "rb") as f:
        data = f.read()
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{name}"'}
    )

# ----------------- Main -----------------
if __name__ == "__main__":
    # If 8000 is busy, change to another port (e.g., 8050)
    app.run(host="0.0.0.0", port=8000)