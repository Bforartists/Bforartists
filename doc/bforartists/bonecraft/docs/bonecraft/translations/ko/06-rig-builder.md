# 리그 빌더 {#rig-builder}

[← 목차](index.md)

두 리그 유형을 해설과 함께 살펴보려면 [IK/FK 입문 설명과 연습 파일](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md)을 참고하세요.

## 새 리그 만들기 {#building-a-new-rig}

Rig Builder는 캐릭터용 새 리그를 만듭니다. **Rig Builder** 탭은 왼쪽 Tool Shelf에 있습니다. **T**를 눌러 도구 선반을 표시하세요. Preferences → Tabs → Scene Properties → Show가 켜져 있으면 **Properties** 편집기의 **Scene** 탭에도 Rig Builder가 나타납니다. 도구 선반이 좁으면 짧은 레이블을 사용하는 간결한 배치로 표시됩니다. Auto-Rig Wizard가 맨 위에 있고, 그 아래에 Quick Rig와 Mannequin이 있습니다. 뷰포트의 Add → Armature 메뉴에서도 마법사와 Quick Rig를 사용할 수 있습니다.

---

### 자동 리깅 마법사 {#auto-rig-wizard}

<strong>기능:</strong> 메시 위에 마커를 배치하고 이를 바탕으로 웨이트가 있는 완전한 리그를 만드는 단계별 안내입니다. 캐릭터를 처음부터 리깅할 때 사용하는 기본 방법입니다.

[가이드 1](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat)에서 전체 과정을 단계별로 설명합니다.

<strong>단계:</strong> Select Mesh → Rig Type → Body Markers → Finger Markers → Face Markers → Review → Generate

<strong>주요 컨트롤:</strong>

- **Start Auto-Rig**는 마법사를 엽니다. **Back**과 **Cancel**은 맨 위에 있습니다. 메시, 리그 유형, 마커 단계에서는 **Next**가 맨 아래에 있습니다. Review에서는 Next 대신 **Generate Rig**를 사용합니다. 마지막 단계에서는 **Close Wizard**를 사용합니다.
- 메시 목록에서 사용할 메시를 클릭합니다. 다음 단계에서는 **Body + Face**, **Body Only**, 또는 기존 아마추어에 사용할 **Face Only**를 선택할 수 있습니다.
- Smart Detection의 **Detect Markers**는 메시의 팔다리를 따라가며 모든 신체 마커를 배치하고 신뢰도를 표시합니다. **Accept High**는 신뢰도가 높은 마커를 유지하고, **Reset Low**는 신뢰도가 낮은 마커를 지웁니다.
- 신체에는 **Guess Markers from Mesh**와 **Guess Precision**, 손가락에는 **Guess Finger Markers**, 얼굴에는 **Guess Face Markers**가 있습니다. 손가락 마커는 손의 형태를 바탕으로 배치됩니다.
- Finger Detail은 만들 손가락 수를 정합니다. 범위는 “0 — No Fingers”부터 “5 — Full Human Hand”까지입니다.
- 각 마커 행에는 **Place Marker** 화살표 아이콘, **Confirm Marker** 확인 표시, **Reset Marker** 원형 화살표가 있습니다. 좌우 마커에는 첫 번째 아이콘으로 **Toggle Symmetry**도 있습니다.
- **Mirror L to R**과 **Mirror R to L**은 확인된 마커를 중심선 반대편으로 복사합니다.
- **Confirm All Placed**는 현재 단계에서 배치된 모든 마커를 확인합니다.
- **Generate Rig**는 확인된 마커로 리그를 만듭니다. 마지막 단계에서는 아래에 설명한 **Build Control Rig**와 **Close Wizard**를 사용할 수 있습니다.

<strong>Generate Rig가 만드는 항목:</strong>

- 선택한 수의 척추 및 목 분절과, IK/FK·IK 전용·FK 전용 중 선택한 방식의 팔과 다리를 갖춘 신체 리그입니다. 방식은 **Kinematics** 옵션으로 정합니다.
- 선택한 손가락 수에 맞는 손가락 본입니다.
- **Body + Face**를 선택하면 얼굴 리그가 생성됩니다. **Generate Control Shapes**가 켜져 있으면 컨트롤 셰이프도 생성됩니다.
- 선택한 품질의 스킨 웨이트입니다. 조밀한 메시는 더 가벼운 프록시 메시를 거쳐 웨이트를 계산하므로, 정점이 678,000개인 캐릭터도 오류 안내 없이 실패하는 대신 약 한 분 안에 처리됩니다.

<strong>Build Control Rig:</strong> 검토 단계에는 **Twist Bones**, **Skirt Bones**, **Face Controls**, **Joint Correctives**도 표시됩니다. Generate Rig는 이 옵션들을 적용하지 않습니다. 이들은 엔진용 컨트롤 리그의 옵션입니다. 이 리그에는 트위스트 본, 다리를 따라가는 스커트 본, 눈 조준 및 깜박임 컨트롤, 관절 보정 셰이프 키가 포함됩니다. Generate Rig 실행 후 마지막 단계에서 **Build Control Rig**를 사용할 수 있습니다. 이 명령은 생성된 아마추어 위에 선택한 옵션의 컨트롤 리그를 만듭니다. **Close Wizard**를 누르기 전에 **Build Control Rig**를 클릭하세요. 마법사를 닫으면 옵션이 초기화됩니다. Rig Tools의 Control Layer 패널은 이 방법으로 만든 리그에서만 나타납니다.

<strong>위치:</strong> Rig Builder → Auto-Rig Wizard

<strong>뷰포트 도구로 여러 마커 배치하기:</strong>

1. 마법사를 시작합니다.
2. 신체, 손가락 또는 얼굴 마커 단계로 이동합니다.
3. 오브젝트 모드에서 뷰포트 도구 모음의 Place Rig Markers를 활성화합니다.

도구 헤더에는 다음 미확인 마커의 이름과 축 잠금, 미러 스위치가 표시됩니다.

4. 마법사에서 선택한 메시를 클릭해 해당 마커를 배치하고 확인합니다.
5. 도구가 현재 단계의 배치를 마쳤다고 표시하면 마법사에서 **Next**를 누릅니다.

대칭은 마법사의 설정을 따릅니다. 마커별 Place 버튼도 계속 사용할 수 있습니다. 메시가 아닌 곳을 클릭하면 마커가 배치되지 않습니다.

