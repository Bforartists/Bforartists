# 새로운 기능 {#whats-new}

[← 목차](index.md)

최신 버전부터 나열합니다.

## 9.2.19 — 패널 컨트롤(로컬 후보 버전) {#9219--panel-controls-local-candidate}

이 로컬 후보 버전은 아직 공개되지 않았습니다. 독립형 릴리스는 여전히 9.2.18입니다.

- Collections와 Visibility Bookmarks는 패널 그리기 밖에서 설정을 초기화합니다.
- 그룹화된 패널은 자체 컨트롤을 사용하고 현재 선택과 모드를 확인합니다.
- Hair Physics는 현재 호스트에서 선택된 포즈 본을 읽습니다.
- Bone Inspector는 레스트 본의 롤을 표시하고 헤더 버튼으로 이름을 복사합니다.
- Eye Tracking은 저장된 설정을 보존하면서 각도 값을 도 단위로 표시합니다.

영문 설명서에는 도구와 설정에 맞는 그림이 추가되었습니다. 이전 그림은 원래 버전 표시를 유지합니다.

## 9.2.18 — 저장된 메커니즘 폼 {#9218--saved-mechanism-forms}

이전에 저장한 폼도 현재 Bforartists 빌드에서 읽고 사용할 수 있습니다. 폼을 열거나 적용해도 다시 저장하지 않습니다. **Save Form**은 현재 값을 현재 형식으로 저장합니다. 기존 핸들, 슬라이더 및 패널 위치는 바뀌지 않습니다.

