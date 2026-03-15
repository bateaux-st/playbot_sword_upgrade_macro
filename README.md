# playbot_macro v11.0

카카오톡 **플레이봇 검키우기** 게임 자동 강화 매크로.

카카오톡 채팅창에 게임 명령어(`/강화`, `/판매`, `/합성` 등)를 자동 입력하고, 채팅 로그를 읽어 결과를 파싱한 뒤 다음 행동을 결정합니다.

## 주요 기능

| 모드 | 설명 |
|---|---|
| **1. 모든 검 강화** | 현재 장착 검을 목표 강화 레벨까지 반복 강화 |
| **2. 히든 검 강화** | 히든 무기가 나올 때까지 판매→재획득 반복 후 목표까지 강화. 파괴 시 자동 재시작 |
| **3. 단순 돈벌기** | 목표까지 강화 → 판매를 무한 반복 |
| **6. 21강 만들기** | 장착검 +20 달성 → 교체 → 보관검 +20 달성 → 합성으로 +21 시도 |

## 요구 사항

- Python 3.11+
- Windows (pyautogui 기반 마우스/키보드 제어)
- 카카오톡 PC버전

```
pip install pyautogui pyperclip keyboard
```

## 실행

```bash
# 개발 모드
python __main__.py

# PyInstaller 빌드
pyinstaller playbot_sword_upgrade.spec
```

## 사용법

1. 카카오톡에서 플레이봇이 있는 채팅방을 엽니다.
2. 매크로를 실행하고 모드를 선택합니다.
3. 목표 강화 레벨을 입력합니다 (21강 만들기는 자동 +20).
4. 채팅 입력창에 마우스를 올려놓고 3초 대기 (또는 좌표 고정 모드 사용).
5. 매크로가 자동으로 명령어를 입력하고 결과를 처리합니다.

### 단축키

| 키 | 동작 |
|---|---|
| **F8** | 일시정지 / 재개 |
| **F9** | 메뉴로 복귀 |
| **마우스 모서리** | 긴급 중지 (pyautogui failsafe) |

### 옵션 설정

메뉴 4번에서 조정 가능:

- **감속 시작 레벨**: 이 레벨부터 강화 딜레이 증가 (기본 9강)
- **일반/고강 속도**: 강화 대기 시간 (기본 2.7초 / 4.5초)
- **최소 골드**: 이 금액 이하 시 자동 중지
- **클립보드 안전 시간**: 렉 발생 시 0.5 이상으로 조정
- **좌표 고정**: 매번 마우스 위치를 지정하지 않고 저장된 좌표 사용

## 모드별 흐름도

### 1. 모든 검 강화 (TargetMode)

```mermaid
flowchart TD
    S([시작]) --> LOAD[/프로필 조회/]
    LOAD --> CHK{목표 레벨\n달성?}
    CHK -- Yes --> DONE([완료])
    CHK -- No --> ADV{+0 & 파편\n충분?}
    ADV -- Yes --> AE[/상급강화/]
    ADV -- No --> EN[/강화/]
    AE --> RES{결과}
    EN --> RES
    RES -- 성공 --> CHK
    RES -- 유지 --> CHK
    RES -- 파괴 --> CHK
    RES -- 골드부족 --> STOP([중지])
```

### 2. 히든 검 강화 (HiddenMode)

```mermaid
flowchart TD
    S([시작]) --> LOAD[/프로필 조회/]
    LOAD --> H{히든 무기?}
    H -- Yes --> ENH[목표까지 강화]
    H -- No --> SELL_READY[강화하여\n판매 가능하게]
    SELL_READY --> SELL[/판매/]
    SELL --> H

    ENH --> ERES{결과}
    ERES -- 목표 달성 --> AUTO{자동판매\n모드?}
    ERES -- 파괴 --> H
    ERES -- 골드부족 --> STOP([중지])

    AUTO -- No --> DONE([완료])
    AUTO -- Yes --> SELL2[/판매/]
    SELL2 --> H
```

### 3. 단순 돈벌기 (MoneyMode)

```mermaid
flowchart TD
    S([시작]) --> LOAD[/프로필 조회/]
    LOAD --> ENH[목표까지 강화]
    ENH --> RES{결과}
    RES -- 목표 달성 --> SELL[/판매/]
    RES -- 골드부족 --> STOP([중지])
    SELL --> ENH
```

### 6. 21강 만들기 (FusionMode)

