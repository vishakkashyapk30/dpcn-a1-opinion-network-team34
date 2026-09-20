#!/usr/bin/env python3
"""Regenerate classy seaborn charts and Cytoscape.js network figures."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent  # repo root
ART = ROOT / "artifacts"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
CYTO = FIG / "cytoscape"
CYTO.mkdir(exist_ok=True)

# Editorial palette (ink, clay, brass, moss, dusk)
INK = "#1b2a36"
CLAY = "#c1666b"
BRASS = "#c4a35a"
MOSS = "#4a7c59"
DUSK = "#5c4d7a"
PAPER = "#f6f1e8"
GRID = "#d9d0c3"
MUTED = "#6b6358"
PALETTE = [INK, CLAY, BRASS, MOSS, DUSK, "#2f6f7a"]
THEME_COLORS = {"T": "#2f6f7a", "E": MOSS, "S": BRASS, "V": DUSK}


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


def polish(ax, title: str, xlabel: str | None = None, ylabel: str | None = None) -> None:
    ax.set_title(title, pad=12, color=INK)
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)


def chart_eda() -> None:
    kept = pd.read_csv(ART / "encoded_respondents.csv")
    item_cols = [c for c in kept.columns if c not in ("respondent_id", "completeness")]
    flat = kept[item_cols].stack().dropna()
    vc = flat.value_counts().sort_index()
    themes = {
        "T": [c for c in item_cols if c.startswith("T")],
        "E": [c for c in item_cols if c.startswith("E")],
        "S": [c for c in item_cols if c.startswith("S")],
        "V": [c for c in item_cols if c.startswith("V")],
    }
    theme_means = pd.Series({t: kept[cols].stack().dropna().mean() for t, cols in themes.items()})

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    sns.barplot(x=vc.index.astype(str), y=vc.values, ax=axes[0], color=INK, saturation=1)
    polish(axes[0], "Encoded Likert mass", "value on [-1, 1]", "count")
    for p in axes[0].patches:
        p.set_edgecolor(PAPER)
        p.set_linewidth(0.8)

    theme_df = theme_means.rename("mean").reset_index().rename(columns={"index": "theme"})
    sns.barplot(
        data=theme_df,
        x="theme",
        y="mean",
        hue="theme",
        ax=axes[1],
        palette=THEME_COLORS,
        saturation=1,
        legend=False,
    )
    axes[1].axhline(0, color=MUTED, lw=1)
    polish(axes[1], "Mean stance by domain", "theme", "mean score")
    fig.tight_layout()
    fig.savefig(FIG / "eda_likert_and_themes.png", bbox_inches="tight")
    plt.close(fig)


def chart_similarity() -> None:
    S = np.load(ART / "similarity_matrix.npy")
    vals = S[np.triu_indices(S.shape[0], k=1)]
    vals = vals[np.isfinite(vals)]
    theta = json.loads((ART / "chosen_theta.json").read_text())["theta"]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    sns.histplot(vals, bins=36, ax=ax, color=CLAY, edgecolor=PAPER, kde=True, line_kws={"color": INK, "lw": 1.6})
    ax.axvline(theta, color=BRASS, ls="--", lw=2, label=f"chosen theta = {theta}")
    polish(ax, "Pairwise agreement similarity", "S_ij", "count")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "similarity_distribution.png", bbox_inches="tight")
    plt.close(fig)


def chart_threshold() -> None:
    thr = pd.read_csv(ART / "threshold_scan.csv").sort_values("theta")
    thr = thr.iloc[:: max(1, len(thr) // 250)]
    theta = json.loads((ART / "chosen_theta.json").read_text())["theta"]
    target = json.loads((ART / "chosen_theta.json").read_text()).get("giant_frac_target", 0.8)

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    sns.lineplot(data=thr, x="theta", y="giant_frac", ax=ax, color=INK, lw=2.2)
    ax.fill_between(thr["theta"], thr["giant_frac"], alpha=0.12, color=CLAY)
    ax.axhline(target, color=MUTED, ls=":", lw=1.4, label=f"target {target:.0%}")
    ax.axvline(theta, color=BRASS, ls="--", lw=2, label=f"theta = {theta}")
    polish(ax, "Giant-component threshold search", "agreement threshold", "giant fraction")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "threshold_giant_component.png", bbox_inches="tight")
    plt.close(fig)


def chart_degree() -> None:
    G = nx.read_graphml(ART / "agent_network.graphml")
    deg = pd.DataFrame({"degree": [d for _, d in G.degree()]})
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    sns.histplot(data=deg, x="degree", discrete=True, ax=ax, color=MOSS, edgecolor=PAPER)
    polish(ax, "Agent-network degree distribution", "degree", "respondents")
    fig.tight_layout()
    fig.savefig(FIG / "agent_degree_distribution.png", bbox_inches="tight")
    plt.close(fig)


def chart_community_profiles() -> None:
    profile = pd.read_csv(ART / "community_theme_profiles.csv")
    # keep communities with size >= 3 for readability
    if "size" in profile.columns:
        profile = profile[profile["size"] >= 3].copy()
    long = profile.melt(
        id_vars=[c for c in profile.columns if c.startswith("louvain") or c == "Unnamed: 0" or c == "size"],
        value_vars=["mean_T", "mean_E", "mean_S", "mean_V"],
        var_name="theme",
        value_name="mean_score",
    )
    if "louvain" not in long.columns and "Unnamed: 0" in long.columns:
        long = long.rename(columns={"Unnamed: 0": "louvain"})
    long["theme"] = long["theme"].str.replace("mean_", "", regex=False)

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    sns.barplot(
        data=long,
        x="louvain",
        y="mean_score",
        hue="theme",
        palette=THEME_COLORS,
        ax=ax,
        saturation=1,
    )
    ax.axhline(0, color=MUTED, lw=1)
    polish(ax, "Louvain communities: theme means (size >= 3)", "community", "mean score")
    ax.legend(title="theme", frameon=False, ncols=4)
    fig.tight_layout()
    fig.savefig(FIG / "community_theme_profiles.png", bbox_inches="tight")
    plt.close(fig)


def chart_attitude_clustermap() -> None:
    G_att = nx.read_graphml(ART / "attitude_network.graphml")
    nodes = sorted(G_att.nodes())
    mat = pd.DataFrame(0.0, index=nodes, columns=nodes)
    for u, v, d in G_att.edges(data=True):
        w = float(d.get("weight", 0.0))
        mat.loc[u, v] = w
        mat.loc[v, u] = w
    # drop all-zero isolates for a tighter map
    keep = mat.sum(axis=1) > 0
    mat = mat.loc[keep, keep]
    if mat.shape[0] < 4:
        return
    cg = sns.clustermap(
        mat,
        cmap="mako",
        figsize=(9.5, 9.0),
        dendrogram_ratio=0.12,
        linewidths=0.0,
        xticklabels=True,
        yticklabels=True,
        cbar_kws={"label": "co-endorsement weight"},
    )
    cg.fig.patch.set_facecolor(PAPER)
    cg.ax_heatmap.set_facecolor(PAPER)
    cg.ax_heatmap.tick_params(labelsize=7, colors=INK)
    cg.fig.suptitle("Attitude co-endorsement clustermap", color=INK, fontweight="bold", y=1.02)
    cg.savefig(FIG / "attitude_clustermap.png", dpi=240, bbox_inches="tight", facecolor=PAPER)
    plt.close("all")


def chart_importance_and_contested() -> None:
    imp = pd.read_csv(ART / "item_importance.csv").head(15)
    contested = pd.read_csv(ART / "item_stats.csv").head(15)

    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    sns.barplot(
        data=imp.sort_values("importance"),
        y="item",
        x="importance",
        hue="theme",
        dodge=False,
        palette=THEME_COLORS,
        ax=ax,
        saturation=1,
    )
    polish(ax, "Items that structure opinion groups", "importance (1 - ARI after shuffle)", None)
    ax.legend(title="theme", frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "item_importance_top15.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    sns.barplot(
        data=contested.sort_values("variance"),
        y="item",
        x="variance",
        hue="theme",
        dodge=False,
        palette=THEME_COLORS,
        ax=ax,
        saturation=1,
    )
    polish(ax, "Most contested survey items", "response variance", None)
    ax.legend(title="theme", frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "contested_items_variance.png", bbox_inches="tight")
    plt.close(fig)


def graph_to_cyto_elements(G: nx.Graph, node_color_attr: str, color_map: dict) -> list[dict]:
    elements = []
    for n, d in G.nodes(data=True):
        key = d.get(node_color_attr, "default")
        # GraphML may store ints as strings
        if isinstance(key, str) and key.lstrip("-").isdigit():
            key_cast: object = int(key)
        else:
            key_cast = key
        color = color_map.get(key_cast, color_map.get(str(key), INK))
        label = str(n)
        elements.append(
            {
                "data": {
                    "id": str(n),
                    "label": label,
                    "color": color,
                    **{k: ("" if v is None else str(v)) for k, v in d.items()},
                }
            }
        )
    for u, v, d in G.edges(data=True):
        w = float(d.get("weight", 1.0))
        elements.append(
            {
                "data": {
                    "id": f"{u}_{v}",
                    "source": str(u),
                    "target": str(v),
                    "weight": w,
                }
            }
        )
    return elements


def write_cytoscape_html(
    name: str,
    elements: list[dict],
    title: str,
    node_size: int = 22,
    show_labels: bool = True,
    weight_max: float = 80.0,
) -> Path:
    html_path = CYTO / f"{name}.html"
    payload = {
        "title": title,
        "elements": elements,
        "nodeSize": node_size,
        "showLabels": show_labels,
        "weightMax": weight_max,
        "bg": PAPER,
        "edge": "#8a8074",
    }
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>LOADING</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
  <style>
    html, body {{ margin: 0; height: 100%; background: {PAPER}; }}
    #cy {{ width: 1200px; height: 860px; background: {PAPER}; border-top: 1px solid {GRID}; }}
    h1 {{
      font-family: Georgia, 'DejaVu Serif', serif;
      color: {INK};
      font-size: 22px;
      margin: 18px 24px 0;
      font-weight: 600;
    }}
    .sub {{
      font-family: Georgia, 'DejaVu Serif', serif;
      color: {MUTED};
      margin: 4px 24px 12px;
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="sub">Cytoscape.js force-directed layout (edge strength = spring force)</div>
  <div id="cy"></div>
  <script>
    const payload = {json.dumps(payload)};
    const cy = cytoscape({{
      container: document.getElementById('cy'),
      elements: payload.elements,
      style: [
        {{
          selector: 'node',
          style: {{
            'background-color': 'data(color)',
            'label': payload.showLabels ? 'data(label)' : '',
            'color': '{INK}',
            'font-family': 'Georgia, DejaVu Serif, serif',
            'font-size': 9,
            'font-weight': 600,
            'text-valign': 'center',
            'text-halign': 'center',
            'width': payload.nodeSize,
            'height': payload.nodeSize,
            'border-width': 1.5,
            'border-color': '{PAPER}',
            'text-outline-width': 3,
            'text-outline-color': '{PAPER}',
            'overlay-padding': 4
          }}
        }},
        {{
          selector: 'edge',
          style: {{
            'width': 'mapData(weight, 0, ' + payload.weightMax + ', 0.5, 4.0)',
            'line-color': payload.edge,
            'opacity': 0.42,
            'curve-style': 'bezier',
            'control-point-step-size': 20
          }}
        }}
      ],
      layout: {{
        name: 'cose',
        animate: false,
        padding: 40,
        nodeRepulsion: 9000,
        gravity: 0.7,
        numIter: 2500,
        initialTemp: 300,
        nestingFactor: 1.2,
        idealEdgeLength: edge => {{
          const w = Number(edge.data('weight')) || 1;
          const t = Math.min(Math.max(w / payload.weightMax, 0), 1);
          return 35 + 120 * (1 - t);
        }},
        edgeElasticity: edge => {{
          const w = Number(edge.data('weight')) || 1;
          const t = Math.min(Math.max(w / payload.weightMax, 0), 1);
          return 80 + 220 * t;
        }}
      }}
    }});
    document.title = 'READY';
  </script>
</body>
</html>
"""
    html_path.write_text(html)
    return html_path


