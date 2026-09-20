#!/usr/bin/env python3
"""Investigate the "answers get less varied toward the end" claim.

Tests three independent signatures of survey fatigue / satisficing:
  1. Item-level: does missingness rise, entropy fall, and the share of
     extreme (Strongly Agree/Disagree) answers rise as item position
     increases -- both across the whole 60-item survey and *within*
     each 15-item theme block (which removes the topic/position
     confound, since theme is presented block-by-block: T, E, S, V)?
  2. Respondent-level (straightlining): for each kept respondent, does
     their own run of identical consecutive answers get longer, and
     their own share of extreme answers get higher, in the second half
     of the items they answered versus the first half?
  3. Summary numbers (Spearman correlations, Wilcoxon signed-rank
     tests) that make the claim falsifiable rather than eyeballed.

Writes CSVs to artifacts/ and figures to figures/ (fatigue_*.png).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "artifacts"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

INK = "#1b2a36"
CLAY = "#c1666b"
BRASS = "#c4a35a"
MOSS = "#4a7c59"
DUSK = "#5c4d7a"
PAPER = "#f6f1e8"
GRID = "#d9d0c3"
MUTED = "#6b6358"
THEME_COLORS = {"T": "#2f6f7a", "E": MOSS, "S": BRASS, "V": DUSK}
THEME_NAMES = {"T": "Technology", "E": "Education", "S": "Ethics/Society", "V": "Environment"}

LIKERT_LEVELS = [-1.0, -0.5, 0.0, 0.5, 1.0]


def apply_style() -> None:
    sns.set_theme(
        style="whitegrid",
        context="talk",
        font="DejaVu Serif",
        rc={
            "axes.facecolor": PAPER,
            "figure.facecolor": PAPER,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "axes.titleweight": "bold",
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "figure.dpi": 140,
            "savefig.dpi": 240,
            "savefig.facecolor": PAPER,
            "font.family": "DejaVu Serif",
        },
    )


def polish(ax, title, xlabel=None, ylabel=None) -> None:
    ax.set_title(title, pad=12, color=INK)
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)


def shade_theme_blocks(ax, n_items=60, block=15):
    for i, t in enumerate("TESV"):
        start = i * block + 0.5
        end = start + block
        ax.axvspan(start, end, color=THEME_COLORS[t], alpha=0.07, lw=0)
        ax.text((start + end) / 2, ax.get_ylim()[1], t, ha="center", va="bottom",
                fontsize=11, color=THEME_COLORS[t], fontweight="bold")


def normalized_entropy(values: np.ndarray) -> float:
    values = values[~np.isnan(values)]
    if len(values) == 0:
        return np.nan
    counts = np.array([(values == lv).sum() for lv in LIKERT_LEVELS], dtype=float)
    p = counts / counts.sum()
    p = p[p > 0]
    h = -(p * np.log(p)).sum()
    return float(h / np.log(len(LIKERT_LEVELS)))


def main() -> None:
    apply_style()

    kept = pd.read_csv(ART / "encoded_respondents.csv")
    item_cols = [c for c in kept.columns if c not in ("respondent_id", "completeness")]
    n_items = len(item_cols)
    n_resp = len(kept)
    themes = [c[0] for c in item_cols]

    X = kept[item_cols].to_numpy(dtype=float)  # n_resp x n_items, survey order preserved

    # ---------- 1. Item-level position statistics ----------
    rows = []
    for pos, col in enumerate(item_cols, start=1):
        col_vals = X[:, pos - 1]
        non_missing = col_vals[~np.isnan(col_vals)]
        rows.append({
            "position": pos,
            "item": col.split(".")[0].strip(),
            "theme": themes[pos - 1],
            "within_block_position": ((pos - 1) % 15) + 1,
            "n_answered": int(len(non_missing)),
            "missing_rate": 1.0 - len(non_missing) / n_resp,
            "mean": float(non_missing.mean()) if len(non_missing) else np.nan,
            "variance": float(non_missing.var()) if len(non_missing) else np.nan,
            "extreme_rate": float(np.mean(np.abs(non_missing) == 1.0)) if len(non_missing) else np.nan,
            "entropy_norm": normalized_entropy(col_vals),
        })
    pos_df = pd.DataFrame(rows)
    pos_df.to_csv(ART / "fatigue_item_position_stats.csv", index=False)

    def rolling(s, w=5):
        return s.rolling(w, center=True, min_periods=1).mean()

    # --- Figure A: missingness by position (whole-survey dropout / skipping) ---
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.bar(pos_df["position"], pos_df["missing_rate"] * 100, color=MUTED, width=0.8, alpha=0.55)
    ax.plot(pos_df["position"], rolling(pos_df["missing_rate"]) * 100, color=INK, lw=2.2)
    shade_theme_blocks(ax)
    polish(ax, "Missing-answer rate by item position (survey order)", "item position (1-60)", "% of 87 kept respondents missing")
    fig.tight_layout()
    fig.savefig(FIG / "fatigue_missingness_by_position.png", bbox_inches="tight")
    plt.close(fig)

    # --- Figure B: extreme-response rate by position ---
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.scatter(pos_df["position"], pos_df["extreme_rate"] * 100, color=CLAY, s=26, alpha=0.75, zorder=3)
    ax.plot(pos_df["position"], rolling(pos_df["extreme_rate"]) * 100, color=INK, lw=2.2, zorder=4)
    shade_theme_blocks(ax)
    polish(ax, "Share of extreme answers (Strongly Agree/Disagree) by item position", "item position (1-60)", "% extreme")
    fig.tight_layout()
    fig.savefig(FIG / "fatigue_extreme_rate_by_position.png", bbox_inches="tight")
    plt.close(fig)

    # --- Figure C: normalized entropy by position (variety of answers) ---
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.scatter(pos_df["position"], pos_df["entropy_norm"], color=DUSK, s=26, alpha=0.75, zorder=3)
    ax.plot(pos_df["position"], rolling(pos_df["entropy_norm"]), color=INK, lw=2.2, zorder=4)
    shade_theme_blocks(ax)
    polish(ax, "Normalized response entropy by item position (1.0 = most varied)", "item position (1-60)", "entropy / log(5)")
    fig.tight_layout()
    fig.savefig(FIG / "fatigue_entropy_by_position.png", bbox_inches="tight")
    plt.close(fig)

    # --- Figure D: variance by position, in survey order (not sorted like contested_items_variance) ---
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.bar(pos_df["position"], pos_df["variance"], color=[THEME_COLORS[t] for t in pos_df["theme"]], width=0.8, alpha=0.85)
    ax.plot(pos_df["position"], rolling(pos_df["variance"]), color=INK, lw=2.0, zorder=4)
    shade_theme_blocks(ax)
    polish(ax, "Response variance by item position, in survey order", "item position (1-60)", "variance")
    fig.tight_layout()
    fig.savefig(FIG / "fatigue_variance_by_position.png", bbox_inches="tight")
    plt.close(fig)

    # --- Figure E: within-block position overlay (removes theme/topic confound) ---
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for t in "TESV":
        sub = pos_df[pos_df["theme"] == t].sort_values("within_block_position")
        axes[0].plot(sub["within_block_position"], sub["extreme_rate"] * 100, marker="o", ms=4,
                     color=THEME_COLORS[t], label=THEME_NAMES[t])
        axes[1].plot(sub["within_block_position"], sub["entropy_norm"], marker="o", ms=4,
                     color=THEME_COLORS[t], label=THEME_NAMES[t])
    polish(axes[0], "Extreme-answer share vs. position within block", "position within 15-item block", "% extreme")
    polish(axes[1], "Entropy vs. position within block", "position within 15-item block", "entropy / log(5)")
    axes[0].legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fatigue_within_block_position.png", bbox_inches="tight")
    plt.close(fig)

    # ---------- 2. Respondent-level straightlining ----------
    resp_rows = []
    for i in range(n_resp):
        seq = X[i, :]
        answered_positions = np.where(~np.isnan(seq))[0]
        vals = seq[answered_positions]
        n_ans = len(vals)
        if n_ans < 10:
            continue
        half = n_ans // 2
        first_vals, second_vals = vals[:half], vals[half:]

        def run_lengths(v):
            if len(v) == 0:
                return np.array([])
            runs = []
            cur = 1
            for k in range(1, len(v)):
                if v[k] == v[k - 1]:
                    cur += 1
                else:
                    runs.append(cur)
                    cur = 1
            runs.append(cur)
            return np.array(runs)

        first_runs = run_lengths(first_vals)
        second_runs = run_lengths(second_vals)

        resp_rows.append({
            "respondent_id": kept.loc[i, "respondent_id"],
            "n_answered": n_ans,
            "avg_run_first_half": float(first_runs.mean()) if len(first_runs) else np.nan,
            "avg_run_second_half": float(second_runs.mean()) if len(second_runs) else np.nan,
            "max_run_first_half": int(first_runs.max()) if len(first_runs) else 0,
            "max_run_second_half": int(second_runs.max()) if len(second_runs) else 0,
            "extreme_rate_first_half": float(np.mean(np.abs(first_vals) == 1.0)),
            "extreme_rate_second_half": float(np.mean(np.abs(second_vals) == 1.0)),
        })
    resp_df = pd.DataFrame(resp_rows)
    resp_df.to_csv(ART / "fatigue_respondent_straightlining.csv", index=False)

    # --- Figure F: paired first-half vs second-half run length ---
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    for _, r in resp_df.iterrows():
        ax.plot([0, 1], [r["avg_run_first_half"], r["avg_run_second_half"]], color=MUTED, alpha=0.25, lw=1.0)
    ax.scatter(np.zeros(len(resp_df)), resp_df["avg_run_first_half"], color=THEME_COLORS["T"], s=22, zorder=3, label="first half")
    ax.scatter(np.ones(len(resp_df)), resp_df["avg_run_second_half"], color=CLAY, s=22, zorder=3, label="second half")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["first half\nof answers", "second half\nof answers"])
    ax.set_xlim(-0.3, 1.3)
    polish(ax, "Per-respondent average run length of identical answers", None, "average consecutive-repeat length")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "fatigue_straightlining_paired.png", bbox_inches="tight")
    plt.close(fig)

    # --- Figure G: distribution of the within-respondent shift (second - first half) ---
    shift_run = resp_df["avg_run_second_half"] - resp_df["avg_run_first_half"]
    shift_extreme = (resp_df["extreme_rate_second_half"] - resp_df["extreme_rate_first_half"]) * 100
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8))
    sns.histplot(shift_run, bins=20, color=DUSK, ax=axes[0], edgecolor=PAPER)
    axes[0].axvline(0, color=INK, lw=1.4, ls="--")
    axes[0].axvline(shift_run.mean(), color=CLAY, lw=2.0, label=f"mean = {shift_run.mean():+.2f}")
    polish(axes[0], "Change in run length (second half - first half)", "run-length shift", "respondents")
    axes[0].legend(frameon=False)

    sns.histplot(shift_extreme, bins=20, color=BRASS, ax=axes[1], edgecolor=PAPER)
    axes[1].axvline(0, color=INK, lw=1.4, ls="--")
    axes[1].axvline(shift_extreme.mean(), color=CLAY, lw=2.0, label=f"mean = {shift_extreme.mean():+.1f} pp")
    polish(axes[1], "Change in % extreme answers (second half - first half)", "percentage-point shift", "respondents")
    axes[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "fatigue_shift_distributions.png", bbox_inches="tight")
    plt.close(fig)

    # ---------- 3. Summary statistics ----------
    valid = pos_df.dropna(subset=["extreme_rate", "entropy_norm", "variance"])
    spearman_extreme_all = stats.spearmanr(valid["position"], valid["extreme_rate"])
    spearman_entropy_all = stats.spearmanr(valid["position"], valid["entropy_norm"])
    spearman_variance_all = stats.spearmanr(valid["position"], valid["variance"])
    spearman_missing_all = stats.spearmanr(pos_df["position"], pos_df["missing_rate"])

    within_block = {}
    for metric in ["extreme_rate", "entropy_norm", "variance"]:
        rs, ps = [], []
        for t in "TESV":
            sub = valid[valid["theme"] == t]
            r, p = stats.spearmanr(sub["within_block_position"], sub[metric])
            rs.append(r)
            ps.append(p)
        within_block[metric] = {"per_theme_rho": rs, "per_theme_p": ps, "mean_rho": float(np.nanmean(rs))}

    wilcoxon_run = stats.wilcoxon(resp_df["avg_run_second_half"], resp_df["avg_run_first_half"])
    wilcoxon_extreme = stats.wilcoxon(resp_df["extreme_rate_second_half"], resp_df["extreme_rate_first_half"])

    summary = {
        "n_kept_respondents": n_resp,
        "n_items": n_items,
        "whole_survey_position_correlations": {
            "extreme_rate_vs_position": {"spearman_rho": spearman_extreme_all.statistic, "p_value": spearman_extreme_all.pvalue},
            "entropy_vs_position": {"spearman_rho": spearman_entropy_all.statistic, "p_value": spearman_entropy_all.pvalue},
            "variance_vs_position": {"spearman_rho": spearman_variance_all.statistic, "p_value": spearman_variance_all.pvalue},
            "missing_rate_vs_position": {"spearman_rho": spearman_missing_all.statistic, "p_value": spearman_missing_all.pvalue},
        },
        "within_block_position_correlations_theme_controlled": within_block,
        "respondent_level_paired_tests": {
            "run_length_second_vs_first_half": {
                "mean_first": float(resp_df["avg_run_first_half"].mean()),
                "mean_second": float(resp_df["avg_run_second_half"].mean()),
                "wilcoxon_stat": float(wilcoxon_run.statistic),
                "p_value": float(wilcoxon_run.pvalue),
            },
            "extreme_rate_second_vs_first_half": {
                "mean_first": float(resp_df["extreme_rate_first_half"].mean()),
                "mean_second": float(resp_df["extreme_rate_second_half"].mean()),
                "wilcoxon_stat": float(wilcoxon_extreme.statistic),
                "p_value": float(wilcoxon_extreme.pvalue),
            },
        },
        "missing_cells_by_theme_block": {
            t: int(kept[[c for c in item_cols if c.startswith(t)]].isna().sum().sum()) for t in "TESV"
        },
    }
    (ART / "fatigue_summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps(summary, indent=2, default=float))
    print("wrote fatigue_* figures and artifacts")


if __name__ == "__main__":
    main()