이 릴리스는 새 호스트의 호환성 진단을 수정합니다. 해당 진단만으로 이전 호스트에서 저장된 폼을 사용할 수 없었다고 판단할 수는 없습니다. [폼](07-mechanisms.md#forms)과 [릴리스 노트](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md)를 참고하세요.

이것은 독립형 Toolkit 릴리스이며 공식 Bforartists에 수용되었음을 뜻하지 않습니다. 과거 스크린샷과 튜토리얼 테스트의 한계는 해당 장에 유지됩니다.

## 9.2.17 — 내보내기 이름과 모드 복원 {#9217--export-naming-and-mode-restoration}

**Unity / VRChat**과 **Unreal Engine 5**에 **Bone Names**가 추가되어 **Keep Original Names**, **Unity-Preset**, **Unreal-Preset**을 선택할 수 있습니다. 미리보기는 인식한 본과 제안 이름을 표시합니다. 이름 변경은 내보내기 사본의 버텍스 그룹, 애니메이션 채널 및 Unity 사이드카 참조에도 적용됩니다. 작업 리그의 이름은 유지됩니다.

두 주요 엔진 내보내기 버튼은 이제 오브젝트, 포즈 및 편집 모드를 지원합니다. 내보내기나 정리 후 원래 모드와 선택을 복원합니다. 활성 액션의 FBX 베이크에 별도 NLA 스트립이 필요하지 않습니다.

인식된 선택적 휴머노이드 본, 손가락 및 발가락도 이름 변경에 참여합니다. 이름 충돌이나 모호한 매핑이 있으면 이름 변경을 차단합니다. 이 프로필들은 계층, 방향 및 레스트 포즈를 유지하며 Manny/Quinn 스켈레톤을 만들지 않습니다.

이름을 바꾼 **Export (Profile)** 출력은 **Active Action**과 **No Animation**을 지원합니다. **All Actions**에는 **Keep Original Names**가 필요합니다. [게임 엔진 내보내기](08-vrchat.md#game-engine-export)와 [9.2.17 노트](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.17/RELEASE-NOTES.md)를 참고하세요.

## 9.2.15 — 검토를 거치는 머티리얼 아틀라스 작업 흐름 {#9215--reviewed-material-atlas-workflow}

패널은 대상 선택, 머티리얼과 텍스처 선택, 베이크와 검토의 세 단계를 제공합니다. **Smart Combine Materials**는 초기 자동 단축 경로입니다. 분석 후 **Refresh Analysis**가 목록을 다시 만들며 **Bake Checked Sources**가 검토한 선택을 베이크합니다.

두 소스 목록 모두 **Select All**과 **Deselect All**이 있습니다. 활성 그룹과 소스 목록 안에서만 Include 확인란을 변경합니다. 누락된 텍스처는 선택하지 않습니다. 일괄 선택은 꺼진 그룹을 켜지 않습니다. **Object → Atlas Source Selection**에서도 같은 작업을 제공합니다.

**Source Details**는 처음에 접혀 있습니다. **Copy Debug Report**는 **Advanced Options** 안에 있습니다. Backup, Accept 및 Revert는 계속 보입니다. 이 UI 변경은 기존 베이크 흐름과 보존 제약을 유지합니다.

## 9.2.14 — 색상만 있는 메시 {#9214--color-only-meshes}

작성된 UV가 없는 색상 전용 메시는 최종 조립 때 베이크된 아틀라스 UV 레이어를 받습니다.

## 9.2.13 — 머티리얼 수 {#9213--material-counts}

머티리얼 추정과 결과는 모든 출력 메시의 아틀라스 슬롯을 계산합니다. Revert는 결과를 초기화합니다.

## 9.2.12 — 내보내기 UV0 {#9212--export-uv0}

**Keep Source UV Maps**가 꺼져 있으면 다시 구성된 아틀라스 메시는 `atlas_uv`를 UV0으로 내보냅니다. 소스 맵을 유지하면 아틀라스가 UV1에 남을 수 있습니다.

## 9.2.11 — 변경된 소스 검사 {#9211--changed-source-checks}

사전 검사는 아틀라스 백업 생성 전에 분석한 머티리얼 소스의 누락이나 변경을 거부합니다.

1. 분석을 새로 고치세요.

2. 소스 선택을 다시 검토하세요.

## 9.2.10 — 제외된 머티리얼 {#9210--excluded-materials}

아틀라스 조립은 제외된 머티리얼과 공유 머티리얼 참조를 유지합니다.

## 9.2.9 — 렌더에서 숨긴 소스 {#929--render-hidden-sources}

결합기는 임시 사본으로 렌더에서 숨긴 소스를 베이크합니다. Revert는 원래 표시 상태를 복원합니다.

## 9.2.8 — 연결된 셰이더 입력 {#928--connected-shader-inputs}

결합기는 베이크 중 연결된 Principled 틴트, 매핑 및 알파 그래프를 보존합니다. MToon은 대체 처리 경로를 유지합니다. **Metallic**과 **Pack ORM Channels**는 사전 검사에서 계속 차단합니다.

## 9.2.7 — 투명도 분류 {#927--transparency-classification}

머티리얼 분류는 최신 DITHERED 불투명도와 연결되거나 상수인 알파를 처리합니다. 렌더 설정만으로 불투명 머티리얼을 투명 그룹에 강제로 넣지 않습니다.

## 9.2.6 — MMD와 PMX 설치 {#926--mmd-and-pmx-installation}

설치기는 최신 MMD Extensions와 기존 애드온을 인식합니다. 확장 설치는 의존 패키지를 보존하고 사용할 수 없는 로컬 저장소를 알립니다. 기존 애드온 메타데이터가 없어도 활성 확장을 인식합니다. 취소한 PMX 가져오기는 성공으로 보고하지 않고 취소 상태를 유지합니다.

[날짜별 수정 기록](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md)은 9.2.6–9.2.15와 생성한 테스트 예제 검사를 다룹니다. [9.2.15 UI 검토](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md)는 오퍼레이터 검사와 시각 테스트 한계를 기록합니다. 이 과거 기록은 9.2.18에서 전체 설명서를 새로 재실행했다고 주장하지 않습니다.

## 9.2.5 — Starter Rigs 카탈로그 탭 {#925--starter-rigs-catalog-tab}

Starter Rigs는 이제 아래쪽 기본 에셋 셸프의 카탈로그 탭 하나를 사용합니다. 왼쪽 위 뷰포트 컨트롤을 대체합니다. 다른 카탈로그 옆에 탭을 표시하려면 셸프의 카탈로그 메뉴에서 **Starter Rigs**를 한 번 켜세요. 기본 에셋 가져오기와 **Add → Armature → Starter Rig Catalog**는 계속 사용할 수 있습니다.

## 9.2.4 — 작업 보드와 기본 도구 {#924--task-board-and-native-tools}

**Open Health Check**는 리그 검증을 실행하고 결과를 엽니다. 사용 전에 아마츄어나 연결된 메시를 선택하세요. **Quick Wins**는 권장 사항을 최대 세 개 표시하며 **Remaining Tasks**에는 이 카드들을 중복 표시하지 않습니다. **Refresh Task Board**는 다시 검사합니다.

Place Rig Markers와 Build Mechanism은 뷰포트 도구로 계속 사용할 수 있습니다. 등록 때문에 오브젝트 및 포즈 모드의 기본 Grab/Move나 도구 순환이 고장 나던 문제가 수정되었습니다.

## 9.2.3 — VRChat 내보내기 위치 {#923--vrchat-export-location}

Avatar Tools의 중복 Export to VRChat 패널을 제거합니다. 내보내기는 CATS → Import / Export → Unity / VRChat에 남습니다.

## 9.2.2 — 현재 인터페이스 {#922--current-interface}

각 탭에는 작업 공간 그룹이 있습니다. Setup Rigging, Skin, Review, Avatar Tools 및 Facial은 탭 안에서 펼치는 섹션입니다. 아래 경로는 영어 UI 이름을 사용하며 번역 이름은 Language 환경설정에 따라 달라집니다.

- Bone Merge → BoneCraft → Setup Rigging
- Delta Mush / Proximity Wrap → BoneCraft → Skin
- Viseme Library / Lip Sync → CATS → Avatar Tools
- VRChat Viseme Mapping / Face Tracking → CATS → VRChat Tools → Facial

## 9.2.0 (2026년 10월) {#920-october-2026}

- **완전한 스타터 카탈로그:** 번들 스켈레톤/메타리그 9종에 처음부터 썸네일이 있습니다. Basic Humanoid, Simple Human, Full Human, Basic Quadruped, Cat, Horse, Wolf, Bird, Shark입니다. 카탈로그 선택기는 Humans, Quadrupeds 및 Other Animals로 묶습니다.
- **필요할 때 Rigify:** Basic Humanoid는 독립적으로 작동합니다. Rigify가 꺼져 있어도 Rigify 스타터는 보입니다. 하나를 선택하면 **Enable Rigify & Add Rig** 또는 Cancel을 제공합니다. 취소, 활성화 실패 또는 프리셋 부재 시 리그를 추가하지 않습니다.
- **선택 셸프, 과거 9.2.0 위치:** 뷰포트 헤더의 **Starter Rigs** 스위치가 일반 에셋 셸프로 돌아왔고 선택은 환경설정에 저장되었습니다. 9.2.5는 이 스위치를 기본 카탈로그 탭으로 대체합니다. **Add → Armature → Starter Rig Catalog**는 계속 선택기를 팝업으로 엽니다.
- **클릭 또는 드래그:** 스타터를 클릭하거나 뷰포트 안에 놓으면 추가됩니다. 메시 맞춤은 처음에 켜져 있고 웨이트와 컨트롤 생성은 꺼져 있습니다. Adjust Last Operation에서 이 옵션을 제어합니다. 기본 클릭, 드롭, 취소 및 실행 취소/다시 실행 검사는 Bforartists 5.2.0에서 수행했습니다.

## 9.1.2 (2026년 10월) {#912-october-2026}

- **Scene Properties 스위치:** Preferences > Tabs에 Scene Properties 행이 추가되었습니다. Show 버튼은 Properties > Scene 탭의 모든 BoneCraft 섹션(Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools, Import / Export)을 제어합니다. 처음에 켜져 있으며 파란색으로 표시됩니다. 애드온을 비활성화하거나 뷰포트 탭 또는 Armature 탭을 바꾸지 않습니다. [기능 위치](01-start.md#where-things-are)를 참고하세요.

## 9.1.1 (2026년 10월) {#911-october-2026}

- **명확한 아이콘:** 인터페이스 전반에서 각 아이콘은 한 의미로 쓰입니다. 약 60개 버튼에 기능에 더 맞는 Bforartists 아이콘이 적용되었습니다. Apply All Transforms, Decimate, Normalize Names, Translate, Merge, Separate, Blend Pose, Lip Sync 등이 있으며 모든 패널에서 같은 버튼은 같은 아이콘을 씁니다.
- **차분한 패널:** 제목과 고정 텍스트에 주제 아이콘을 붙이지 않습니다. 상태를 알리는 안내에는 정보, 경고 또는 확인 아이콘을 표시합니다.
- **읽기 쉬운 아이콘 격자:** Pose와 Weights 툴 셸프 탭의 모든 버튼에 고유 아이콘이 있어 좁은 셸프에서도 구별할 수 있습니다.

## 9.1.0 (2026년 10월) {#910-october-2026}

- **Bforartists 기본 도구와 같은 위치:** Add → Armature와 Pose, Weights 및 Object 메뉴에 BoneCraft 항목이 추가됩니다. Bforartists의 Pose와 Weights 툴 셸프 탭에도 버튼 패널이 추가됩니다.
- **먼저 실행하고 나중에 조정:** Quick Rig, Fit Dropped Rig, 웨이트 도구는 마지막 값으로 즉시 실행됩니다. Ribbon, Spline IK, Delta Mush 및 CATS 본 도구도 마찬가지입니다. 이후 Adjust Last Operation에서 옵션을 제어하므로 확인 팝업 수가 줄었습니다.
- **작업 먼저, 옵션은 접어서:** 여러 패널에서 선택 설정 접이식 영역 위에 버튼을 표시합니다. 필수 입력과 Fix Model 정리 스위치는 작업 위에 남습니다. 설정은 버튼 대신 확인란을 쓰며 패널 헤더에는 아이콘이 없습니다.
- **제스처 도구:** Place Rig Markers와 Build Mechanism이 뷰포트 도구 모음에 있습니다. 전자는 메시를 클릭하면 Auto-Rig Wizard의 다음 마커를 배치하고 후자는 부품을 클릭하면 관절이나 링크 생성을 시작합니다.
- **아바타 섹션, 과거 9.1.0 위치:** Avatar Tools에는 휴머노이드 매핑, 머리카락, 비짐 및 내보내기가 있었습니다. 별도 VRChat Tools에는 Performance, Clothing 및 Naming 유틸리티가 있습니다. 현재 내보내기는 **Import / Export → Game Engine Export → Unity / VRChat**에 있습니다.
- **툴팁:** 모든 오퍼레이터와 옵션에 설명이 있습니다.
- **숨기지 않고 안내:** 리그가 없어도 섹션을 표시하며 선택할 대상을 안내합니다. Rig Builder에서 Auto-Rig Wizard가 먼저 나타나고 셸프는 읽기 충분한 너비로 시작합니다.
- **수정:** Generate Spline IK가 다시 작동하며 Add Influence는 선택한 본을 사용하고 비짐 미리보기는 해당 세트를 사용합니다.

## 9.0.0 (2026년 10월) {#900-october-2026}

- **Mechanisms:** BoneCraft 탭과 Properties의 Scene 탭에 소품과 기계를 리깅하는 새 섹션이 있습니다. Hinge, Slide, Telescope, Piston, Gear Link, Follow 및 Sequence를 단계별 안내로 만듭니다. Test는 모션을 검사합니다. BoneCraft는 수동 편집을 자동으로 덮어쓰지 않습니다. **Keep mine**은 편집을 유지하고 **Restore**는 메커니즘을 재구성합니다. [Mechanisms](07-mechanisms.md)를 참고하세요.
- **예제 파일:** `examples/crescent-rose/`에는 Mechanisms로 리깅한 Crescent Rose(낫, 소총, 접힌 형태)가 있으며 설명서의 [12장](12-crescent-rose.md)에서 단계별로 만듭니다.
- **탭 위치:** 각 뷰포트 탭을 왼쪽 툴 셸프나 오른쪽 사이드바에 둘 수 있습니다(Preferences → Tabs → Left / Right). BoneCraft와 Rig Builder는 왼쪽, CATS는 오른쪽에서 시작합니다.
- **Rig Builder:** Properties의 Scene 탭에 항상 나타나며 별도 뷰포트 탭도 있습니다. 좁은 툴 셸프에는 간결한 배치를 사용합니다. BoneCraft Rigs 에셋 라이브러리에는 Basic Humanoid가 있으며 Fit Dropped Rig는 에셋 셸프에서 놓은 리그를 맞춥니다.
- **CATS 탭:** Import / Export가 CATS 탭으로 이동했습니다. CATS, VRChat 및 Import / Export는 Scene 탭에도 항상 있습니다.
- **Show Helpers:** 하나의 환경설정으로 BoneCraft 설명 문구를 표시하거나 숨깁니다. Compact Mode는 같은 환경설정을 제어합니다.
- **Rig Validator:** 하이픈이 있는 본 이름을 허용합니다. 드라이버는 Python이 필요한 표현식만 경고합니다. Mechanisms 리그도 검사하며 Task Board의 검증 작업 결과가 다시 보고됩니다.
- **이름:** 애드온 이름은 BoneCraft입니다.

## 8.9.x (2026년 9월–10월) {#89x-septemberoctober-2026}

- **8.9.6:** 의상 전체가 엉덩이 관통 없이 스커트 본을 따릅니다. 턱 벌림 입꼬리 보정이 붙는 입술을 지원합니다.
- **8.9.5:** IK/FK 팔꿈치 전환이 튀지 않고 포즈를 유지합니다. 어깨 감지가 대칭이며 눈 마커가 더 이상 튀지 않습니다. Control Picker가 선택을 표시합니다. 더 둥근 입꼬리, 허벅지 위 의상 보정, 완화된 리타기팅 쇄골 및 T-포즈 내보내기도 포함됩니다.
- **8.9.4:** 더 둥근 무릎을 위해 보정이 Preserve Volume을 대체합니다. 깊게 굽힐 때의 접촉 키와 어깨 이음새 블렌딩도 추가됩니다.
- **8.9.3:** 2구간 스커트 본이 다리를 따라가며 다리도 이 본들을 밀어냅니다.
- **8.9.2:** 셰이프 키로 눈꺼풀 접힘 없이 눈을 깜박이며 입 벌림은 타원형입니다.
- **8.9.1:** 고밀도 메시 스키닝이 빨라졌습니다(678,000개 정점: 232 s에서 57 s). 본 히트는 조용히 실패하는 대신 더 가벼운 프록시 메시를 사용합니다.
- **8.9.0:** 관절 보정 셰이프 키와 눈 조준, 깜박임, 입술 추종용 얼굴 컨트롤이 추가됩니다. 의상은 관절과 함께 구부러집니다.
- 8.9는 자동 본 웨이트 재계산과 더 명확한 아틀라스 선택도 추가합니다.

## 8.7–8.8 (2026년 9월) {#8788-september-2026}

- **8.8.0:** 리타기팅 패널이 Blender 5 호스트에서 작동합니다. 손가락 마커는 손 모양을 사용합니다. 피부까지 늘어나는 IK, Preserve Volume 옵션 및 Delta Mush 바인딩 수정도 포함됩니다.
- **8.7.0:** 통합 컨트롤 리그, 팔다리 추적 관절 감지, 방향을 맞추는 리타기팅 및 트위스트 본이 추가됩니다.

## 8.5–8.6 (2026년 7월) {#8586-july-2026}

- **8.6.1–8.6.3:** Material Atlas는 베이크 후 타일 진단과 혼합 머티리얼의 더 나은 분할을 제공합니다. 실제 텍스처 알파를 기준으로 MToon 투명도를 확인하고 아틀라스 생성 중 보존합니다.
- **8.5.5–8.5.10:** VRM / MToon 머티리얼이 알파 모드를 따릅니다. Blender 5 호스트에서도 알파가 작동합니다. 과도한 발광 방지, 마젠타 진단 및 안전한 아틀라스 이름도 추가됩니다.
- **8.5.4:** 휴머노이드 매핑을 올바르게 불러오며 Naming Prep 안내도 추가됩니다.
- **8.5.2–8.5.3:** VRoid 다운로드(.zip) 가져오기와 VRoid 프로젝트 인계 카드가 추가됩니다.
- **8.5.1:** FBX 내보내기가 블렌드 셰이프를 보존합니다.

## 이전 버전 {#earlier-versions}

**8.5.0:** 베이크 후 Smart Combine은 기본적으로 `atlas_uv`를 내보내기 UV0으로 만듭니다. Advanced 설정의 **Keep Source UV Maps**를 켜지 않으면 생성된 아틀라스 메시에서 아틀라스 이전 소스 UV 맵을 제거합니다. 공개 Blender 빌드도 이제 CATS / Material Combiner / UVToolkit 파생 컨트롤을 공유합니다. 프로덕션 리깅, 컨트롤, 리타기팅/내보내기 및 B4Artists 전용 릴리스 시스템은 B4Artists에만 제공됩니다.

8.5.0은 내보내기와 검증도 갱신합니다. VRChat, VRM, MMD 및 Unreal 내보내기에 BoneCraft 패널의 폴더와 파일 이름 컨트롤이 제공됩니다. 내보내기 설정은 더 이상 Blender 파일 브라우저 기본값에만 의존하지 않습니다. VRChat/Unity와 Unreal FBX 내보내기는 머티리얼 가져오기를 쉽게 하기 위해 기본적으로 **Embed Textures**를 켭니다. **Helper Meshes**를 켜지 않으면 VRChat FBX에서 도우미/컨트롤 셰이프 메시를 제외합니다. VRM 패널에는 **Lint Now**와 **Fix Humanoid Map**이 추가됩니다. Fix Humanoid Map은 본 이름을 바꾸지 않고 내보내기 전에 오래된 휴머노이드 별칭 매핑을 복구합니다.

**8.4.5:** 베이크 중 Smart Combine은 소스 텍스처가 보존된 아틀라스 이전 UV를 샘플링하게 합니다. 원본을 숨기기 전에 생성된 아틀라스 메시를 검증하며 모든 아틀라스 면을 최종 아틀라스 머티리얼 슬롯으로 재설정합니다. 의상 부분이 회색이나 뒤섞인 상태가 되는 문제를 방지합니다.

**8.4.4:** Material Atlas Combiner는 품질 동등성을 위한 베이크 전 검사 컨트롤을 추가합니다. 셰이더/머티리얼 진단, 텍스처 역할 이름, 중복/공유 소스 표시, 머티리얼별 크기 재정의 및 패킹 프리셋이 포함됩니다. 선택 출력 베이크는 Normal/Emission/Roughness를 지원합니다. 검증될 때까지 사전 검사가 Metallic/ORM 채널 패킹을 차단합니다.

**8.4.3:** Material Atlas Combiner는 기존 작업 흐름에 선택 가능한 UV 패킹 방법을 추가합니다. Smart Pack, Grid Pack, Seeded Variation, Oriented Pack, Fit 0-1 Bounds, Advanced Variation 및 Rotation Step이 있습니다. 디버그 보고서와 베이크 기록은 UV 방법 세부 사항을 기록합니다.

**8.4.2:** 베이크 중 Material Atlas Combiner는 생성된 아틀라스 UV를 대상으로 하며 복사된 소스 텍스처 노드는 아틀라스 이전 UV를 명시적으로 읽습니다. 서로 다른 UV 맵을 샘플링해서 발생하던 의상 아틀라스 오류를 수정합니다. 8.4.1의 선택 가능한 머티리얼과 텍스처 행은 유지됩니다.

**7.1.3(환경설정 이름 정리):** 두 애드온 환경설정 스위치 이름이 사이드바 탭에 맞게 바뀌었습니다. “VRChat Avatar Tools”는 CATS 사이드바 탭에 맞춰 **CATS**가 되고 “Task Board & Sidebar”는 Rig Builder 사이드바 탭에 맞춰 **Rig Builder**가 됩니다. Edit > Preferences > Add-ons > BoneCraft의 스위치 이름만 바뀌었으며 제거된 도구는 없습니다.

**7.1.1:** BoneCraft에 VRChat 아바타 정리, 최적화 및 설정을 위한 전체 CATS 도구 모음이 추가됩니다. CATS는 자체 사이드바 탭이 있으며 파이프라인은 작업 순서를 안내합니다.

다음: [튜토리얼: Mechanisms로 Crescent Rose 만들기](12-crescent-rose.md)
