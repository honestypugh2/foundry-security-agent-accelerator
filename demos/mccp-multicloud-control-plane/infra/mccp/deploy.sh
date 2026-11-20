#!/usr/bin/env bash
# mccp deploy: preflight checks -> bicep build -> validate -> what-if -> deploy -> .env.mccp.azure -> smoke test.
#
# Run from the demo folder: cd <repo>/demos/mccp-multicloud-control-plane
# NEW mode (own Foundry account + gpt-5-mini):
#   infra/mccp/deploy.sh --rg rg-contoso-mccp --location eastus2
# ATTACH mode (reuse the Foundry account the repo root's infra/live.bicep created; nothing in it is changed except one role
# assignment for the gateway's managed identity):
#   infra/mccp/deploy.sh --rg rg-contoso-mccp --attach-rg <your-fsa-lab-resource-group>
#
# Options: --email you@company.com (default: your az login user)   --okta (use Okta instead of Entra)
#          --what-if-only   --yes (skip the confirmation)   --sku BasicV2|StandardV2|Developer
set -euo pipefail

RG="rg-contoso-mccp"; LOCATION=""; ATTACH_RG=""; EMAIL="${MCCP_ALERT_EMAIL:-}"; IDP="entra"
WHATIF_ONLY=0; ASSUME_YES=0; SKU="${MCCP_APIM_SKU:-BasicV2}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rg) RG="$2"; shift 2;;
    --location) LOCATION="$2"; shift 2;;
    --attach-rg) ATTACH_RG="$2"; shift 2;;
    --email) EMAIL="$2"; shift 2;;
    --okta) IDP="okta"; shift;;
    --sku) SKU="$2"; shift 2;;
    --what-if-only) WHATIF_ONLY=1; shift;;
    --yes|-y) ASSUME_YES=1; shift;;
    -h|--help) sed -n 2,14p "$0"; exit 0;;
    *) echo "Unknown option: $1"; exit 2;;
  esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"   # the demo folder: demos/mccp-multicloud-control-plane
OUTDIR="$ROOT/artifacts/mccp"; SMOKE="$OUTDIR/smoke-response.json"
MAIN="$HERE/main.bicep"; PARAMS="$HERE/main.bicepparam"
ok()   { printf '\033[32m  ✔ %s\033[0m\n' "$*"; }
warn() { printf '\033[33m  ! %s\033[0m\n' "$*"; }
die()  { printf '\033[31m  ✘ %s\033[0m\n' "$*"; exit 1; }
step() { printf '\n\033[1m▸ %s\033[0m\n' "$*"; }

step "1/8 Tools and sign-in"
command -v az >/dev/null || die "Azure CLI not found. WSL/Ubuntu: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
az bicep version >/dev/null 2>&1 || { warn "Installing Bicep for the Azure CLI"; az bicep install; }
ok "$(az bicep version 2>/dev/null | head -1)"
az account show >/dev/null 2>&1 || die "Not signed in. Run: az login --use-device-code   (then az account set -s <subscription>)"
SUB_NAME=$(az account show --query name -o tsv); SUB_ID=$(az account show --query id -o tsv)
ok "Subscription: $SUB_NAME ($SUB_ID)"
[[ -n "$EMAIL" ]] || EMAIL=$(az account show --query user.name -o tsv)
[[ "$EMAIL" == *@* ]] || die "Pass --email you@company.com (alerts and the APIM publisher email need a real address)"
ok "Alert email: $EMAIL"

step "2/8 Resource providers"
for ns in Microsoft.ApiManagement Microsoft.CognitiveServices Microsoft.Insights Microsoft.OperationalInsights Microsoft.Logic Microsoft.Consumption Microsoft.AlertsManagement; do
  state=$(az provider show -n "$ns" --query registrationState -o tsv 2>/dev/null || echo NotRegistered)
  if [[ "$state" != "Registered" ]]; then warn "Registering $ns ($state)"; az provider register -n "$ns" >/dev/null; else ok "$ns"; fi
done

