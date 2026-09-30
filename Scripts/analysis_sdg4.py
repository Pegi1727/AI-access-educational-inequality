#!/usr/bin/env python3
"""Reproducible quantitative analysis for the SDG4 AI-access dataset.

Primary inference: two-sided pooled-variance independent-samples t tests
(Premium minus Free), as specified in the manuscript (df = n1+n2-2).
Run: python analysis_sdg4.py [--data /path/SDG4_Quant_Data.csv] [--outdir results]
Requires pandas, numpy, scipy, matplotlib.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

OUTCOMES = ["Lexical_TTR", "Syntactic_Cscore", "Cohesion_Score"]
GROUPS = ["Premium", "Free"]
LABELS = {"Lexical_TTR": "Lexical diversity (TTR)",
          "Syntactic_Cscore": "Syntactic complexity (C-score)",
          "Cohesion_Score": "Cohesion score"}
REQUIRED = ["Participant_ID", "Group", *OUTCOMES]


def holm_adjust(p_values):
    """Holm family-wise adjusted p-values, returned in input order."""
    p = np.asarray(p_values, dtype=float)
    m = len(p); order = np.argsort(p); adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m-rank)*p[idx])
        adj[idx] = min(1.0, running)
    return adj


def validate(df):
    missing = sorted(set(REQUIRED) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Dataset uses 'Group' (not 'Condition').")
    if df.empty:
        raise ValueError("Input dataset contains no rows.")
    if df["Participant_ID"].isna().any() or df["Participant_ID"].duplicated().any():
        raise ValueError("Participant_ID values must be present and unique.")
    if df["Group"].isna().any() or not set(df["Group"].unique()).issubset(GROUPS):
        raise ValueError(f"Group must contain only {GROUPS}; found {df['Group'].unique().tolist()}.")
    if set(df["Group"].unique()) != set(GROUPS):
        raise ValueError(f"Both groups are required: {GROUPS}.")
    for v in OUTCOMES:
        df[v] = pd.to_numeric(df[v], errors="coerce")
        if df[v].isna().any() or not np.isfinite(df[v]).all():
            raise ValueError(f"{v} contains missing, nonnumeric, or non-finite values.")
    if not df["Lexical_TTR"].between(0, 1).all():
        raise ValueError("Lexical_TTR values must lie between 0 and 1.")
    if not df["Cohesion_Score"].between(0, 10).all():
        raise ValueError("Cohesion_Score values must lie between 0 and 10.")
    counts = df["Group"].value_counts()
    if (counts < 2).any():
        raise ValueError("Each group must have at least two observations.")
    return df


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="/mnt/data/SDG4_Quant_Data.csv", help="Input participant-level CSV")
    parser.add_argument("--outdir", default="sdg4_analysis_results", help="Directory for tables, report, and figure")
    args = parser.parse_args()
    data_path, outdir = Path(args.data), Path(args.outdir)
    if not data_path.is_file():
        parser.error(f"Data file not found: {data_path}")
    outdir.mkdir(parents=True, exist_ok=True)
    df = validate(pd.read_csv(data_path))
    counts = df["Group"].value_counts().reindex(GROUPS)

    # Descriptive statistics by group and outcome.
    descriptives = []
    for outcome in OUTCOMES:
        for group in GROUPS:
            x = df.loc[df.Group == group, outcome].to_numpy(float)
            descriptives.append({"Outcome": outcome, "Group": group, "n": len(x),
                "Mean": x.mean(), "SD": x.std(ddof=1), "Median": np.median(x),
                "Q1": np.quantile(x, .25), "Q3": np.quantile(x, .75),
                "Minimum": x.min(), "Maximum": x.max()})
    desc = pd.DataFrame(descriptives)
    desc.to_csv(outdir/"descriptive_statistics.csv", index=False, float_format="%.8g")

    results = []
    for outcome in OUTCOMES:
        a = df.loc[df.Group == "Premium", outcome].to_numpy(float)
        b = df.loc[df.Group == "Free", outcome].to_numpy(float)
        n1, n2 = len(a), len(b); dfree = n1+n2-2
        m1, m2 = a.mean(), b.mean(); s1, s2 = a.std(ddof=1), b.std(ddof=1)
        sp = np.sqrt(((n1-1)*s1**2+(n2-1)*s2**2)/dfree)
        diff = m1-m2; se = sp*np.sqrt(1/n1+1/n2)
        tcrit = stats.t.ppf(.975, dfree)
        tstat, p = stats.ttest_ind(a, b, equal_var=True, alternative="two-sided")
        d = diff/sp
        J = 1 - 3/(4*dfree-1)  # small-sample correction
        g = J*d
        # Secondary diagnostics/sensitivity; Shapiro omitted only if n outside its limits.
        lev_stat, lev_p = stats.levene(a, b, center="median")
        sh_a = stats.shapiro(a).pvalue if 3 <= n1 <= 5000 else np.nan
        sh_b = stats.shapiro(b).pvalue if 3 <= n2 <= 5000 else np.nan
        tw, pw = stats.ttest_ind(a, b, equal_var=False, alternative="two-sided")
        results.append({"Outcome": outcome, "Premium_n": n1, "Free_n": n2,
            "Premium_mean": m1, "Premium_SD": s1, "Free_mean": m2, "Free_SD": s2,
            "Mean_difference_Premium_minus_Free": diff, "Difference_CI95_low": diff-tcrit*se,
            "Difference_CI95_high": diff+tcrit*se, "Student_t": tstat, "Student_df": dfree,
            "Student_p": p, "Cohens_d": d, "Hedges_g": g, "Levene_median_stat": lev_stat,
            "Levene_median_p": lev_p, "Shapiro_Premium_p": sh_a, "Shapiro_Free_p": sh_b,
            "Welch_t": tw, "Welch_df": (s1*s1/n1+s2*s2/n2)**2/((s1*s1/n1)**2/(n1-1)+(s2*s2/n2)**2/(n2-1)),
            "Welch_p": pw})
    res = pd.DataFrame(results)
    res["Student_p_Holm"] = holm_adjust(res["Student_p"].to_numpy())
    res["Welch_p_Holm"] = holm_adjust(res["Welch_p"].to_numpy())
    res.to_csv(outdir/"group_comparisons.csv", index=False, float_format="%.10g")

    # Publication-ready forest-style mean plot; error bars are 95% t CIs for each mean.
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 4.2))
    colors = {"Premium": "#3569a8", "Free": "#d17a22"}
    for ax, outcome in zip(axes, OUTCOMES):
        sub = desc[desc.Outcome == outcome].set_index("Group").loc[GROUPS]
        for pos, group in enumerate(GROUPS):
            row = sub.loc[group]; n = int(row.n); crit = stats.t.ppf(.975, n-1)
            margin = crit*row.SD/np.sqrt(n)
            ax.errorbar(pos, row.Mean, yerr=margin, fmt='o', ms=7, capsize=4,
                        color=colors[group], lw=1.7, label=group)
        ax.set_xticks([0,1], GROUPS); ax.set_title(LABELS[outcome], fontsize=10)
        ax.set_ylabel("Mean (95% CI)"); ax.spines[["top","right"]].set_visible(False)
        ax.grid(axis="y", alpha=.22)
    fig.suptitle("Linguistic outcomes by AI-access group", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(outdir/"group_means_95ci.png", dpi=320, bbox_inches="tight")
    plt.close(fig)

    lines = ["SDG4 quantitative analysis", "="*29,
             f"Input: {data_path}", f"N = {len(df)}; group sizes: Premium={counts['Premium']}, Free={counts['Free']}",
             "Primary analysis: two-sided pooled-variance independent-samples Student t tests; contrast = Premium - Free.",
             "Effect size: pooled Cohen's d; Hedges' g also reported. 95% CI is for the raw mean difference.",
             "Holm adjustment is across the three primary tests. Welch tests and diagnostics are sensitivity/checks.",
             "", "Descriptives (mean ± SD)"]
    for outcome in OUTCOMES:
        rows = desc[desc.Outcome == outcome].set_index("Group")
        lines.append(f"{outcome}: Premium {rows.loc['Premium','Mean']:.4f} ± {rows.loc['Premium','SD']:.4f}; "
                     f"Free {rows.loc['Free','Mean']:.4f} ± {rows.loc['Free','SD']:.4f}")
    lines += ["", "Primary tests and diagnostics"]
    for r in res.itertuples(index=False):
        lines.append(f"{r.Outcome}: t({r.Student_df})={r.Student_t:.3f}, p={r.Student_p:.4g}, "
            f"Holm p={r.Student_p_Holm:.4g}, d={r.Cohens_d:.3f}, g={r.Hedges_g:.3f}, "
            f"difference={r.Mean_difference_Premium_minus_Free:.4f}, 95% CI [{r.Difference_CI95_low:.4f}, {r.Difference_CI95_high:.4f}]; "
            f"Levene p={r.Levene_median_p:.4g}, Shapiro p (Premium/Free)={r.Shapiro_Premium_p:.4g}/{r.Shapiro_Free_p:.4g}, "
            f"Welch t({r.Welch_df:.2f})={r.Welch_t:.3f}, p={r.Welch_p:.4g}")
    lines += ["", "Interpretation caveat: this non-randomized between-group dataset has no baseline or covariate data; findings describe group associations and do not establish causal effects of Premium access.",
              "Diagnostics (Shapiro-Wilk and median-centered Levene) are screening tools, not proof of assumptions."]
    (outdir/"analysis_report.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("Analysis complete. Files:")
    for name in ["descriptive_statistics.csv","group_comparisons.csv","analysis_report.txt","group_means_95ci.png"]:
        print(outdir/name)
    print("\nPrimary results:")
    print(res[["Outcome","Student_t","Student_df","Student_p","Student_p_Holm","Cohens_d","Mean_difference_Premium_minus_Free","Difference_CI95_low","Difference_CI95_high"]].to_string(index=False))

if __name__ == "__main__":
    main()
