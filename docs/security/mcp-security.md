# MCP boundary

The supplied agent has no remote tools and no MCP server registration. Its read-only
tool registry is application-controlled; an LLM cannot dynamically add or call tools.

Before adding MCP, require an approved server inventory, authenticated transport,
scoped credentials, argument/result schemas, explicit data classification,
egress controls, server/tool-description change review and independent approval
for side effects. Treat tool descriptions/results as untrusted content, not authority.

Do not grant shell execution, arbitrary URL fetching, a generic cloud administrator
tool or writer access to reproduce a demo. Reject unauthorized tool requests before
invocation and record controlled status, never secret-bearing results.
No MCP protection or remote-server validation is claimed by this implementation.
