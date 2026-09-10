# DPCN Assignment 1 - Opinion Network (Team 34)

Opinion network analysis for SC1.440 Dynamical Processes in Complex Networks (DPCN) Assignment 1.

We build respondent (agent) and attitude networks from the class Likert survey using the bipartite-projection / agreement-threshold methods of MacCarron et al. (2020) and Dinkelberg et al. (2021), then interpret communities and item drivers in the written report.

## Repository layout

```
code/                 # notebooks + figure regeneration script
  01_data_and_network.ipynb
  02_analysis.ipynb
  regenerate_figures.py
artifacts/            # GraphML, tables, metrics (rebuilt by notebooks)
figures/              # seaborn charts + Cytoscape screenshots/HTML
report/               # report.md source and report.pdf
requirements.txt
README.md
Survey_Results_UC.csv # local only (gitignored)
```

## Setup

```bash
python3 -m pip install -r requirements.txt
```

Place `Survey_Results_UC.csv` at the repository root (gitignored). The assignment PDF is also gitignored.

## Reproduce

From the repository root:

```bash
jupyter nbconvert --to notebook --execute code/01_data_and_network.ipynb --inplace
jupyter nbconvert --to notebook --execute code/02_analysis.ipynb --inplace
python3 code/regenerate_figures.py
```

Build the PDF (run pandoc inside `report/` so figure paths resolve):

```bash
cd report
pandoc report.md -o report.pdf --pdf-engine=xelatex
cd ..
```

Or open the notebooks under `code/` in Jupyter; they resolve the repo root automatically when launched from `code/` or the root.

## Outputs

| Path | Contents |
|:-----|:---------|
| `artifacts/*.graphml` | Agent and attitude networks (Cytoscape Desktop import) |
| `artifacts/communities.csv` | Louvain / Girvan-Newman labels |
| `artifacts/item_importance.csv` | Shuffle-based item ranking |
| `figures/*.png` | Seaborn charts and Cytoscape screenshots |
| `figures/cytoscape/*.html` | Interactive Cytoscape.js views (`index.html`) |
| `report/report.pdf` | Assignment report |

### Cytoscape workflow

1. Run the notebooks and `code/regenerate_figures.py`.
2. Optional Desktop: import `artifacts/agent_network_communities.graphml`, style by `louvain` / `theme`, edge width by `weight`.
3. Or open `figures/cytoscape/index.html` for the interactive views embedded (as screenshots + links) in the report.

## Method references

1. MacCarron, P., Maher, P. J., Quayle, M. (2020). Identifying opinion-based groups from survey data: a bipartite network approach. https://arxiv.org/abs/2012.11392
2. Dinkelberg, A., et al. (2021). Detect opinion-based groups and reveal polarisation in survey data. https://arxiv.org/abs/2104.14427
3. Maher, P. J., MacCarron, P., Quayle, M. (2020). Mapping public health responses with attitude networks. British Journal of Social Psychology.

## Team

Team 34:

1. Kushal Balabhadruni
2. Rohit Jeswanth
3. Vishak Kashyap K

See Individual Contribution in `report/report.pdf`.
