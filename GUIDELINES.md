# 개발 가이드라인

쇼핑 리스트 앱(`app.py`)을 만들고 고칠 때 지키는 규칙입니다. 요구사항은 `PRD.md`, 구현 지시문은 `PROMPT.md`를 봅니다.

---

## 1. 코드 구조

`app.py`는 아래 순서로 씁니다.

```python
# 1) import / 상수
import json, uuid
from datetime import datetime
from pathlib import Path
import streamlit as st

DATA_FILE = Path(__file__).parent / "shopping_list.json"

# 2) 저장소 함수 — 파일 입출력만 담당
def load_items() -> list[dict]: ...
def save_items(items: list[dict]) -> None: ...

# 3) 아이템 함수 — items 리스트만 다루고 st.* 는 쓰지 않음
def add_item(items, name, quantity): ...
def update_item(items, item_id, name, quantity): ...
def delete_item(items, item_id): ...
def toggle_item(items, item_id): ...
def clear_checked(items): ...

# 4) 화면 함수
def render_header(items): ...
def render_add_form(): ...
def render_item_row(item): ...
def render_edit_row(item): ...

# 5) main()
def main(): ...

main()
```

- 저장소 함수와 아이템 함수에서는 `st.*`를 부르지 않습니다. 그래야 테스트하기 쉽습니다.
- 입력값 확인(공백 제거, 빈 이름, 수량 1 이상)은 `validate(name, quantity)` 함수 하나로 모으고, 추가와 수정에서 함께 씁니다.
- 함수에는 타입 힌트를 붙이고, 주석은 한국어로 짧게 한 줄만 씁니다.

## 2. 데이터 규칙

| 필드 | 규칙 |
| --- | --- |
| `id` | `str(uuid.uuid4())`, 만든 뒤에는 바꾸지 않음 |
| `name` | 앞뒤 공백 제거, 빈 문자열 불가 |
| `quantity` | 1 이상의 정수 |
| `checked` | 새 아이템은 `False`. 수정해도 값이 유지됨 |
| `created_at` | `datetime.now().isoformat(timespec="seconds")` |

- 저장은 `json.dump(items, f, ensure_ascii=False, indent=2)`로 하고, 파일은 `encoding="utf-8"`로 엽니다.
- 불러올 때 `OSError`나 `ValueError`(JSON 손상, UTF-8 아님)가 나면 `[]`를 돌려줍니다.
- 아이템은 `normalize_item()`으로 하나씩 정리합니다. 이름이 없으면 버리고, 수량이 이상하면 1로 바꾸고, `checked`는 `True`일 때만 참으로 두고, 중복된 id는 새로 발급합니다(중복 id는 위젯 key 충돌로 앱을 멈추게 함).
- 저장은 `.json.tmp`에 쓴 뒤 `os.replace`로 교체합니다. 저장 실패(`OSError`, OneDrive가 파일을 잠갔을 때 등)는 `persist()`가 받아서 `st.error`로 보여 줍니다.
- 필드를 새로 추가하면 `normalize_item()`에서 기본값을 채워서 예전 파일과도 호환되게 합니다.

## 3. Streamlit 패턴

- **상태 초기화:** `main()`을 시작할 때 한 번만 합니다.
  ```python
  if "shopping_items" not in st.session_state:
      st.session_state.shopping_items = load_items()
  st.session_state.setdefault("editing_id", None)
  ```
