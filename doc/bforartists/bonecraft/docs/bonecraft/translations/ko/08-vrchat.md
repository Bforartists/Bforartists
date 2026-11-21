# VRChat 도구 {#vrchat-tools}

[← 목차](index.md)

## VRChat 도구 {#vrchat-tools-1}

VRChat 도구는 오른쪽 사이드바의 **CATS** 탭 **Avatar Tools** 섹션에 있습니다. **N**으로 사이드바를 표시하세요. Avatar Tools는 휴머노이드 본, 머리카락 물리 및 Viseme Library / Lip Sync를 다룹니다. VRChat 내보내기는 CATS → Import / Export → Unity / VRChat에 있습니다. 그 아래 별도 **VRChat Tools** 섹션에는 Check Performance, Attach Clothing, Facial 및 VRChat Naming Extras가 있습니다. Preferences → Tabs → Scene Properties → Show가 켜져 있으면 프로퍼티스 에디터의 **Scene** 탭에도 이 섹션이 나타납니다. 이 스위치는 CATS 뷰포트 탭을 숨기지 않습니다.

---

### 휴머노이드 본 설정 {#set-up-humanoid-bones}

스켈레톤의 본을 VRChat 휴머노이드 슬롯에 매핑하고 매핑을 검사합니다.

[가이드 5: 아바타를 VRChat의 몸 시스템에 매핑하기](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)를 참고하세요.

영문 원본 이미지 설명(이미지 생략): Auto-Map All을 실행하기 전의 필수 휴머노이드 슬롯. 매핑 후 각 슬롯을 검토하고 남은 빈칸을 채우세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Auto-Map All을 실행하기 전의 필수 휴머노이드 슬롯. 매핑 후 각 슬롯을 검토하고 남은 빈칸을 채우세요.*

---

### 머리카락 물리 추가 {#add-hair-physics}

머리카락, 귀, 꼬리 및 액세서리에 콜라이더와 PhysBone 체인을 설정합니다.