```mermaid
flowchart TD
    S([시작]) --> PROF[/프로필 조회/]
    PROF --> CHK_A{장착검\n+20?}
    CHK_A -- No --> ENH_A[장착검 강화\n→ +20]
    CHK_A -- Yes --> CHK_B
    ENH_A -- 달성 --> CHK_B
    ENH_A -- 실패/중지 --> STOP([중지])

    CHK_B{보관검\n+20?}
    CHK_B -- Yes --> FUSE
    CHK_B -- No --> SWAP[/교체/]
    SWAP --> ENH_B[새 장착검 강화\n→ +20]
    ENH_B -- 달성 --> FUSE
    ENH_B -- 실패/중지 --> STOP

    FUSE[/합성/] --> FRES{결과}
    FRES -- 성공 --> SUCCESS([+21 획득!])
    FRES -- 실패 --> FAIL([합성 실패])
```

## 프로젝트 구조

```
__main__.py               # 엔트리포인트 (stdio, hotkey, 메인 루프)
actions.py                # 게임 액션 (강화, 판매, 합성, 프로필 등)
parsing.py                # 채팅 로그 파서 (순수 함수, I/O 없음)
config.py                 # AppConfig 데이터클래스
state.py                  # AppState (threading.Event 기반 스레드 안전)
stats.py                  # 강화 통계 (메모리 누적, 세션 종료 시 저장)
models.py                 # WeaponState, ProfileState, ActionResult
constants.py              # 명령어/모드 상수
macro_logger.py           # 통합 로깅
weapon_catalog.py         # 무기 카탈로그 (CSV 기반 히든/일반 분류)
paths.py                  # PyInstaller 경로 해석
playbot_sword_upgrade.spec  # PyInstaller 빌드 설정
weapon_catalog.csv        # 무기 데이터 (2,400+ 항목)
chat_io/
  protocol.py             # ChatIO 추상 인터페이스
  kakaotalk.py            # pyautogui+pyperclip 구현체
modes/
  base.py                 # BaseMode + MODE_REGISTRY 디스패치
  target.py               # 목표 강화 모드
  hidden.py               # 히든 검 강화 모드
  money.py                # 돈벌기 모드
  fusion.py               # 21강 합성 모드
ui/
  menu.py                 # 콘솔 메뉴
tests/
  conftest.py             # FakeChatIO + 공유 픽스처
  test_parsing.py         # 파서 단위 테스트
  test_parsing_fixtures.py  # 실제 카톡 메시지 기반 테스트
  test_weapon_catalog.py
  test_config.py
  test_stats.py
  test_state.py           # 스레드 안전 테스트 포함
  test_actions.py
  test_modes.py
  test_fusion.py
  fixtures/
    all_messages.txt      # 실제 카톡 메시지 샘플 (테스트 데이터)
```

## 아키텍처

```
__main__.py (엔트리포인트)
  ├── ui/menu.py (사용자 입력)
  ├── modes/* (모드 실행)
  │     └── actions.py (게임 액션 조합)
  │           └── chat_io/kakaotalk.py (실제 I/O)
  │           └── chat_io/protocol.py (추상 인터페이스)
  ├── parsing.py (순수 함수 파서)
  ├── config.py / state.py / stats.py
  └── weapon_catalog.py
```

- **모든 비즈니스 로직은 `ChatIO` 인터페이스를 통해 I/O와 분리**되어 있어, `FakeChatIO`로 pyautogui 없이 단위 테스트 가능.
- **모드 추가**는 `@register_mode` 데코레이터로 클래스 1개만 작성하면 자동 등록.
- **강화 통계**는 메모리에 누적되다가 세션 종료 시 `enhance_stats.json`에 한 번만 저장.

## 테스트

```bash
pip install pytest
python -m pytest tests/ -v
```

165개 테스트 커버:
- 채팅 로그 파싱 (실제 카톡 메시지 기반)
- 무기 카탈로그 히든/일반 분류
- 설정 로드/저장 라운드트립
- 강화 통계 메모리 누적 + flush
- `AppState` 스레드 안전 (동시 접근, 일시정지/재개)
- `GameActions` + `FakeChatIO` 통합 테스트
- 합성 모드 파싱/액션

## 설정 파일

| 파일 | 위치 | 용도 |
|---|---|---|
| `sword_config.json` | 실행 파일 옆 | 사용자 설정 (자동 생성) |
| `enhance_stats.json` | 실행 파일 옆 | 누적 강화 확률 통계 |
| `weapon_catalog.csv` | 번들 내장 | 무기 이름→종류 매핑 |

## 원본 출처

이 프로젝트는 [KEY의 일기장](https://blog.naver.com/ableyoung/224132261950)에서 공유된 `검키우기_통합판v10.2.py` 소스코드를 기반으로 개발되었습니다.
