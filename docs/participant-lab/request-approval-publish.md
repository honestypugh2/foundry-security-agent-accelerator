# Lab 07: request, approval and publication with a policy template

## Learning objective

Explain how a maker's organizational submission differs from administrator
publication, agent activation and resource authorization. Demonstrate the
decision boundaries with an executable **local model**, then optionally observe
existing native configuration without changing it.

**Technical level:** L300; 25-35 minutes. **Prerequisites:** Python 3.12, the frozen
workshop environment, notebook 00 and the repository `.venv` kernel.
**Cost and permissions:** the local lab needs no Azure account, credentials,
license, service requests or model budget. The optional portal tour needs
separately authorized read access and appropriate product availability.
Read the [production/WAF disclaimer](README.md#production-and-well-architected-framework-waf-disclaimer).

Start [07: Request, approval and publication](../../notebooks/07_agent365_request_approval_publish.ipynb).
Bash and PowerShell, from the repository root:

```text
uv sync --frozen --all-extras --dev
uv run python -m fsa --mode local lifecycle e2e
```

The CLI records a new isolated local story and prints its real report/audit paths.
It refuses Azure mode. No command in this lab submits, approves, publishes,
rejects, activates, blocks, assigns access or accepts consent in a tenant.

## 1. Understand the two maker routes

| Route | Product behavior to review | Boundary |
|---|---|---|
| Copilot Studio | Submit the organizational Teams/Microsoft Copilot distribution for administrator approval [STUDIO] | Publishing inside the maker environment and requesting organizational distribution are different steps |
| Foundry | Publish to Microsoft 365 Copilot/Teams with organizational scope [FOUNDRY] | **People in your organization** requires admin approval; **Just you** does not |
| Administrator review | Microsoft 365 admin center > Agents > All agents > Requests [REQUESTS] | Review actual platform, channel, version and state; UI labels can differ during rollout |

The notebook does not create an agent in either product. It reuses the repository
local lifecycle implementation as a fictional submission. A local `REQUESTED`
status is not a native **Pending review** entry or proof of registry sync.
The existing Foundry function-tool client is not automatically publishable with
working remote tools: its handlers run in the caller, not the portal playground.
A production channel deployment needs a separately reviewed execution/identity path.

## 2. Require evidence before the independent decision

The model evaluates these seven named checks, not a fictional Microsoft scoring API:

| Check | Evidence/question |
|---|---|
| REQ01 | Are both owner and sponsor identified? |
| REQ02 | Is there a distinct synthetic agent identity? Native identity must be separately authenticated |
| REQ03 | Did the actual release gate pass for the exact proposed version? |
| REQ04 | Are consequential writes behind independent approval? |
| REQ05 | Is outbound access bounded rather than open? |
| REQ06 | Is clearance no higher than the reviewed Internal cap? |
| REQ07 | Are requested resources within the approved synthetic package and its bounded lifetime? |

In the lab, all seven pass for v1. The maker's self-approval is refused.
An independent **synthetic** `ai-admin` issues an exact, five-minute approval.
This models separation of duties; it does not authenticate a real AI
Administrator, establish their tenant role or prove that Microsoft universally
prevents every dual-role maker/admin from self-approval. Apply that organizational
requirement independently.

## 3. Review the four publication stages

The native publishing wizard covers **audience -> policy template -> permissions
and admin consent -> publish** [REQUESTS]. Review these stages; do not click them
in the optional tour.

The local model instead writes a **DRY_RUN publication receipt**. Its template,
Conditional Access and attribute strings are descriptive. No store, Entra policy,
group, OAuth permission or admin consent is changed. Its conceptual default
principles are not the real tenant's Microsoft default-policy inventory.

### Policy-template details that change the customer answer

- Templates apply to **new activation**. Editing a template does not update
  already-approved agents [TEMPLATES]. This is not a claim that editing a
  referenced native CA policy cannot affect identities already in scope.
- Microsoft defaults include several product protections, some requiring
  additional setup. Do not promise a fixed count of nine or mark Purview/Defender
  enabled from this model. The current policy list is in [TEMPLATES].
- Custom Entra policies must already exist before selection. The template
  documentation describes at least one selected agent identity for selectable CA
  policies, and separately notes that all-agent policies are automatically selected
  and cannot be overridden. Confirm the actual tenant experience [TEMPLATES].
- An `IT_Approved` custom attribute is an **example organizational approval value**,
  not a built-in automatic approval flag. Its attribute set, definition, assignment,
  CA target resources, exclusions and effective agent sign-in must all be reviewed.
- **Report-only CA does not block access.** Review impact before any separately
  authorized enforcement. This lab never changes report-only to On [CA].
- Agent-targeted CA requires the relevant agent-identity authentication flow.
  Running this repository with a developer credential or a synthetic role is not
  proof that the agent signs in as its own Entra identity [TEMPLATES, CA].
- A package policy's **All agents** scope describes who can request that package,
  not permission for every agent to access its resources [PACKAGES].

### Separate the administrative roles

| Responsibility | Required review |
|---|---|
| Organizational agent review/publication | Authorized AI Administrator or other documented permitted administrator; independent of the maker in this lab |
| Apply/create package through the template experience | The policy-template article describes AI admin package capabilities; verify exact resource type and delegated authority |
| Create packages in Entra | The access-package article specifies Identity Governance Administrator; adding OAuth API permissions or directory roles requires Global Administrator in that procedure [PACKAGES] |
| Configure agent CA | Conditional Access Administrator and supported licenses [CA] |
| Assign custom security attributes | Explicit Attribute Assignment Administrator; Global Administrator alone does not remove this prerequisite [TEMPLATES] |

Do not grant Global Administrator merely to make a demonstration work. Current
documentation has route-specific role details: verify actual scope, resource
ownership, permission type and least privilege with the responsible administrators.

## 4. Observe bounded access and a rejected update

Before local approval, both synthetic resources are **BLOCKED**. After exact
approval/publication, only reviewed local reads are **READ_ONLY**; an out-of-package
resource and WRITE remain **BLOCKED**. The synthetic package lasts **180 days in
this scenario**, not a universal product default. The five-minute approval TTL
and 180-day package lifetime are different controls.

In a real tenant, a reviewed package may contain security-group membership,
supported directory roles or API permission grants [PACKAGES]. The lab's two
abstract resource names stand in for reviewed entitlements; no real group or API
grant is exercised. Other direct grants and resource authorization still need
review before claiming access is possible *only* through a package.

The v2 candidate fails six **named** checks: REQ01, REQ03, REQ04, REQ05, REQ06 and
REQ07. REQ02 still passes. Additional allowlist findings can also be present.
The model refuses approval/publication of that candidate, retains version 1 and
confirms a v1 read still works. Native **Pending update** and retaining the
previous available version are documented separately [REQUESTS].

## 5. Optional read-only portal observation

Use only already-existing, authorized synthetic examples. Do not submit a new
request just to populate the page. Keep records private; record labels and
outcomes, not tenant IDs, resource endpoints, identity IDs or customer content.

| Observation | Record privately |
|---|---|
| Agents > Settings > Templates visible? | NOT_CHECKED / observed / blocked, with time and narrow reason |
| Existing custom template and selected CA/package visible? | Actual descriptive state; visibility is not enforcement |
| Agents > All agents > Requests accessible? | Actual available filters, including Pending review/update/activate if shown |
| Existing request's owner, sponsor, version and channel visible? | Scope match without copying identifiers |
| Existing package's resource roles, request scope and expiration visible? | Whether the reviewed group/API grants and duration actually match |
| Existing CA state and authenticated subject independently verified? | Report-only vs On, applicable target resources and actual agent sign-in evidence |
| Native audit, Defender or Purview evidence present? | Separate actual observation, or UNKNOWN; never substitute local audit |

**Stop before** Add template, Save, Publish to store, Update in store, Activate,
Approve, Reject, Block/Unblock, grant consent, assign attributes/packages or
change CA. Missing access, missing features or service errors are blockers, not
permission to remediate. Existing inventory does not establish this lifecycle path.

## Expected results and security explanation

- `kind=LOCAL_SIMULATION_NOT_AGENT365_OR_ENTRA`;
  `platform_actions=NOT_EXECUTED`; all supplied publication receipts are DRY_RUN.
- Fresh local report, seven initial checks, self-approval refusal, package-bounded
  reads, blocked writes/outside-package reads, rejected v2 and retained v1.
- Hash-linked local audit verifies against its retained head. This is not a
  Purview event, immutable remote anchor or authenticated tenant approval.
- Product licensing, government-cloud availability, feature previews and the
  current tenant rollout remain separately verifiable. Do not label every linked
  feature GA: agent risk is explicitly preview in [CA], and the template article
  has Frontier/AI-teammate limitations. Never promise GCC/GCCH/DoD parity.

## Troubleshooting

If imports fail, select the prepared repository kernel; do not install packages
inside notebook cells. If a local assertion fails, retain the actual report and
investigate rather than modifying expected results. If a portal page is blocked
or absent, use the local notebook and record the native observation as unverified.
The local-only CLI deliberately rejects `--mode azure lifecycle e2e`.

## Cleanup

The notebook uses a scoped temporary directory and explicitly cleans it up in its
final cell. The CLI retains ignored local lifecycle evidence; remove only the
specific generated run directory after retaining any required evidence. Never
delete original audit evidence merely to make verification pass. Clear notebook
outputs before sharing. No cloud cleanup is needed because no cloud mutation ran.

## Source modules and official references

Implementation: [lifecycle.py](../../src/foundry_security_accelerator/lifecycle.py),
[audit.py](../../src/foundry_security_accelerator/audit.py),
[CLI](../../src/foundry_security_accelerator/cli.py),
[tests](../../tests/test_lifecycle.py). Source code is not proof of native integration.

- [REQUESTS: Manage agent requests](https://learn.microsoft.com/en-us/microsoft-agent-365/admin/agent-requests)
- [TEMPLATES: Agent 365 policy templates](https://learn.microsoft.com/en-us/microsoft-agent-365/admin/policy-template)
- [PACKAGES: Access packages for agent identities](https://learn.microsoft.com/en-us/entra/agent-id/agent-access-packages)
- [CA: Secure autonomous agents with Conditional Access](https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-autonomous-agents)
- [FOUNDRY: Publish to Microsoft Copilot and Teams](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot)
- [STUDIO: Connect Copilot Studio agents to Teams and Microsoft Copilot](https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams)
- [Foundry and Agent 365 integration](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-365-integration)
- [Agent 365 overview and current prerequisites](https://learn.microsoft.com/en-us/microsoft-agent-365/overview)

Use the topic-specific current guidance where the broader integration overview
uses earlier terminology. Read-only observation is not permission to follow the
mutation steps in linked product articles.
