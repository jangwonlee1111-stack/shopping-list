import base64
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "shopping_list.json"
HERO_IMAGE = BASE_DIR / "assets" / "hero.svg"

# 이름에 키워드가 들어 있으면 해당 이모지를 붙임 (가장 긴 키워드가 우선)
ITEM_EMOJIS = [
    (("두유",), "🥛"), (("우유", "밀크"), "🥛"), (("계란", "달걀", "메추리알"), "🥚"),
    (("치즈",), "🧀"), (("버터",), "🧈"), (("요거트", "요구르트"), "🍶"),
    (("빵", "식빵", "베이글"), "🍞"), (("케이크",), "🍰"), (("쿠키", "과자"), "🍪"),
    (("초콜릿", "초코"), "🍫"), (("사탕", "젤리"), "🍬"), (("아이스크림",), "🍨"),
    (("사과",), "🍎"), (("배",), "🍐"), (("바나나",), "🍌"), (("포도",), "🍇"),
    (("딸기",), "🍓"), (("수박",), "🍉"), (("귤", "오렌지", "한라봉"), "🍊"),
    (("레몬",), "🍋"), (("복숭아",), "🍑"), (("체리",), "🍒"), (("망고",), "🥭"),
    (("파인애플",), "🍍"), (("키위",), "🥝"), (("블루베리",), "🫐"), (("토마토",), "🍅"),
    (("당근",), "🥕"), (("감자",), "🥔"), (("고구마",), "🍠"), (("양파",), "🧅"),
    (("마늘",), "🧄"), (("오이",), "🥒"), (("브로콜리",), "🥦"), (("양배추", "배추", "상추", "시금치", "채소", "야채"), "🥬"),
    (("고추", "파프리카", "피망"), "🌶️"), (("옥수수",), "🌽"), (("버섯",), "🍄"), (("아보카도",), "🥑"),
    (("소고기", "돼지고기", "고기", "삼겹살", "차돌", "스테이크"), "🥩"), (("닭", "치킨"), "🍗"),
    (("햄", "베이컨", "소시지"), "🥓"), (("생선", "고등어", "연어", "참치"), "🐟"),
    (("새우",), "🦐"), (("오징어", "문어"), "🦑"), (("두부",), "🧊"),
    (("쌀", "밥"), "🍚"), (("라면", "국수", "면", "파스타"), "🍜"), (("김치",), "🥬"),
    (("김",), "🍙"), (("피자",), "🍕"), (("햄버거",), "🍔"),
    (("커피",), "☕"), (("차", "녹차"), "🍵"), (("주스",), "🧃"), (("물", "생수"), "💧"),
    (("맥주",), "🍺"), (("와인",), "🍷"), (("소주", "술"), "🍶"), (("콜라", "사이다", "음료"), "🥤"),
    (("소금", "설탕", "간장", "된장", "고추장", "소스", "케첩", "기름"), "🧂"),
    (("휴지", "티슈", "물티슈", "화장지"), "🧻"), (("세제", "비누", "샴푸", "린스"), "🧴"),
    (("칫솔", "치약"), "🪥"), (("면도기",), "🪒"), (("건전지", "배터리"), "🔋"), (("꽃",), "💐"),
]
DEFAULT_EMOJI = "🛍️"

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
.hero {
    display: flex; align-items: center; gap: 18px;
    padding: 18px 24px; margin-bottom: 8px; border-radius: 22px;
    background: linear-gradient(135deg, #FFE1D2 0%, #FFF3C4 100%);
    box-shadow: 0 6px 18px rgba(255, 122, 89, 0.18);
}
.hero img { width: 110px; height: auto; flex-shrink: 0; }
.hero h1 {
    font-family: 'Jua', sans-serif; font-size: 2.4rem; font-weight: 400;
    margin: 0; padding: 0; color: #3D3A36;
}
.hero p { margin: 4px 0 0; color: #7A6A5E; font-size: 1rem; }
.empty-state { text-align: center; padding: 28px 0 8px; }
.empty-state .big { font-size: 3.6rem; line-height: 1.2; }
.empty-state .hint { color: #7A6A5E; margin-top: 6px; }
@media (max-width: 480px) {
    .hero { padding: 14px 16px; gap: 12px; }
    .hero img { width: 72px; }
    .hero h1 { font-size: 1.8rem; }
}
</style>
"""


# ---------- 저장소 ----------

def now_iso() -> str:
    # 현재 시각을 ISO 8601 문자열로 반환
    return datetime.now().isoformat(timespec="seconds")


def normalize_item(raw, seen_ids: set[str]) -> dict | None:
    # 파일에서 읽은 아이템 하나를 올바른 형태로 정리 (쓸 수 없으면 None)
    if not isinstance(raw, dict):
        return None
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    try:
        quantity = max(int(raw.get("quantity", 1)), 1)
    except (TypeError, ValueError):
        quantity = 1
    item_id = raw.get("id")
    if not isinstance(item_id, str) or not item_id or item_id in seen_ids:
        item_id = str(uuid.uuid4())
    seen_ids.add(item_id)
    created_at = raw.get("created_at")
    return {
        "id": item_id,
        "name": name.strip(),
        "quantity": quantity,
        "checked": raw.get("checked") is True,
        "created_at": created_at if isinstance(created_at, str) else now_iso(),
    }


def load_items() -> list[dict]:
    # JSON 파일에서 아이템 목록을 읽음 (없거나 손상되면 빈 리스트)
    try:
        with DATA_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    seen_ids: set[str] = set()
    items = [normalize_item(raw, seen_ids) for raw in data]
    return [item for item in items if item]


def save_items(items: list[dict]) -> None:
    # 아이템 목록 전체를 임시 파일에 쓴 뒤 교체 (저장 중 꺼져도 파일이 깨지지 않음)
    tmp = DATA_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


# ---------- 아이템 로직 ----------

def validate(name: str, quantity) -> tuple[str, int, str | None]:
    # 입력값 검증: (정리된 이름, 수량, 오류 메시지 또는 None)
    name = (name or "").strip()
    if not name:
        return name, 1, "아이템 이름을 입력해 주세요."
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return name, 1, "수량은 1 이상의 숫자로 입력해 주세요."
    if quantity < 1:
        return name, quantity, "수량은 1 이상의 숫자로 입력해 주세요."
    return name, quantity, None


def add_item(items: list[dict], name: str, quantity: int) -> dict:
    # 새 아이템을 리스트 맨 아래에 추가
    item = {
        "id": str(uuid.uuid4()),
        "name": name,
        "quantity": quantity,
        "checked": False,
        "created_at": now_iso(),
    }
    items.append(item)
    return item


def update_item(items: list[dict], item_id: str, name: str, quantity: int) -> None:
    # 이름과 수량만 변경 (체크 상태 유지)
    for item in items:
        if item["id"] == item_id:
            item["name"] = name
            item["quantity"] = quantity
            return


def delete_item(items: list[dict], item_id: str) -> None:
    # 해당 id의 아이템만 삭제
    items[:] = [item for item in items if item["id"] != item_id]


def toggle_item(items: list[dict], item_id: str) -> None:
    # 구매 완료 상태 전환
    for item in items:
        if item["id"] == item_id:
            item["checked"] = not item["checked"]
            return


def clear_checked(items: list[dict]) -> int:
    # 완료된 아이템을 모두 삭제하고 삭제 개수 반환
    before = len(items)
    items[:] = [item for item in items if not item["checked"]]
    return before - len(items)


# ---------- 화면 ----------

def escape_md(text: str) -> str:
    # 모든 ASCII 문장부호를 이스케이프해 마크다운·수식($)·이모지(:)로 해석되지 않게 함
    return re.sub(r"([!-/:-@\[-`{-~])", r"\\\1", text)


def persist() -> None:
    # 현재 목록을 저장하고, 실패하면 화면에 표시할 오류를 남김
    try:
        save_items(st.session_state.shopping_items)
    except OSError as e:
        st.session_state.save_error = f"저장하지 못했어요. 파일이 다른 프로그램에서 열려 있는지 확인해 주세요. ({e})"


def commit(message: str | None = None) -> None:
    # 변경 사항 저장 후 화면 갱신
    persist()
    if message:
        st.session_state.flash = message
    st.rerun()


def on_toggle(item_id: str) -> None:
    # 체크박스 콜백 (콜백 종료 후 자동으로 다시 그려짐)
    toggle_item(st.session_state.shopping_items, item_id)
    persist()


def on_add() -> None:
    # 추가 버튼 콜백: 검증 → 추가 → 저장 → 입력창 초기화
    name, quantity, error = validate(st.session_state.new_name, st.session_state.new_qty)
    if error:
        st.session_state.add_error = error
        return
    add_item(st.session_state.shopping_items, name, quantity)
    persist()
    st.session_state.flash = f"'{escape_md(name)}'을(를) 추가했어요."
    st.session_state.new_name = ""
    st.session_state.new_qty = 1


def item_emoji(name: str) -> str:
    # 가장 길게 일치하는 키워드의 이모지 반환 ("배추"가 "배"보다 우선, 없으면 기본 쇼핑백)
    best, best_len = DEFAULT_EMOJI, 0
    for keywords, emoji in ITEM_EMOJIS:
        for keyword in keywords:
            if keyword in name and len(keyword) > best_len:
                best, best_len = emoji, len(keyword)
    return best


@st.cache_data
def hero_image_uri() -> str:
    # 헤더 일러스트를 data URI로 변환 (파일이 없으면 빈 문자열)
    try:
        encoded = base64.b64encode(HERO_IMAGE.read_bytes()).decode()
    except OSError:
        return ""
    return f"data:image/svg+xml;base64,{encoded}"


def render_style() -> None:
    # 사용자 입력이 들어가지 않는 고정 CSS만 HTML로 삽입
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header(items: list[dict]) -> None:
    # 헤더 일러스트, 제목, 진행 현황 표시
    uri = hero_image_uri()
    img = f'<img src="{uri}" alt="장바구니 일러스트">' if uri else ""
    st.markdown(
        f'<div class="hero">{img}<div><h1>🛒 쇼핑 리스트</h1>'
        f"<p>오늘 장보기, 빠짐없이 챙겨요 🥕🥛🍎</p></div></div>",
        unsafe_allow_html=True,
    )
    total = len(items)
    done = sum(item["checked"] for item in items)
    all_done = total > 0 and done == total
    st.caption(f"🎯 완료 {done} / 전체 {total}" + ("  ·  🎉 장보기 끝!" if all_done else ""))
    if total:
        st.progress(done / total)
    # 모두 완료된 순간에 한 번만 풍선 효과
    if all_done and not st.session_state.celebrated:
        st.balloons()
    st.session_state.celebrated = all_done


def render_add_form() -> None:
    # 아이템 추가 폼
    with st.form("add_form"):
        col_name, col_qty, col_btn = st.columns([5, 1.5, 1], vertical_alignment="bottom")
        col_name.text_input("📝 아이템 이름", placeholder="예: 우유, 사과, 식빵", key="new_name")
        col_qty.number_input("🔢 수량", min_value=1, step=1, key="new_qty")
        col_btn.form_submit_button("추가", icon="➕", type="primary", on_click=on_add, width="stretch")
    error = st.session_state.pop("add_error", None)
    if error:
        st.warning(error, icon="⚠️")


def render_item_row(item: dict) -> None:
    # 일반 모드의 아이템 한 줄: 체크 | 이름 x수량 | 수정 | 삭제
    item_id = item["id"]
    col_check, col_name, col_edit, col_del = st.columns([0.6, 5, 1, 1], vertical_alignment="center")
    col_check.checkbox(
        "구매 완료",
        value=item["checked"],
        key=f"check_{item_id}",
        on_change=on_toggle,
        args=(item_id,),
        label_visibility="collapsed",
    )
    name = escape_md(item["name"])
    name = f"~~{name}~~" if item["checked"] else f"**{name}**"
    col_name.markdown(f"{item_emoji(item['name'])} {name} :orange-badge[x{item['quantity']}]")
    if col_edit.button("수정", icon="✏️", key=f"edit_{item_id}", width="stretch"):
        st.session_state.editing_id = item_id
        st.rerun()
    if col_del.button("삭제", icon="🗑️", key=f"del_{item_id}", width="stretch"):
        delete_item(st.session_state.shopping_items, item_id)
        if st.session_state.editing_id == item_id:
            st.session_state.editing_id = None
        commit(f"'{escape_md(item['name'])}'을(를) 삭제했어요.")


def render_edit_row(item: dict) -> None:
    # 수정 모드의 아이템 한 줄: 이름 | 수량 | 저장 | 취소
    item_id = item["id"]
    col_name, col_qty, col_save, col_cancel = st.columns([4.6, 1.5, 1, 1], vertical_alignment="bottom")
    name = col_name.text_input("아이템 이름", value=item["name"], key=f"edit_name_{item_id}")
    quantity = col_qty.number_input(
        "수량", min_value=1, value=item["quantity"], step=1, key=f"edit_qty_{item_id}"
    )
    if col_save.button("저장", icon="💾", key=f"save_{item_id}", type="primary", width="stretch"):
        name, quantity, error = validate(name, quantity)
        if error:
            st.warning(error, icon="⚠️")
        else:
            update_item(st.session_state.shopping_items, item_id, name, quantity)
            st.session_state.editing_id = None
            commit()
    if col_cancel.button("취소", icon="↩️", key=f"cancel_{item_id}", width="stretch"):
        st.session_state.editing_id = None
        st.rerun()


def main() -> None:
    # 상태 초기화 후 전체 화면 구성
    st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒")
    render_style()

    if "shopping_items" not in st.session_state:
        st.session_state.shopping_items = load_items()
        # 이미 모두 완료된 목록을 열 때는 풍선을 띄우지 않음
        loaded = st.session_state.shopping_items
        st.session_state.celebrated = bool(loaded) and all(item["checked"] for item in loaded)
    st.session_state.setdefault("editing_id", None)
    st.session_state.setdefault("flash", None)
    st.session_state.setdefault("new_qty", 1)
    st.session_state.setdefault("celebrated", False)

    if st.session_state.flash:
        st.toast(st.session_state.flash, icon="✨")
        st.session_state.flash = None

    items = st.session_state.shopping_items
    render_header(items)
    save_error = st.session_state.pop("save_error", None)
    if save_error:
        st.error(save_error, icon="⚠️")
    render_add_form()

    if not items:
        st.markdown(
            '<div class="empty-state"><div class="big">🧺</div>'
            '<div class="hint">장바구니가 텅 비었어요</div></div>',
            unsafe_allow_html=True,
        )
        st.info("리스트가 비어 있어요. 살 물건을 추가해 보세요.", icon="💡")
        return

    st.subheader("📋 살 물건")
    for item in list(items):
        with st.container(border=True):
            if item["id"] == st.session_state.editing_id:
                render_edit_row(item)
            else:
                render_item_row(item)

    if any(item["checked"] for item in items):
        _, col_clear = st.columns([2.5, 1.5])
        if col_clear.button("완료 항목 삭제", icon="🧹", width="stretch"):
            count = clear_checked(items)
            commit(f"완료 항목 {count}개를 삭제했어요.")


main()
