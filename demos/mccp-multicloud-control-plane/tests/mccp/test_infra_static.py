"""Static checks of infra/mccp that catch the usual Bicep compile errors without the Bicep CLI:
module paths, parameters passed vs declared, outputs referenced vs declared, loadTextContent paths,
and both identity variants of the gateway policy. `az bicep build` (deploy.sh step 4) is still the real check."""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INFRA = REPO / "infra" / "mccp"


def block_after(text: str, start: int) -> str:
    """Text of the {...} block that starts at the first '{' at or after start."""
    i = text.index("{", start)
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    raise ValueError("unbalanced braces")


def top_level_keys(body: str) -> set[str]:
    keys, depth = set(), 0
    for line in body.splitlines():
        stripped = line.split("//")[0]
        if depth == 0:
            m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", stripped)
            if m:
                keys.add(m.group(1))
        depth += stripped.count("{") + stripped.count("[") - stripped.count("}") - stripped.count("]")
    return keys


def declared(path: Path, kind: str) -> dict[str, bool]:
    """param/output names -> has default (params only)."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(rf"^{kind}\s+([A-Za-z_][A-Za-z0-9_]*)\s+\S+(\s*=)?", line)
        if m:
            out[m.group(1)] = bool(m.group(2))
    return out


def modules(path: Path):
    text = path.read_text(encoding="utf-8")
    for m in re.finditer(r"^module\s+(\w+)\s+'([^']+)'", text, re.M):
        body = block_after(text, m.end())
        pm = re.search(r"\bparams\s*:", body)
        params = top_level_keys(block_after(body, pm.end())) if pm else set()
        yield m.group(1), (path.parent / m.group(2)).resolve(), params


class InfraStaticTests(unittest.TestCase):
    bicep_files = sorted([INFRA / "main.bicep", *(INFRA / "modules").glob("*.bicep")])

    def test_module_paths_and_params_match(self):
        for f in self.bicep_files:
            for name, target, passed in modules(f):
                self.assertTrue(target.exists(), f"{f.name}: module {name} -> missing {target}")
                params = declared(target, "param")
                unknown = passed - set(params)
                missing = {p for p, has_default in params.items() if not has_default} - passed
                self.assertFalse(unknown, f"{f.name}: module {name} passes undeclared params {unknown}")
                self.assertFalse(missing, f"{f.name}: module {name} misses required params {missing}")

    def test_module_outputs_referenced_exist(self):
        for f in self.bicep_files:
            text = f.read_text(encoding="utf-8")
            mods = {name: target for name, target, _ in modules(f)}
            for name, out in re.findall(r"\b(\w+)!?\.outputs\.(\w+)", text):
                self.assertIn(name, mods, f"{f.name}: {name} is not a module")
                self.assertIn(out, declared(mods[name], "output"), f"{f.name}: {name}.outputs.{out} not declared")

    def test_load_text_content_paths_exist(self):
        for f in self.bicep_files:
            for rel in re.findall(r"loadTextContent\('([^']+)'\)", f.read_text(encoding="utf-8")):
                self.assertTrue((f.parent / rel).exists(), f"{f.name}: missing {rel}")

    def test_bicepparam_sets_only_declared_params(self):
        params = declared(INFRA / "main.bicep", "param")
        text = (INFRA / "main.bicepparam").read_text(encoding="utf-8")
        self.assertIn("using './main.bicep'", text)
        for name in re.findall(r"^param\s+(\w+)\s*=", text, re.M):
            self.assertIn(name, params, f"main.bicepparam sets unknown param {name}")
        required = {p for p, d in params.items() if not d}
        set_names = set(re.findall(r"^param\s+(\w+)\s*=", text, re.M))
        self.assertFalse(required - set_names, f"required params not set: {required - set_names}")
        self.assertNotIn("@", "".join(re.findall(r"'([^']*)'", text)).replace("@{", ""), "no email addresses in bicepparam")

    def test_no_placeholder_email_or_retired_model(self):
        for f in [*self.bicep_files, INFRA / "main.bicepparam"]:
            t = f.read_text(encoding="utf-8")
            self.assertNotIn("contoso-health.example", t.replace("contoso-health.okta.example", ""), f.name)
            self.assertNotIn("gpt-4.1", t, f"{f.name}: gpt-4.1 family is deprecated (retires 2027-04-14)")
        self.assertFalse((INFRA / "main.parameters.json").exists())

    def _policy(self, idp: str) -> str:
        s = (INFRA / "policies" / "ai-gateway.xml").read_text(encoding="utf-8")
        for t in ("__TPM_PER_AGENT__", "__AGENT_MONTHLY_TOKEN_QUOTA__", "__USER_TIER2_MONTHLY_TOKEN_QUOTA__", "__USER_MONTHLY_TOKEN_QUOTA__"):
            s = s.replace(t, "1000")
        disabled = "ENTRA" if idp == "okta" else "OKTA"  # mirrors apim.bicep
        s = s.replace(f"<!--__{disabled}_BEGIN__-->", f"<!-- {disabled.lower()} identity block disabled at deploy time")
        return s.replace(f"<!--__{disabled}_END__-->", "-->")

    def test_policy_identity_switch(self):
        apim = (INFRA / "modules" / "apim.bicep").read_text(encoding="utf-8")
        self.assertIn("<!--__${disabled}_BEGIN__-->", apim)
        self.assertIn("<!--__${disabled}_END__-->", apim)
        for idp, expect in (("entra", "login.microsoftonline.com/{{entra-tenant-id}}/v2.0/.well-known"),
                            ("okta", "{{okta-issuer}}/.well-known")):
            x = self._policy(idp)
            comments = re.findall(r"<!--(.*?)-->", x, re.S)
            self.assertFalse([c for c in comments if "--" in c], f"{idp}: '--' inside an XML comment")
            live = re.sub(r"<!--.*?-->", "", x, flags=re.S)
            self.assertNotIn("<!--", live)
            self.assertNotIn("-->", live)
            self.assertEqual(live.count("<validate-jwt"), 1, idp)
            self.assertIn(expect, live)
            self.assertTrue(live.lstrip().startswith("<policies>"))
            self.assertIsNone(re.search(r"__[A-Z0-9_]+__", live), f"{idp}: unreplaced token")
        self.assertIn("https://sts.windows.net/{{entra-tenant-id}}/", self._policy("entra"))

    def test_killswitch_reads_named_value_with_list_value(self):
        k = (INFRA / "modules" / "killswitch.bicep").read_text(encoding="utf-8")
        self.assertIn("/namedValues/killed-agents/listValue", k)
        self.assertNotIn("[\\'properties\\']?[\\'value\\']", k)
        self.assertNotIn("https://management.azure.com", k)

    def test_subscription_scope_format(self):
        apim = (INFRA / "modules" / "apim.bicep").read_text(encoding="utf-8")
        self.assertIn("scope: '/products/${product.name}'", apim)
        self.assertIn("instrumentationKey:", apim)


if __name__ == "__main__":
    unittest.main()
