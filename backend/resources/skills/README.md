# Curated SkillNet reference packages

30 packages from qing1989620/skillnet-demo at `0af2de6a9c8b129e174e3442b67c5f7cb4324db9`.
These are selected for personal deployment, coding, debugging, documents and data tasks. This is a focused product selection, not a global quality ranking.

`catalog.json` records each original repository, exact commit, source URL, license and per-file hashes. All 221 packaged source files are unchanged, including attribution/license files. Chinese titles/summaries and relations to Xinxin base capabilities are adaptations authored for this platform; the upstream skill instructions have not been rewritten. Attribution applies independently of this project's private status.

- Alireza Rezvani / [claude-skills](https://github.com/alirezarezvani/claude-skills), revision `19392f7a08264ed00486a251f5b2098321771f94`: MIT, original notices retained per package.
- Contributors to [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills), revision `ec0254763ac8d61a810899fe8d961c1ac01215e8`: original code MIT; original written content [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), subject to more specific upstream notices. The skill-security-audit package is CC0-1.0. Supplied `LICENSE`, `LICENSE-CONTENT`, and other package attributions are retained. Original authorship/frontmatter, source links and full resource hashes remain available.
- K-Dense Inc. / [scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills), revision `92ace75ac21efe19a620434e0ca4e356081fe807`: MIT, original notices retained per package.

The runtime reads only listed resources, checks their hashes, confines paths and returns 6,000-character pages. Scripts are reference data and are never imported or executed on load. References to other tools, models, services or skills do not install those dependencies. Runtime permissions and tool verification remain separate. Do not equate a checked resource hash with an execution certification.

Reproduce using `python scripts/curate_skillnet.py <local-pinned-skillnet-checkout>`. The source checkout is an offline import input and is not a runtime dependency.
