# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 상태

Streamlit으로 만드는 단일 파일 쇼핑 리스트 앱(추가 / 수정 / 삭제 / 체크)입니다. 코드는 `app.py`에 있습니다.

- `PRD.md` — 요구사항 원본. 기능 ID(F-01~F-07), 데이터 모델, 수용 기준이 있습니다. 범위를 판단할 때 이 문서를 따릅니다.
- `PROMPT.md` — PRD를 구현 지시문으로 압축한 문서입니다. PRD와 내용이 다르면 PRD를 우선하고, 두 문서를 함께 고칩니다.
- `GUIDELINES.md` — 코딩 규칙, Streamlit 패턴, 작업 절차.

## 명령어

```bash
pip install -r requirements.txt    # streamlit만 설치
python -m streamlit run app.py     # 앱 실행 (http://localhost:8501). streamlit.exe가 PATH에 없어서 python -m 으로 실행
run.bat                            # 위 명령을 더블클릭으로 실행하는 파일 (브라우저 자동으로 열림)
```

테스트 도구와 린터는 정하지 않았습니다. 검증은 PRD §8의 수용 기준 체크리스트로 합니다. 테스트를 추가한다면 순수 함수(`load_items`, `save_items`, `add_item` 등)만 `pytest`로 테스트하고, 파일 경로는 `tmp_path`로 바꿔 씁니다.

## 아키텍처

- **파일 하나:** 모든 코드는 `app.py`에 둡니다. `requirements.txt`에는 `streamlit`만 넣습니다.
- **데이터 흐름:** 시작할 때 `shopping_list.json`을 읽어 `st.session_state.shopping_items`에 넣습니다. 사용자가 무언가를 바꾸면 아이템 함수로 `items`를 고친 뒤, 곧바로 `save_items()`로 파일 전체를 다시 저장하고 `st.rerun()`을 호출합니다.
- **파일이 진짜 기준:** 저장은 바뀔 때마다 즉시 하고, 새로고침하면 파일에서 다시 불러옵니다. 캐시나 저장 지연은 쓰지 않습니다.
- **session_state 키 이름:** `items`, `keys`, `values`, `get` 같은 이름은 쓰지 않습니다. `st.session_state.items`는 저장한 값이 아니라 dict 메서드를 가리킵니다. 그래서 목록은 `shopping_items`에 둡니다.
- **수정 모드:** `st.session_state.editing_id`에 수정 중인 아이템 id 하나만 둡니다. 값이 있으면 그 행만 입력창과 저장/취소 버튼으로 바뀝니다.
- **위젯 key:** 아이템 행의 위젯 key는 반드시 아이템의 `id`(uuid4)로 만듭니다(`f"check_{id}"`, `f"del_{id}"`). 목록 순서 번호를 쓰면 삭제 후 key가 엉킵니다.
- **꾸미기:** 헤더 일러스트는 `assets/hero.svg`를 data URI로 넣고, 색은 `.streamlit/config.toml` 테마로 정합니다. `unsafe_allow_html`은 고정 HTML/CSS에만 쓰고 사용자 입력에는 쓰지 않습니다. 자세한 규칙은 `GUIDELINES.md` §4에 있습니다.
- **망가진 저장 파일:** JSON 파일이 없거나 파싱할 수 없으면 빈 리스트로 시작합니다. 앱을 멈추면 안 됩니다.

## 범위

PRD §7(범위 외)에 있는 기능은 추가하지 않습니다. 로그인, DB, 카테고리, 가격, 드래그 정렬 등이 해당합니다. UI 문구는 모두 한국어로 씁니다.
