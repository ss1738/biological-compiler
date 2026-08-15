# MCP Stack: What's Actually Verified

The original install list had real errors in it: wrong package names, at least one unconfirmed endpoint. Every entry below was checked directly (npm registry, official docs, or a direct fetch of the endpoint) before being marked verified, then actually installed and health-checked via `claude mcp list`. Package existing and package *connecting* turned out to be two different things.

First install attempt was scoped to whatever project directory happened to be open at the time, which meant none of it was actually usable from this repo. Fixed: everything general-purpose is registered at user (global) scope now, so it's available regardless of which project is open. `filesystem` still points specifically at this repo's path, since that's its whole purpose.

## Installed and connected (`claude mcp list` shows ✔, user scope)

| Server | Install | Notes |
|---|---|---|
| Context7 | `claude mcp add -s user context7 -- npx -y @upstash/context7-mcp` | Verified on npm, v4.0.2, actively maintained by Upstash |
| Firecrawl | `claude mcp add -s user firecrawl -- npx -y firecrawl-mcp` | Verified on npm, v3.24.0, actively maintained |
| Playwright | `claude mcp add -s user playwright -- npx -y @playwright/mcp` | Verified, official Microsoft package |
| Filesystem | `claude mcp add -s user filesystem -- npx -y @modelcontextprotocol/server-filesystem <path>` | Verified, official |
| Sequential Thinking | `claude mcp add -s user sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking` | The originally requested package name (`sequentialthinking-mcp`) does not exist: 404 on npm. This is the real one, official, verified, connected. |

## Not connecting yet, real fixes identified

| Server | Error | Fix |
|---|---|---|
| Brave Search | `Connection closed` | Needs a `BRAVE_API_KEY` environment variable. Confirmed via the project's actual README (`github.com/mikechao/brave-search-mcp`), not guessed. Get a key at [api.search.brave.com/app/keys](https://api.search.brave.com/app/keys), then: `claude mcp add-json brave-search '{"command":"npx","args":["-y","brave-search-mcp"],"env":{"BRAVE_API_KEY":"YOUR_KEY"}}'` |
| Exa | `Connection closed` | Needs an `EXA_API_KEY` environment variable, confirmed via the package's README. Get a key at [dashboard.exa.ai/api-keys](https://dashboard.exa.ai/api-keys). Also worth knowing: last published version is 0.0.7 from April 2025, over a year stale as of this writing, so this may be an unmaintained package rather than just a missing-key issue. |
| GitHub MCP | `Incompatible auth server: does not support dynamic client registration` | The endpoint is real, but this auth flow didn't work as configured. Probably needs a PAT/token passed a different way rather than OAuth dynamic client registration. Not resolved yet. |

## Needs manual setup, not a `claude mcp add` install

| Server | Why it's different |
|---|---|
| Higgsfield | It's an OAuth connector: URL `https://mcp.higgsfield.ai/mcp`, added via Claude's Connectors UI, sign-in required through a Higgsfield account. Draws credits from that account, not free, not API-key-based. |

## Not installed

| Server | Why |
|---|---|
| Perplexity | The requested URL (`https://docs.perplexity.ai/mcp`) returned HTTP 405 on a direct check, consistent with a real JSON-RPC-only endpoint but not proof of one. No independent confirmation this is Perplexity's actual documented MCP offering. Not adding an unverified remote endpoint without clearer confirmation. If you have a link to Perplexity's actual MCP docs, send it and this gets redone properly. |

**Raw note:** "verified" here means the package exists and the endpoint responds as expected for its type. It doesn't mean any of these have been used enough to vouch for how well they work in practice. That's a different, longer test.