step "3/8 Model behind the gateway"
export MCCP_EXISTING_FOUNDRY_ACCOUNT="" MCCP_EXISTING_FOUNDRY_RG=""
DEPLOYMENT_NAME="${MCCP_MODEL_DEPLOYMENT:-policy-model}"
if [[ -n "$ATTACH_RG" ]]; then
  az group show -n "$ATTACH_RG" >/dev/null 2>&1 || die "Resource group $ATTACH_RG not found (the lab from infra/live.bicep may have been deleted). Re-create it from the repo root (cd ../.. && make live) or deploy without --attach-rg."
  ACCOUNT=$(az cognitiveservices account list -g "$ATTACH_RG" --query "[?kind=='AIServices'] | [0].name" -o tsv)
  [[ -n "$ACCOUNT" ]] || die "No AIServices (Foundry) account in $ATTACH_RG"
  az cognitiveservices account deployment show -g "$ATTACH_RG" -n "$ACCOUNT" --deployment-name "$DEPLOYMENT_NAME" >/dev/null 2>&1 \
    || die "Deployment '$DEPLOYMENT_NAME' not found on $ACCOUNT. Set MCCP_MODEL_DEPLOYMENT to an existing deployment name."
  MODEL=$(az cognitiveservices account deployment show -g "$ATTACH_RG" -n "$ACCOUNT" --deployment-name "$DEPLOYMENT_NAME" --query "properties.model.[name,version]" -o tsv | tr '\t' ' ')
  PROJECT="${MCCP_PROJECT_NAME:-security-project}"
  az resource show -g "$ATTACH_RG" --resource-type Microsoft.CognitiveServices/accounts/projects -n "$ACCOUNT/$PROJECT" >/dev/null 2>&1 \
    || die "Project '$PROJECT' not found on $ACCOUNT. Set MCCP_PROJECT_NAME."
  export MCCP_EXISTING_FOUNDRY_ACCOUNT="$ACCOUNT" MCCP_EXISTING_FOUNDRY_RG="$ATTACH_RG" MCCP_PROJECT_NAME="$PROJECT"
  [[ -n "$LOCATION" ]] || LOCATION=$(az group show -n "$ATTACH_RG" --query location -o tsv)
  ok "ATTACH: $ACCOUNT / project $PROJECT / deployment $DEPLOYMENT_NAME ($MODEL) in $ATTACH_RG — no changes to it except one role assignment"
else
  [[ -n "$LOCATION" ]] || LOCATION="eastus2"
  M="${MCCP_MODEL_NAME:-gpt-5-mini}"; V="${MCCP_MODEL_VERSION:-2025-08-07}"; CAP="${MCCP_MODEL_CAPACITY:-20}"
  n=$(az cognitiveservices model list -l "$LOCATION" --query "length([?model.name=='$M' && model.version=='$V' && contains(model.skus[].name, 'GlobalStandard')])" -o tsv 2>/dev/null || echo "?")
  if [[ "$n" == "0" ]]; then die "$M $V is not offered as GlobalStandard in $LOCATION. Try --location eastus2/swedencentral or set MCCP_MODEL_NAME/MCCP_MODEL_VERSION."; fi
  [[ "$n" == "?" ]] && warn "Could not list models in $LOCATION; the deployment will tell you if $M $V is unavailable" || ok "$M $V GlobalStandard available in $LOCATION"
  free=$(az cognitiveservices usage list -l "$LOCATION" --query "[?name.value=='OpenAI.GlobalStandard.$M'] | [0].[limit,currentValue]" -o tsv 2>/dev/null | awk '{print $1-$2}')
  if [[ -n "${free:-}" ]]; then (( ${free%.*} >= CAP )) && ok "Quota: ${free%.*}K TPM free, need ${CAP}K" || die "Quota: only ${free%.*}K TPM free for $M; set MCCP_MODEL_CAPACITY lower or request quota"; else warn "Could not read quota for $M"; fi
fi
ok "Gateway region: $LOCATION · identity provider: $IDP · APIM SKU: $SKU"

step "4/8 Compile and lint the Bicep"
az bicep build --file "$MAIN" --stdout >/dev/null && ok "main.bicep compiles"
export MCCP_ALERT_EMAIL="$EMAIL" MCCP_IDENTITY_PROVIDER="$IDP" MCCP_APIM_SKU="$SKU"
az bicep build-params --file "$PARAMS" --stdout >/dev/null && ok "main.bicepparam resolves"
if [[ "$IDP" == "okta" && "${OKTA_ISSUER:-}" == "" ]]; then die "--okta needs OKTA_ISSUER (and OKTA_AUDIENCE) exported"; fi

step "5/8 Resource group"
az group create -n "$RG" -l "$LOCATION" --tags purpose=mccp-demo owner="$EMAIL" -o none && ok "$RG ($LOCATION)"

step "6/8 Validate + what-if"
az deployment group validate -g "$RG" -f "$MAIN" -p "$PARAMS" -o none && ok "ARM validation passed"
az deployment group what-if -g "$RG" -f "$MAIN" -p "$PARAMS" --result-format ResourceIdOnly
[[ $WHATIF_ONLY -eq 1 ]] && { ok "What-if only: nothing was deployed"; exit 0; }
if [[ $ASSUME_YES -ne 1 ]]; then read -r -p "Deploy now? API Management v2 usually takes 5-15 minutes. [y/N] " a; [[ "$a" =~ ^[Yy]$ ]] || exit 0; fi

