# 빠른 해결과 용어집 {#quick-fixes-and-glossary}

[← 목차](index.md)

## 빠른 해결 색인 {#quick-fix-index}

문제에 맞는 안내를 찾으려면 이 색인을 사용하세요.

| 문제 | 참고 위치 |
|---|---|
| 업로드 실패 — 본을 인식하지 못함 | [가이드 4](02-guides-a.md#guide-4-fix-your-avatars-bone-names) + [VRChat Naming Extras](08-vrchat.md#vrchat-naming-extras) |
| 아바타가 T-포즈이거나 움직임을 추적하지 않음 | [가이드 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system) + [Set Up Humanoid Bones](08-vrchat.md#set-up-humanoid-bones) |
| 메시 변형이 이상하거나 피부가 늘어남 | [Weight Transfer](05-rig-tools.md#weight-transfer) + [Weight Mirror](05-rig-tools.md#weight-mirror), 또는 [Automatic Bone Weight Recalculation](05-rig-tools.md#automatic-bone-weight-recalculation)으로 재계산 |
| 몸 양쪽의 웨이트가 다름 | [Weight Mirror](05-rig-tools.md#weight-mirror) |
| 머리카락이 머리를 관통함 | [가이드 6, 5단계](02-guides-a.md#step-5--add-colliders-recommended) — 콜라이더 추가 |
| 머리카락 물리가 움직이지 않음 | [가이드 6](02-guides-a.md#guide-6-add-hair-physics) — 체인 감지와 PhysBone 프리셋 확인 |
| 의상이 몸을 관통함 | [가이드 7](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body): <ol><li>포즈를 취한 메시를 확인하세요.</li><li>관통하면 맞춤이나 웨이트를 조정하세요.</li></ol> **Detect Collisions**는 본 이름만 검사합니다. |
| 립싱크가 작동하지 않음 | [가이드 8](03-guides-b.md#guide-8-set-up-lip-sync) + [VRChat Viseme Mapping](08-vrchat.md#vrchat-viseme-mapping) |
| 아바타 성능이 Very Poor임 | [가이드 9](03-guides-b.md#guide-9-improve-your-avatars-performance) + [Check Performance](08-vrchat.md#check-performance) |
| VRM 가져오기 실패 | [가이드 2, 1단계](02-guides-a.md#step-1--install-the-vrm-add-on) — VRM 애드온 설치 |
| MMD 가져오기 실패 | [가이드 3, 1단계](02-guides-a.md#step-1--install-mmd_tools) — mmd_tools 설치 |
| MMD가 설치되어 있으나 브리지가 비활성 | **Open Add-on Preferences**에서 mmd_tools를 켜세요. [가이드 3](02-guides-a.md#step-1--install-mmd_tools)의 설치 메시지를 검토하세요. |
| 새로 고친 후 아틀라스 선택이 바뀜 | **Refresh Analysis**는 선택 목록을 다시 만듭니다. <ol><li>소스를 검토하세요.</li><li>Bake Checked Sources를 선택하세요.</li></ol> [Material Atlas Combiner](09-cats.md#material-atlas-combiner)를 참고하세요. |
| Select All이 텍스처 하나를 선택하지 않음 | 누락된 텍스처는 제외됩니다. 일괄 선택은 활성 그룹의 해당 목록만 변경합니다 — [소스 선택](09-cats.md#analyze-and-choose-sources) |
| 아틀라스가 소스 변경을 알림 | <ol><li>분석을 새로 고치세요.</li><li>소스를 다시 검토하세요.</li></ol> 사전 검사는 백업 생성 전에 오래된 분석 소스를 거부합니다. |
| 아틀라스에 Revert가 없음 | **Preserve Backup Duplicate**가 꺼져 있었거나 Accept가 백업을 삭제했습니다. 저장한 파일 체크포인트를 사용하세요. |
| Metallic 또는 ORM 아틀라스 베이크가 차단됨 | **Metallic**과 **Pack ORM Channels**를 꺼 두세요. 이 패스는 9.2.18에서도 차단됩니다. |
| 엔진에서 아틀라스 텍스처가 뒤섞임 | UV0을 확인하세요. **Keep Source UV Maps**는 `atlas_uv`를 UV1에 남길 수 있습니다 — [UV 설정](09-cats.md#advanced-options) |
| 포즈 또는 편집 모드에서 내보내기 실패 | 현재의 주요 Unity 또는 Unreal 버튼을 사용하세요. 모드와 선택을 복원합니다. <strong>Export (Profile)</strong>에는 오브젝트 모드를 사용하세요. |
| 내보내기 이름 충돌 | 대상 이름이나 휴머노이드 매핑을 수정하세요 — [내보내기 본 이름](08-vrchat.md#export-bone-naming) |
| 이름 프리셋을 쓰면 All Actions가 차단됨 | **Active Action**, **No Animation** 또는 **Keep Original Names**를 선택하세요 — [검증된 프로필 내보내기](08-vrchat.md#validated-profile-export). |
| 이전 메커니즘 폼에 현재 버전이 필요함 | 9.2.18은 이전 폼을 다시 저장하지 않고 읽고 적용합니다 — [폼](07-mechanisms.md#forms) |
| 리그 검증기가 오류를 표시함 | [Rig Validator](05-rig-tools.md#rig-validator): <ol><li>검증을 실행하세요.</li><li>메시지를 따르세요.</li></ol> |
| 본이 사라졌거나 보이지 않음 | [Bone Collections](05-rig-tools.md#bone-collections) → **Show All Collections** |
| BoneCraft 패널을 찾을 수 없음 | BoneCraft와 Rig Builder는 왼쪽 툴 셸프(**T**), CATS는 오른쪽 사이드바(**N**)에 있습니다. [기능 위치](01-start.md#where-things-are)를 참고하세요. |
| 완전한 Mechanisms 예제가 필요함 | [튜토리얼: Crescent Rose](12-crescent-rose.md) — 준비 8단계와 Mechanisms 30단계의 서면 지침 및 영문 원본 이미지 설명. 완성 파일은 `examples/crescent-rose/`에 있습니다 |
| 탭이 반대쪽에 있음 | Preferences → Add-ons → BoneCraft → Tabs → Left 또는 Right |
| Properties → Scene에 BoneCraft 섹션이 없음 | Preferences → Add-ons → BoneCraft → Tabs → Scene Properties → Show. 파란색은 켜짐입니다. Tools의 도구 패키지도 확인하세요. |
| Properties → Scene에서 BoneCraft를 숨기고 싶음 | Preferences → Tabs에서 Scene Properties → Show를 끄세요. 뷰포트 탭과 아마츄어 데이터 탭은 바뀌지 않습니다. |
| 옵션을 고르기 전에 도구가 실행됨 | 9.1에서는 실행 직후 다른 작업 전에 뷰포트의 Adjust Last Operation 패널에서 옵션을 조정합니다 |
| Place Rig Markers가 마커를 배치하지 않음 | <ol><li>Auto-Rig Wizard를 시작하세요.</li><li>마커 단계로 이동하세요.</li><li>오브젝트 모드로 바꾸세요.</li><li>마법사에서 선택한 메시를 클릭하세요.</li></ol> [리그 빌더](06-rig-builder.md#auto-rig-wizard)를 참고하세요. |
| Build Mechanism이 사용할 부품을 모름 | <ol><li>먼저 Add Parts from Selection을 사용하세요.</li><li>메커니즘 리그나 부품 하나를 선택하세요.</li><li>도구 헤더에서 유형을 선택하세요.</li><li>첫 부품을 클릭하세요.</li></ol> [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each)를 참고하세요. |
| 본이 있는데도 휴머노이드 본 누락으로 내보내기가 차단됨 | 필수 본이 실제로 없다면 먼저 만들어야 합니다. 필수 본이 있다면: <ol><li>Auto-Map All을 실행하세요.</li><li>VRM / VRoid의 lint 아래에서 Fix Humanoid Map을 실행하세요.</li></ol> [가이드 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)를 참고하세요. |
| 내보낸 FBX에 거대한 도우미 모양이나 튜브가 보임 | 컨트롤 또는 커스텀 셰이프 메시가 필요하지 않다면 **Helper Meshes**를 꺼 두세요. |
| Unity나 Unreal에서 머티리얼이 회색으로 들어옴 | <ol><li>Embed Textures를 켜고 내보내세요.</li><li>Unity의 머티리얼 가져오기/추출 옵션이나 Unreal의 FBX 머티리얼 가져오기를 사용하세요.</li></ol> |
| 웨이트가 잘못된 본에 모두 할당됨 | 마법사의 Generate Rig를 다시 실행하거나 [Weight Transfer](05-rig-tools.md#weight-transfer) 또는 CATS 탭의 **Smart Automatic Weights**를 사용하세요 |
| 두 리그를 하나로 합쳐야 함 | [가이드 11: 두 리그 합치기](03-guides-b.md#guide-11-merge-two-rigs-together) |
| 보정 셰이프가 켜지지 않음 | [Corrective Shape Keys](05-rig-tools.md#corrective-shape-keys)에서 본 축과 각도를 확인하세요 |
| 다른 리그에서 애니메이션이 이상함 | [Retarget](05-rig-tools.md#retarget) — 본 매핑 확인 |
| CATS 도구가 “Run Fix Model first”를 경고함 | <ol><li>정리 옵션을 검토하세요.</li><li>아바타에 필요한지 판단하세요.</li></ol> 경고는 도구를 잠그지 않습니다. [CATS 파이프라인](04-cats-pipeline.md)을 참고하세요. |
| 말할 때 입이 찢어지거나 갈라짐 | 소스 입 키, 메시 토폴로지 및 모디파이어를 확인하세요 — [CATS: Visemes](09-cats.md#visemes) |
| VRChat에서 눈이 아래를 본 채 멈춤 | <ol><li>좌우 본 할당, 방향 및 컨스트레인트를 확인하세요.</li><li>내보낸 아바타를 확인하세요.</li></ol> [CATS: Eye Tracking](09-cats.md#eye-tracking)을 참고하세요. |
| 셰이프 키를 켜면 메시가 폭발함 | <ol><li>그 키만 테스트하세요.</li><li>토폴로지, 소스 키 값 및 모디파이어를 확인하세요.</li></ol> BoneCraft는 본 변형이 아니라 키 혼합을 저장합니다. [CATS: Pose & Shape Keys](09-cats.md#pose--shape-keys)를 참고하세요. |
| VRChat에서 아바타 크기가 잘못됨 | 메시 변환, 아마츄어 변환 및 내보내기/가져오기 스케일 설정을 확인하세요. 복원이 필요하면 실행 취소나 저장한 체크포인트를 사용하세요. [Apply All Transforms](09-cats.md#apply-all-transforms)를 참고하세요. |
| 본 이름이 일본어/중국어/한국어임 | [CATS: Translate Bone Names](09-cats.md#translate-bone-names) |
| 립싱크도 입 셰이프 키도 없음 | [CATS: Visemes](09-cats.md#visemes): 먼저 기본 입 모양을 만드세요. CATS는 세 소스 A, O, CH에서 비짐 15개를 생성합니다. |
| 메커니즘에 “changed by hand”가 표시됨 | [Mechanisms](07-mechanisms.md) — **Keep mine** 또는 **Restore** 사용 |

## 용어집 {#glossary}

**Adjust Last Operation:** 마지막 작업의 옵션을 바꾸는 뷰포트 패널입니다. BoneCraft 9.1의 여러 도구는 먼저 실행한 뒤 여기서 옵션을 표시합니다. 다른 작업 전에 조정하세요.

**Armature(아마츄어):** Bforartists에서 스켈레톤을 부르는 말입니다. 포즈와 애니메이션을 만들 수 있는 본의 집합입니다.

**Blend shape(블렌드 셰이프):** Shape key를 참고하세요.

**Bone(본):** 스켈레톤의 한 구간입니다. 부모 → 자식 계층을 이루며 자식 본은 부모를 따릅니다.

**Bone collection(본 컬렉션):** 이름이 있는 본 그룹입니다. 컬렉션 전체를 한 번에 표시하거나 숨길 수 있습니다.

**Bone Names:** 내보내기 이름 선택입니다. Keep Original Names는 이름을 유지하며 Unity-Preset과 Unreal-Preset은 내보내기 사본에서 인식한 본 이름을 바꿉니다.

**Bake Checked Sources:** 분석을 자동으로 다시 하지 않고 검토한 그룹과 소스 선택을 베이크하는 아틀라스 작업입니다.

**CATS:** 정리, 비짐, 눈 추적 및 변환의 안내 파이프라인으로 VRChat 모델을 준비하는 도구입니다. CATS 탭에 있습니다.

**CATS pipeline:** Fix Model → Material Atlas → Visemes → Eye Tracking → Pose to Shape → Apply Transforms의 여섯 단계 순서입니다. 필요한 앞 단계가 완료되지 않으면 경고합니다.

**Corrective shape key(보정 셰이프 키):** 본이 특정 각도에 도달하면 켜져 극단적인 포즈의 메시를 보정하는 셰이프 키입니다.

**Deform bone(변형 본):** 메시를 움직이는 본입니다. 일부 본은 컨트롤 전용이며 메시를 변형하지 않습니다.

**Eye tracking(눈 추적):** 눈 본(`LeftEye`, `RightEye`)과 VRChat이 눈을 움직이는 데 사용하는 회전 컨스트레인트를 설정하는 CATS 도구입니다.

**FBT(Full Body Tracking):** Vive Trackers 같은 추가 하드웨어로 엉덩이와 발을 포함한 전신을 추적하는 VRChat 기능입니다. Fix FBT는 이 기능에 맞게 루트 본을 조정합니다.

**FBX:** 프로그램 사이에 3D 모델, 스켈레톤 및 애니메이션을 전달하는 파일 형식입니다. VRChat의 표준 형식입니다.

**Fix Model:** 중복 정점, 느슨한 지오메트리, 노멀 및 기타 데이터를 위한 선택 가능한 CATS 정리 작업입니다.

1. 옵션을 검토하세요.

2. 아바타에 필요한 작업만 실행하세요.

**FK(Forward Kinematics):** 어깨, 팔꿈치, 손목처럼 체인의 각 본을 차례로 회전하여 포즈를 만듭니다. 몸의 큰 포즈에 자연스럽습니다.

**IK(Inverse Kinematics):** 손이나 발 같은 체인의 끝점을 배치하면 중간 본이 따라오는 포즈 방식입니다. 손발의 정밀한 배치에 적합합니다.

**Humanoid(휴머노이드):** 모든 아바타가 같은 움직임 컨트롤을 쓰도록 본을 표준 몸 슬롯에 매핑하는 VRChat 아바타 시스템입니다.

**Mechanism(메커니즘):** 일반 본과 컨스트레인트로 만든 소품이나 기계 리그입니다. 관절(Hinge, Slide, Telescope)이나 링크(Piston, Gear Link, Follow)가 될 수 있습니다. [Mechanisms](07-mechanisms.md)를 참고하세요.

**Mesh(메시):** 눈에 보이는 아바타 몸을 이루는 3D 표면입니다.

**MMD(MikuMikuDance):** 일본과 애니메이션 커뮤니티에서 인기 있는 무료 3D 애니메이션 소프트웨어입니다. 모델은 `.pmx`, 애니메이션은 `.vmd` 파일을 사용합니다.

**Morph target(모프 타깃):** Shape key를 참고하세요.

**Operation Ledger:** 실행한 모든 CATS 작업의 시간과 결과를 기록하는 목록입니다.

**PhysBone:** 본이 흔들리고 튀며 충돌하게 하는 VRChat 컴포넌트입니다. 머리카락, 꼬리 및 늘어진 액세서리에 사용합니다.

**Pipeline Status:** 여섯 단계와 완료된 단계의 확인 표시가 있는 CATS 목록입니다.

**PMX:** MikuMikuDance의 주요 3D 모델 형식입니다.

**Pose Mode(포즈 모드):** 본의 포즈와 애니메이션을 만드는 모드입니다.

1. 아마츄어를 선택하세요.

2. Ctrl+Tab을 누르세요.

또는 뷰포트 왼쪽 위의 모드 드롭다운에서 Pose Mode를 선택하세요.

**Rig / rigging(리그/리깅):** 3D 모델 안에 스켈레톤을 만들고 메시를 연결하여 포즈와 애니메이션을 만들 수 있게 하는 작업입니다.

**Shape key(셰이프 키):** 변형된 위치의 메시를 저장한 형태입니다. 서로 다른 강도로 블렌딩하여 표정, 립싱크 및 몸 모프를 만듭니다.

**SDK(Software Development Kit):** VRChat에서는 아바타 업로드에 사용하는 VRChat Creator Companion과 Unity 도구를 뜻합니다.

**Spline IK:** 커브를 따르는 본 체인입니다. 꼬리, 촉수, 긴 머리카락 및 척추에 사용합니다.

**T-pose(T-포즈):** 똑바로 서서 팔을 양옆으로 뻗은 기준 포즈입니다.

**Tool Shelf(툴 셸프):** 3D 뷰포트의 왼쪽 패널(**T**)입니다. BoneCraft와 Rig Builder는 기본적으로 이 패널을 사용합니다.

**Vertex(정점):** 3D 공간의 한 점입니다. 메시는 많은 정점이 에지와 면으로 연결되어 이루어집니다.

**Vertex group(버텍스 그룹):** 어느 정점을 본이 움직일지 정하는 이름 있는 정점 집합입니다.

**Viseme(비짐):** 발음에 따른 입 모양입니다. VRChat은 립싱크에 15개 비짐을 사용합니다.

**Weight / weight painting(웨이트/웨이트 페인팅):** 각 본이 각 정점을 얼마나 강하게 움직일지 정하는 0.0~1.0 값입니다. 웨이트 페인팅은 이를 시각적으로 조정하는 방법입니다.

**Wizard(마법사):** Rig Builder의 Auto-Rig Wizard입니다. 메시에 마커를 놓고 그 마커로 리그를 만듭니다.

**Zero-weight bone(제로 웨이트 본):** 아무 정점도 움직이지 않는 본입니다. 외형 변화 없이 성능만 낮춥니다. Fix Model과 성능 최적화기가 이 본을 제거합니다.

다음: [새로운 기능](11-whats-new.md)
