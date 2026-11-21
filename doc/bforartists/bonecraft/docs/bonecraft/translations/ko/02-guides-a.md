# 가이드 1–7 {#guides-17}

[← 목차](index.md)

## 가이드 1: 첫 아바타를 VRChat에 올리기 {#guide-1-get-your-first-avatar-into-vrchat}

연습용 메시는 [서면 마네킹 워크숍](06-rig-builder.md#illustrated-mannequin-workshop)을 따르세요. Simple Human, 리그 없는 마네킹, Auto-Rig 및 IK/FK 단계로 구성됩니다.

> **시간:** 처음 전체 과정을 진행하면 약 45–60분
> **결과:** 리깅되어 VRChat SDK용으로 내보낸 VRChat 준비 아바타

**시작 전 확인:**

- [ ] 3D 모델을 Bforartists로 가져왔습니다(File > Import에서 형식 선택)
- [ ] 모델이 T-포즈(팔은 양옆, 몸은 수직) 또는 그에 가까운 자세입니다
- [ ] 명백히 깨진 지오메트리(뜬금없이 떠 있는 삼각형)가 없습니다
- [ ] 3D 뷰포트에서 단단한 회색 형태의 모델이 보입니다

---

### 1단계 — Rig Builder 열기 {#step-1--open-the-rig-builder}

1. 3D 뷰포트에서 **T**로 왼쪽 툴 셸프를 표시하세요.

2. **Rig Builder**를 여세요.

Preferences → Tabs → Scene Properties → Show가 켜져 있으면 **Properties → Scene**에도 Rig Builder가 나타납니다. **Auto-Rig Wizard**, Quick Rig(기성 아마츄어), **Mannequin**의 세 부분으로 구성됩니다.

3. **Auto-Rig Wizard**를 펼치세요.

4. **Start Auto-Rig**를 선택하세요.

3D 뷰포트의 Add → Armature → Auto-Rig Wizard 메뉴로 시작한 뒤 Rig Builder에서 계속할 수도 있습니다.

영문 원본 이미지 설명(이미지 생략): Rig Builder 탭의 Auto-Rig Wizard.

*과거 워크숍 캡처. Rig Builder 탭의 Auto-Rig Wizard.*

---

### 2단계 — 메시 선택 {#step-2--select-your-mesh}

마법사는 장면의 메시를 나열합니다.

1. 목록에서 아바타 메시를 선택하세요.

2. **Next**를 선택하세요.

**표시되는 결과:** 메시 이름이 있는 “Selected:” 줄이 나타난 뒤 리그 유형 단계로 이동합니다.

영문 원본 이미지 설명(이미지 생략): Auto-Rig Wizard에 사용할 입력 메시 선택.

*과거 워크숍 캡처. Auto-Rig Wizard에 사용할 입력 메시 선택.*

---

### 3단계 — 리그 유형 선택 {#step-3--choose-the-rig-type}

1. 눈 깜박임, 표정 및 립싱크에는 **Body + Face**를 선택하세요.

2. 얼굴 컨트롤 없는 몸에는 **Body Only**를 선택하세요.

3. Generation Options에서 **Kinematics**를 IK/FK, IK only 또는 FK only로 설정하세요.

4. **Next**를 선택하세요.

영문 원본 이미지 설명(이미지 생략): 몸 리그 유형과 IK/FK 방식 선택.

*과거 워크숍 캡처. 몸 리그 유형과 IK/FK 방식 선택.*

---

### 4단계 — 몸 마커 배치 {#step-4--place-body-markers}

마커는 골반, 척추, 목, 머리, 어깨, 팔, 손, 다리 및 발 위치를 나타냅니다. BoneCraft는 이 위치로 본을 만듭니다. 각 마커를 주의 깊게 확인하세요.

**Smart Detection:**

1. **Detect Markers**를 선택하세요.

2. **Accept High**로 신뢰도가 높은 마커를 유지하세요.

3. **Reset Low**로 신뢰도가 낮은 마커를 지우고 수동 배치하세요.

BoneCraft는 메시 팔다리를 추적하고 마커별 신뢰도를 매깁니다. **Guess Markers from Mesh**는 대신 메시 비율로 위치를 추정합니다.

**뷰포트 도구 사용:**

1. 오브젝트 모드(Object Mode)에서 도구 모음의 Place Rig Markers를 활성화하세요.

2. 메시를 클릭하여 도구 헤더에 표시된 마커를 배치하고 확인하세요.

3. 다음 미확인 마커에서도 반복하세요.

4. 마커 단계가 끝나면 마법사의 **Next**를 선택하세요.

도구 헤더에는 축 잠금과 미러 스위치도 있습니다.

**마커를 하나씩 배치:** 각 마커 행에는 아이콘 버튼이 있습니다. 포인터를 올려 툴팁을 읽으세요.

1. 해당 행의 화살표 아이콘 **Place Marker**를 선택하세요.

2. 아바타의 필요한 위치를 클릭하세요.

3. 위치가 맞으면 확인 표시 **Confirm Marker**를 선택하세요.

원형 화살표 **Reset Marker**는 배치한 마커를 지워 다시 배치하게 합니다.

**대칭:** **Toggle Symmetry**는 마커를 놓을 때 반대쪽도 배치합니다. 좌우 마커 행의 첫 아이콘입니다. **Mirror L to R**, **Mirror R to L**은 확인한 모든 마커를 반대쪽으로 복사합니다.

1. 모든 마커를 놓았다면 **Confirm All Placed**를 선택하세요.

2. **Next**를 선택하세요.

영문 원본 이미지 설명(이미지 생략): 조정 전에 감지된 몸 마커를 검토합니다.

*과거 워크숍 캡처. 조정 전에 감지된 몸 마커를 검토합니다.*

---

### 5단계 — 손가락 마커 배치 {#step-5--place-finger-markers}

1. Finger Detail에서 “0 — No Fingers”부터 “5 — Full Human Hand”까지 손가락 수를 선택하세요.

2. **Guess Finger Markers**를 선택하세요.

3. 잘못된 마커 위치를 조정하세요.

4. **Next**를 선택하세요.

BoneCraft는 손 모양을 사용해 각 손가락을 관절에서 끝까지 추적합니다. 표준 손은 “5 — Full Human Hand”를 사용합니다.

---

### 6단계 — 얼굴 마커 배치(Body + Face 전용) {#step-6--place-face-markers-body--face-only}

1. **Guess Face Markers**를 선택하세요.

2. 필요에 따라 눈, 눈꺼풀, 눈썹, 입꼬리 및 턱을 조정하세요.

3. **Next**를 선택하세요.

눈 마커는 수동 할당한 위치를 유지합니다.

---

### 7단계 — 검토와 생성 {#step-7--review-and-generate}

검토 단계는 경고와 생성 옵션을 나열합니다. **Generate Rig**를 클릭하세요.

**표시되는 결과:** 아바타 안에 IK/FK 팔다리와 손가락을 포함한 주황색 본이 나타납니다. Body + Face 리그에는 얼굴 리그도 있습니다. 본을 움직이면 연결된 스킨이 변형됩니다.

최종 단계에는 **Build Control Rig**와 **Close Wizard**가 있습니다. Build Control Rig는 Generate Rig가 적용하지 않는 검토 옵션을 적용합니다. [리그 빌더](06-rig-builder.md)에서 두 컨트롤을 설명합니다.

> **스킨 웨이트**는 메시의 각 부분을 어느 본이 움직일지 정합니다. BoneCraft가 자동 설정하며 세부 조정에는 [리그 도구](05-rig-tools.md)의 Weight Tools를 사용하세요.

영문 원본 이미지 설명(이미지 생략): 생성 전에 리그 설정을 검토합니다.

*과거 워크숍 캡처. 생성 전에 리그 설정을 검토합니다.*

---

### 8단계 — VRChat 휴머노이드 본에 매핑 {#step-8--map-to-vrchats-humanoid-bones}

1. **N**으로 오른쪽 사이드바를 표시하세요.

2. **CATS → Avatar Tools → Set Up Humanoid Bones**를 여세요.

3. **Auto-Map All**을 선택하세요.

4. **Normalize Names**를 선택하세요.

5. **Validate**를 선택하세요.

Auto-Map All은 본을 VRChat 몸 슬롯에 연결합니다. Normalize Names는 매핑된 본에 VRChat이 기대하는 이름을 붙입니다.

**표시되는 결과:** Hips, Spine, Head, LeftUpperArm 등의 필수 슬롯에 각각 본이 표시됩니다. 가이드 5에서 슬롯을 설명합니다.

[휴머노이드 매핑 컨트롤](08-vrchat.md#set-up-humanoid-bones)을 참고하세요.

---

### 9단계 — VRChat용 내보내기 {#step-9--export-for-vrchat}

[Unity / VRChat 내보내기 설정](08-vrchat.md#export-to-vrchat)을 참고하세요.

1. 아바타 아마츄어를 선택하세요.
2. **CATS → Import / Export → Game Engine Export → Unity / VRChat**를 여세요.
3. **Folder**를 설정하세요.
4. **Avatar**를 내보낼 이름으로 설정하세요.
5. **Bone Names**를 선택하세요.
6. 프리셋을 쓰면 이름 미리보기를 검토하세요.
7. <strong>Export to VRChat (Unity)</strong>를 클릭하세요.

기본값은 **Keep Original Names**입니다. **Unity-Preset**과 **Unreal-Preset**은 내보내기 사본의 인식된 본 이름을 바꾸며 작업 리그 이름은 유지합니다.

주요 Unity 및 Unreal 내보내기 버튼은 오브젝트, 포즈 및 편집 모드를 지원하며 이전 모드와 선택을 복원합니다.

충돌, 매핑 및 애니메이션 제약은 [내보내기 이름과 한계](08-vrchat.md#export-bone-naming)를 참고하세요.

**표시되는 결과:** 선택한 폴더에 내보낸 아바타가 있으며 Unity의 VRChat Creator Companion과 VRChat SDK에서 사용할 준비가 됩니다.

---

**가능해진 작업:** 리깅된 VRChat 아바타가 완성되었습니다. 다음에는 머리카락 물리(가이드 6), 의상(가이드 7), 립싱크(가이드 8), 성능 검사(가이드 9)를 진행할 수 있습니다. CATS 정리와 VRChat 설정은 [가이드 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)을 참고하세요.

---

## 가이드 2: VRoid 아바타를 VRChat으로 가져오기 {#guide-2-bring-a-vroid-avatar-into-vrchat}

> **시간:** 약 15–25분
> **결과:** VRChat용으로 내보낼 준비가 된 VRoid 아바타

**시작 전 확인:**

- [ ] VRoid Studio에서 `.vrm`으로 내보냈거나 VRoid Hub에서 `.zip`으로 다운로드했습니다
- [ ] BoneCraft가 설치되고 활성화되어 있습니다

---

### 1단계 — VRM 애드온 설치 {#step-1--install-the-vrm-add-on}

BoneCraft가 `.vrm`을 읽으려면 VRM 애드온이 필요합니다.

1. **CATS → Import / Export → VRM / VRoid**를 여세요.

2. 가져오기 전에 의존 패키지를 설치하세요.

3. 의존 패키지를 켜세요.

비활성 브리지에는 **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website**, **Show Manual Instructions**가 있습니다.

오프라인 패키지:

1. 기본 Preferences를 여세요.

2. 기존 애드온 ZIP은 <strong>Add-ons → Install from Disk…</strong>로 설치하세요.

3. 최신 확장 패키지는 대신 기본 Extensions 설치 메뉴를 사용하세요.

4. 브리지로 돌아오세요.

5. **Active**가 표시되는지 확인하세요.

[형식 브리지 설치 컨트롤](08-vrchat.md#vrm-bridge)을 참고하세요.

---

### 2단계 — 아바타 가져오기 {#step-2--import-your-avatar}

1. **VRM / VRoid**에서 <strong>Import VRM…</strong>을 선택하세요.

2. `.vrm` 파일을 선택하세요.

VRoid 다운로드 파일:

1. 대신 <strong>Import VRoid (.vroid / .zip)…</strong>를 선택하세요.

2. 다운로드한 `.zip` 파일을 선택하세요.

VRoid Studio 프로젝트(`.vroid`)를 선택하면 “VRoid Studio Project” 카드가 나타납니다. 프로젝트는 아직 아바타가 아닙니다.

프로젝트 파일의 경우:

1. VRoid Studio에서 프로젝트를 VRM으로 내보내세요.

2. 해당 VRM 파일을 가져오세요.

**표시되는 결과:** 뷰포트에 스켈레톤이 있는 VRoid 캐릭터가 나타납니다.

---

### 3단계 — VRChat 휴머노이드 본에 매핑 {#step-3--map-to-vrchats-humanoid-bones}

1. **CATS → Avatar Tools → Set Up Humanoid Bones**를 여세요.

2. **Auto-Map All**을 선택하세요.

VRoid 스켈레톤은 표준 배치를 따라 보통 모든 슬롯을 채웁니다. 잘못된 슬롯이 있으면 **VRM / VRoid**의 Lint 아래 **Fix Humanoid Map**을 선택하세요. 흔한 VRoid 이름 매핑 오류를 복구합니다.

---

### 4단계 — 본 이름 수정 {#step-4--fix-bone-names}

**Set Up Humanoid Bones**에서 **Normalize Names**를 선택하세요. 매핑된 본의 VRoid 이름을 VRChat이 기대하는 이름으로 바꿉니다.

---

### 5단계 — 비짐(립싱크) 설정 {#step-5--set-up-visemes-lip-sync}

VRoid 아바타에는 립싱크 입 모양이 이미 있습니다. **VRM / VRoid**에서 **Map VRoid Visemes**를 클릭하세요. BoneCraft가 VRoid 셰이프 키를 VRChat 립싱크 모양에 맞춥니다.

---

### 6단계 — 머리카락 물리(선택) {#step-6--hair-physics-optional}

VRoid 머리카락은 SpringBones를 사용합니다. **VRM / VRoid**의 **Convert SpringBones → PhysBones**가 VRChat PhysBones로 바꿉니다. 가이드 6에서 자세히 설명합니다.

---

### 7단계 — 내보내기 {#step-7--export}

가이드 1의 9단계처럼 내보내세요.

**가능해진 작업:** VRoid 아바타가 VRChat Creator Companion용으로 준비되었습니다. 업로드 전에 성능 검사(가이드 9)도 할 수 있습니다.

---

## 가이드 3: MMD 아바타를 VRChat으로 가져오기 {#guide-3-bring-an-mmd-avatar-into-vrchat}

> **시간:** 약 20–30분
> **결과:** VRChat용으로 준비된 MMD `.pmx` 모델

**시작 전 확인:**

- [ ] `.pmx` 또는 `.pmd` MMD 모델 파일이 있습니다
- [ ] BoneCraft가 설치되어 있습니다

---

### 1단계 — mmd_tools 설치 {#step-1--install-mmd_tools}

MMD 파일을 읽으려면 **mmd_tools**가 필요합니다. BoneCraft는 기존 애드온과 최신 Blender Extensions를 모두 인식합니다.

1. **CATS → Import / Export → MMD / PMX**를 여세요.
2. 의존 패키지 누락이 표시되면 **Auto-Install Latest from GitHub**를 클릭하세요.
3. 설치되었지만 꺼진 사본은 **Open Add-on Preferences**로 켜세요.
4. 가져오기 전에 **Active**가 표시되는지 확인하세요.

수동 설치:

1. 비활성 브리지 카드에서 **Website**나 **Show Manual Instructions**를 선택하세요.

2. **Preferences → Get Extensions**에서 공식 MMD 확장을 설치하세요.

오프라인 ZIP:

1. 최신 확장 패키지는 확장 설치 메뉴를 사용하세요.

2. 기존 애드온 패키지는 대신 <strong>Add-ons → Install from Disk…</strong>를 사용하세요.

독립형 브리지 콘텐츠가 표시되면 <strong>Install from .zip on Disk...</strong>도 있습니다.

로컬 확장 저장소가 없다고 보고하면:

1. **Preferences → Get Extensions → Repositories**를 여세요.

2. 로컬 저장소를 추가하거나 켜세요.

3. 설치를 다시 시도하세요.

업스트림 릴리스 패키지를 사용하세요. 설치 오류나 취소한 가져오기는 성공한 가져오기가 아닙니다.

[형식 브리지 설치 컨트롤](08-vrchat.md#vrm-bridge)을 참고하세요.

---

### 2단계 — PMX 파일 가져오기 {#step-2--import-your-pmx-file}

1. **MMD / PMX**에서 <strong>Import PMX / PMD...</strong>를 선택하세요.

2. 모델을 선택하세요.

**표시되는 결과:** 뷰포트에 일본어 본 이름을 가진 MMD 캐릭터가 나타납니다.

---

### 3단계 — 본 이름 수정 {#step-3--fix-bone-names}

VRChat 내보내기 전에 MMD 본을 Unity 휴머노이드 슬롯에 매핑하세요.

1. **MMD / PMX**에서 **Convert Bone Names -> Unity**를 선택하세요.

다른 언어의 이름:

1. **CATS → CATS → Translate Bone Names**를 여세요.

2. 소스 **Language**를 선택하세요.

3. **Translate Bone Names**를 선택하세요.

---

### 4단계 — 모델 정리 {#step-4--clean-up-the-model}

MMD 모델에는 여분의 지오메트리와 별도 부품이 있는 경우가 많습니다.

1. **CATS → CATS**를 여세요.

2. **Fix Model** 옵션을 검토하세요.

3. 아바타에 필요한 정리 작업을 선택하세요.

4. **Fix Model**을 실행하세요.

5. VRChat 권장 방식으로 몸 부품을 하나의 메시로 합치려면 **Join Meshes**를 선택하세요.

[가이드 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)은 전체 CATS 파이프라인을 설명합니다.

---

### 5단계 — VRChat 휴머노이드 본에 매핑 {#step-5--map-to-vrchats-humanoid-bones}

1. **CATS → Avatar Tools → Set Up Humanoid Bones**를 여세요.

2. **Auto-Map All**을 선택하세요.

3. 빈 슬롯은 해당 버튼을 선택하세요.

4. 해당 본을 선택하세요.

MMD와 VRChat 스켈레톤은 비슷하므로 대부분 자동으로 채워집니다.

---

### 6단계 — 물리와 내보내기 {#step-6--physics-and-export}

**MMD / PMX**의 **Convert Physics -> PhysBones**는 MMD의 강체 머리카락/스커트 물리를 VRChat PhysBones로 바꿉니다. 그다음 가이드 1의 9단계처럼 내보내세요.

**가능해진 작업:** MMD 아바타가 VRChat용으로 준비되었습니다. 업로드 전에 머리카락 물리(가이드 6)와 립싱크(가이드 8)를 설정할 수 있습니다.

---

## 가이드 4: 아바타의 본 이름 수정 {#guide-4-fix-your-avatars-bone-names}

> **시간:** 약 5–15분
> **결과:** VRChat이 필요로 하는 본의 이름이 호환 가능한 이름으로 변경됨

**시작 전 확인:**

- [ ] 아바타를 열었고 스켈레톤(아마츄어)이 보입니다

---

### 1단계 — 현재 이름 방식 감지 {#step-1--detect-the-current-naming-style}

[Naming 컨트롤](08-vrchat.md#vrchat-naming-extras)을 참고하세요.

1. **CATS → VRChat Tools**를 여세요.

2. Naming에서 **Detect**를 선택하세요.

3. 이름 변경 후 **Force Rescan**으로 다시 확인하세요.

BoneCraft는 Mixamo, VRoid, Unity 등의 감지된 이름 방식과 점수를 보고합니다.

일본어, 중국어, 한국어, 포르투갈어, 스페인어 또는 프랑스어 본 이름의 경우:

1. **CATS → CATS → Translate Bone Names**를 여세요.

2. 소스 **Language**를 선택하세요.

3. **Translate Bone Names**를 선택하세요.

인식된 이름을 영어로 변환합니다.

---

### 2단계 — VRChat 이름으로 변경 {#step-2--rename-to-vrchat-names}

내보내기에서만 이름을 바꾸려면 작업 이름은 유지하고 내보내기 섹션에서 **Unity-Preset**을 선택하세요. [내보내기 본 이름](08-vrchat.md#export-bone-naming)을 참고하세요.

1. 가이드 5의 2단계대로 본을 매핑하세요.

2. **Set Up Humanoid Bones**에서 **Normalize Names**를 선택하세요.

매핑된 모든 본에 VRChat이 기대하는 이름이 붙습니다.

**표시되는 결과:** `Hips`, `Spine`, `Chest`, `LeftUpperArm` 같은 본 이름.

---

### 3단계 — 수동 수정(필요한 경우) {#step-3--manual-fixes-if-needed}

**VRChat Tools**의 Naming 그룹에는 남은 본을 위한 일괄 도구도 있습니다.

- **Find and Replace** — 모든 본 이름에서 한 문구를 다른 문구로 바꾸기
- **Add Prefix**, **Add Suffix** — 모든 본 이름의 앞뒤에 문구 추가
- **Remove Prefix**, **Remove Suffix** — 다시 제거
- **Regex Replace** — 정규 표현식으로 같은 작업 수행

**가능해진 작업:** 올바른 본 이름은 휴머노이드 매핑(가이드 5)을 자동으로 작동하게 합니다. 이름이 맞지 않으면 VRChat이 캐릭터 움직임을 판단할 수 없습니다.

---

## 가이드 5: 아바타를 VRChat의 몸 시스템에 매핑하기 {#guide-5-map-your-avatar-to-vrchats-body-system}

> **시간:** 약 10–15분
> **결과:** VRChat 휴머노이드 움직임 시스템에 연결된 아바타 스켈레톤

**시작 전 확인:**

- [ ] 본 이름이 적절합니다(아니면 가이드 4 참고)
- [ ] 스켈레톤이 선택되어 있습니다
- [ ] **Object Mode**입니다(뷰포트 왼쪽 위 드롭다운 확인)

---

### 1단계 — Set Up Humanoid Bones 열기 {#step-1--open-set-up-humanoid-bones}

**CATS** 탭에서 **Avatar Tools** → **Set Up Humanoid Bones**를 펼치세요.

---

### 2단계 — 자동 매핑 {#step-2--auto-map}

**Auto-Map All**을 클릭하세요. BoneCraft가 스켈레톤을 검색해 몸 슬롯을 채웁니다.

> 휴머노이드 슬롯은 Hips, Head, Left Hand 같은 몸 부위를 식별합니다. BoneCraft는 여기에 본을 할당합니다. 저장한 휴머노이드 매핑은 파일을 다시 열면 올바르게 불러옵니다.

**표시되는 결과:** 본 할당과 필수 슬롯 충족 비율. 필수 슬롯은 Hips, Spine, Head와 양쪽 upper arms, lower arms, hands, upper legs, lower legs, feet의 15개입니다. 선택 사항인 슬롯에는 Chest, UpperChest, Neck이 있습니다.

---

### 3단계 — 매핑 확인 {#step-3--check-the-mapping}

**Validate**를 클릭하세요. 모든 필수 슬롯에 본이 있고 계층이 적절한지 확인합니다.

---

### 4단계 — 빈 슬롯 수동 채우기 {#step-4--fill-empty-slots-by-hand}

빈 슬롯은 “(click to map)”을 표시합니다.

1. 빈 슬롯을 선택하세요.

2. 올바른 본을 선택하세요.

3. **Validate**를 다시 선택하세요.

4. **Normalize Names**로 매핑된 본에 VRChat 이름을 붙이세요.

---

### 5단계 — 눈 추적 설정(선택) {#step-5--set-up-eye-tracking-optional}

아바타에 눈 본이 있다면:

1. **CATS → CATS → Eye Tracking**을 여세요.

2. **Auto-Detect**로 눈 본 이름을 검색하세요.

3. **Left Eye**, **Right Eye** 할당을 확인하세요.

4. 필요하면 올바른 본을 수동 선택하세요.

5. 회전 한계를 설정하세요.

6. **Create Eye Tracking**을 선택하세요.

[가이드 13, 3단계](03-guides-b.md#phase-3--eye-tracking)에서 설정을 설명합니다.

**가능해진 작업:** 휴머노이드 매핑으로 VRChat에서 아바타가 사용자의 움직임을 따릅니다. IK(역운동학)는 게임 안의 손이 컨트롤러를 따르게 합니다.

---

## 가이드 6: 머리카락 물리 추가 {#guide-6-add-hair-physics}

> **시간:** 약 15–25분
> **결과:** VRChat에서 자연스럽게 흔들리는 머리카락과 다른 부드러운 부위

**시작 전 확인:**

- [ ] 아바타를 열고 스켈레톤을 선택했습니다
- [ ] Set Up Humanoid Bones가 완료되었습니다(가이드 5)

> PhysBone은 무게가 있는 것처럼 본이 튀고 흔들리게 하는 VRChat 컴포넌트입니다. BoneCraft는 머리카락, 귀, 꼬리, 스커트 및 액세서리의 본 체인에 설정합니다.

---

### 1단계 — Add Hair Physics 열기 {#step-1--open-add-hair-physics}

**CATS** 탭의 **Avatar Tools** → **Add Hair Physics**를 펼치세요. Hair Chain Detection, Hair Chain Generation, PhysBone Configuration, Hair Physics Colliders의 네 부분입니다.

---

### 2단계 — 머리카락 체인 찾기 {#step-2--find-the-hair-chains}

본이 이미 있다면 **Detect Hair Physics Chains**를 선택하세요. BoneCraft는 루트부터 끝까지 연결된 머리카락형 본 체인을 검색합니다. 목록에는 체인별 루트 본과 길이가 표시됩니다.

본이 없다면:

1. 머리카락 메시들을 선택하세요.

2. Hair Chain Generation에서 **Generate**를 선택하세요.

3. 즉시 **Adjust Last Operation**의 **Chain Density**를 Low, Medium 또는 High로 설정하세요.

**Replace**는 확인을 요청하며 현재는 기존 체인을 제거하지 않고 새 체인을 만듭니다.

다시 생성하기 전에:

1. 본 목록을 검토하세요.

2. 원치 않는 체인이 있다면 제거하세요.

---

### 3단계 — PhysBone 프리셋 선택 {#step-3--choose-a-physbone-preset}

1. 체인의 본 하나를 선택하세요.

2. PhysBone Configuration에서 **Hair**, **Skirt** 또는 **Tail**을 선택하세요.

Skirt는 스커트와 망토, Tail은 꼬리와 밧줄에 적합합니다.

**표시되는 결과:** 체인의 Pull, Spring, Stiffness, Gravity 및 Max Angle 값.

---

### 4단계 — 세부 조정(선택) {#step-4--fine-tune-optional}

패널은 체인 값을 표시하지만 편집하지 못합니다. Stiffness가 높으면 덜 구부러지고 Gravity가 높으면 아래로 당깁니다. Max Angle이 작으면 흔들림이 제한됩니다. 값을 바꾸려면 다른 프리셋을 선택하거나 아바타를 가져온 뒤 Unity의 PhysBone 컴포넌트를 편집하세요.

---

### 5단계 — 콜라이더 추가(권장) {#step-5--add-colliders-recommended}

콜라이더는 머리카락이 머리와 몸을 통과하지 않게 하는 보이지 않는 형태입니다. Hair Physics Colliders에서 **Place Default Colliders**를 선택하면 머리, 어깨 및 가슴에 추가됩니다. **Add Collider**, **Remove Collider**는 하나씩 추가하거나 제거합니다.

**가능해진 작업:** VRChat에서 고개를 돌리거나 점프하거나 춤출 때 머리카락이 자연스럽게 움직입니다. 꼬리, 귀, 스커트 및 늘어진 액세서리에도 같은 절차를 사용합니다.

---

## 가이드 7: 몸과 함께 움직이는 의상 부착 {#guide-7-attach-clothing-that-moves-with-your-body}

> **시간:** 약 20–30분
> **결과:** 아바타 스켈레톤에 붙어 몸과 함께 움직이는 의상

**시작 전 확인:**

- [ ] 기본 아바타의 스켈레톤이 완성되고 몸에 웨이트가 있습니다
- [ ] 의상이 같은 파일에 있습니다(자체 아마츄어가 있다면 함께)
- [ ] 의상이 대략 아바타 몸에 맞습니다

---

### 1단계 — Attach Clothing 열기 {#step-1--open-attach-clothing}

[Clothing 컨트롤과 선택 순서](08-vrchat.md#attach-clothing)를 참고하세요.

**CATS** 탭의 **VRChat Tools**를 펼쳐 Clothing 그룹을 찾으세요. Bone Matching, Collision Detection, Clothing Merge의 세 부분입니다.

---

### 2단계 — 본 맞추기 {#step-2--match-bones}

의상에 아마츄어가 있다면:

1. 오브젝트 모드(Object Mode)로 바꾸세요.

2. 의상과 아바타 아마츄어를 모두 선택하세요.

3. **Match Bones**로 본 이름을 비교하세요.

**표시되는 결과:** HIGH, MEDIUM, LOW, UNMATCHED 일치 수. 패널은 본 쌍 목록을 표시하지 않습니다. 의상에 아마츄어가 없다면 이 단계를 건너뛰세요.

아마츄어 둘을 합치기 전:

1. **Detect Collisions**로 충돌하는 본 이름을 확인하세요.

2. 제안된 새 이름을 검토하세요.

3. 의상 아마츄어를 활성화하세요.

4. **Resolve Collisions**로 해당 아마츄어에 이름 변경을 적용하세요.

Detect Collisions는 이름만 검사하며 메시 교차를 검사하지 않습니다.

---

### 3단계 — 의상 병합 {#step-3--merge-the-clothing}

1. 의상 아마츄어가 있다면 해당 아마츄어와 메시를 선택하세요.

2. 없다면 의상 메시만 선택하세요.

3. 아바타 아마츄어를 마지막에 Shift-클릭하여 활성화하세요.

4. **Merge Clothing**를 선택하세요.

의상 아마츄어가 있으면 의상을 아바타 스켈레톤으로 옮기고 본을 합칩니다. 없으면 몸의 웨이트를 의상 메시에 전달합니다.

> 웨이트(웨이트 페인팅)는 각 본이 메시의 각 점을 얼마나 움직일지 정하는 숫자입니다. 왼쪽 소매에 왼팔 본의 웨이트가 있으면 본을 움직일 때 소매도 따라옵니다.

**표시되는 결과:** 의상이 아바타 스켈레톤 아래에 있으며 본을 움직이면 몸과 의상이 함께 움직입니다.

---

### 4단계 — 관통 확인 {#step-4--check-for-clipping}

1. 아바타에 포즈를 취하세요.

2. 의상이 몸을 통과하는 위치를 확인하세요.

3. 관통하면 해당 위치의 의상 맞춤이나 웨이트를 조정하세요.

[리그 도구](05-rig-tools.md)의 Weight Tools를 참고하세요. **Detect Collisions**는 물리적 관통을 검사하지 않습니다.

**가능해진 작업:** 몸과 자연스럽게 움직이는 의상입니다. 의상 부품마다 반복하세요.

다음: [가이드 8–13](03-guides-b.md)
