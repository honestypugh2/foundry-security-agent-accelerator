# mccp: multi-cloud AI control plane demo

A self-contained demo that lives in **`demos/mccp-multicloud-control-plane/`** of
[`foundry-security-agent-accelerator`](https://github.com/honestypugh2/foundry-security-agent-accelerator).
It does not change any file outside this folder: it has its own `pyproject.toml`, `.venv`, `.env`, `.gitignore` and `artifacts/`.

What it shows: one inventory of agents across Azure, AWS and SaaS; agent identity (Entra or Okta); token and dollar limits at the
Azure API Management AI gateway; FinOps forecasts; and a kill switch with receipts. All data is synthetic ("Contoso Health").

## Set up (WSL2 / Linux / macOS)

```bash
# 1. Go to your clone and start a branch (commit or stash open changes first)
cd ~/foundry-security-agent-accelerator
git status
git checkout -b feature/multicloud-control-plane      # creates the branch and switches to it

# 2. Unzip into a NEW folder under demos/ (nothing goes to /tmp or the repo root)
sudo apt-get install -y unzip                          # only if unzip is missing
mkdir -p demos/mccp-multicloud-control-plane
unzip -o "/mnt/c/Users/<WindowsUser>/Downloads/mccp-multicloud-control-plane-addon.zip" \
      -d demos/mccp-multicloud-control-plane
cd demos/mccp-multicloud-control-plane
chmod +x infra/mccp/deploy.sh

# 3. Run it offline (no Azure, no credentials, no cost)
uv run python -m mccp demo --mode local --color        # 12-scene story
uv run pytest -q                                       # expect: 58 passed
#    without uv:
#    PYTHONPATH=src python3 -m mccp demo --mode local --color
#    python3 -m unittest discover -s tests/mccp -q

# 4. Commit the demo folder on the branch
cd ../..
git add demos/mccp-multicloud-control-plane
git commit -m "Add multi-cloud AI control plane demo (demos/mccp-multicloud-control-plane)"
git push -u origin feature/multicloud-control-plane
```

`uv run` creates `demos/mccp-multicloud-control-plane/.venv` the first time (git-ignored). Run it from this folder, not the repo root,
so it uses this folder's `pyproject.toml` and leaves the base repo's environment alone.

## Deploy to Azure (optional, from this folder)

```bash
az login --use-device-code && az account set -s <subscription>
infra/mccp/deploy.sh --rg rg-contoso-mccp --attach-rg <your-lab-rg> --what-if-only   # preview, deploys nothing
infra/mccp/deploy.sh --rg rg-contoso-mccp --attach-rg <your-lab-rg>                  # ATTACH to the existing lab
infra/mccp/deploy.sh --rg rg-contoso-mccp --location eastus2                          # or NEW (own Foundry account)
uv sync --extra azure                                                                 # Azure SDKs for --mode azure
uv run python -m mccp call --mode azure --agent contoso-claims-triage                 # expect HTTP 200
```

`deploy.sh` writes `.env.mccp.azure` and `artifacts/mccp/smoke-response.json` **in this folder** (both git-ignored).
See [infra/mccp/README.md](infra/mccp/README.md) for what ATTACH and NEW change.

## Shortcuts

| Command | Does |
|---|---|
| `make demo` | Offline 12-scene demo |
| `make test` | Unit and static tests |
| `make whatif ATTACH_RG=<lab-rg>` | Compile, validate and what-if (deploys nothing) |
| `make deploy ATTACH_RG=<lab-rg>` | Deploy (asks before it changes anything) |
| `make clean` | Delete `artifacts/mccp` |

## Folder map

| Path | What |
|---|---|
| `src/mccp/` | Python package (`python -m mccp`) |
| `tests/mccp/` | Tests |
| `infra/mccp/` | Bicep (`main.bicep`, `main.bicepparam`, 6 modules), gateway policy, KQL, `deploy.sh` |
| `notebooks/mccp/` | Six walkthrough notebooks; pick this folder's `.venv` as the kernel |
| `docs/mccp/` | PLAN, ARCHITECTURE, DEMO_RUNBOOK |
| `data/mccp/` | Synthetic agents, budgets, ILLUSTRATIVE prices, usage fixture |
| `otel/`, `datadog/` | OpenTelemetry Collector config, Datadog monitor and webhook payload |
| `mccp/README.md` | Command reference |
| `.env.example` | Settings template: copy to `.env` in this folder for live mode |
| `BUILD_REPORT.md` | What was built and tested, and what is still VALIDATE |

## PR checklist
- [ ] `uv run pytest -q` passes and `uv run python -m mccp demo --mode local` runs offline
- [ ] `infra/mccp/deploy.sh --what-if-only` succeeds and the what-if has been reviewed
- [ ] No secrets in the diff (`git status` shows no `.env`, `.env.mccp.azure` or `artifacts/`)
- [ ] Only synthetic names (Contoso Health / `contoso-*`)
- [ ] Every `VALIDATE` item is confirmed or listed in the PR description
- [ ] The ServiceNow AI Control Tower table/API is confirmed with the ServiceNow team