def export_cytoscape_views() -> list[Path]:
    G = nx.read_graphml(ART / "agent_network_communities.graphml")
    G_att = nx.read_graphml(ART / "attitude_network_communities.graphml")

    # normalize community attrs possibly stored as strings
    for n in G.nodes:
        for key in ("louvain", "girvan_newman"):
            if key in G.nodes[n]:
                try:
                    G.nodes[n][key] = int(float(G.nodes[n][key]))
                except Exception:
                    pass

    louvain_ids = sorted({G.nodes[n].get("louvain", 0) for n in G.nodes})
    louvain_colors = {cid: PALETTE[i % len(PALETTE)] for i, cid in enumerate(louvain_ids)}
    gn_ids = sorted({G.nodes[n].get("girvan_newman", -1) for n in G.nodes})
    gn_colors = {cid: PALETTE[i % len(PALETTE)] for i, cid in enumerate(gn_ids)}

    paths = []
    el_agent = graph_to_cyto_elements(G, "louvain", louvain_colors)
    paths.append(
        write_cytoscape_html(
            "agent_louvain",
            el_agent,
            "Agent agreement network (Louvain)",
            node_size=20,
            show_labels=False,
            weight_max=70,
        )
    )

    # giant only for GN view
    giant = max(nx.connected_components(G), key=len)
    Gg = G.subgraph(giant).copy()
    el_gn = graph_to_cyto_elements(Gg, "girvan_newman", gn_colors)
    paths.append(
        write_cytoscape_html(
            "agent_girvan_newman",
            el_gn,
            "Giant component (Girvan-Newman cut)",
            node_size=22,
            show_labels=False,
            weight_max=70,
        )
    )

    el_att = graph_to_cyto_elements(G_att, "theme", THEME_COLORS)
    paths.append(
        write_cytoscape_html(
            "attitude_themes",
            el_att,
            "Attitude co-endorsement network by theme",
            node_size=28,
            show_labels=True,
            weight_max=55,
        )
    )

    # also write a small index of links
    index = CYTO / "index.html"
    links = "\n".join(f'<li><a href="{p.name}">{p.stem}</a></li>' for p in paths)
    index.write_text(
        f"""<!DOCTYPE html><html><body style="background:{PAPER};font-family:Georgia,serif;color:{INK};padding:2rem">
        <h1>Cytoscape network views</h1>
        <ul>{links}</ul>
        <p>Open these HTML files in a browser, or use the PNGs exported beside them in the report.</p>
        </body></html>"""
    )
    return paths