---

### 빠른 리그 {#quick-rig}

<strong>기능:</strong> 한 번의 클릭으로 BoneCraft의 Basic Humanoid 또는 Rigify 메타리그 하나를 추가합니다. Basic Humanoid는 본이 19개이며 Rigify가 필요하지 않습니다. Quick Rig는 마법사보다 빠르지만 메시 형태에 맞춘 조정은 적습니다.

<strong>주요 컨트롤:</strong>

- Basic Humanoid 버튼과 Rigify 메타리그가 있습니다. Rigify가 꺼져 있을 때 Rigify 프리셋을 사용하려면 먼저 **Enable Rigify**를 선택합니다.
- 리그 버튼은 리그를 즉시 추가합니다. Adjust Last Operation에서 맞춤 배치, 자동 웨이트, **Add IK/FK Controllers**, **Initial Pose**를 설정할 수 있습니다.
- **T-Pose**와 **A-Pose**는 선택한 리그의 레스트 포즈를 전환합니다.
- Troubleshooting을 펼치면 <strong>Diagnose Quick Rig (print to console)</strong>이 나타납니다. 활성 아마추어가 메타리그가 아니면 **Inspect Active Rig Controls**도 표시됩니다.
- Rigify 메타리그가 활성 상태이면 Troubleshooting에 Inspect Active Rig Controls 대신 <strong>Generate Control Rig (active metarig)</strong>가 나타납니다. 이 명령은 Rigify 컨트롤 리그를 생성합니다.

<strong>BoneCraft Rigs 시작 카탈로그:</strong> 기본 제공되는 아홉 시작 리그는 모두 네이티브 하단 에셋 선반의 **Starter Rigs** 카탈로그를 공유합니다.

1. 선반 왼쪽의 카탈로그 메뉴를 엽니다.
2. 라이브러리에서 **All**을 선택합니다.
3. **Starter Rigs**를 한 번 활성화해 기존 카탈로그 탭 옆에 탭을 추가합니다.
4. 해당 탭을 선택해 시작 리그를 살펴봅니다.

**Add → Armature → Starter Rig Catalog**는 의존성을 확인하면서 시작 리그를 맞추고 추가하는 팝업을 엽니다.

Basic Humanoid는 Rigify가 필요하지 않습니다. 다른 썸네일에는 **Rigify** 레이블이 있습니다. Rigify가 비활성 상태일 때 카탈로그 팝업에서 해당 리그를 선택하거나 드롭하면 **Enable Rigify & Add Rig**와 Cancel이 나타납니다. 수락하면 설치된 Rigify를 활성화한 뒤 선택한 시작 리그의 추가를 계속합니다. 취소하면 아무것도 추가하지 않습니다. **Quick Rig**에도 **Enable Rigify**가 있습니다. Rigify를 사용할 수 없을 때는 카탈로그 팝업의 컨텍스트 메뉴에서도 이 명령을 제공합니다. 의존성이나 프리셋이 없으면 이유를 설명합니다. 설치된 버전에 해당 프리셋이 없을 때 팝업이 다른 리그를 대신 추가하지는 않습니다.

네이티브 하단 에셋 선반은 아마추어 에셋을 가져옵니다. 아래의 의존성 확인 흐름을 사용하려면 **Add → Armature → Starter Rig Catalog**를 여세요.

메시가 선택되어 있으면 시작 리그를 추가할 때 그 메시에 맞춥니다. 팝업에서 썸네일을 클릭하거나 뷰포트로 드래그하면 시작 리그가 추가됩니다. 자동 웨이트와 컨트롤 생성은 처음에는 꺼져 있습니다. 추가 후 **Adjust Last Operation**에서 이 옵션들을 조정하세요.

선택된 메시가 없었다면:

1. 새 시작 리그를 선택합니다.
2. Quick Rig에서 **Mesh**를 선택합니다.
3. **Fit Dropped Rig**를 클릭합니다.

맞춤 작업은 골격의 크기와 위치를 조정합니다. 컨트롤이나 웨이트를 생성하기 전에:

1. 관절 위치를 살펴봅니다.
2. 필요에 따라 관절 위치를 편집합니다.

뷰포트 밖으로 드래그하거나 Esc 또는 마우스 오른쪽 버튼을 누르면 아무것도 추가하지 않고 취소합니다.

<strong>위치:</strong> Rig Builder → Quick Rig이며, Add → Armature → Quick Rig에서도 미리 만들어진 리그를 추가할 수 있습니다.

---

### 마네킹 {#mannequin}

<strong>기능:</strong> 기존 리그 주위에 미리보기 메시를 만들어 완성된 캐릭터 메시 없이도 변형을 살펴볼 수 있습니다. 아직 리그가 없다면 Quick Rig로 하나를 추가하세요. Mannequin을 사용하기 전에 아마추어나 해당 아마추어를 부모로 하는 메시를 선택합니다. 마네킹은 미리보기용이므로 최종 사용 전에는 자신의 메시로 교체하세요.

<strong>주요 컨트롤:</strong>

- **Quick Mannequin**은 고정된 기본값으로 미리보기를 만들고, 이 리그의 기존 마네킹을 교체합니다.
- **Add Mannequin**은 장면 설정으로 미리보기를 만듭니다. 기본적으로 기존 마네킹을 교체하며, 클릭한 후 Adjust Last Operation에서 Replace Existing을 설정할 수 있습니다.
- **Regenerate**는 저장된 설정으로 기존 미리보기를 다시 만듭니다.
- **Remove**는 마네킹 메시만 삭제하고 아마추어는 유지합니다.
- 버튼 아래 Options에는 **Mode**, **Body Type**, 밀도, **Radius Scale**이 있습니다. Options 안의 Advanced에는 부위별 배율과 출력 설정이 있습니다. 변경한 장면 설정을 사용하려면 **Add Mannequin**을 다시 클릭합니다.

<strong>위치:</strong> Rig Builder → Mannequin

---

## 마네킹 실습: 텍스트 안내 {#illustrated-mannequin-workshop}

