# 시작하기 {#getting-started}

[← 목차](index.md)

## BoneCraft란? {#what-is-bonecraft}

BoneCraft는 Bforartists용 애드온입니다. 캐릭터와 소품을 리깅하고 VRChat, VRoid / VRM 및 MMD용 3D 아바타를 준비합니다. 패널에서 리그 생성, 웨이트 페인팅, 본 이름, 립싱크, 눈 추적 및 내보내기를 자동화합니다.

**BoneCraft가 할 수 없는 일:**

- 아바타의 체형을 모델링하거나 조각할 수 없습니다
- 텍스처나 머티리얼을 처음부터 만들 수 없습니다
- VRChat에 직접 업로드할 수 없습니다(VRChat Creator Companion / SDK가 필요합니다)

---

## BoneCraft와 BoneForge {#bonecraft-and-boneforge}

BoneCraft는 Blender 포크인 Bforartists에서만 실행됩니다. BoneForge는 도구 수가 더 적은 표준 Blender용 별도 애드온입니다. 둘 중 하나만 설치하세요. 표준 Blender에서 BoneCraft는 안내와 Bforartists 다운로드 버튼만 표시하며 도구를 불러오지 않습니다.

BoneForge 9.0.0 이상은 표준 Blender용입니다. BoneCraft는 별도의 Bforartists 애드온입니다. 둘 다 Auto-Rig Wizard, Quick Rig, Mannequin 및 공통 CATS/Material Atlas 도구를 제공합니다. BoneCraft에는 Mechanisms, Control Picker 및 프로덕션용 컨트롤 리그, 조인트 감지, 프로필 내보내기 도구도 있습니다. 배치가 비슷하다고 BoneForge에도 이 도구들이 있는 것은 아닙니다.

## 제공된 빌드 빠른 시작 {#supplied-build-quick-start}

원래 제공된 Bforartists 빌드에는 BoneCraft 9.2.18이, 새 로컬 미리보기에는 9.2.19 후보 버전이 포함됩니다. 두 빌드 모두 팩토리 설정에서 BoneCraft를 활성화하므로 ZIP 설치나 수동 활성화가 필요하지 않습니다.

1. 제공된 Bforartists 빌드를 여세요.
2. **T**를 눌러 왼쪽 툴 셸프를 표시하세요.
3. **BoneCraft** 또는 **Rig Builder**를 선택하세요.
4. **N**을 눌러 오른쪽 사이드바를 표시하세요.
5. 아바타 도구와 **Import / Export**에는 **CATS**를 선택하세요.

이 설명서의 같은 인터페이스 경로와 설정을 사용하세요. 선택적 도구 패키지와 의존 패키지의 요구 사항도 그대로 적용됩니다. Rigify 스타터와 VRM/MMD 브리지에는 명시된 의존 패키지가 필요합니다.

