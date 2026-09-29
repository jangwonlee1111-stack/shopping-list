# 쇼핑 리스트 앱 개발 프롬프트

아래 내용을 AI 코딩 도구(Claude, ChatGPT 등)에 그대로 붙여 넣어 사용하세요.
같은 폴더의 `PRD.md`를 함께 첨부하면 더 정확합니다.

---

## 프롬프트

```
너는 Python과 Streamlit에 능숙한 시니어 개발자야.
아래 요구사항에 맞는 쇼핑 리스트 앱을 Streamlit으로 구현해줘.

[목표]
- 아이템 추가, 수정, 삭제, 체크 기능이 있는 간단한 쇼핑 리스트 웹 앱
- 단일 파일 app.py로 구현하고, `python -m streamlit run app.py`로 실행

[기술 조건]
- Python 3.10 이상, Streamlit 1.50 이상
- 외부 라이브러리는 streamlit만 사용 (json, uuid, datetime, pathlib 등 표준 라이브러리는 허용)
- 데이터는 app.py와 같은 폴더의 shopping_list.json에 저장
- 파일이 없거나, JSON이 손상되었거나, UTF-8이 아니면 빈 리스트로 시작하고 오류로 멈추지 않을 것
- 불러올 때 아이템을 하나씩 정리: 이름 없는 항목은 버림, 수량이 이상하면 1, 중복 id는 새로 발급
- 저장은 임시 파일에 쓴 뒤 os.replace로 교체하고, 저장 실패(OSError)는 st.error로 알림

[데이터 구조]
각 아이템은 다음 필드를 가진 dict:
- id: str (uuid4)
- name: str
- quantity: int (1 이상)
- checked: bool
- created_at: str (ISO 8601)

[상태 관리]
- st.session_state.shopping_items: 아이템 리스트
- st.session_state.editing_id: 수정 중인 아이템 id (없으면 None)
- 변경이 생길 때마다 session_state를 갱신하고 즉시 JSON 파일에 저장

[기능 요구사항]
1. 추가
   - st.form 안에 이름 text_input(key="new_name"), 수량 number_input(key="new_qty", 최소 1, 기본 1), "추가" form_submit_button(on_click=콜백)
   - 입력창 초기화는 clear_on_submit 대신 콜백에서 st.session_state.new_name/new_qty를 직접 초기화
   - 이름은 앞뒤 공백 제거, 비어 있으면 st.warning으로 경고하고 추가하지 않음
   - 새 아이템은 리스트 맨 아래에 추가
2. 수정
   - 각 행의 "수정" 버튼을 누르면 그 행이 이름/수량 입력창 + "저장"/"취소" 버튼으로 바뀜
   - 한 번에 하나의 아이템만 수정 모드
   - 저장 시 추가와 같은 입력 검증 적용, 체크 상태는 유지
3. 삭제
   - 각 행의 "삭제" 버튼으로 해당 아이템만 즉시 삭제
4. 체크
   - 각 행의 체크박스로 구매 완료/미완료 전환
   - 완료 항목은 이름에 취소선(~~텍스트~~) 표시
5. 진행 현황
   - 상단에 "완료 N / 전체 M" 표시와 st.progress 바
6. 완료 항목 일괄 삭제
   - 체크된 아이템이 있을 때만 "완료 항목 삭제" 버튼 표시

[UI]
- 한국어 UI, 제목은 "🛒 쇼핑 리스트"
- 각 아이템 행은 st.columns로 [체크박스 | 이름 x수량 | 수정 | 삭제] 배치
- 위젯 key는 아이템 id를 사용해 중복되지 않게 할 것 (예: f"check_{id}")
- 아이템이 없으면 "리스트가 비어 있어요. 살 물건을 추가해 보세요." 안내
- 동작 후 화면 갱신이 필요하면 st.rerun() 사용
- 버튼 너비는 width="stretch" 사용 (use_container_width는 지원 종료 예정)
- 아이템 이름은 모든 ASCII 문장부호를 이스케이프해서 표시 (마크다운·수식 $·이모지 : 로 해석되는 것 방지)

[코드 품질]
- load_items(), save_items(items), add_item(), update_item(), delete_item(), toggle_item() 처럼 기능별 함수로 분리
- 각 함수에 짧은 한국어 주석
- JSON 저장 시 ensure_ascii=False, indent=2

[출력 형식]
1. app.py 전체 코드
2. requirements.txt 내용
3. 실행 방법 (설치 → 실행 명령어)
4. 아래 수용 기준을 어떻게 만족하는지 간단한 확인 방법

[수용 기준]
- 이름을 입력하고 "추가"를 누르면 리스트 맨 아래에 새 아이템이 나타난다
- 빈 이름으로 추가하면 경고가 나오고 리스트는 바뀌지 않는다
- "수정" → 값 변경 → "저장" 시 반영되고, "취소" 시 원래 값이 유지된다
- "삭제"를 누르면 해당 아이템만 사라진다
- 체크하면 취소선이 표시되고 진행 현황 숫자가 바뀐다
- 앱을 재실행해도 리스트와 체크 상태가 유지된다
- shopping_list.json을 지워도 오류 없이 빈 리스트로 시작한다

[하지 말 것]
- 로그인, DB, 카테고리, 가격 계산, 드래그 정렬 등 위에 없는 기능 추가 금지
```