<!-- 실습의 각 단계를 한데 유지하고 설명서의 인쇄 배율을 보존합니다. -->
<style>
section.chapter:has(#ch-06-rig-builder) img { max-width: 100%; max-height: 155mm; width: auto; height: auto; }
@media print {
  [id="06-rig-builder--illustrated-mannequin-workshop"] { break-before: page; break-after: avoid; }
  h4[id^="06-rig-builder--"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] + h4 { break-before: avoid; }
  section.chapter:has(#ch-06-rig-builder) h4 + p { break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) { break-before: avoid; break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) + p { break-before: avoid; }
}
</style>

다음 세 부분을 순서대로 진행하세요.

1. [A — Simple Human에서 마네킹 만들기](#part-a-simple-human-to-mannequin).
2. [B — 리그 없는 마네킹에 Auto-Rig 적용하기](#part-b-rigless-mannequin-through-auto-rig).
3. [C — 웨이트 테스트와 IK/FK 사용하기](#part-c-test-weights-and-use-ikfk).

영문 원본은 실습의 모든 번호 단계에 실제 인터페이스 스크린샷을 제공하며, 빨간 번호는 해당 그림 설명과 대응합니다. 이 스크린샷은 **BoneCraft 9.1.2 릴리스**를 `Bforartists 5.2.0`에서 사용해 촬영했습니다. 본 텍스트 전용판은 이미지를 생략하고 서면 단계, 이미지 설명, 그림 설명을 유지합니다. Blender의 패널 배치와 단축키는 다를 수 있으므로 이름으로 표시된 명령을 기준으로 삼으세요.

본 판에서 생략한 영문 원본 스크린샷은 9.1.2 촬영 레이블을 그대로 유지합니다. 현재 경로는 **Rig Builder → Quick Rig**, **Rig Builder → Auto-Rig Wizard**, **BoneCraft → Skin → Weight Tools**입니다. Starter Rigs는 이제 네이티브 하단 카탈로그 탭을 사용합니다. 이 텍스트 전용판은 9.2.18 또는 9.2.19에서 새로 과정을 재현했다고 주장하지 않습니다.

이 연습은 리깅 학습용의 단순한 캡슐 미리보기를 만듭니다. 머리, 손, 몸통은 임시 형태이며 완성된 캐릭터 모델이 아닙니다. 새 파일에서 시작하세요. 원본 메타리그를 잃지 않고 변환을 반복할 수 있도록 두 저장 체크포인트를 모두 보관하세요.

저장소의 `examples/mannequin/`에는 두 체크포인트가 들어 있습니다. `SimpleHuman_Mannequin.blend`는 중립 자세의 A부 결과이며, `Mannequin_AutoRig.blend`는 웨이트를 수정하고 포즈를 적용한 C부의 완성 예제입니다.

### A부: Simple Human에서 마네킹 만들기 {#part-a-simple-human-to-mannequin}

#### A1. Rigify 활성화 {#a1-enable-rigify}

1. 새 장면에서 시작합니다.
2. **Scene Properties → Rig Builder → Quick Rig**를 엽니다.
3. Rigify 프리셋을 사용할 수 없으면 **Enable Rigify**를 클릭합니다.

이 튜토리얼은 Rigify의 `Simple Human` 메타리그를 사용합니다. <strong>BoneCraft Basic Humanoid (19 bones)</strong>는 다른 프리셋입니다.

영문 원본 이미지 설명(이미지 생략): A1: Rigify 활성화

*1 — Scene Properties. 2 — Enable Rigify.*

#### A2. Simple Human 추가 {#a2-add-simple-human}

Quick Rig에서 `Simple Human`을 클릭합니다. 편집 가능한 메타리그가 생성되며 아직 메시가 아닙니다. 이 릴리스에서는 본이 29개입니다.

영문 원본 이미지 설명(이미지 생략): A2: Simple Human 추가

*1 — Simple Human 프리셋.*

#### A3. 메타리그 살펴보기 {#a3-inspect-the-metarig}

1. 포인터를 뷰포트로 옮깁니다.
2. `Numpad 1`을 눌러 Front Orthographic으로 전환합니다.
3. 골격 전체가 보이는지 확인합니다.
4. 마우스 휠로 골격이 화면에 맞도록 조정합니다.

새 메타리그는 처음에 포즈 모드일 수 있습니다.

영문 원본 이미지 설명(이미지 생략): A3: 메타리그 살펴보기

*1 — 정면 뷰. 2 — Simple Human 골격.*

#### A4. 오브젝트 모드로 돌아가기 {#a4-return-to-object-mode}

레스트 포즈를 바꾸거나 마네킹을 생성하기 전에:

1. 뷰포트 모드 드롭다운에서 **Object Mode**를 선택합니다.
2. `SimpleHumanArmature`를 선택한 상태로 유지합니다.

영문 원본 이미지 설명(이미지 생략): A4: 오브젝트 모드로 돌아가기

*1 — 모드 드롭다운. 2 — Object Mode.*

#### A5. T 포즈 사용 {#a5-use-a-t-pose}

Quick Rig에서 **T-Pose**를 클릭합니다. 팔이 수평으로 뻗습니다. 사용자 지정 신체는 미리보기를 생성하기 전에 편집 모드에서 메타리그를 맞추세요. 이 연습에서는 좌우 관절을 대칭으로 유지합니다.

영문 원본 이미지 설명(이미지 생략): A5: T 포즈 사용

*1 — T-Pose 명령.*

#### A6. 마네킹 생성 {#a6-generate-the-mannequin}

1. **Mannequin → Options**를 펼칩니다.
2. `Mode: Universal`을 설정합니다.
3. `Body Type: Neutral`을 설정합니다.
4. **Medium**을 선택합니다.
5. `Radius Scale: 1.00`을 설정합니다.
6. Advanced의 부위별 배율은 1.00으로 유지합니다.
7. `Joined (non-manifold)`를 선택합니다.
8. **Flat colour**를 선택합니다.
9. **Joint Smoothing**을 켭니다.
10. Unified Volume은 끈 상태로 둡니다.
11. **Add Mannequin**을 클릭합니다.

생략된 영문 원본 스크린샷에는 생성된 캡슐 메시가 표시됩니다. Add는 현재 옵션을 사용하고, Regenerate는 저장된 마네킹 설정을 다시 사용합니다.

영문 원본 이미지 설명(이미지 생략): A6: 마네킹 생성

*1 — Add Mannequin. 2 — Universal 및 신체 설정. 3 — Joined 출력과 스무딩.*

#### A7. 본 포즈 시험하기 {#a7-try-a-bone-pose}

정면 뷰에서 캐릭터의 왼쪽은 화면의 오른쪽입니다.

1. 아마추어를 선택합니다.
2. **Pose Mode**로 전환합니다.
3. 왼쪽 아래팔 본을 클릭합니다.
4. Rotate 도구로 본을 조금 회전합니다.

연결된 마네킹이 따라 움직입니다. 이것은 메타리그에 웨이트가 적용된 미리보기이며, 아직 C부에서 사용할 애니메이터 컨트롤은 없습니다.

영문 원본 이미지 설명(이미지 생략): A7: 본 포즈 시험하기

*1 — Pose Mode. 2 — 선택한 아래팔과 변환 기즈모.*

#### A8. 미리보기 복원 및 저장 {#a8-restore-and-save-the-preview}

1. 포인터를 뷰포트에 둔 상태에서 모든 포즈 본을 선택합니다.
2. **F3**을 누릅니다.
3. `Clear Pose Transforms`를 검색합니다.
4. **All**을 선택합니다.
5. 마네킹이 T 포즈로 돌아왔는지 확인합니다.
6. **File → Save As**를 엽니다.
7. 파일을 `SimpleHuman_Mannequin.blend`로 저장합니다.

계속하기 전에 이 체크포인트를 보관하세요.

영문 원본 이미지 설명(이미지 생략): A8: 미리보기 복원 및 저장

*1 — Clear Pose Transforms 검색. 2 — All은 선택한 포즈 본을 초기화합니다.*

### B부: 리그 없는 마네킹에 Auto-Rig 적용하기 {#part-b-rigless-mannequin-through-auto-rig}

#### B1. 마네킹 메시 선택 {#b1-select-the-mannequin-mesh}

A부의 중립 자세 체크포인트에서 계속합니다. 이 부분에서는 마법사를 실행하기 전에 의도적으로 마네킹의 리그를 제거합니다.

1. **Object Mode**로 전환합니다.
2. 아웃라이너에서 `SimpleHumanArmature_Mannequin`을 선택합니다.

A부를 보존하려면 결과를 다른 파일 이름으로 저장하세요.

영문 원본 이미지 설명(이미지 생략): B1: 마네킹 메시 선택

*1 — 아마추어가 아닌 메시를 선택합니다.*

#### B2. 미리보기를 메시로 굳히기 {#b2-bake-the-preview-into-a-mesh}

마네킹을 복원된 T 포즈로 유지하고 마네킹만 선택합니다.

1. **F3**을 누릅니다.
2. `Convert Mesh`를 검색합니다.
3. `Convert Mesh`를 실행합니다.

이 작업은 보이는 중립 자세의 지오메트리를 유지하고 Armature 모디파이어를 제거합니다.

영문 원본 이미지 설명(이미지 생략): B2: 미리보기를 메시로 굳히기

*1 — Convert Mesh 명령.*

#### B3. 부모 관계 해제 {#b3-clear-the-parent}

1. **Alt+P**를 누릅니다.
2. `Clear and Keep Transformation`을 선택합니다.

메시를 이동하지 않고 기존 메타리그와의 부모 관계를 해제합니다.

영문 원본 이미지 설명(이미지 생략): B3: 부모 관계 해제

*1 — Clear and Keep Transformation.*

#### B4. 기존 웨이트 제거 {#b4-remove-the-old-weights}

이 작업은 버려도 되는 이 연습용 메시에만 적용합니다. 기존 그룹은 이전 메타리그의 그룹이며, 마법사가 새 그룹을 만듭니다.

1. **Object Data Properties → Vertex Groups**를 엽니다.
2. 목록의 드롭다운 메뉴에서 `Delete All Groups`를 선택합니다.

영문 원본 이미지 설명(이미지 생략): B4: 기존 웨이트 제거

*1 — Vertex Groups 메뉴. 2 — Delete All Groups.*

#### B5. 리그 없는 체크포인트 확인 {#b5-verify-the-rigless-checkpoint}

1. 아웃라이너의 눈 아이콘으로 기존 `SimpleHumanArmature`를 숨깁니다.
2. 마네킹이 계속 보이는지 확인합니다.
3. Modifiers 패널에 Armature 모디파이어가 없는지 확인합니다.
4. Vertex Groups 목록이 비어 있는지 확인합니다.

이것이 리그 없는 마네킹 입력입니다. BoneCraft 9.1.2는 아마추어로부터 마네킹을 생성합니다. 이 미리보기의 연결을 해제하면 리그 없는 연습용 메시를 얻을 수 있습니다.

영문 원본 이미지 설명(이미지 생략): B5: 리그 없는 체크포인트 확인

*1 — 기존 메타리그 숨기기. 2 — 빈 모디파이어 스택.*

#### B6. 뷰포트 Rig Builder 탭 활성화 {#b6-enable-the-viewport-rig-builder-tab}

테스트한 9.1.2 호스트에서는 Scene Properties에서 시작한 Place Marker가 뷰포트 클릭을 받지 않았습니다. 마커를 배치할 때는 뷰포트 탭을 사용하세요.

1. **Edit → Preferences → Add-ons → BoneCraft → Tabs**를 엽니다.
2. **Rig Builder**를 켭니다.
3. **Left**를 선택합니다.
4. Preferences를 닫습니다.
5. 포인터를 뷰포트 위로 옮깁니다.
6. 왼쪽 Tool Shelf가 숨겨져 있으면 **T**를 누릅니다.

영문 원본 이미지 설명(이미지 생략): B6: 뷰포트 Rig Builder 탭 활성화

*1 — Rig Builder 활성화. 2 — 왼쪽 Tool Shelf 배치.*

#### B7. Auto-Rig 시작 {#b7-start-auto-rig}

리그 없는 마네킹을 선택한 상태에서 **Start Auto-Rig**를 클릭합니다. 생략된 영문 원본 스크린샷에는 같은 기능의 Scene Properties 버튼이 표시됩니다. 이전 단계에서 활성화한 뷰포트 Rig Builder 탭에도 맨 위에 같은 명령이 있습니다.

영문 원본 이미지 설명(이미지 생략): B7: Auto-Rig 시작

*1 — Start Auto-Rig.*

#### B8. 입력 메시 선택 {#b8-choose-the-input-mesh}

위젯이나 다른 미리보기 오브젝트를 선택하지 마세요.

1. `Select Mesh`에서 마네킹을 선택합니다.
2. 선택된 메시의 확인 표시를 확인합니다.
3. **Next**를 클릭합니다.

영문 원본 이미지 설명(이미지 생략): B8: 입력 메시 선택

*1 — 입력 마네킹. 2 — Next.*

#### B9. 두 방식을 모두 사용하는 신체 리그 선택 {#b9-choose-a-body-rig-with-both-methods}

이 캡슐 마네킹에는 얼굴 토폴로지가 없으므로 Body + Face는 필요하지 않습니다.

1. **Body Only**를 선택합니다.
2. `Kinematics: IK + FK`를 선택합니다.
3. **Generate Control Shapes**를 켠 상태로 유지합니다.
4. **Next**를 클릭합니다.

영문 원본 이미지 설명(이미지 생략): B9: 두 방식을 모두 사용하는 신체 리그 선택

*1 — Body Only. 2 — IK + FK. 3 — Next.*

#### B10. 초기 신체 마커 감지 {#b10-detect-initial-body-markers}

감지된 추정 위치는 시작점일 뿐입니다. 확인하지 않은 추정 위치를 그대로 수락하지 마세요.

1. 이 대칭 마네킹에서는 **Mirror Symmetry**를 켠 상태로 유지합니다.
2. Body Markers의 Smart Detection 아래에서 **Detect Markers**를 클릭합니다.

영문 원본 이미지 설명(이미지 생략): B10: 초기 신체 마커 감지

*1 — Detect Markers. 2 — Mirror Symmetry.*

#### B11. 감지 위치 검토 {#b11-review-the-detected-positions}

분절된 이 미리보기에서는 신뢰도가 낮은 추정 위치가 여러 개 나옵니다. 생성 전에:

1. 보이는 메시와 비교해 정수리, 목 아래, 골반, 손목, 발목을 확인합니다.
2. 주요 기준점과 선택적 정밀 기준점을 검토합니다.
3. 필요에 따라 기준점을 수정합니다.

신뢰도 레이블은 원래 감지 결과를 설명합니다. 행 앞의 녹색 확인 표시는 현재 배치가 확인되었음을 뜻합니다.

영문 원본 이미지 설명(이미지 생략): B11: 감지 위치 검토

*1 — 감지 신뢰도 요약. 2 — 신체 마커 행.*

#### B12. 메시 위에 손목 배치 {#b12-place-a-wrist-on-the-mesh}

정면 뷰에서 캐릭터의 왼쪽 손목은 화면 오른쪽에 있습니다.

1. 마커가 이미 확인되어 있다면 해당 행을 초기화해 배치 버튼을 표시합니다.
2. 뷰포트의 **Rig Builder** 탭에서 Wrist Left 행의 **Place Marker** 스포이드를 클릭합니다.
3. 뷰포트에서 손목 표면을 클릭합니다.

영문 원본 이미지 설명(이미지 생략): B12: 메시 위에 손목 배치

*1 — Wrist Left 배치 컨트롤. 2 — 손목 표면 클릭.*

#### B13. 대칭 손목과 발목 확인 {#b13-check-the-mirrored-wrist-and-ankles}

1. 두 손목 행에 녹색 확인 표시가 있고 X 좌표의 부호가 반대인지 확인합니다.
2. `Ankle Left`도 같은 방법으로 배치하되 발끝이 아닌 관절 위치에 놓습니다.

대칭 기능이 Ankle Right를 채웁니다. 메시와 비교해 대칭을 확인하세요. 크기가 다른 캐릭터에 예제 좌표를 그대로 복사하지 마세요.

영문 원본 이미지 설명(이미지 생략): B13: 대칭 손목과 발목 확인

*1 — 확인된 손목 쌍. 2 — 메시 위의 대칭 손목.*

#### B14. 어깨와 팔꿈치 다듬기 {#b14-refine-shoulders-and-elbows}

1. Precision Markers까지 스크롤합니다.
2. `Shoulder Left`를 초기화합니다.
3. `Shoulder Left`를 위팔의 회전축 위치에 배치합니다.
4. `Elbow Left`를 초기화합니다.
5. `Elbow Left`를 팔꿈치 틈에 배치합니다.
6. 대칭으로 배치된 반대쪽 마커를 확인합니다.
7. 손목은 아래팔의 손 쪽 끝에 유지합니다.

이 점들이 팔 체인을 결정합니다. 어깨나 팔꿈치가 잘못된 캡슐 위에 추정되었다면 수정하세요.

영문 원본 이미지 설명(이미지 생략): B14: 어깨와 팔꿈치 다듬기

*1 — 어깨와 팔꿈치 마커 행. 2 — 어깨. 3 — 팔꿈치.*

#### B15. 엉덩관절과 무릎 다듬기 {#b15-refine-hips-and-knees}

1. `Hip Left`를 허벅지 맨 위에 배치합니다.
2. `Knee Left`를 허벅지와 정강이 사이의 틈에 배치합니다.
3. 대칭 기능이 배치한 반대쪽을 확인합니다.
4. 골반은 양쪽 엉덩관절 사이의 중심선에 유지합니다.

영문 원본 이미지 설명(이미지 생략): B15: 엉덩관절과 무릎 다듬기

*1 — 엉덩관절과 무릎 행. 2 — 엉덩관절 표면. 3 — 무릎 틈.*

#### B16. 측면에서 깊이와 발끝 확인 {#b16-check-depth-and-toes-from-the-side}

1. 포인터를 뷰포트 위에 두고 `Numpad 3`을 누릅니다.
2. 정면뿐 아니라 Right Orthographic에서도 기준점을 확인합니다.
3. `Toe Left`를 발 앞부분 가까이에 배치합니다.
4. 대칭으로 배치된 반대쪽 마커를 확인합니다.

정면에서는 올바르게 보이는 마커도 몸보다 너무 앞이나 뒤에 있을 수 있습니다.

영문 원본 이미지 설명(이미지 생략): B16: 측면에서 깊이와 발끝 확인

*1 — Right Orthographic. 2 — 발끝 마커 행. 3 — 발 표면.*

#### B17. 발뒤꿈치 배치 {#b17-place-the-heels}

1. 발뒤꿈치가 잘못 추정되었다면 해당 마커를 초기화합니다.
2. 측면 뷰에서 `Heel Left`를 발 뒤쪽 가까이에 배치합니다.
3. Heel Right를 확인합니다.

이 마커들은 선택 사항입니다. 테스트한 릴리스에서는 둘 다 영점에 두면 근접 경고가 발생했습니다. 발 위에 배치하자 해당 경고가 사라졌습니다.

영문 원본 이미지 설명(이미지 생략): B17: 발뒤꿈치 배치

*1 — 확인된 발뒤꿈치 쌍. 2 — 발뒤꿈치 위치.*

#### B18. 확인 후 계속하기 {#b18-confirm-and-continue}

1. 정수리, 목 아래, 골반과 모든 좌우 기준점을 검토합니다.
2. **Confirm All Placed**를 클릭합니다.
3. **Next**를 클릭합니다.

이름 옆의 녹색 확인 표시는 확인 상태를 뜻합니다. 9.1.2에서는 원래의 REVIEW/ADJUST 신뢰도 레이블이 계속 보일 수 있습니다.

영문 원본 이미지 설명(이미지 생략): B18: 확인 후 계속하기

*1 — Confirm All Placed. 2 — Next.*

#### B19. 이 메시에서는 손가락 건너뛰기 {#b19-skip-fingers-for-this-mesh}

이 마네킹에는 손 모양 캡슐은 있지만 손가락 지오메트리는 없습니다.

1. `0 — No Fingers`를 선택합니다.
2. **Next**를 클릭합니다.

실제 손 메시를 사용할 때는:

1. 적절한 손가락 수를 선택합니다.
2. 손가락 마커를 배치합니다.

영문 원본 이미지 설명(이미지 생략): B19: 이 메시에서는 손가락 건너뛰기

*1 — No Fingers. 2 — Next.*

#### B20. 검토 및 생성 {#b20-review-and-generate}

진행 전에 **All checks passed**를 반드시 확인하세요. 이 설정은 단순한 이 연습용 마네킹을 위한 것이며, 모든 내보내기에 공통으로 필요한 조건은 아닙니다.

1. **IK + FK**를 선택합니다.
2. 컨트롤 셰이프를 켭니다.
3. `Spine Segments: 3`을 설정합니다.
4. `Neck Segments: 1`을 설정합니다.
5. `No Fingers`를 선택합니다.
6. **Game Ready**를 선택합니다.
7. Twist Bones를 끕니다.
8. Skirt Bones를 끕니다.
9. Preserve Volume을 끕니다.
10. Joint Correctives를 끕니다.
11. **Generate Rig**를 클릭합니다.

영문 원본 이미지 설명(이미지 생략): B20: 검토 및 생성

*1 — 마커 검사. 2 — 생성 설정. 3 — Generate Rig.*

#### B21. 애니메이터 컨트롤 만들기 {#b21-build-the-animator-controls}

생성이 끝나면 **Build Control Rig**를 클릭합니다. Generate Rig는 신체 리그와 웨이트를 제공하며, Build Control Rig는 아래에서 사용할 컨트롤 레이어를 추가합니다. 완료 패널에 일반적인 마네킹 생성 제안이 표시되더라도 입력 메시는 이미 있습니다. Quick Mannequin을 다시 클릭하지 마세요.

영문 원본 이미지 설명(이미지 생략): B21: 애니메이터 컨트롤 만들기

*1 — Build Control Rig.*

#### B22. 마법사 마치기 {#b22-finish-the-wizard}

1. 컨트롤 리그 완료 메시지가 나타날 때까지 기다립니다.
2. **Close Wizard**를 클릭합니다.
3. 기존 Simple Human 메타리그는 숨긴 상태로 유지합니다.

새 아마추어가 아웃라이너에 나타납니다. 새 리그가 메시를 실제로 변형해야 합니다. 본이 보이는 것만으로는 변형이 작동한다고 볼 수 없습니다.

영문 원본 이미지 설명(이미지 생략): B22: 마법사 마치기

*1 — 생성 버튼이 이제 비활성 상태입니다. 2 — Close Wizard.*

### C부: 웨이트 테스트와 IK/FK 사용하기 {#part-c-test-weights-and-use-ikfk}

테스트한 릴리스에서 생성된 아마추어의 오브젝트 이름은 다음과 같습니다. 아웃라이너와 웨이트 도구에서 이 이름을 사용하세요.

```text
BoneForge_Rig
```

`FK (Forward Kinematics)`는 계층을 따라 회전을 전달합니다. 위팔을 회전하면 아래팔과 손이 차례로 영향을 받습니다. 크게 휘두르는 동작이나 자유롭게 움직이는 팔다리에 적합합니다. `IK (Inverse Kinematics)`는 끝점에서 시작합니다. 손목이나 발목 타깃을 움직이면 솔버가 체인을 구부려 타깃에 도달하게 합니다. 바닥에 고정한 발이나 표면에 닿아야 하는 손에 적합합니다.

| 작업 | 사용할 컨트롤 | 확인할 사항 |
|---|---|---|
| 팔 휘두르기 | FK 어깨 및 팔꿈치 컨트롤 | 자식 컨트롤이 부모를 따라갑니다. |
| 손 위치 잡기 | IK 손목 타깃 | 어깨와 팔꿈치가 타깃에 맞게 조정됩니다. |
| 발 고정하기 | 해당 다리의 IK 발목 타깃 | 도달 가능한 타깃을 제자리에 둔 채 몸을 움직입니다. |
| 팔꿈치나 무릎이 굽는 방향 정하기 | IK 폴 컨트롤 | 폴은 굽힘 방향을 정하며 손목·발목 타깃과는 다릅니다. |
| 방식 전환하기 | 팔다리의 IK/FK 버튼 | 애니메이션 키를 넣기 전에 스냅된 포즈를 확인합니다. |

아래 연습에서는 같은 팔을 두 모드로 비교합니다. 각 팔다리에는 별도의 전환 스위치가 있습니다. `Bake IK / Bake FK`는 애니메이션 변환 도구입니다. 한 포즈에서 모드를 전환하는 것은 애니메이션 베이크나 키 삽입을 대신하지 않습니다. 다른 컨트롤은 [컨트롤 레이어](05-rig-tools.md#control-layer-ikfk)를 참고하세요.

#### C1. 컨트롤 레이어 열기 {#c1-open-the-control-layer}

1. **생성된 아마추어**를 선택합니다.
2. **Pose Mode**를 선택합니다.
3. **BoneCraft → Review → Control Layer**를 엽니다.
4. **arm-L → FK**를 선택합니다.

각 팔과 다리에는 별도의 IK/FK 스위치가 있습니다. 왼쪽과 오른쪽은 캐릭터를 기준으로 합니다. 정면 뷰에서 arm-L은 화면 오른쪽에 있습니다.

영문 원본 이미지 설명(이미지 생략): C1: 컨트롤 레이어 열기

*1 — Pose Mode. 2 — Control Layer와 arm-L 스위치.*

#### C2. 애니메이터 컨트롤 표시 {#c2-show-the-animator-controls}

1. 아마추어의 **Object Data Properties → Bone Collections**를 엽니다.
2. `Controls`의 Solo 별을 선택합니다.
3. **FK**의 Solo 별을 선택합니다.
4. 메시가 컨트롤을 가리면 Viewport Display에서 **In Front**를 켭니다.
5. 나중에 타깃을 사용할 때는 **IK**도 포함합니다.

이 Solo 선택으로 해당 컨트롤 셰이프만 표시됩니다. 이 호스트에서 BoneCraft Collections 패널을 그리지 못하더라도 이 네이티브 컬렉션 목록은 사용할 수 있습니다.

영문 원본 이미지 설명(이미지 생략): C2: 애니메이터 컨트롤 표시

*1 — Controls와 FK의 Solo 별. 2 — In Front.*

#### C3. 아래팔 FK 컨트롤 선택 {#c3-select-the-forearm-fk-control}

1. 정면 뷰에서 캐릭터 왼쪽 팔꿈치의 원형 컨트롤을 클릭합니다.
2. 뷰포트의 선택 이름이 **forearm.fk-L**인지 확인합니다.

FK 아래팔 컨트롤은 팔꿈치를 중심으로 회전합니다. 어깨 컨트롤을 선택하면 대신 위팔과 그 자식들이 회전합니다.

영문 원본 이미지 설명(이미지 생략): C3: 아래팔 FK 컨트롤 선택

*1 — 선택한 forearm.fk-L 컨트롤. 2 — arm-L에서 FK가 활성 상태입니다.*

#### C4. 회전하고 변형 확인하기 {#c4-rotate-and-inspect-the-deformation}

이 정면 뷰 예제의 목표는 글로벌 **Y**를 중심으로 약 `−45°` 회전하는 것입니다. 다음 중 한 방법을 사용하세요.

- Rotate 도구로 선택한 FK 컨트롤을 회전합니다.
- 예제의 Bforartists 키맵에서는 다음 순서로 조작합니다.

1. **Ctrl+E**를 누릅니다.
2. **Y**를 누릅니다.
3. **-45**를 입력합니다.
4. **Enter**를 누릅니다.

Blender의 기본 회전 단축키는 **R**입니다. 생략된 영문 원본 스크린샷은 초기 웨이트 문제를 의도적으로 보여 줍니다. 위팔 캡슐이 아래팔과 함께 기울어집니다. 이를 완성된 리그로 받아들이지 마세요.

영문 원본 이미지 설명(이미지 생략): C4: 회전하고 변형 확인하기

*1 — FK 테스트 중 위팔이 잘못 움직입니다.*

#### C5. 마네킹 웨이트 다시 계산하기 {#c5-recalculate-the-mannequin-weights}

위 포즈 테스트가 실패하면 다음 단계를 따르세요.

1. **Object Mode**로 전환합니다.
2. 메시를 선택합니다.
3. **BoneCraft → Skin → Weight Tools → Automatic Bone Weight Recalculation**을 엽니다.
4. Mesh to Reweight를 마네킹으로 설정합니다.
5. Existing Armature를 **생성된 아마추어**로 설정합니다.
6. **Body**를 선택합니다.
7. `Body Method: Bone Heat`를 선택합니다.
8. `New Weight Strength: 1.00`을 설정합니다.
9. `Smooth Passes: 0`을 설정합니다.
10. `Max Bones per Vertex: 0`을 설정합니다.
11. `Minimum Weight: 0.001`을 설정합니다.
12. **Keep Weight Backup**을 켠 상태로 유지합니다.
13. **Automatic Bone Weight Recalculation**을 실행합니다.

테스트한 릴리스에서는 이 작업으로 분절된 미리보기를 수정했습니다.

영문 원본 이미지 설명(이미지 생략): C5: 마네킹 웨이트 다시 계산하기

*1 — 메시와 아마추어. 2 — Bone Heat. 3 — 교체 설정과 백업. 4 — 다시 계산.*

#### C6. 수정된 FK 굽힘 확인 {#c6-verify-the-repaired-fk-bend}

1. 생성된 아마추어를 다시 선택합니다.
2. **Pose Mode**로 돌아갑니다.

이제 위팔은 어깨에서 팔꿈치까지 수평으로 유지되고, 아래팔은 팔꿈치에서 위로 올라가야 합니다. 숨겨진 `WEIGHTS_BACKUP_…` 오브젝트에 기존 웨이트가 보존됩니다. 자신의 캐릭터로 애니메이션을 만들기 전에는 다른 팔다리도 테스트하세요. 골격이 생성되었다는 사실만으로 스키닝이 올바르다고 볼 수 없습니다.

영문 원본 이미지 설명(이미지 생략): C6: 수정된 FK 굽힘 확인

*1 — 위팔이 제자리에 유지됩니다. 2 — 아래팔이 팔꿈치에서 구부러집니다.*

#### C7. 같은 팔을 IK로 전환 {#c7-switch-the-same-arm-to-ik}

**arm-L → IK**를 클릭합니다. 전환 시 타깃이 현재 포즈에 스냅되므로 팔은 들어 올린 상태를 유지해야 합니다. 타깃이 숨겨져 있으면 보이는 Solo 컬렉션에 **IK**를 추가하세요. 전환은 체인을 구동하는 컨트롤을 바꾸며 새 애니메이션을 기록하지 않습니다.

영문 원본 이미지 설명(이미지 생략): C7: 같은 팔을 IK로 전환

*1 — arm-L의 IK 스위치. 2 — 전환해도 포즈가 유지됩니다.*

#### C8. 손목 IK 타깃 선택 {#c8-select-the-wrist-ik-target}

1. 손목의 컨트롤을 클릭합니다.
2. 선택 이름이 **forearm.ik-L**인지 확인합니다.

이름에는 아래팔이 들어 있지만 팔 체인의 끝점 타깃입니다. 이 타깃을 움직여 손의 위치를 정하세요. 솔버가 어깨와 팔꿈치 각도를 바꿔 타깃에 도달하게 합니다.

영문 원본 이미지 설명(이미지 생략): C8: 손목 IK 타깃 선택

*1 — 선택한 손목 타깃. 2 — 선택 이름.*

#### C9. 타깃 이동 후 비교 {#c9-move-the-target-and-compare}

타깃이 팔의 도달 범위 안에 있도록 유지하세요. 목표는 글로벌 **X**를 따라 손목 타깃을 조금 안쪽으로 움직이는 것입니다. 이 예제에서는 `−0.15 m` 이동하면 굽힘이 눈에 띄게 달라집니다. 다음 중 한 방법을 사용하세요.

- Move 도구의 X 화살표를 드래그합니다.
- 예제의 키맵에서는 다음 순서로 조작합니다.

1. **Ctrl+W**를 누릅니다.
2. **X**를 누릅니다.
3. `-0.15`를 입력합니다.
4. **Enter**를 누릅니다.

Blender의 기본 이동 단축키는 **G**입니다. FK 예제와 팔 전체를 비교하세요. 끝점이 먼저 움직이고 두 팔 분절이 따라갑니다.

영문 원본 이미지 설명(이미지 생략): C9: 타깃 이동 후 비교

*1 — 손목 끝점. 2 — 반응하는 체인. 3 — X 이동 예제.*

#### C10. 다시 전환하고 예제 저장하기 {#c10-switch-back-and-save-the-example}

1. **arm-L → FK**를 다시 클릭합니다.

FK 컨트롤이 현재 IK 포즈에 스냅됩니다.

2. 메시가 갑자기 이동하지 않는지 확인합니다.
3. **File → Save As**를 엽니다.
4. `Mannequin_AutoRig.blend`를 저장합니다.

생략된 영문 원본 스크린샷에는 FK가 활성 상태인 저장 예제가 표시됩니다. 중립 자세의 연습용 사본을 만들려면:

1. 네 팔다리를 모두 FK로 둡니다.
2. 보이는 포즈 컨트롤을 모두 선택합니다.
3. **F3**을 누릅니다.
4. A부와 같이 `Clear Pose Transforms`를 검색합니다.
5. **All**을 선택합니다.
6. 중립 자세 사본을 별도 이름으로 저장합니다.

영문 원본 이미지 설명(이미지 생략): C10: 다시 전환하고 예제 저장하기

*1 — FK가 다시 활성 상태입니다. 2 — 포즈가 유지됩니다. 3 — 저장된 파일 이름.*

<strong>완료 확인:</strong> 원본 메타리그 미리보기가 저장되어 있습니다. 연결을 해제한 마네킹에 새 신체 리그와 컨트롤이 생겼고, 미리보기 웨이트를 수정했습니다. FK 회전과 IK 타깃 이동도 비교했습니다. 저장한 리그는 학습 예제로 보관하세요. 실제 제작에는 미리보기 대신 적절한 캐릭터 지오메트리를 사용하세요.

---

### 애니메이션 리타기팅 {#animation-retargeting}

한 골격에서 다른 골격으로 애니메이션을 옮기는 방법은 [리그 도구: 리타기팅](05-rig-tools.md#retarget)에서 설명합니다.

클립 컨트롤은 [리타기팅 그림 설명](05-rig-tools.md#retarget)을 참고하세요.

---

## 본 병합 {#bone-merge}

<strong>기능:</strong> 신체 리그와 의상 또는 머리카락 리그처럼 두 아마추어를 하나로 합치면서 모든 웨이트를 유지합니다.

[가이드 11](03-guides-b.md#guide-11-merge-two-rigs-together)에서 단계별 과정을 설명합니다.

<strong>세 단계:</strong>

- Scope — 두 아마추어를 선택하고 차이를 검토합니다.
- Rename — 이름 충돌을 해결하고 새 본을 구분합니다.
- Merge — 미리보기 후 최종 병합을 진행합니다.

<strong>주요 컨트롤:</strong>

- **Base**는 유지할 아마추어입니다. 다른 아마추어는 여기에 병합된 뒤 숨겨집니다.
- **Analyze**는 두 골격을 비교합니다. **Acknowledge Scope — Proceed to Rename**은 단계 2를 엽니다.
- **Normalize Both Armatures**는 두 리그의 표준 본 이름을 하나의 명명 규칙으로 맞춥니다. Mixamo Prefixed, Mixamo Stripped 또는 사용자 지정 규칙을 사용합니다.
- **Auto-Propose Renames**는 병합할 리그 고유 본의 이름을 제안합니다.
- **Apply Rename**은 한 항목의 이름을 바꿉니다. 한 번의 실행은 한 번의 실행 취소 단계입니다. **Apply Batch Pattern**은 `{bone}`, `{side}`, `{index}`가 포함된 패턴으로 여러 이름을 바꿉니다.
- **Mark as Unique**는 본을 병합하는 대신 새 본으로 유지합니다.
- **Verify Rename — Proceed to Merge**는 단계 3을 엽니다.
- **Run Merge Preview**는 아무것도 변경하지 않고 병합 시 수행할 내용을 보고합니다.
- **Merge Armatures**는 두 아마추어를 백업한 뒤 병합합니다.

<strong>위치:</strong> BoneCraft → Setup Rigging → Bone Merge

영문 원본 이미지 설명(이미지 생략): Bone Merge는 Stage 1: Scope에서 시작합니다. 앞 단계의 검사가 끝날 때까지 이후 단계는 잠겨 있습니다.

*네이티브 패널 팝오버, BoneCraft 9.2.18. Bone Merge는 Stage 1: Scope에서 시작합니다. 앞 단계의 검사가 끝날 때까지 이후 단계는 잠겨 있습니다.*

다음: [기계 장치](07-mechanisms.md)
