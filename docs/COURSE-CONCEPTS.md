# Course concepts applied in this project

The IBM SkillsBuild course covers Enterprise Design Thinking, AI agents, RAG, multi-agent systems and IBM Bob. This is where each one shows up in the project.

## Enterprise Design Thinking
- **Problem statement:** Older Vietnamese adults struggle to tell true from false health claims on Facebook and Zalo, because misinformation uses the folk phrasing they know, while official sources are long, hard to find and written in clinical terms. (It names the user and does not mention the solution.)
- **Hill:** *Who* Mrs. Hoa (66) and her grandson Minh (24). *What* paste a message and within seconds know whether it is true, false or misleading, with a Ministry of Health or WHO source, in their own words. *Wow* measured accuracy, latency and cost on a labelled eval set, with every verdict cited.
- **Empathy map (Mrs. Hoa):** *Says* "My neighbour was cured by this family remedy." *Thinks* "The hospital is expensive; I don't want to bother my children." *Does* forwards videos to the family Zalo group and buys remedies online. *Feels* worried about illness; trusts acquaintances more than online doctors.
- **As-is → To-be:** Mrs. Hoa forwards a video and Minh stays quiet (only 16.2% of young Vietnamese push back) → Minh pastes it into the tool, sees "False" and "Understood: tai biến → đột quỵ (stroke)", and taps *Copy to family*.
- **Principles:** focus on user outcomes (large text, folk language, copy button); restless reinvention (every change re-measured by the eval, an Observe–Reflect–Make loop); diverse empowered teams.
- **Playback and Sponsor Users:** the pitch opens with Mrs. Hoa's story, not the architecture; the roadmap pilots with five Sponsor Users over 60.

## AI agents
A **goal-based agent** with the loop Perceive (normalize folk terms) → Process (hybrid retrieval) → Decide (cited judge with confidence) → Act (verdict card, family message) → Re-check (retry once with an expanded query, otherwise decline). Implemented with LangGraph in `src/graph.py`.

## RAG (five steps)
1. Prompt creation: the normalized claim.
2. Information search: BM25 + dense embeddings, fused with Reciprocal Rank Fusion.
3. Retrieval: top-5 chunks from trusted sources.
4. Prompt augmentation: chunks inserted into the judge prompt.
5. Grounded generation: a JSON verdict that must cite a chunk, else "Not enough evidence".

## Multi-agent systems (roadmap)
Split normalization, retrieval and safety checks into separate agents coordinated by watsonx Orchestrate, with Granite Guardian as a safety agent.

## IBM Bob
`agents.md` holds short, enforceable project rules; `.bobignore` keeps secrets and data out of context. Bob was used to review the judge and agent graph (/review, Ask mode), improve the offline judge (Code mode) and commit on its own branch, reviewed through a pull request. Session reports go in `docs/bob-sessions/`.