[가이드 6: 머리카락 물리 추가](02-guides-a.md#guide-6-add-hair-physics)를 참고하세요.

영문 원본 이미지 설명(이미지 생략): Hair Physics 체인, 생성 작업, 프리셋 및 콜라이더 컨트롤. 물리를 적용하기 전에 감지한 체인을 검토하세요.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. Hair Physics 체인, 생성 작업, 프리셋 및 콜라이더 컨트롤. 물리를 적용하기 전에 감지한 체인을 검토하세요.*

---

### 의상 부착 {#attach-clothing}

**위치:** CATS 탭 → VRChat Tools → Clothing

의상을 아바타 스켈레톤에 병합하고 웨이트를 전달합니다.

[가이드 7: 몸과 함께 움직이는 의상 부착](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body)을 참고하세요.

영문 원본 이미지 설명(이미지 생략): Clothing 컨트롤과 Pre-Merge 선택 순서. 의상을 합치기 전에 본을 맞추고 본 이름 충돌을 확인하세요.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. Clothing 컨트롤과 Pre-Merge 선택 순서. 의상을 합치기 전에 본을 맞추고 본 이름 충돌을 확인하세요.*

---

### VRChat 이름 추가 도구 {#vrchat-naming-extras}

**위치:** CATS 탭 → VRChat Tools → Naming

**기능:** 스켈레톤의 이름 방식을 감지하고 본 이름을 일괄 변경합니다.

[가이드 4: 아바타의 본 이름 수정](02-guides-a.md#guide-4-fix-your-avatars-bone-names)을 참고하세요.

**일괄 도구:** **Find and Replace**, **Add Prefix**, **Remove Prefix**, **Add Suffix**, **Remove Suffix**, **Regex Replace**

영문 원본 이미지 설명(이미지 생략): 이 예제에서 Naming은 Unity Humanoid를 16/24 신뢰도로 감지합니다. 일괄 작업 전에 이름을 검토하세요.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 이 예제에서 Naming은 Unity Humanoid를 16/24 신뢰도로 감지합니다. 일괄 작업 전에 이름을 검토하세요.*

---

### VRChat 비짐 매핑 {#vrchat-viseme-mapping}

**위치:** CATS → VRChat Tools → Facial. Face Tracking도 같은 섹션에 있습니다.

**기능:** 메시의 셰이프 키를 VRChat 립싱크 비짐 15개에 매핑합니다.

[가이드 8: 립싱크 설정](03-guides-b.md#guide-8-set-up-lip-sync)을 참고하세요. 아직 없는 비짐을 만들려면 [CATS 도구: 비짐](09-cats.md#visemes)을 참고하세요.

**VRChat 비짐 슬롯 15개:** `sil`, `PP`, `FF`, `TH`, `DD`, `kk`, `CH`, `SS`, `nn`, `RR`, `aa`, `E`, `I`, `O`, `U`

영문 원본 이미지 설명(이미지 생략): 매핑 전의 비짐 슬롯과 Face Tracking. 비짐이 매핑되지 않았고 표정 55개 중 0개가 매핑된 예제입니다.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 매핑 전의 비짐 슬롯과 Face Tracking. 비짐이 매핑되지 않았고 표정 55개 중 0개가 매핑된 예제입니다.*

---

### 성능 검사 {#check-performance}

**위치:** CATS 탭 → VRChat Tools → Performance

**기능:** 아바타의 VRChat 성능 등급을 측정하고 수정 방안을 제공합니다.

[가이드 9: 아바타 성능 개선](03-guides-b.md#guide-9-improve-your-avatars-performance)을 참고하세요.

**성능 등급(좋은 순서):** Excellent → Good → Medium → Poor → Very Poor

**도구:**

- **Calculate Performance Rank** — 현재 등급과 폴리곤, 스킨 메시, 머티리얼 슬롯, 본, PhysBone 및 접촉 항목별 수치
- 최적화기는 **Remove Zero-Weight Bones**, **Merge Same-Material Meshes**, **Remove Unused Shape Keys**, **Remove Unused Vertex Groups**를 제공합니다. **What-If Mode**는 수정 시 바뀔 내용을 보여 줍니다
- VRChat Decimation — 셰이프 키를 보호하면서 비율에 따라 폴리곤 수를 줄입니다

VRChat Decimation 사용:

1. 아바타 메시를 선택하세요.
2. **Preview**를 선택하세요.
3. **Apply**를 선택하세요.

영문 원본 이미지 설명(이미지 생략): 성능 지표와 What-If 컨트롤. 메시 정리 작업에는 아바타 메시를 선택하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. 성능 지표와 What-If 컨트롤. 메시 정리 작업에는 아바타 메시를 선택하세요.*

영문 원본 이미지 설명(이미지 생략): Preview나 Apply 전의 Decimation 설정. Ratio 0.50과 Shape Key Safety를 사용하며 아래 정리 작업의 What-If Mode가 켜져 있습니다.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. Preview나 Apply 전의 Decimation 설정. Ratio 0.50과 Shape Key Safety를 사용하며 아래 정리 작업의 What-If Mode가 켜져 있습니다.*

---

### VRChat으로 내보내기 {#export-to-vrchat}

**기능:** 완성한 아바타를 Unity의 VRChat SDK용 FBX로 내보냅니다. **Remove Shape Keys**가 켜져 있지 않으면 셰이프 키(블렌드 셰이프)를 보존합니다.

**설정:**

- **Folder** — 내보낼 폴더
- **Avatar** — 내보낸 파일 이름
- **Sidecar** — BoneCraft Unity 가져오기 도구용 `.bfvrc` 설정 파일도 저장
- **Merge Meshes** — 내보내기 사본의 메시를 하나로 결합
- **Separate Clothing** — 의상을 별도 메시로 유지
- **Remove Shape Keys** — 내보내기 사본의 베이시스에 셰이프 키 적용
- **Embed Textures** — Unity가 찾을 수 있도록 텍스처를 FBX에 포함
- **Helper Meshes** — 숨긴 메시나 도우미 메시 포함. 일반 아바타에서는 꺼 두세요
- **Bone Names** — **Keep Original Names**, **Unity-Preset**, **Unreal-Preset**을 내보내기 사본에 적용

**위치:** CATS → Import / Export → Game Engine Export → Unity / VRChat.

내보내기 전:

1. 필수 슬롯이 비어 있다면 여기서 **Auto-Map Humanoid**를 실행하세요.
2. 슬롯을 검토하세요.

내보내기 전 성능 검사는 **Check Performance Rank**를 선택하세요. **Bone Names** 프리셋을 쓰기 전에 매핑이나 이름 충돌을 수정하세요. 아래 **내보내기 본 이름**에서 충돌을 설명합니다. 내보내기 전에 링크된 오브젝트를 로컬로 만드세요. FBX를 저장하려면 <strong>Export to VRChat (Unity)</strong>를 선택하세요.

**Normalize Names**는 작업 리그의 이름을 바꾸고 **Bone Names** 프리셋은 내보내기 사본의 이름을 바꿉니다.

Unity/VRChat 내보내기는 애니메이션 없이 레스트 포즈를 저장합니다. 주요 Unity 및 Unreal 버튼은 오브젝트, 포즈, 편집 모드를 지원합니다. 잠시 오브젝트 모드를 사용한 뒤 이전 모드와 선택을 복원합니다.

영문 원본 이미지 설명(이미지 생략): 폴더와 휴머노이드 매핑을 설정하기 전의 Unity / VRChat 설정. 필수 슬롯 15개 중 0개가 매핑되어 있습니다.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 폴더와 휴머노이드 매핑을 설정하기 전의 Unity / VRChat 설정. 필수 슬롯 15개 중 0개가 매핑되어 있습니다.*

---

### 정리 {#cleanup}

내보내기 전 메시 정리는 CATS의 **Fix Model**, **Join Meshes**, **Apply All Transforms**를 사용합니다. [CATS 도구](09-cats.md)를 참고하세요.

---

## VRM 브리지 {#vrm-bridge}

VRM 도구는 **CATS** 탭 → **Import / Export** → **VRM / VRoid**에 있으며 VRM 애드온이 필요합니다. 비활성 브리지에는 **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website**, **Show Manual Instructions**가 있습니다.

오프라인 패키지는 기본 Preferences에서 설치하세요. 기존 애드온 ZIP에는 **Add-ons → Install from Disk…**, 최신 확장 패키지에는 기본 Extensions 설치 메뉴를 사용합니다.

1. 알맞은 기본 메뉴에서 패키지를 설치하세요.
2. 의존 패키지를 켜세요.
3. 브리지가 **Active**를 표시하는지 확인하세요.

비활성 허브 카드에는 ZIP 설치 버튼이 없습니다.

영문 원본 이미지 설명(이미지 생략): 두 형식 브리지 모두 꺼진 예제. 필요한 브리지를 설치하면 해당 가져오기와 내보내기 컨트롤이 나타납니다.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 두 형식 브리지 모두 꺼진 예제. 필요한 브리지를 설치하면 해당 가져오기와 내보내기 컨트롤이 나타납니다.*

---

### VRM과 VRoid 가져오기 {#vrm-and-vroid-import}

**기능:** VRoid Studio, Virtual Cast 등의 `.vrm` 아바타를 머티리얼, 스켈레톤 및 셰이프 키와 함께 가져옵니다.

- **Import VRM…** — `.vrm` 파일
- **Import VRoid (.vroid / .zip)…** — VRoid Hub 다운로드(`.zip`). VRoid Studio 프로젝트(`.vroid`)에는 먼저 VRM으로 내보내는 방법을 설명하는 카드가 나타납니다.

---

### VRM 내보내기 {#vrm-export}

**기능:** 리깅된 캐릭터를 VRM이나 대상 앱 형식으로 내보냅니다.

**설정:**

- **Folder**, **File** — 저장 위치와 파일 이름. 확장자는 대상에 따릅니다
- **Target** — VRM 1.0, VRM 0.x, VRChat FBX, VSeeFace, Warudo, Resonite
- **Scope** — 활성 아마츄어 또는 VRM 데이터가 있는 모든 아마츄어
- Skip lint — 대상 검사 없이 내보냅니다. 보고된 위험을 이해할 때만 사용하세요

<strong>Export…</strong>를 클릭하세요.

---

### VRM 린트 {#vrm-lint}

**기능:** 내보내기 전에 선택한 대상에 맞게 아마츄어를 검사합니다. 휴머노이드 매핑, VRM 메타데이터, 대상 비짐 및 대상 앱 요구 사항을 확인합니다.

**Lint Now**는 변경 없이 검사합니다. lint를 건너뛰지 않으면 오류가 내보내기를 차단합니다. 경고는 대상 앱에서 성능이 낮아질 수 있는 콘텐츠를 알립니다.

실제로 있는 휴머노이드 본이 누락되었다고 보고하면 **Fix Humanoid Map**을 클릭하세요. 슬롯을 다시 감지하고 매핑을 저장하며 본 이름은 바꾸지 않습니다.

**함께 있는 도구:** **Convert SpringBones → PhysBones**(VRoid 머리카락 물리를 VRChat용으로 변환), **Map VRoid Visemes**.

---

## MMD 브리지 {#mmd-bridge}

MMD 도구는 **CATS → Import / Export → MMD / PMX**에 있습니다. **mmd_tools**를 설치하고 켜야 합니다. BoneCraft는 기존 패키지와 최신 Blender Extensions를 인식합니다.

비활성 브리지에는 **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website**, **Show Manual Instructions**가 있습니다. 독립형 브리지 콘텐츠가 표시되면 <strong>Install from .zip on Disk...</strong>도 있습니다. 설치와 로컬 확장 저장소 검사는 [가이드 3](02-guides-a.md#step-1--install-mmd_tools)을 참고하세요.

---

### MMD 가져오기 {#mmd-import}

- **Import PMX / PMD...** — MMD 모델
- **Import VMD Motion...** — MMD 애니메이션
- **Import VPD Pose...** — MMD 포즈

가져오기가 성공적으로 끝났는지 확인하세요. PMX 가져오기를 취소하거나 설치 오류가 나면 작업은 미완료입니다. 가져온 모델은 변환 전에 머티리얼과 본 매핑 검사가 필요할 수 있습니다.

---

### MMD 내보내기 {#mmd-export}

**설정:** **Folder**는 저장 위치입니다. 각 형식에 파일 이름과 범위 설정이 있습니다.

- **PMX File**, **PMX Scope**.
- **VMD File**, **VMD Scope**.
- **VPD File**, **VPD Scope**.

각 범위는 활성 모델 또는 장면의 모든 MMD 모델을 선택합니다.

**버튼:** **Export PMX...**, **Export VMD Motion...**, **Export VPD Pose...**

**함께 있는 도구:** **Convert Bone Names -> Unity**, **Convert Physics -> PhysBones**.

---

## 게임 엔진 내보내기 {#game-engine-export}

**Game Engine Export**는 **CATS → Import / Export** 안의 인라인 영역이며 **Unity / VRChat**과 **Unreal Engine 5**를 포함합니다. 별도 하위 패널 **Game Export**는 검증된 프로필 내보내기를 제공합니다.

### Unreal Engine 5 {#unreal-engine-5}

**Bake Anim**을 켜면 활성 액션을 베이크합니다. 별도 NLA 스트립은 필요하지 않으며 무관한 모든 액션을 내보내지 않습니다.

**Bone Names** 프리셋을 쓰기 전에 매핑이나 이름 충돌을 수정하세요. 아래 **내보내기 본 이름**에서 설명합니다. 내보내기 전에 링크된 오브젝트를 로컬로 만드세요.

1. 아마츄어와 메시를 선택하세요.
2. **CATS → Import / Export → Game Engine Export → Unreal Engine 5**를 여세요.
3. **Folder**를 설정하세요.
4. **File**을 FBX 이름으로 설정하세요.
5. **Bone Names**와 미리보기를 검토하세요.
6. 활성 애니메이션이 필요하면 **Bake Anim**을 켜세요.
7. <strong>Export to Unreal (FBX)</strong>를 클릭하세요.

**Selected Only**는 처음에 켜져 있으므로 메시와 함께 아마츄어도 포함하세요. **Unit Scale**은 켜짐, **Leaf Bones**는 꺼짐, **Embed Textures**는 켜짐으로 시작합니다. 패널은 **Bake Animation**을 **Bake Anim**으로 줄여 씁니다.

<strong>Import from Unreal (FBX)</strong>는 가져오기 파일 브라우저를 엽니다.

영문 원본 이미지 설명(이미지 생략): 출력 폴더 선택 전의 Unreal Engine 5 설정. 내보내기 전에 Bone Names, Selected Only 및 Bake Anim을 검토하세요.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 출력 폴더 선택 전의 Unreal Engine 5 설정. 내보내기 전에 Bone Names, Selected Only 및 Bake Anim을 검토하세요.*

### 내보내기 본 이름 {#export-bone-naming}

두 엔진 섹션 모두 같은 **Bone Names** 선택지를 제공합니다.

| 선택 | 내보내기 결과 |
| --- | --- |
| Keep Original Names | 기존 본 이름을 유지합니다. 기본값입니다. |
| Unity-Preset | `Hips`, `LeftUpperArm`, `LeftIndexProximal` 등 인식된 Unity Humanoid 이름을 사용합니다. |
| Unreal-Preset | `pelvis`, `spine_01`, `upperarm_l`, `index_01_l`, `ball_l` 등 인식된 Unreal 휴머노이드 이름을 사용합니다. |

아마츄어를 선택하면 미리보기에 **Recognized / renamed** 수와 제안 변경을 최대 세 개 표시합니다. 인식되지 않은 본은 이름을 유지합니다.

저장한 휴머노이드 매핑이 이름 감지보다 우선합니다. 인식된 선택적 chest, neck, shoulder, eye, jaw, 손가락 및 발가락 본도 참여합니다. 별도로 인식된 `Root`는 **Unreal-Preset**에서 `root`가 됩니다.

대상 이름 충돌, 모호한 본 및 재사용된 휴머노이드 슬롯은 이름 변경을 차단합니다. 내보내기 전에 수정하세요. 충돌 해결을 위해 `.001` 접미사를 붙이지 않습니다.

내보내기 전에 링크된 오브젝트를 로컬로 만드세요. 프리셋은 임시 내보내기 사본의 이름을 바꾸므로 작업 리그의 본 이름은 유지됩니다. 내보내는 버텍스 그룹, 애니메이션 채널 및 Unity 사이드카 본 참조는 선택한 이름을 따릅니다. 성공하거나 실패하면 임시 데이터를 정리합니다.

이 프리셋은 이름만 변경하며 계층, 본 방향 및 레스트 포즈를 유지합니다. 누락된 관절을 추가하거나 완전한 Manny/Quinn 스켈레톤을 만들지 않습니다. Unity Avatar 매핑이나 Unreal 리타기팅이 여전히 필요할 수 있습니다.

### 검증된 프로필 내보내기 {#validated-profile-export}

**기능:** Unreal humanoid 또는 universal, Unity humanoid, Godot humanoid, generic FBX 또는 GLB의 검증된 프로필로 내보냅니다. 결과 목록은 가능한 수정을 표시하며 수정에는 명시적 사용자 실행이 필요합니다.

이 프로필 작업 흐름에는 오브젝트 모드를 사용하세요. Object/Pose/Edit 모드 복원 보장은 두 주요 엔진 내보내기 버튼에 적용됩니다.

**Bone Names** 프리셋을 쓰기 전에 매핑과 이름 충돌을 수정하세요. 위의 **내보내기 본 이름**에서 설명합니다. 내보내기 전에 링크된 오브젝트를 로컬로 만드세요.

**파일 브라우저 설정:** **Profile**, **Animation**, **Bone Names**, **Root Motion**, **Interpolation**, **T-Pose**. **Bone Names**는 처음에 Unreal 섹션 선택을 따르지만 내보내기 형식 프로필은 별도 선택입니다.

이름 프리셋에는 **Active Action**이나 **No Animation**을 선택하세요. 다른 리그의 액션을 포함할 수 있는 **All Actions**에는 **Keep Original Names**가 필요합니다.

기본 **T-Pose**는 프로필에 따릅니다. Unity humanoid와 VRChat 프로필은 T-포즈를 사용합니다. T-포즈 내보내기는 애니메이션 없이 레스트 포즈를 포함합니다. 모델링한 레스트 포즈가 필요하면 **Export as modelled**를 선택하세요.

1. 아마츄어와 메시를 선택하세요.
2. **CATS → Import / Export → Game Export**를 여세요.
3. **Check for Export**를 클릭하세요.
4. 결과와 명시적으로 실행할 수정을 검토하세요.
5. <strong>Export (Profile)</strong>을 클릭하세요.
6. 파일 브라우저에서 설정을 선택하세요.
7. 출력 파일을 선택하세요.
8. 내보내기를 확인하세요.

영문 원본 이미지 설명(이미지 생략): 확인 전의 프로필 내보내기 옵션. Generic FBX, Active Action 및 Keep Original Names를 사용한 예제입니다.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 확인 전의 프로필 내보내기 옵션. Generic FBX, Active Action 및 Keep Original Names를 사용한 예제입니다.*

**버튼:**

- **Check for Export** — 리그를 프로필과 비교해 검사하고 결과를 나열
- **Apply Transforms (Fix)** — 검사에서 제공할 수 있는 명시적 수정 중 하나
- **Export (Profile)** — 프로필로 내보내기

**위치:** **CATS** 탭 → **Import / Export** → **Game Export**

이름 세부 사항과 과거 호스트 검증은 [독립형 내보내기 이름 안내](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/export-bone-naming.md)를 참고하세요.

영문 원본 이미지 설명(이미지 생략): Check for Export, 명시적 수정 및 Export (Profile). 아직 프로필 검사 결과가 없는 예제입니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Check for Export, 명시적 수정 및 Export (Profile). 아직 프로필 검사 결과가 없는 예제입니다.*

---

## 작업 보드 {#task-board}

**기능:** 현재 리그의 건강 점수, 빠른 개선 및 범주별 작업을 요약합니다. 휴머노이드 본 누락, 미해결 이름, 비짐 누락 및 리그 검증 경고 등을 다룹니다. **Quick Wins**는 권장 작업을 최대 세 개 표시하며 **Remaining Tasks**에는 나머지만 있습니다. **Open Health Check**는 검증을 실행하고 결과를 엽니다. **Refresh Task Board**는 다시 검사합니다.

**위치:** **BoneCraft** 탭 → **Overview** → **Task Board**

영문 원본 이미지 설명(이미지 생략): 활성 예제 리그의 건강 검사 결과와 빠른 작업을 나열한 Task Board.

*기본 패널 팝오버, BoneCraft 9.2.18. 활성 예제 리그의 건강 검사 결과와 빠른 작업을 나열한 Task Board.*

---

### 본 검사기 {#bone-inspector}

**기능:** 활성 포즈 본의 레스트 치수, 부모, 컨스트레인트, 사용자 데이터, 드라이버 및 스킨 웨이트를 표시합니다.

정보는 읽기 전용입니다. 포즈 모드에서 본을 활성화하고 패널을 여세요. 본 이름을 복사하려면 헤더의 **Copy Name**을 선택하세요.

**위치:** **BoneCraft** 탭 → **Review** → **Bone Inspector**

영문 원본 이미지 설명(이미지 생략): Bone Inspector가 레스트 본 세부 정보, 컨스트레인트, 사용자 데이터, 드라이버 및 스킨 웨이트를 표시합니다. 헤더에는 Copy Name이 있습니다.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. Bone Inspector가 레스트 본 세부 정보, 컨스트레인트, 사용자 데이터, 드라이버 및 스킨 웨이트를 표시합니다. 헤더에는 Copy Name이 있습니다.*

다음: [CATS 도구](09-cats.md)