- **변경 처리 순서:** 아이템 함수 호출 → `persist()` → `st.rerun()`(콜백 안에서는 `st.rerun()` 생략).
- **위젯 key:** 아이템 id로 만듭니다(`f"check_{item['id']}"`, `f"edit_{item['id']}"`, `f"del_{item['id']}"`). `enumerate` 순서 번호는 쓰지 않습니다.
- **추가 폼:** `st.form("add_form")` 안에 `text_input(key="new_name")`, `number_input(min_value=1, step=1, key="new_qty")`, `form_submit_button("추가", on_click=on_add)`을 둡니다. 입력창은 `on_add` 콜백에서 `new_name`/`new_qty`를 직접 초기화해서 비웁니다(`clear_on_submit`은 쓰지 않음). `new_qty` 기본값은 `main()`에서 `setdefault`로 넣고, 위젯에 `value=`를 같이 주지 않습니다(두 곳에서 값을 주면 Streamlit이 경고함).
- **체크박스:** `on_change` 콜백으로 `toggle_item`을 실행한 뒤 저장합니다. 콜백 안에서는 `st.rerun()`을 부르지 않습니다(콜백이 끝나면 화면이 알아서 다시 그려집니다).
- **취소선:** 완료된 아이템 이름은 `st.markdown(f"~~{name}~~")`으로 씁니다. 이름은 `escape_md()`로 모든 ASCII 문장부호를 이스케이프해서, `$`(수식), `:`(이모지), `*`/`_`(강조)로 해석되지 않게 합니다. 이름이 들어가는 toast 메시지도 마찬가지입니다.
- **버튼 너비:** `width="stretch"`를 씁니다. `use_container_width`는 지원 종료 예정입니다.
- **행 배치:** `st.columns([0.6, 5, 1, 1])` 비율로 [체크 | 이름 x수량 | 수정 | 삭제]를 놓습니다.
- **알림:** 잘못된 입력에는 `st.warning`, 추가·삭제 완료에는 `st.toast`를 씁니다.

## 4. UI 문구와 꾸미기

| 위치 | 문구 |
| --- | --- |
| 헤더 | 🛒 쇼핑 리스트 / 오늘 장보기, 빠짐없이 챙겨요 🥕🥛🍎 (왼쪽에 `assets/hero.svg` 일러스트) |
| 진행 현황 | 🎯 완료 {n} / 전체 {m} (모두 완료되면 `· 🎉 장보기 끝!` + 풍선 한 번) |
| 입력 라벨 | 📝 아이템 이름 · 🔢 수량 |
| 버튼 | ➕추가 · ✏️수정 · 🗑️삭제 · 💾저장 · ↩️취소 · 🧹완료 항목 삭제 |
| 아이템 행 | `{이모지} **이름** :orange-badge[x수량]`, 완료되면 이름에 취소선 |
| 빈 이름 경고 | ⚠️ 아이템 이름을 입력해 주세요. |
| 빈 목록 | 🧺 장바구니가 텅 비었어요 + 💡 리스트가 비어 있어요. 살 물건을 추가해 보세요. |

- **버튼 이모지:** 라벨 글자에 넣지 않고 `icon=` 인자로 줍니다. 라벨은 글자만 남아서 테스트나 검색에서 찾기 쉽습니다.
- **아이템 이모지:** `ITEM_EMOJIS` 표에서 이름에 들어 있는 키워드 중 **가장 긴 것**을 고릅니다("배추"가 "배"보다 우선). 맞는 게 없으면 🛍️. 새 키워드는 이 표에만 추가합니다.
- **HTML:** `unsafe_allow_html=True`는 고정 CSS, 헤더, 빈 목록 그림에만 씁니다. 사용자가 입력한 이름은 절대 HTML에 넣지 않습니다.
- **테마:** 색은 `.streamlit/config.toml`의 밝은 테마(주황 `#FF7A59`)로 정합니다. CSS에서 색을 고정하므로 어두운 테마는 쓰지 않습니다.
- **풍선:** 모두 완료로 바뀌는 순간에 한 번만 띄웁니다(`celebrated` 상태). 이미 모두 완료된 목록을 열 때는 띄우지 않습니다.

## 5. 작업 절차

1. 먼저 PRD의 기능 ID(F-01~F-07)를 확인합니다. PRD에 없는 기능은 PRD를 먼저 고친 다음 구현합니다.
2. 구현은 PRD §10 순서를 따릅니다: 저장/목록 → 체크/삭제 → 수정/입력 확인 → 진행 현황/일괄 삭제.
3. 단계가 끝날 때마다 `streamlit run app.py`로 PRD §8 수용 기준 중 해당 항목을 직접 확인합니다.
4. 요구사항이 바뀌면 `PRD.md`, `PROMPT.md`, `CLAUDE.md`를 함께 고칩니다.

## 6. 하지 않는 것

- `streamlit` 말고 다른 외부 패키지(pandas, DB 드라이버 등)를 추가하지 않습니다.
- `st.cache_data`나 `st.cache_resource`로 아이템 목록을 캐시하지 않습니다. 파일과 화면 내용이 어긋날 수 있습니다.
- `app.py`를 여러 파일로 나누지 않습니다. 300줄을 넘으면 그때 다시 검토합니다.
- PRD §7(범위 외) 기능은 넣지 않습니다.
