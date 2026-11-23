# Submission statements

Placeholders in [brackets] are filled with final numbers at submission time.

## 1. Problem and Solution Statement

**Problem.** In Vietnam, middle-aged and older adults are the people most harmed by health misinformation. Videos and Zalo posts promise "family remedies" and miracle cures, written in the folk language older people use every day ("trúng gió", "nóng trong", "thuốc gia truyền"). The harm is real. VietNamNet (July and August 2025) reported a man of nearly 70 with suspected stomach cancer who refused hospital care to follow a "7-day fasting and sunbathing cure", a 69-year-old woman left wheelchair-bound after years of an unlicensed joint-pain remedy laced with corticosteroids. Older adults are also the most likely to pass such content on: in a Science Advances study (Guess et al., 2019), 11% of users over 65 shared fake news links, compared with 3% of users aged 18 to 29. Younger relatives rarely push back: in a 2025 Scientific Reports survey of 1,850 young Vietnamese, only 16.2% act to stop fake news.

**Point of view.** Older Vietnamese adults need a way to check a health claim in their own words, because trusted sources (Ministry of Health, WHO) are long, hard to find and written in clinical terms that do not match how they talk.

**User.** Our primary user is Mrs. Hoa, 66, on a small pension, who receives health videos on Facebook and Zalo and forwards them to her family. Our secondary user is her grandson Minh, 24, who wants to correct her politely without starting an argument.

**Solution.** We built an agentic fact-checker for Vietnamese health claims. A user pastes a message. The agent:
1. Translates folk phrases into clinical terms and shows what it understood ("Đã hiểu: tai biến → đột quỵ").
2. Retrieves evidence from trusted Vietnamese and WHO sources.
3. Gives a colour-coded verdict (True, False, Misleading, or Not enough evidence) with a two-sentence explanation in plain Vietnamese and the source link.

If the evidence is weak, the agent searches again once. If the evidence is still weak, it refuses to guess and says "not enough evidence". Danger signs trigger "see a doctor now". A "Copy to family" button drafts a respectful message, with the source, that Minh can paste straight into the family Zalo group.

**Impact and evidence.** Because IBM Cloud could not provision watsonx.ai Runtime (catalog error), the numbers below come from offline mode; the watsonx path is implemented. On a hand-labelled set of [C] common Vietnamese health myths, the full agent reached [X]% verdict accuracy and [R]% recall@5. Our ablation shows each component's contribution: from [X0]% with plain dense retrieval to [X]% with hybrid search, folk-term normalization and the retry loop. Median response time is [Y] seconds at about [Z] per check.

**Scale.** Adding a new health topic means adding source documents and glossary entries, with no retraining. Next steps:
- A Zalo bot, so older users never leave the app they already use.
- Watsonx Orchestrate to coordinate specialized agents.
- Pilots with five older Sponsor Users and community health workers.

---

## 2. Technology Statement (IBM Bob)


**Two AI partners, one human-led workflow.** Under a 60-minute build, we split the work between two AI coding assistants and kept every decision with our team of two. Claude Code planned the project and wrote the first working version: ingestion, hybrid retrieval with Reciprocal Rank Fusion, the folk-term normalizer, the cited JSON judge, the LangGraph agent with its retry loop, the evaluation harness and the Streamlit interface. IBM Bob then became our reviewer and improver, working on that code directly in our repository.

How we used IBM Bob:
- **Reviewing (/review, Ask mode):** Bob reviewed the judge and the agent graph and listed the most severe bugs and risks for a health tool, without editing files.
- **Improving (Code mode):** Bob improved the offline judge so it detects "misleading" claims, the label our evaluation showed was weakest. We measured accuracy before and after on the same labelled claims: [B0]% to [B1]%.
- **Shipping:** Bob committed its change on its own branch and pushed it; we reviewed the diff in a pull request before merging, so the Git history shows which assistant wrote what.

**Guardrails for a health project.**
- An `agents.md` file kept Bob's rules short and enforceable:
  - always cite a source
  - never diagnose
  - Vietnamese with full diacritics
  - fixed verdict labels
  - secrets only from `.env`
- `.bobignore` kept API keys, source documents and the vector index out of Bob's context.
- We read every shell command and diff before approving it.

**Efficiency.** We used [N] Bobcoins across two accounts and [P] prompts in a 60-minute build. Exported Bob session reports are included in the repository under `docs/bob-sessions/`.

**IBM watsonx.ai.**
- **LLM:** [model ID] normalizes claims and produces cited verdicts as validated JSON.
- **Embeddings:** [embedding model ID] are multilingual embeddings that power semantic retrieval in Vietnamese.
- **Status:** implemented in `src/watsonx_client.py`; an IBM Cloud catalog error blocked provisioning, so the demo runs in labelled offline mode.

**Architecture.** The agent follows a goal-based loop:
1. Perceive: normalize the folk phrase.
2. Process: hybrid retrieval.
3. Decide: LLM judge with confidence.
4. Act: verdict card and family message.
5. Re-check: retry once or decline.

This is a RAG design with five steps: prompt creation, information search, retrieval, prompt augmentation and grounded generation.

**Measured, not assumed.** Every improvement was introduced behind a feature flag and evaluated on the same [C] labelled claims. Our ablation table reports accuracy, recall@5, median latency and cost per request for each variant.

**Roadmap on IBM technology.**
- Granite Guardian for groundedness and harm checks.
- Watsonx Orchestrate for multi-agent coordination.
- IBM Code Engine for deployment.
- Watsonx.governance for monitoring once real users are involved.