def screenshot_cytoscape(html_paths: list[Path]) -> None:
    import subprocess

    chrome = "google-chrome"
    for html in html_paths:
        out = CYTO / f"{html.stem}.png"
        url = html.resolve().as_uri()
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=8000",
            "--window-size=1280,1000",
            f"--screenshot={out}",
            url,
        ]
        subprocess.run(cmd, check=False, capture_output=True)
        print("screenshot", out, "size", out.stat().st_size if out.exists() else 0)
        dest = FIG / f"cytoscape_{html.stem}.png"
        if out.exists():
            dest.write_bytes(out.read_bytes())


def fallback_network_pngs() -> None:
    """Polished static network PNGs if screenshots fail; still label as Cytoscape-ready views."""
    G = nx.read_graphml(ART / "agent_network_communities.graphml")
    for n in G.nodes:
        for key in ("louvain", "girvan_newman"):
            if key in G.nodes[n]:
                try:
                    G.nodes[n][key] = int(float(G.nodes[n][key]))
                except Exception:
                    pass
    G_att = nx.read_graphml(ART / "attitude_network_communities.graphml")

    def draw(Gdraw, attr, path, title, color_lookup):
        pos = nx.spring_layout(
            Gdraw,
            weight="weight",
            seed=42,
            k=2.1 / np.sqrt(max(Gdraw.number_of_nodes(), 1)),
            iterations=200,
        )
        labels = [Gdraw.nodes[n].get(attr) for n in Gdraw.nodes]
        node_colors = [color_lookup.get(v, INK) for v in labels]
        weights = np.array([float(d.get("weight", 1.0)) for *_, d in Gdraw.edges(data=True)], dtype=float)
        if len(weights):
            widths = 0.25 + 2.2 * (weights - weights.min()) / (weights.max() - weights.min() + 1e-9)
        else:
            widths = 1.0
        fig, ax = plt.subplots(figsize=(9.5, 7.2))
        fig.patch.set_facecolor(PAPER)
        ax.set_facecolor(PAPER)
        nx.draw_networkx_edges(Gdraw, pos, ax=ax, width=widths, alpha=0.28, edge_color="#8a8074")
        nx.draw_networkx_nodes(
            Gdraw,
            pos,
            ax=ax,
            node_color=node_colors,
            node_size=85,
            linewidths=0.6,
            edgecolors=PAPER,
        )
        if Gdraw.number_of_nodes() <= 70:
            nx.draw_networkx_labels(Gdraw, pos, ax=ax, font_size=6, font_color=INK, font_family="DejaVu Serif")
        polish(ax, title)
        ax.axis("off")
        uniq = sorted(set(labels), key=lambda x: (x is None, x))
        handles = [mpatches.Patch(color=color_lookup.get(u, INK), label=f"{attr}={u}") for u in uniq[:12]]
        ax.legend(handles=handles, loc="best", frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)

    louvain_ids = sorted({G.nodes[n].get("louvain", 0) for n in G.nodes})
    louvain_colors = {cid: PALETTE[i % len(PALETTE)] for i, cid in enumerate(louvain_ids)}
    draw(G, "louvain", FIG / "agent_network_louvain.png", "Agent agreement network (Louvain)", louvain_colors)

    giant = max(nx.connected_components(G), key=len)
    Gg = G.subgraph(giant).copy()
    gn_ids = sorted({Gg.nodes[n].get("girvan_newman", -1) for n in Gg.nodes})
    gn_colors = {cid: PALETTE[i % len(PALETTE)] for i, cid in enumerate(gn_ids)}
    draw(Gg, "girvan_newman", FIG / "agent_network_girvan_newman.png", "Giant component (Girvan-Newman)", gn_colors)
    draw(Gg, "louvain", FIG / "agent_network_giant.png", "Giant component (Louvain colors)", louvain_colors)
    draw(G_att, "theme", FIG / "attitude_network_themes.png", "Attitude network by theme", THEME_COLORS)


def main() -> None:
    apply_style()
    chart_eda()
    chart_similarity()
    chart_threshold()
    chart_degree()
    chart_community_profiles()
    chart_importance_and_contested()
    chart_attitude_clustermap()
    html_paths = export_cytoscape_views()
    screenshot_cytoscape(html_paths)
    fallback_network_pngs()
    # Prefer Cytoscape screenshots for named report assets when non-empty
    for stem, dest_name in [
        ("agent_louvain", "cytoscape_agent_louvain.png"),
        ("agent_girvan_newman", "cytoscape_agent_girvan_newman.png"),
        ("attitude_themes", "cytoscape_attitude_themes.png"),
    ]:
        src = CYTO / f"{stem}.png"
        if src.exists() and src.stat().st_size > 10_000:
            (FIG / dest_name).write_bytes(src.read_bytes())
    print("figures refreshed")


if __name__ == "__main__":
    main()
