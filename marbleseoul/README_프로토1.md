# Marble서울 Prototype v0.1 – README

본 문서는 "프로토 버전 1차"(단계 2까지) 실행 가이드를 제공합니다.

---

## 1. 환경 준비

### 1.1 의존 패키지 설치 (Windows PowerShell)
```powershell
chcp 65001; # UTF-8
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

필수 주요 라이브러리:
- streamlit
- streamlit-folium
- folium
- langchain
- openai (선택)

### 1.2 환경 변수
```
setx OPENAI_API_KEY "sk-..."   # LangChain LLM 사용 시
```

---

## 2. 실행 방법

```powershell
chcp 65001;  # UTF-8 설정
streamlit run marble/marbleseoul/app/main.py
```

브라우저에서 `http://localhost:8501` 로 접속하면 다음 UI가 표시됩니다:
1. 좌측 – 서울 지도(기본 로드)
2. 우측 – 챗봇 인터페이스(응답 Echo 또는 OpenAI 연결)

---

## 3. 기능 요약
| 구분 | 설명 |
|------|------|
| 지도 렌더러 | Folium + streamlit-folium 로 서울 중심 맵 표시 |
| 챗봇 UI | Streamlit `st.chat_message` 사용, LangChain ConversationChain 연결 |
| 세션 상태 | `session_state.py` – `AppState` dataclass로 상태 유지 |

---

## 4. 다음 단계 로드맵
- 단계 3: 서울 전체 평균매매가 계산 및 지도·챗봇 오버레이
- 단계 4: 자치구 랭킹 기능

---

## 5. 변경 이력
| 날짜 | 내용 |
|------|------|
| 2025-08-02 | README 최초 작성 – 설치/실행/기능 요약 | 