이 지침은 로컬 기여 미리보기를 설명합니다. 공식 Bforartists 5.2.3 패키지에는 이 번들이 포함되지 않습니다. 검토 이력은 [기여 제안](https://github.com/Bforartists/Bforartists/pull/7067)을 참고하세요.

## BoneCraft 설치 {#installing-bonecraft}

독립형 Toolkit ZIP에는 이 절차를 사용하세요. 제공된 빌드 사용자는 위의 기존 탭에서 시작하면 됩니다.

링크된 공개 ZIP은 9.2.18입니다. 9.2.19 후보 버전의 수정은 공개될 때까지 로컬 미리보기를 사용하세요.

**준비물:**

- Bforartists(BoneCraft는 Bforartists 5.2에서 테스트되었습니다)
- 독립형 [BoneCraft-BFA-9.2.18.zip](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/bonecraft-v9.2.18/BoneCraft-BFA-9.2.18.zip) 파일

**단계:**

업데이트하는 경우:

1. 작업을 저장하세요.

2. 이전 독립형 BoneCraft 애드온을 비활성화하세요.

3. 이전 독립형 BoneCraft 애드온을 제거하세요.

4. 새 ZIP을 설치하기 전에 Bforartists를 다시 시작하세요.

처음 설치하는 경우 여기서 시작하세요.

1. Bforartists를 여세요.
2. **Edit** → **Preferences** → **Add-ons**를 여세요.
3. **Install from Disk…** 항목을 선택하세요.

4. BoneCraft `.zip` 파일을 선택하세요.

5. BoneCraft 옆의 확인란을 켜세요.
6. 링크된 공개 ZIP의 경우 Preferences에 **9.2.18**이 표시되는지 확인하세요.

7. BoneCraft 항목을 펼치면 **Language**, **Tabs**, **Shelf Width**, **Show Helpers** 및 **Tools**가 나타납니다.

이 절차는 독립형 Toolkit ZIP을 설치합니다. 제공된 빌드에 BoneCraft가 이미 있다면 제공된 빌드 빠른 시작을 사용하세요. 독립형 사본과 내장 사본을 중복 활성화하지 마세요.

**표시되는 결과:** 왼쪽 툴 셸프(**T**)에 BoneCraft와 Rig Builder 탭이, 오른쪽 사이드바(**N**)에 CATS 탭이 나타납니다.

## 기능 위치 {#where-things-are}

각 탭에는 작업 공간 그룹이 있습니다. Setup Rigging, Skin, Review, Avatar Tools 및 Facial은 탭 안에서 펼치는 섹션입니다. 아래 경로는 영어 UI 이름을 사용하며 번역 이름은 Language 환경설정에 따라 달라집니다.

| 탭 | 기본 위치 | 섹션 |
| --- | --- | --- |
| Rig Builder | 왼쪽 툴 셸프(T) | Auto-Rig Wizard, Quick Rig - 기성 아마츄어, Mannequin |
| BoneCraft | 왼쪽 툴 셸프(T) | Overview, Setup Rigging, Skin, Mechanisms, Review |
| CATS | 오른쪽 사이드바(N) | CATS, Avatar Tools, VRChat Tools, Import / Export |

영문 원본 이미지 설명(이미지 생략): 왼쪽 툴 셸프에서 BoneCraft가, 오른쪽 사이드바에서 CATS가 선택되어 있습니다. T 또는 N을 눌러 각 영역을 표시합니다.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 왼쪽 툴 셸프에서 BoneCraft가, 오른쪽 사이드바에서 CATS가 선택되어 있습니다. T 또는 N을 눌러 각 영역을 표시합니다.*

| 도구 | 여는 경로 |
| --- | --- |
| Bone Merge | BoneCraft → Setup Rigging → Bone Merge |
| Delta Mush / Proximity Wrap | BoneCraft → Skin → Delta Mush / Proximity Wrap |
| Viseme Library / Lip Sync | CATS → Avatar Tools → Viseme Library → Lip Sync |
| VRChat Viseme Mapping / Face Tracking | CATS → VRChat Tools → Facial |
| Humanoid / Hair | CATS → Avatar Tools → Set Up Humanoid Bones / Add Hair Physics |
| VRChat 내보내기 | CATS → Import / Export → Game Engine Export → Unity / VRChat |
| Unreal 내보내기 및 Bone Names | CATS → Import / Export → Game Engine Export → Unreal Engine 5 |
| 검증된 프로필 내보내기 | CATS → Import / Export → Game Export → Export (Profile) |
| Material Atlas | CATS → CATS → Material Atlas → Analyze Materials / Refresh Analysis → Bake Checked Sources |
| VRM / MMD / I/O Hub | CATS → Import / Export → VRM / VRoid, MMD / PMX, Game Engine Export |
| Performance / Clothing / Naming | CATS → VRChat Tools → Check Performance / Attach Clothing / VRChat Naming Extras |

리그와 비짐 라이브러리 컨트롤에는 아마츄어를 선택하세요. Delta Mush와 Proximity Wrap에는 오브젝트 모드의 메시를 선택하세요. Lip Sync에는 포즈 모드의 아마츄어가 필요합니다. 섹션 삼각형을 펼치면 버튼이 나타납니다. 옵션 접이식 영역에는 선택적 설정이 있습니다. 도구가 즉시 실행된다면 다른 작업 전에 Adjust Last Operation에서 조정하세요.

세 얼굴 작업 흐름의 용도는 다릅니다. CATS 비짐 생성은 입 셰이프 키를 만듭니다. Viseme Library / Lip Sync는 포즈를 저장하고 애니메이션 키를 삽입합니다. Facial은 기존 셰이프 키를 VRChat에 매핑하거나 얼굴 추적을 설정합니다.

UV 패킹 컨트롤은 **CATS → CATS → Material Atlas → Advanced Options → UV Packing**에 있습니다. 이전 지침은 이 접이식 영역을 Override Inherited Settings라고 부릅니다. BoneCraft는 독립형 UVToolkit 애드온 전체가 아니라 공통 아틀라스 UV 도우미를 제공합니다.

**Starter Rigs:**

1. 아래쪽 에셋 셸프의 카탈로그 메뉴에서 **Starter Rigs**를 켜세요.

2. 필요하다면 **All** 라이브러리를 선택하세요.

9.2.5 버전은 왼쪽 위의 이전 Starter Rigs 컨트롤을 제거했습니다. **Add → Armature → Starter Rig Catalog**는 의존 패키지를 확인하면서 맞춤과 생성을 제공합니다.

**탭 이동:**

1. **Edit** → **Preferences** → **Add-ons** → BoneCraft → **Tabs**를 여세요.

2. 해당 탭의 **Left** 또는 **Right**를 선택하세요.

각 탭에는 표시 스위치도 있습니다. 변경은 즉시 적용됩니다. 탭이 숨겨져 있으면 Left와 Right 버튼은 회색이 되지만 계속 작동합니다.

**프로퍼티스 에디터:** Preferences → Tabs의 **Scene Properties**는 처음에 켜져 있습니다. 프로퍼티스 에디터의 Scene 탭에 Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools 및 Import / Export를 표시합니다.

이 섹션들을 숨기거나 표시하려면 **Show**를 선택하세요. 파란색은 표시 중이라는 뜻입니다. 이 스위치는 뷰포트 탭이나 아마츄어 데이터 탭을 바꾸지 않습니다.

아마츄어를 선택하면 BoneCraft의 아마츄어 도구가 아마츄어 데이터 탭에도 나타납니다. 이 도구들은 표시 스위치를 따르지 않습니다. Rig Builder, Mechanisms 및 CATS 섹션은 Scene 탭을 사용합니다.

모든 위치에서 도구를 제거하려면 **Tools**에서 해당 패키지를 비활성화하세요. 또는 애드온을 비활성화하세요.

**Shelf Width:** Widen Narrow Shelves는 처음에 켜져 있습니다. BoneCraft 탭이 있는 셸프 너비가 Left 또는 Right 최솟값보다 작으면 한 번 넓힙니다. UI 배율 1×에서 기본값은 Left 240픽셀, Right 260픽셀입니다. 이후 직접 셸프를 좁히면 선택한 너비를 유지합니다. 너비를 수동으로 제어하려면 스위치를 끄세요. 너비 필드가 비활성화됩니다.

영문 원본 이미지 설명(이미지 생략): Tabs는 BoneCraft와 Rig Builder를 왼쪽에, CATS를 오른쪽에 배치합니다. 아래에는 Shelf Width와 Show Helpers가 있습니다.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. Tabs는 BoneCraft와 Rig Builder를 왼쪽에, CATS를 오른쪽에 배치합니다. 아래에는 Shelf Width와 Show Helpers가 있습니다.*

**메뉴와 기본 툴 셸프 탭:** 3D 뷰포트의 헤더 메뉴에서도 도구를 열 수 있습니다.

| 위치 | 도구 |
| --- | --- |
| Add → Armature | Quick Rig, Auto-Rig Wizard, Mannequin for Active Rig |
| Pose → BoneCraft(포즈 모드) | 포즈 도구, 피커, 본 컬렉션, 리그 설정 및 검사 |
| Weights → BoneCraft(웨이트 페인트 모드) | 웨이트 전체 채우기, 대칭 및 정규화 |
| Object → Mechanisms(오브젝트 모드) | 부품, 관절 및 링크 추가, 모션 테스트 |
| Tool Shelf → Pose 또는 Weights → BoneCraft | 자주 쓰는 포즈 또는 웨이트 작업 버튼 |

Pose와 Weights 셸프 버튼은 넓은 셸프에서 텍스트를 표시하며 좁으면 아이콘 격자가 됩니다. 아이콘 위에 포인터를 올려 툴팁을 읽으세요. 이 위치들은 BoneCraft 탭과 같은 도구를 사용합니다. 켜진 도구 패키지만 사용할 수 있습니다.

**뷰포트 도구:** Place Rig Markers는 메시를 클릭한 위치에 Auto-Rig Wizard의 다음 마커를 배치합니다. Build Mechanism은 부품을 클릭하면 관절이나 링크 생성 안내를 시작합니다. 설정과 컨트롤은 [리그 빌더](06-rig-builder.md#auto-rig-wizard)와 [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each)를 참고하세요.

**먼저 실행하고 나중에 조정:** Quick Rig, Fit Dropped Rig, Weight Mirror, Weight Transfer, Flood to Custom, Ribbon, Spline IK 및 Delta Mush는 즉시 실행됩니다.

1. 도구를 선택하세요.

2. 즉시 뷰포트의 Adjust Last Operation 패널에서 옵션을 조정하세요.

3. 다른 작업 전에 조정을 끝내세요.

다른 패널의 작업 버튼 아래 접이식 영역에는 선택적 설정이 있습니다. 이 설정을 사용하려면 영역을 펼치세요. 다른 선택이 필요한 패널도 계속 표시되면서 선택할 대상을 안내할 수 있습니다.

**Show Helpers:** BoneCraft는 짧은 “무엇/언제” 문구와 “How this works” 설명으로 섹션을 안내합니다. 숨기려면 애드온 환경설정의 **Show Helpers**를 끄세요. Avatar Tools의 **Compact Mode**는 같은 스위치를 제어합니다.

**Language:** 애드온 환경설정의 **Language**는 BoneCraft 자체 패널을 English, 日本語, 한국어, 中文, Français, Português 또는 Español로 바꿉니다.

영문 원본 이미지 설명(이미지 생략): 로컬 미리보기는 BoneCraft 9.2.19와 Language의 English를 표시합니다.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 로컬 미리보기는 BoneCraft 9.2.19와 Language의 English를 표시합니다.*

**먼저 정리를 검토하세요:**

1. Fix Model 옵션을 확인하세요.

2. 아바타에 필요한 작업을 선택하세요.

3. 변경 전에 파일 체크포인트를 저장하세요.

4. 작업 후 결과를 확인하세요.

Pipeline Status와 Operation Ledger는 진행 상황을 기록합니다. [CATS 파이프라인](04-cats-pipeline.md)을 참고하세요.

**빠른 패널:** 3D 뷰포트에서 **Ctrl+Shift+R**을 누르면 커서 아래에 BoneCraft 리그 패널이 팝업으로 열립니다.

---

## 어디서 시작해야 하나요? {#where-should-i-start}

작업에 맞는 가이드를 선택하세요.

> **새 FBX, OBJ 또는 Blender 모델을 VRChat용으로 리깅합니다.**
> → [가이드 1: 첫 아바타를 VRChat에 올리기](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat)

> **VRoid Studio에서 내보낸 VRM 아바타를 준비합니다.**
> → [가이드 2: VRoid 아바타를 VRChat으로 가져오기](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)

> **MMD 모델(PMX 파일)을 VRChat용으로 준비합니다.**
> → [가이드 3: MMD 아바타를 VRChat으로 가져오기](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)

> **리깅된 아바타의 업로드를 막는 본 이름을 수정합니다.**
> → [가이드 4: 아바타의 본 이름 수정](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

> **리깅된 아바타의 립싱크, 눈 추적 및 메시를 VRChat용으로 준비합니다.**
> → [가이드 13: CATS로 아바타를 VRChat용으로 준비하기](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)

> **특정 문제의 해결 방법을 찾습니다.**
> → [빠른 해결 색인](10-reference.md#quick-fix-index)

다음: [가이드 1–7](02-guides-a.md)
