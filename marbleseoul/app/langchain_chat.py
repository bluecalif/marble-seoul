# -*- coding: utf-8 -*-
"""langchain_chat.py
간단한 LLM 래퍼 – ConversationChain 제거하여 Pydantic v1/v2 충돌 회피.
"""
from __future__ import annotations

import os
from typing import Any
from dotenv import load_dotenv

# Streamlit secrets 지원을 위한 import
try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# 환경 변수 로드 (.env 파일 - 로컬 개발용)
load_dotenv()

try:
    # 최신 langchain-openai 패키지 구조 우선
    from langchain_openai import ChatOpenAI  # type: ignore
except ImportError:
    try:
        from langchain.chat_models import ChatOpenAI  # type: ignore
    except ImportError:
        from langchain.llms import OpenAIChat as ChatOpenAI  # type: ignore


class EchoResponder:
    """OPENAI_API_KEY 없을 시 단순 에코."""

    def invoke(self, prompt: str, **_: Any) -> str:  # noqa: D401
        return f"[echo] {prompt}"


_llm: Any | None = None


def get_api_key() -> str | None:
    """API 키를 로컬(.env) 또는 Streamlit Cloud(secrets)에서 가져옵니다."""
    # 1. 로컬 환경변수에서 확인 (.env 파일)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("🔑 API Key found in environment variables (local .env)")
        return api_key

    # 2. Streamlit secrets에서 확인 (Streamlit Cloud)
    if HAS_STREAMLIT:
        try:
            # 방법 1: st.secrets["OPENAI_API_KEY"] 직접 접근
            if "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
                print("🔑 API Key found in Streamlit secrets (cloud - method 1)")
                return api_key
            
            # 방법 2: st.secrets.get() 사용
            api_key = st.secrets.get("OPENAI_API_KEY")
            if api_key:
                print("🔑 API Key found in Streamlit secrets (cloud - method 2)")
                return api_key
                
        except Exception as e:
            print(f"🔴 Error accessing Streamlit secrets: {e}")
            # 더 자세한 디버깅을 위해 st.secrets 전체 내용 확인
            try:
                print(f"🔵 Available secrets keys: {list(st.secrets.keys())}")
            except Exception as e2:
                print(f"🔴 Cannot access secrets keys: {e2}")

    print("🔴 No API Key found in .env or Streamlit secrets")
    return None


def get_llm(force_reset: bool = False):  # noqa: D401
    global _llm
    if _llm is None or force_reset:
        print(f"🔄 {'Force resetting' if force_reset else 'Initializing'} LLM...")
        api_key = get_api_key()
        if api_key:
            print(f"🔵 Creating ChatOpenAI with API key: {api_key[:10]}...")
            _llm = ChatOpenAI(
                temperature=0.3, model_name="gpt-4o-mini", openai_api_key=api_key
            )
        else:
            print("🔴 No API key available, using EchoResponder")
            _llm = EchoResponder()
    else:
        print(f"🔵 Using cached LLM: {type(_llm)}")
    return _llm


def predict(prompt: str, context: str | None = None) -> str:
    """입력 프롬프트와 컨텍스트에 대해 LLM 응답 반환."""
    print(f"🔵 LANGCHAIN_CHAT.PREDICT CALLED")
    print(f"🔵 PROMPT: {prompt}")
    print(f"🔵 CONTEXT: {context[:100] if context else 'None'}...")

    # API 키 변경 감지를 위해 매번 강제 재설정
    llm = get_llm(force_reset=True)  
    print(f"🔵 LLM TYPE: {type(llm)}")

    # 최종 프롬프트 구성
    final_prompt = f"""
[사용자 질문]
{prompt}

[참고 데이터]
{context}

---
위 참고 데이터를 바탕으로 사용자 질문에 답변해주세요. 참고 데이터의 구체적인 수치와 정보를 활용하여 상세하게 답변해주세요.
"""
    print(f"🔵 FINAL PROMPT LENGTH: {len(final_prompt)}")

    try:
        if hasattr(llm, "invoke"):
            print("🔵 USING LLM.INVOKE")
            resp = llm.invoke(final_prompt)
            print(f"🔵 RAW RESPONSE TYPE: {type(resp)}")

            # ChatOpenAI.invoke 경우 BaseMessage 반환 → content 추출
            if hasattr(resp, "content"):
                result = resp.content  # type: ignore[attr-defined]
                print(f"🔵 EXTRACTED CONTENT: {result[:100]}...")
                return result
            # dict 형태일 경우
            if isinstance(resp, dict) and "content" in resp:
                result = resp["content"]  # type: ignore[index]
                print(f"🔵 DICT CONTENT: {result[:100]}...")
                return result
            result = str(resp)
            print(f"🔵 STRING CONVERSION: {result[:100]}...")
            return result
        elif callable(llm):
            print("🔵 USING CALLABLE LLM")
            result = llm(final_prompt)
            print(f"🔵 CALLABLE RESULT: {result[:100]}...")
            return result
        else:
            print("🔵 LLM NOT INVOKABLE OR CALLABLE")
            return "[error] LLM unavailable"
    except Exception as e:
        print(f"🔴 LANGCHAIN_CHAT ERROR: {str(e)}")
        return f"[error] {str(e)}"
