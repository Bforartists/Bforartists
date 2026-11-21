# 가이드 8–13 {#guides-813}

[← 목차](index.md)

## 가이드 8: 립싱크 설정 {#guide-8-set-up-lip-sync}

> **시간:** 약 10–20분
> **결과:** VRChat에서 말할 때 올바르게 움직이는 아바타의 입

**시작 전 확인:**

- [ ] 머리 메시에 입 셰이프 키가 있습니다(블렌드 셰이프 또는 모프 타깃이라고도 하며 발음에 따른 입 위치입니다)
- [ ] 셰이프 키 이름을 대략 알고 있습니다(메시의 Object Data 속성의 Shape Keys 목록 확인)

> 비짐은 소리에 따른 입 모양입니다. `aa`는 “아”, `O`는 “오” 소리 등입니다. VRChat은 립싱크에 비짐 15개를 사용합니다.
>
> 셰이프 키(블렌드 셰이프)는 메시의 다른 위치를 저장한 형태입니다. 입 벌림 셰이프 키는 입을 벌린 메시입니다.

---

### 1단계 — VRChat Viseme Mapping 열기 {#step-1--open-vrchat-viseme-mapping}

[Viseme Mapping과 Face Tracking 컨트롤](08-vrchat.md#vrchat-viseme-mapping)을 참고하세요.

**CATS → VRChat Tools → Facial → VRChat Viseme Mapping**을 여세요.

---

### 2단계 — 비짐 자동 매핑 {#step-2--auto-map-visemes}

**Auto-Map All Visemes**를 클릭하세요. BoneCraft가 메시의 셰이프 키를 읽어 이름으로 VRChat 비짐 슬롯 15개에 맞춥니다.

**표시되는 결과:** 대부분의 슬롯에 매핑된 셰이프 키가 있는 비짐 목록.

---

### 3단계 — 빈 슬롯 채우기 {#step-3--fill-in-missing-slots}

빈 슬롯은 “(unmapped)”를 표시합니다.

1. 슬롯 버튼을 선택해 메시의 셰이프 키 검색 목록을 여세요.

2. 입력하여 목록을 필터링하세요.

3. 가장 가까운 셰이프 키를 선택하세요.

슬롯을 비우려면 “(unmapped)”를 선택하세요. 흔한 대응 관계:

| VRChat 비짐 | 소리 | 찾을 셰이프 키 |
|---|---|---|
| `aa` | “아” | mouth_open, A, aa |
| `O` | “오” | mouth_o, OH, oh |
| `CH` | “ch” / “sh” | mouth_ch, CH |
| `PP` | 입술을 붙임(P, B, M) | mouth_m, MM, lips_together |
| `SS` | “sss” / “zzz” | mouth_s, SS |

**비짐 셰이프 키가 없는 경우:** CATS → **Visemes**는 A, O, CH의 세 기본 모양으로 15개 키를 만듭니다. 입 모양이 없다면 먼저 이 세 가지를 만드세요. [가이드 13, 2단계](#phase-2--viseme-generation)를 참고하세요.

---

### 4단계 — 입 모양 확인 {#step-4--check-a-mouth-shape}

1. **Properties → Object Data → Shape Keys**에서 매핑된 키 값을 1.0으로 설정하세요.

2. 입 모양을 확인하세요.

3. 값을 0으로 되돌리세요.

---

### 5단계 — 얼굴 추적(선택) {#step-5--face-tracking-optional}

비짐 목록 아래의 <strong>Face Tracking (SteamVR)</strong>는 얼굴 추적 하드웨어용 표정 모양을 준비합니다. 선택 사항이며 대부분의 사용자에게 필요하지 않습니다.

**가능해진 작업:** VRChat에서 말할 때 입이 움직입니다. 방금 매핑한 셰이프 키를 바탕으로 표정을 만들 수 있습니다.

---

## 가이드 9: 아바타 성능 개선 {#guide-9-improve-your-avatars-performance}

> **시간:** 약 15–25분
> **결과:** 더 나은 VRChat 성능 등급과 다른 플레이어의 더 빠른 로딩

**시작 전 확인:**

- [ ] 리깅, 의상, 립싱크를 포함해 아바타가 완성되었습니다
- [ ] 목표 등급을 정했습니다(대부분 Good 또는 Excellent)

> 성능 등급은 VRChat이 평가하는 아바타의 자원 요구량입니다. Very Poor 아바타는 다른 플레이어에게 숨겨질 수 있습니다. Good과 Excellent는 빠르게 로딩되고 항상 표시됩니다.

---

### 1단계 — 현재 등급 확인 {#step-1--check-the-current-rank}

1. **CATS → VRChat Tools**를 여세요.

2. Performance에서 **Calculate Performance Rank**를 선택하세요.

BoneCraft는 전체 등급과 각 지표가 다음 등급까지 얼마나 남았는지 보고합니다. 폴리곤, 스킨 메시, 머티리얼 슬롯, 본, PhysBone 및 접촉을 측정합니다.

[Performance 컨트롤](08-vrchat.md#check-performance)을 참고하세요.

---

### 2단계 — 정리 {#step-2--clean-up}

같은 섹션의 VRChat Optimizer가 정리 도구를 나열합니다. **What-If Mode**는 처음에 켜져 있으며 각 수정이 실제 적용 없이 예상 변경을 보고합니다.

1. What-If Mode에서 필요한 수정을 실행하세요.

2. 보고서를 검토하세요.

3. 적용하려면 What-If Mode를 끄세요.

4. 수정을 다시 실행하세요.

사용 가능한 수정:

1. **Remove Zero-Weight Bones** — 메시를 전혀 움직이지 않는 본 삭제
2. **Merge Same-Material Meshes** — 같은 머티리얼을 공유하는 메시 결합
3. **Remove Unused Shape Keys** — 변형이 Basis와 같은 빈 셰이프 키 제거. 다른 도구의 참조는 검사하지 않습니다.
4. **Remove Unused Vertex Groups** — 빈 웨이트 그룹 제거

---

### 3단계 — 폴리곤 수 줄이기(필요한 경우) {#step-3--reduce-the-polygon-count-if-needed}

[Performance와 Decimation 컨트롤](08-vrchat.md#check-performance)을 참고하세요.

폴리곤이 너무 많다면:

1. 메시를 선택하세요.

2. VRChat Decimation에서 목표 비율을 설정하세요.

3. **Preview**를 선택하세요.

4. 결과를 확인하세요.

5. 유지하려면 **Apply**를 선택하세요.

0.5는 폴리곤 수를 절반으로, 0.8은 20% 줄입니다. Decimation은 셰이프 키를 보호합니다.

> 0.8에서 시작하여 외형을 확인하면서 점차 줄이세요. 작은 감소만으로도 눈에 띄는 변화 없이 성능이 개선될 수 있습니다.

---

### 4단계 — 머티리얼 병합(선택) {#step-4--merge-materials-optional}

머티리얼이 많으면 하나의 텍스처 시트(아틀라스)로 합치세요. **CATS** 탭 → **CATS** → **Material Atlas**에서:

1. 파일 사본을 저장하세요.
2. **Target**을 처리할 메시로 설정하세요.
3. **Preserve Backup Duplicate**를 켜 두세요.
4. **Analyze Materials**를 클릭하세요.
5. 아틀라스 그룹을 선택하세요.
6. 켜진 그룹에서 머티리얼을 두 개 이상 선택하세요.
7. 포함할 텍스처 이미지를 선택하세요.
8. 필요하면 각 목록 위의 **Select All** 또는 **Deselect All**을 사용하세요.
9. **Bake Checked Sources**를 클릭하세요.
10. 베이크 확인 전에 사전 검사 요약을 검토하세요.
11. 베이크한 머티리얼, 투명도 및 UV를 확인하세요.
12. 결과를 유지하려면 **Accept — Delete Backup**을 클릭하세요.

수정이 필요하면 대신 **Revert — Restore Originals**를 사용하세요. Accept는 백업을 삭제합니다. **Preserve Backup Duplicate**를 끄면 Revert가 없어집니다.

일괄 선택은 활성 그룹의 해당 소스 목록에만 적용됩니다. 누락된 텍스처는 선택하지 않으며 다른 목록과 그룹은 바뀌지 않습니다.

**Refresh Analysis**는 소스 목록과 선택을 다시 만듭니다. 선택 검토 후 **Bake Checked Sources**를 사용하세요. **Smart Combine Materials**는 초기 자동 단축 경로입니다.

[CATS 도구: 머티리얼 아틀라스 결합기](09-cats.md#material-atlas-combiner)에서 모든 설정을 설명합니다.

---

### 5단계 — 등급 다시 확인 {#step-5--check-the-rank-again}

**Calculate Performance Rank**를 다시 클릭해 개선을 확인하세요.

**가능해진 작업:** 등급이 좋으면 더 많은 플레이어가 아바타를 봅니다. Good 또는 Excellent는 빠르게 로딩되고 GPU 사용량이 적으며 다른 플레이어에게 기본 표시됩니다.

---

## 가이드 10: 포즈 저장과 재사용 {#guide-10-save-and-reuse-poses}

> **시간:** 약 5–10분
> **결과:** 한 번 클릭으로 적용하는 저장된 포즈 라이브러리

**시작 전 확인:**

- [ ] 아바타 스켈레톤이 완성되었습니다
- [ ] **Pose Mode**입니다

포즈 모드로 들어가기:

1. 아마츄어를 선택하세요.

2. Ctrl+Tab을 누르세요.

또는 뷰포트 왼쪽 위 모드 드롭다운의 **Pose Mode**를 선택하세요.

---

### 1단계 — Pose Library 열기 {#step-1--open-the-pose-library}

왼쪽 툴 셸프의 **BoneCraft** 탭에서 **Review** → **Pose Library**를 펼치세요.

[Pose Library 컨트롤](05-rig-tools.md#pose-library)을 참고하세요.

---

### 2단계 — 아바타 포즈 만들기 {#step-2--pose-your-avatar}

저장할 자세로 본을 움직이세요. 팔 회전, 고개 기울임 등 여러 본 위치를 조합할 수 있습니다.

---

### 3단계 — 포즈 저장 {#step-3--save-the-pose}

1. **Save**를 선택하세요.

2. “Peace Sign”이나 “Thinking” 같은 포즈 이름을 입력하세요.

**Category**는 “Greetings” 같은 이름으로 포즈를 묶고 **Filter**는 한 번에 한 범주를 표시합니다. 저장한 포즈에는 뷰포트 썸네일이 포함됩니다.

---

### 4단계 — 저장한 포즈 적용 {#step-4--apply-a-saved-pose}

1. 포즈를 선택하세요.

2. **Apply**를 선택하세요.

- **Blend** — 일부 강도로 적용하여 두 포즈 혼합
- **Mirror** — 좌우를 뒤집어 적용

**Rename**과 **Delete**로 목록을 관리합니다.

---

### 5단계 — 포즈 내보내기와 가져오기 {#step-5--export-and-import-poses}

**Export**는 프로젝트에 보관하거나 공유할 `.bfpose` 파일로 포즈 라이브러리를 저장합니다. **Import**는 `.bfpose`에서 포즈를 불러옵니다.

**가능해진 작업:** 프로젝트 사이에 재사용하고 애니메이션 키용으로 혼합하거나 다른 BoneCraft 사용자와 공유할 개인 포즈 라이브러리입니다.

---

## 가이드 11: 두 리그 합치기 {#guide-11-merge-two-rigs-together}

> **시간:** 복잡도에 따라 약 25–40분
> **결과:** 모든 웨이트를 유지한 하나의 통합 스켈레톤

**시작 전 확인:**

- [ ] 기본 아바타와 두 번째 리그(의상이나 액세서리)가 같은 파일에 있습니다
- [ ] 둘 다 리깅과 웨이트 작업이 되어 있습니다

> 리그 병합은 스켈레톤 하나를 다른 스켈레톤에 흡수하여 하나로 합치는 작업입니다. 몸 리그와 머리카락 또는 의상 리그를 합칠 때 유용합니다.

---

### 1단계 — Bone Merge 열기 {#step-1--open-bone-merge}

**BoneCraft → Setup Rigging → Bone Merge**를 여세요. 완료하는 순서에 따라 세 단계가 열립니다.

[단계별 Bone Merge 컨트롤](06-rig-builder.md#bone-merge)을 참고하세요.

---

### 2단계 — Stage 1: Scope {#step-2--stage-1-scope}

1. 남길 몸 스켈레톤인 **Base** 아마츄어를 선택하세요.

2. 들어올 의상 또는 머리카락 아마츄어를 선택하세요.

3. **Analyze**를 선택하세요.

최종 병합에서 들어오는 아마츄어는 Base에 합쳐진 뒤 숨겨집니다.

Analyze는 두 스켈레톤을 비교해 나열합니다.

- ✓ Matched — 양쪽 모두에 있으며 정렬된 본
- \+ Source only — 병합할 리그에만 있고 Base에는 대응이 없는 본
- − Target only — Base에만 있고 병합할 리그에는 없는 본

목록을 읽은 뒤 **Acknowledge Scope — Proceed to Rename**을 클릭하세요.

---

### 3단계 — Stage 2: Rename {#step-3--stage-2-rename}

각 Source only 본에 맞는 절차를 선택하세요.

Base에 대응 본이 있다면:

1. Base 본 이름을 입력하세요.

2. **Apply Rename**을 선택하세요.

대응 본이 없으면 대신 **Mark as Unique**를 선택하세요. 이름 변경 없이 Base에 추가됩니다.

**Normalize Both Armatures**는 양쪽 리그의 척추, 팔, 다리 등 인식된 표준 본 이름을 정규화합니다. **Auto-Propose Renames**는 위치로 다른 본 이름을 제안합니다. **Apply Batch Pattern**은 하나의 패턴으로 여러 본 이름을 바꿉니다.

모든 Source only 본을 해결하면 **Verify Rename — Proceed to Merge**를 클릭하세요.

---

### 4단계 — Stage 3: Merge {#step-4--stage-3-merge}

먼저 **Run Merge Preview**를 클릭하세요. 변경 없이 병합할 내용을 보고합니다.

보고가 맞으면 **Merge Armatures**를 클릭하세요. BoneCraft는 두 아마츄어를 백업한 뒤 합칩니다.

**표시되는 결과:** 두 스켈레톤의 모든 본과 연결된 모든 메시가 있는 하나의 아마츄어.

**가능해진 작업:** 내보내기와 편집이 쉬운 단일 리그입니다. 별도 의상이나 액세서리 리그가 있는 아바타에 필요합니다.

---

## 가이드 12: 업로드 문제 해결 {#guide-12-fix-upload-problems}

> **시간:** 문제에 따라 약 5–15분

**시작 전:** 아래 목록에서 문제를 찾아 해당 섹션으로 가세요.

---

### “업로드 실패 — 본을 인식하지 못함” {#upload-failed--bones-not-recognized}

VRChat이 이해하지 못하는 본 이름입니다. → [가이드 4: 아바타의 본 이름 수정](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

---

### “VRChat에서 아바타가 T-포즈이거나 나와 함께 움직이지 않음” {#avatar-is-in-t-pose--not-moving-with-me-in-vrchat}

휴머노이드 매핑이 없거나 잘못되었습니다. → [가이드 5: 아바타를 VRChat의 몸 시스템에 매핑하기](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)

---

### “메시 변형이 이상하거나 피부가 잘못 늘어남” {#mesh-is-deforming-weirdly--skin-stretching-wrong}

본 웨이트를 조정해야 합니다. → [리그 도구](05-rig-tools.md)의 Weight Transfer와 Weight Mirror를 보거나 CATS 탭의 **Smart Automatic Weights**를 실행하세요.

---

### “머리카락이 머리를 관통함” {#hair-is-clipping-through-the-head}

콜라이더가 없거나 너무 작습니다. → [가이드 6: 머리카락 물리 추가](02-guides-a.md#guide-6-add-hair-physics)의 5단계.

---

### “성능이 Very Poor라서 다른 플레이어에게 차단됨” {#avatar-is-very-poor-performance-and-being-blocked-by-other-players}

→ [가이드 9: 아바타 성능 개선](#guide-9-improve-your-avatars-performance)

---

### “립싱크가 작동하지 않음” {#lip-sync-not-working}

비짐 매핑이 잘못되었습니다. → [가이드 8: 립싱크 설정](#guide-8-set-up-lip-sync)

---

### “리그 검증기에 오류가 표시됨” {#rig-validator-shows-errors}

1. **BoneCraft → Review → Rig Validator**를 여세요.

2. **Run Validation**을 선택하세요.

3. 결과의 제안을 따르거나 [빠른 해결 색인](10-reference.md#quick-fix-index)을 확인하세요.

각 결과는 문제와 본 이름을 알려 줍니다. **Export Report**는 결과를 파일로 저장합니다.

---

### “VRM 가져오기가 작동하지 않음” {#vrm-import-not-working}

VRM 애드온이 설치되지 않았을 수 있습니다. → [가이드 2](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)의 1단계.

---

### “MMD 가져오기가 작동하지 않음” {#mmd-import-not-working}

**mmd_tools** 설치와 활성화를 확인하세요. 브리지는 최신 Extensions와 기존 패키지를 지원합니다. 다시 시도하기 전에 설치 메시지를 검토하세요. [가이드 3](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)의 1단계를 참고하세요.

---

## 가이드 13: CATS로 아바타를 VRChat용으로 준비하기 {#guide-13-get-your-avatar-vrchat-ready-with-cats}

> **시간:** 전체 파이프라인 약 20–35분
> **결과:** 정리와 최적화, 립싱크, 눈 추적 및 올바른 변환을 갖춰 VRChat 업로드를 준비한 아바타

**시작 전에 먼저 읽으세요:**

CATS 도구에는 권장 파이프라인이 있습니다. Pipeline Status는 Fix Model, Material Atlas, Visemes, Eye Tracking, Pose To Shape 및 Apply Transforms의 완료를 표시합니다. Operation Ledger는 각 CATS 작업을 기록합니다.

앞 단계가 미완료여도 도구는 작동하며 “Run Fix Model first for best results” 같은 경고를 표시합니다.

먼저 Fix Model 정리 옵션을 검토하고 아바타 변경 전에 파일 체크포인트를 저장하세요.

계속하기 전에 [CATS 파이프라인](04-cats-pipeline.md)을 읽으세요.

**시작 전 확인:**

- [ ] 아바타를 가져왔고 3D 뷰포트에 보입니다
- [ ] 오른쪽 사이드바의 CATS 탭이 열려 있습니다(숨겨져 있으면 N)
- [ ] 아바타가 선택되어 있습니다(뷰포트나 아웃라이너에서 클릭)

---

### 1단계 — Fix Model {#phase-1--fix-model}

권장 정리 단계입니다. 가져온 아바타에 맞는 옵션을 검토한 뒤 결과를 확인하고 계속하세요.

**Fix Model의 기능**(옵션에서 각 항목을 끌 수 있음):

- 모디파이어 적용
- 중복 정점과 느슨한 지오메트리(몸에서 떨어져 떠 있는 삼각형) 제거
- 노멀(메시의 어느 쪽이 바깥인지 정하는 방향) 재계산
- 빈 버텍스 그룹과 제로 웨이트 본 제거
- VRChat이 사용할 수 없는 컨스트레인트와 강체 제거

**단계:**

1. **CATS → CATS → Fix Model**을 여세요.

2. 아바타 메시를 선택하세요.

3. **Fix Model**을 선택하세요.

4. 완료될 때까지 기다리세요.

5. Pipeline Status가 Fix Model에 ✓를 표시하는지 확인하세요.

큰 메시는 몇 초 걸릴 수 있습니다.

**표시되는 결과:** 외형이 같거나 조금 정리됩니다. Pipeline Status가 완료 표시하고 Operation Ledger에 실행이 기록됩니다.

**Fix Model 후 모델이 사라지거나 뒤집혀 보이면:**

증상만으로 원인을 알 수는 없습니다.

1. 켜진 정리 옵션, 오브젝트 표시 상태, 지오메트리 및 노멀을 확인하세요.

2. 복원이 필요하면 실행 취소나 저장된 체크포인트로 이전 상태를 복원하세요.

3. 확인한 문제를 수정한 뒤 재시도하세요.

[Fix Model 컨트롤](09-cats.md#fix-model)을 참고하세요.

---

### 2단계 — 비짐 생성 {#phase-2--viseme-generation}

실행 조건: Fix Model ✓

Visemes는 기존 세 기본 입 모양에서 VRChat 비짐 15개를 만듭니다. 비짐이 이미 완비되어 있다면 건너뛸 수 있지만 VRChat Viseme Mapping(가이드 8)에서 확인하세요.

VRChat은 발음에 따라 입을 움직이기 위해 비짐 15개가 필요합니다. 대부분의 아바타에는 기본 입 모양 몇 개만 있으므로 CATS가 이를 혼합해 나머지를 만듭니다.

세 기본 모양:

- **A Shape** — 크게 벌린 입(“아”)
- **O Shape** — 둥근 입(“오”)
- **CH Shape** — 이가 보이게 좁게 벌린 입(“ch” / “sh”)

**입 셰이프 키가 없다면:** 먼저 A, O 및 CH를 셰이프 키로 조각하거나 편집하세요. CATS는 이를 나머지 모양 생성에 사용합니다. 용어집의 Shape Key를 참고하세요.

**단계:**

1. **CATS → CATS → Visemes**를 여세요.

2. 아래에서 자동 또는 수동 소스 선택을 고르세요.

   자동 선택은 **Auto-Detect**로 세 소스 모양을 채웁니다.

   수동 선택은 각 소스 모양에 가장 가까운 키를 선택합니다.

   키 이름 예시는 `mouth_open`, `vrc.v_O`, `mouth_wide`입니다.

3. **Generate Visemes**를 선택하세요.

4. Pipeline Status에 Visemes ✓가 표시되는지 확인하세요.

CATS는 `vrc.v_aa`, `vrc.v_O`, `vrc.v_CH`를 포함한 VRChat 이름의 셰이프 키 15개를 만듭니다.

**표시되는 결과:** 메시의 Shape Keys 목록(Properties → Object Data → Shape Keys)에 새 셰이프 키 15개.

[CATS Visemes 컨트롤](09-cats.md#visemes)을 참고하세요.

---

### 3단계 — 눈 추적 {#phase-3--eye-tracking}

실행 조건: Fix Model ✓

Eye Tracking은 VRChat의 기본 눈 추적에 맞춰 눈 본을 설정하여 다른 플레이어를 바라보도록 움직이게 합니다.

**기능:**

- 왼쪽과 오른쪽 눈 본 찾기
- VRChat 요구 이름(`LeftEye`, `RightEye`) 지정
- 눈을 움직이는 데 필요한 회전 컨스트레인트 추가
- 위, 아래 및 옆으로의 회전을 자연스러운 범위로 제한

Auto-Detect는 흔한 눈 본 이름을 검색하며 메시 지오메트리나 본 위치를 검사하지 않습니다.

본 이름을 바꾸면:

1. 감지를 다시 실행하세요.

2. 양쪽 눈 본 할당을 확인하세요.

눈 움직임이 잘못되면 본 방향, 컨스트레인트 및 내보낸 아바타를 확인하세요.

**단계:**

1. **CATS → CATS → Eye Tracking**을 여세요.

2. **Auto-Detect**로 흔한 좌우 눈 본 이름을 검색하세요.

3. **Left Eye**, **Right Eye** 필드를 확인하세요.

4. 할당이 틀렸다면 올바른 본을 수동 선택하세요.

5. 필요하면 **Up Limit**, **Down Limit**, **Side Limit**를 설정하세요.

6. **Create Eye Tracking**을 선택하세요.

7. Pipeline Status에 Eye Tracking ✓가 표시되는지 확인하세요.

**표시되는 결과:** 양쪽 눈 본의 이름이 바뀌고 Bone Constraints 패널에 회전 컨스트레인트가 있습니다.

> **CATS가 눈 본을 찾지 못한다면:** 스켈레톤에 없을 수 있습니다. 일부 형식, 특히 이전 MMD 모델은 본 대신 셰이프 키로 깜박입니다. 이 단계를 건너뛰세요. VRChat은 눈 본이 없으면 셰이프 키 눈 애니메이션을 대신 사용합니다.

---

### 4단계 — Pose to Shape Key {#phase-4--pose-to-shape-key}

실행 조건: Fix Model ✓

현재 **Pose to Shape Key** 버튼은 선택한 메시의 현재 셰이프 키 혼합을 저장합니다. 아마츄어 본 변형을 베이크하지 않습니다. 본으로 변형한 포즈는 검증된 [기본 Save as Shape Key 작업 흐름](09-cats.md#save-a-bone-deformed-pose)을 사용하세요.

**단계:**

1. 오브젝트 모드(Object Mode)로 바꾸세요.

2. 대상 메시를 선택하세요.

3. 기존 셰이프 키 값을 저장할 혼합으로 설정하세요.

4. 메시를 활성 상태로 유지하세요.

5. **CATS → CATS → Pose & Shape Keys**를 여세요.

6. **Pose to Shape Key**를 선택하세요.

7. 새 셰이프 키 이름을 입력하세요.

8. 작업을 확인하세요.

9. 원래 셰이프 키 값을 0으로 되돌리세요.

10. 새 키만 확인하세요.

11. Pipeline Status에 Pose To Shape ✓가 표시되는지 확인하세요.

도구가 새 키를 이미 1로 설정합니다.

**표시되는 결과:** 저장한 셰이프 키 혼합을 재현하는 새 키입니다. 원래 키를 활성 상태로 두면 그 변형이 다시 더해집니다.

> **Shape Key to Basis:** 활성 비-Basis 셰이프 키를 새 Basis로 만들고 다른 키를 그에 상대적으로 조정합니다. 실행 전에 체크포인트를 저장하고 이후 나머지 키를 검토하세요.

[Pose to Shape Key 컨트롤](09-cats.md#pose-to-shape-key)을 참고하세요.

---

### 5단계 — 변환 적용 {#phase-5--apply-transforms}

실행 조건: 필요한 모든 이전 단계 완료

Apply Transforms는 권장 최종 준비 단계입니다. 메시와 스켈레톤의 위치, 회전, 스케일을 적용하여 채널을 각각 0, 0, 1로 초기화합니다.

실행 전에 체크포인트를 저장하고 전후를 비교하세요. 이전 도구도 계속 사용할 수 있습니다.

내보낸 아바타의 크기가 틀리면 메시와 아마츄어 변환, 내보내기와 가져오기 스케일 설정을 확인하세요. 이전 상태가 필요하면 실행 취소나 저장한 체크포인트를 사용하세요.

**Transforms & FBT 도구:**

- **Apply All Transforms** — 메시와 아마츄어에 위치, 회전, 스케일을 함께 적용
- **Fix FBT** — 전신 추적용 변환 보정(루트 본을 바닥 높이로 이동)
- **Remove FBT** — 해당 보정 제거

Material Atlas와 Pose To Shape는 선택 사항입니다. 기존 비짐을 매핑했다면 Visemes는 미완료로 남습니다.

**단계:**

1. Pipeline Status에서 필요한 단계가 완료 표시되었는지 확인하세요.

2. **CATS → CATS → Transforms & FBT**를 여세요.

3. **Apply All Transforms**를 선택하세요.

4. Pipeline Status에 Apply Transforms ✓가 표시되는지 확인하세요.

5. **CATS → Import / Export → Game Engine Export → Unity / VRChat**으로 내보내세요(가이드 1, 9단계).

**표시되는 결과:** 필요한 단계 뒤에 Apply Transforms 완료 표시. VRChat Creator Companion에서 내보낸 아바타를 검토하세요.

[변환과 FBT 컨트롤](09-cats.md#apply-all-transforms)을 참고하세요.

---

**가능해진 작업:** 선택한 정리, 입 모양, 눈 추적 및 표정을 갖추어 내보내기 검사를 준비한 아바타입니다. 업로드 전에 대상 앱에서 검증하세요.

다음: [CATS 파이프라인](04-cats-pipeline.md)
