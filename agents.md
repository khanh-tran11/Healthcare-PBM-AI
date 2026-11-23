# Project rules for IBM Bob

Project: Vietnamese health-claim fact-checker for middle-aged and older adults. RAG + LangGraph agent on IBM watsonx.ai. Streamlit UI.

## Hard rules
- Every verdict must cite at least one chunk from data/sources/. No citation -> label "chua_du_bang_chung".
- Never diagnose or prescribe. Always include the warning "Thông tin tham khảo, không thay thế bác sĩ".
- All user-facing text is Vietnamese with full diacritics, short sentences, no medical jargon without explanation.
- Labels are exactly: dung, sai, gay_hieu_lam, chua_du_bang_chung.
- Read secrets only from .env via python-dotenv. Never print, log or commit keys.
- Do not run git commit or git push unless the user asks in this chat.

## Code style
- Python 3.11, type hints, Pydantic v2 models in src/schema.py.
- One job per file. Keep functions small. No notebooks.
- Config and feature flags in src/config.py. Model IDs come from env vars.
- Do not read or modify data/sources/, index/, .venv/.