step "7/8 Deploy"
NAME="mccp-$(date +%Y%m%d%H%M)"
az deployment group create -g "$RG" -n "$NAME" -f "$MAIN" -p "$PARAMS" -o none && ok "Deployment $NAME succeeded"
OUT=$(az deployment group show -g "$RG" -n "$NAME" --query properties.outputs -o json)
val() { python3 -c "import json,sys; print(json.load(sys.stdin)['$1']['value'])" <<<"$OUT"; }
APIM_ID=$(val APIM_RESOURCE_ID)
KEY=$(az rest --method post --url "https://management.azure.com${APIM_ID}/subscriptions/agent-contoso-claims-triage/listSecrets?api-version=2024-05-01" --query primaryKey -o tsv)
ENVF="$ROOT/.env.mccp.azure"
cat > "$ENVF" <<ENV
# Written by demos/mccp-multicloud-control-plane/infra/mccp/deploy.sh on $(date -u +%Y-%m-%dT%H:%MZ). Git-ignored. Loaded automatically by python -m mccp.
MCCP_IDENTITY_PROVIDER=$(val MCCP_IDENTITY_PROVIDER)
APIM_GATEWAY_URL=$(val APIM_GATEWAY_URL)
APIM_RESOURCE_ID=$APIM_ID
APIM_API_PATH=ai
APIM_SUBSCRIPTION_KEY=$KEY
FOUNDRY_PROJECT_ENDPOINT=$(val FOUNDRY_PROJECT_ENDPOINT)
FOUNDRY_MODEL_DEPLOYMENT=$(val FOUNDRY_MODEL_DEPLOYMENT)
LOG_ANALYTICS_WORKSPACE_ID=$(val LOG_ANALYTICS_WORKSPACE_ID)
ENV
grep -qx ".env.mccp.azure" "$ROOT/.gitignore" 2>/dev/null || echo ".env.mccp.azure" >> "$ROOT/.gitignore"
ok "Wrote $ENVF (subscription key for agent-contoso-claims-triage included; file is git-ignored)"

step "8/8 Smoke test through the gateway"
TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)
GW=$(val APIM_GATEWAY_URL); DEP=$(val FOUNDRY_MODEL_DEPLOYMENT)
mkdir -p "$OUTDIR"; code=000
for i in 1 2 3 4 5 6; do
  code=$(curl -s -o "$SMOKE" -w '%{http_code}' -X POST "$GW/ai/openai/deployments/$DEP/chat/completions?api-version=2025-04-01-preview" \
    -H "Authorization: Bearer $TOKEN" -H "Ocp-Apim-Subscription-Key: $KEY" -H "Content-Type: application/json" \
    -H "x-agent-id: contoso-claims-triage" -H "x-cloud: azure" -H "x-cost-center: CC-1001" \
    -d '{"messages":[{"role":"user","content":"Reply with OK"}],"max_completion_tokens":200,"reasoning_effort":"minimal"}' || echo 000)
  [[ "$code" == "200" ]] && break
  warn "HTTP $code (attempt $i/6; the role assignment can take a few minutes to apply) — retrying in 30s"; sleep 30
done
if [[ "$code" == "200" ]]; then ok "HTTP 200 through the gateway: $(python3 -c "import json;d=json.load(open('$SMOKE'));print(d['usage'])" 2>/dev/null)"
else warn "Last response: $(head -c 400 "$SMOKE" 2>/dev/null)"; fi

cat <<NEXT

Next:
  1. Portal → Application Insights $(val APPLICATIONINSIGHTS_NAME) → Usage and estimated costs → Custom metrics →
     "Enable alerting on custom metric dimensions" (the automatic kill alert splits token metrics by agent).
  2. PYTHONPATH=src python3 -m mccp call --mode azure --agent contoso-claims-triage
  3. PYTHONPATH=src python3 -m mccp kill --mode azure --agent contoso-rev-cycle-coder            # DRY_RUN
     PYTHONPATH=src python3 -m mccp kill --mode azure --agent contoso-rev-cycle-coder --authorize # real stop
     PYTHONPATH=src python3 -m mccp revive --mode azure --agent contoso-rev-cycle-coder --authorize
  Cleanup: az group delete -n $RG --yes --no-wait   (then purge the soft-deleted APIM: az apim deletedservice purge
           --service-name <name> --location $LOCATION). ATTACH mode leaves the lab's Foundry account untouched.
NEXT
