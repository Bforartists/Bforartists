# 리그 도구 {#rig-tools}

[← 목차](index.md)

이 장은 BoneCraft의 리깅, 애니메이션 및 웨이트 도구를 설명합니다. 기능 세부 사항이나 가이드에서 다루지 않는 상황에 사용하세요.

각 항목은 목적, 용도, 주요 컨트롤 및 위치를 설명합니다. 위치 문구에는 필요한 모드가 있습니다. 리그 컨트롤에는 포즈 모드, Weight Mirror와 Weight Transfer에는 웨이트 페인트 모드, Delta Mush에는 오브젝트 모드가 필요합니다. 실행할 수 없는 경우에도 일부 섹션은 선택 안내와 함께 남습니다.

9.1부터 여러 도구는 즉시 실행하고 Adjust Last Operation에 옵션을 표시합니다. 클릭 직후 다른 작업 전에 옵션을 바꾸세요. 자주 쓰는 작업은 Pose → BoneCraft와 Weights → BoneCraft 메뉴에 있으며 Bforartists의 Pose와 Weights 툴 셸프 탭에도 버튼 패널이 있습니다. [시작하기](01-start.md#where-things-are)에 진입점을 나열했습니다.

그림은 예제 리그와 설정을 보여 줍니다. 각 도구의 경로를 따라 컨트롤을 여세요.

엔진 내보내기는 [VRChat 도구: 게임 엔진 내보내기](08-vrchat.md#game-engine-export)를 사용하세요. **Bone Names** 프리셋은 내보내기 사본을 변경하므로 작업 리그 이름을 바꾸는 도구와 용도가 다릅니다.

---

## 리그 UI 도구 {#rig-ui-tools}

아마츄어 작업 중 본 표시, 구성 및 빠른 접근을 제어합니다.

---

### 본 컬렉션 {#bone-collections}

**기능:** 스켈레톤의 본 컬렉션을 행으로 표시합니다. 이름을 클릭하면 본이 선택되고 눈 아이콘은 컬렉션을 표시하거나 숨깁니다.

> 본 컬렉션은 “IK Controls”, “Face Bones”, “Deform Bones” 같은 이름 있는 본 그룹입니다. 숨기면 뷰포트에서 해당 본이 사라져 리그의 한 부분에 집중할 수 있습니다.

**주요 컨트롤:**

- 각 행: 강조색, **Toggle Collection Visibility**(눈), 컬렉션 이름, **Solo Collection**, **Rename Collection Display**. 이름은 본을 선택합니다. **Rename Collection Display**는 행의 사용자 표시 이름을 정합니다. 아이콘 전용 버튼은 툴팁으로 확인하세요
- 목록 위의 **Show All Collections**, **Hide All Collections**(열린 눈과 닫힌 눈) — 전체를 한 번에 제어
- Sections — 여러 컬렉션을 접을 수 있는 헤더 아래 묶기

**위치:** BoneCraft 탭 → Review → Collections

영문 원본 이미지 설명(이미지 생략): 본 컬렉션과 표시, 선택, 솔로 및 표시 이름 컨트롤.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 본 컬렉션과 표시, 선택, 솔로 및 표시 이름 컨트롤.*

---

### 표시 책갈피 {#visibility-bookmarks}

**기능:** 보이는 본 컬렉션을 저장해 저장된 뷰를 한 번에 전환합니다.

**사용 예:** 표정 작업용 “Face Only”는 얼굴 본만, 웨이트 페인팅용 “Full Rig”는 모든 본을 저장합니다. 한 번 클릭으로 전환합니다.

**주요 컨트롤:** 슬롯 하나가 한 행입니다.

- 책갈피 이름 — 클릭하여 저장된 뷰 적용
- **Save Bookmark** — 현재 표시 상태를 슬롯에 저장. 아이콘에 포인터를 올려 툴팁 확인
- 색 견본 — 책갈피 색상 지정
- **Clear Bookmark**, **Remove Bookmark**(닫기 아이콘) — 슬롯 비우기 또는 추가 슬롯 제거
- **Add Bookmark** — 슬롯 추가

**기본 책갈피:** FK Arms, IK Body, Face Only, Full Rig

**위치:** BoneCraft 탭 → Review → Collections → Visibility Bookmarks

영문 원본 이미지 설명(이미지 생략): Full Rig 뷰 하나를 저장하고 세 슬롯이 비어 있는 Visibility Bookmarks.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. Full Rig 뷰 하나를 저장하고 세 슬롯이 비어 있는 Visibility Bookmarks.*

---

### 단축키 빠른 패널 {#hotkey-quick-panel}

**기능:** 커서 위치에 BoneCraft 리그 패널(컬렉션과 책갈피)을 팝업으로 엽니다.

**사용법:**

1. 3D 뷰포트에서 **Ctrl+Shift+R**을 누르세요.
2. 바깥을 클릭해 닫으세요.

**위치:** 3D 뷰포트의 **Ctrl+Shift+R** 단축키(자체 패널 없음)

위의 [책갈피 컨트롤](#visibility-bookmarks)을 사용합니다.

---

## 애니메이션 도구 {#animation-tools}

---

### 포즈 라이브러리 {#pose-library}

**기능:** 썸네일이 있는 이름 붙인 포즈를 저장하여 한 번 클릭으로 적용합니다.

**주요 컨트롤:**

- **Save** — 현재 본 위치를 이름과 뷰포트 썸네일로 저장
- **Apply** — 저장된 포즈로 본 맞추기
- **Blend** — 현재 위치와 혼합하여 일부 강도로 적용
- **Mirror** — 좌우를 뒤집어 적용
- **Delete**, **Rename**, **Category** — 목록 관리. **Filter**는 범주 하나를 표시
- **Export**, **Import** — `.bfpose` 파일로 저장하거나 불러오기

Blend는 즉시 적용됩니다. 클릭 후 Adjust Last Operation에서 혼합 강도를 설정하세요.

**위치:** BoneCraft 탭 → Review → Pose Library

영문 원본 이미지 설명(이미지 생략): 저장된 예제 포즈에 Apply, Mirror, Blend와 라이브러리 컨트롤이 표시됩니다.

*기본 패널 팝오버, BoneCraft 9.2.18. 저장된 예제 포즈에 Apply, Mirror, Blend와 라이브러리 컨트롤이 표시됩니다.*

---

### 컨트롤 피커 {#control-picker}

**기능:** 리그 컨트롤을 클릭 가능한 지도로 표시합니다. 모양을 클릭하면 본을 선택하고 선택한 컨트롤이 강조됩니다.

**주요 컨트롤:**

- **Generate Picker** — 리그에서 레이아웃 생성
- **Edit Layout** — 레이아웃 편집. 각 컨트롤 행에 **Move Picker Control**, **Resize Picker Control**, **Relabel Picker Control** 아이콘이 있습니다. **Snap**은 격자에 맞추고 **Rebuild Layout**은 다시 생성합니다
- **Mirror Selection** — 반대쪽 컨트롤 선택
- **Pop-up Picker** — **Add Selection Set**도 있는 떠 있는 피커 창 열기

**위치:** BoneCraft 탭 → Review → Control Picker

영문 원본 이미지 설명(이미지 생략): 생성된 Control Picker의 예제 컨트롤, 레이아웃 편집, 반대쪽 선택 및 팝업 피커 작업.

*기본 패널 팝오버, BoneCraft 9.2.18. 생성된 Control Picker의 예제 컨트롤, 레이아웃 편집, 반대쪽 선택 및 팝업 피커 작업.*

---

### 컨트롤 레이어(IK/FK) {#control-layer-ikfk}

서면 실습 비교는 [웨이트 테스트와 IK/FK 사용](06-rig-builder.md#part-c-test-weights-and-use-ikfk)을 따르세요.

**기능:** **Build Control Rig**로 만든 리그의 팔다리를 제어합니다. 튀지 않고 IK와 FK를 전환하며 프레임 범위에서 IK 애니메이션을 FK로 또는 반대로 변환합니다.

**주요 컨트롤:**

- **IK**, **FK** — 팔다리를 전환하고 새 컨트롤을 현재 위치로 맞춥니다. 팔꿈치나 무릎이 튀지 않습니다
- **Bake IK**, **Bake FK** — 프레임 범위 애니메이션을 IK나 FK로 변환
- **Pole Follow**, **Pin**, **Lock-Free**, 보호된 잠금을 유지하는 **Global Rig Scale**

**위치:** BoneCraft 탭 → Review → Control Layer(**Build Control Rig**로 만든 리그 선택. [리그 빌더](06-rig-builder.md) 참고)

영문 원본 이미지 설명(이미지 생략): 팔다리 IK/FK 스위치, 베이크 작업 및 리그 설정이 있는 Control Layer.

*과거 워크숍 캡처. 팔다리 IK/FK 스위치, 베이크 작업 및 리그 설정이 있는 Control Layer.*

---

### Rigify 도구 {#rigify-tools}

**기능:** Rigify 컨트롤 리그를 감지하고 BoneCraft 컬렉션 패널, 책갈피 및 속성 슬라이더를 표준 Rigify 컨트롤에 연결합니다.

> Rigify는 애니메이션용 리그를 생성하는 Bforartists 내장 시스템입니다. Rigify로 만든 리그라면 BoneCraft UI를 Rigify IK/FK 컨트롤에 연결합니다.

**주요 컨트롤:**

- **Auto-Enhance** — 선택한 Rigify 리그용 BoneCraft 패널 설정
- **Re-run Enhancement** — 처음부터 다시 생성
- **Enable Rigify**는 Quick Rig에 있습니다. Troubleshooting 접이식 영역에는 <strong>Generate Control Rig (active metarig)</strong>가 있습니다([리그 빌더](06-rig-builder.md) 참고)
- Rigify Properties — IK/FK, 스트레치, 부모 공간 및 머리/목 추종 슬라이더

**위치:** BoneCraft 탭 → Setup Rigging → Rigify Tools(및 Rigify Properties 섹션)

영문 원본 이미지 설명(이미지 생략): Rigify Tools의 향상 기능 진입점. 생성된 Rigify 리그를 선택하면 해당 컨트롤을 사용할 수 있습니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Rigify Tools의 향상 기능 진입점. 생성된 Rigify 리그를 선택하면 해당 컨트롤을 사용할 수 있습니다.*

---

### 리타기팅 {#retarget}

**기능:** 모션 캡처 클립을 아바타에 옮기는 것처럼 스켈레톤 사이에 애니메이션을 전달합니다. 본 이름과 방향을 맞춰 팔다리 방향을 보존하며 느슨한 쇄골 매칭으로 과도한 어깨 회전을 방지합니다.

**주요 컨트롤:**

- **Import Clip**, **Browse Library** — 클립 불러오기 또는 라이브러리 폴더 설정. 클립 이름을 클릭해 선택
- **Auto-Match Bones**(클립 행의 확인 표시) — 소스와 대상 본 짝짓기. Bone Mapping 목록에 쌍 표시
- **Preview**, **Stop Preview** — 결과 시험
- **Apply** — 클립을 리그에 베이크

**위치:** BoneCraft 탭 → Setup Rigging → Retarget

영문 원본 이미지 설명(이미지 생략): Import Clip과 Browse Library로 시작하는 Retarget. 클립을 불러온 뒤 매핑과 미리보기가 나타납니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Import Clip과 Browse Library로 시작하는 Retarget. 클립을 불러온 뒤 매핑과 미리보기가 나타납니다.*

---

### 보정 셰이프 키 {#corrective-shape-keys}

**기능:** 본이 특정 각도에 도달하면 켜져 극단적인 포즈에서 찝히거나 무너지는 메시를 보정하는 셰이프 키입니다.

**사용 예:** 팔꿈치를 완전히 굽히면 무너지는 캐릭터에 조각한 팔꿈치 보정을 팔 본과 연결하여 굽힐수록 자동 적용합니다.

**주요 컨트롤:**

- New Corrective — **Shape Key**, **Driver Bone**, 회전 축, 최대 강도 각도 및 점진적 적용 설정
- 보정 목록 — 아래의 **Edit**, **Delete**는 선택한 보정에 적용

아마츄어의 자식 메시에는 Basis 셰이프 키가 필요합니다. 아마츄어를 선택하면 New Corrective가 나타나고 자식 메시가 셰이프 키를 제공합니다.

보정 생성:

1. **Shape Key**를 선택하세요.
2. **Driver Bone**을 선택하세요.
3. 회전 축을 선택하세요.
4. 모양이 최대 강도에 도달하는 각도를 설정하세요.
5. 점진적으로 적용되는 정도를 설정하세요.
6. **Create Corrective**를 선택하세요.

기존 보정은 목록의 셰이프 키 이름을 클릭해 선택합니다.

Edit는 현재 보정 값에서 시작합니다. 클릭 후:

1. Adjust Last Operation에서 각도를 바꾸세요.
2. 감쇠를 바꾸세요.

**위치:** BoneCraft 탭 → Skin → Correctives(메시에 Basis 셰이프 키 필요)

영문 원본 이미지 설명(이미지 생략): 아마츄어를 선택하면 New Corrective가 나타나며 자식 메시가 셰이프 키를 제공합니다.

*기본 패널 팝오버, BoneCraft 9.2.18. 아마츄어를 선택하면 New Corrective가 나타나며 자식 메시가 셰이프 키를 제공합니다.*

---

### 그래프 도구 {#graph-tools}

**기능:** 키프레임과 커브의 애니메이션 다듬기 도구입니다.

- **Interactive Breakdown**(Breakdowner) — 좌우로 드래그하여 가장 가까운 키 사이에서 현재 포즈를 혼합. 3D 뷰포트 단축키 **Ctrl+Shift+B**
- **Apply Delta**(Delta Mover) — 선택한 본을 화면 또는 월드 공간에서 정확한 양만큼 오프셋. 3D 뷰포트 단축키 **Ctrl+Shift+D**
- **Capture**, **Swap**(Buffer Curves) — 커브 사본을 유지하여 편집본과 교환
- **Smart Bake** — 컨스트레인트 애니메이션을 키로 베이크하며 불필요한 키 제거(**Tol**로 정도 설정)
- **Euler Filter** — 짐벌 락으로 인한 회전 뒤집힘 수정
- Tangent Handles — 선택 키의 핸들을 **Auto**, **Vector**, **Aligned**, **Free**, **Auto Clamped**로 설정

**위치:** BoneCraft 탭 → Review → Graph Tools

영문 원본 이미지 설명(이미지 생략): Interactive Breakdown이 선택한 포즈 본의 드래그를 시작합니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Interactive Breakdown이 선택한 포즈 본의 드래그를 시작합니다.*

영문 원본 이미지 설명(이미지 생략): Apply Delta와 오프셋 옵션.

*기본 패널 팝오버, BoneCraft 9.2.18. Apply Delta와 오프셋 옵션.*

영문 원본 이미지 설명(이미지 생략): Buffer Curves, Euler Filter, Smart Bake. Options는 접혀 있습니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Buffer Curves, Euler Filter, Smart Bake. Options는 접혀 있습니다.*

영문 원본 이미지 설명(이미지 생략): Auto, Vector, Aligned, Free, Auto Clamped를 제공하는 Tangent Handles.

*기본 패널 팝오버, BoneCraft 9.2.18. Auto, Vector, Aligned, Free, Auto Clamped를 제공하는 Tangent Handles.*

---

## 웨이트 도구 {#weight-tools}

본이 움직일 때 메시가 어떻게 변형되는지 제어합니다. 웨이트는 메시의 각 부분이 어느 본을 얼마나 따를지 정합니다.

---

### 자동 본 웨이트 재계산 {#automatic-bone-weight-recalculation}

**기능:** 메시를 바꾸지 않고 기존 리그에서 웨이트를 다시 계산합니다. 고밀도 메시에는 가벼운 프록시를 사용하여 조용히 실패하지 않습니다.

**주요 컨트롤:** Body는 기존 리그에서 웨이트를 계산하며 Clothing은 올바른 웨이트가 있는 소스 메시에서 전달합니다. 설정은 버튼 위에 있습니다.

1. **Mesh to Reweight**에서 대상 메시를 선택하세요.
2. **Existing Armature**에서 아마츄어를 선택하세요.
3. Body 또는 Clothing 모드를 선택하세요.

Body 모드에서는 방법을 선택하세요.

Clothing 모드에서는:

1. **Weighted Body**에 올바른 웨이트가 있는 소스 메시를 선택하세요.
2. 방법을 선택하세요.

두 모드 모두:

1. 혼합을 설정하세요.
2. 스무딩을 설정하세요.
3. 정점당 최대 본 영향 수를 설정하세요.
4. 최소 웨이트를 설정하세요.
5. 백업 보관 여부를 선택하세요.
6. **Automatic Bone Weight Recalculation**을 선택하세요.

CATS 단축 경로 **Smart Automatic Weights**는 대상 메시, 아마츄어 및 모드 대화상자를 엽니다. Clothing 모드에는 소스 메시도 있습니다.

**위치:** BoneCraft 탭 → Skin → Weight Tools

영문 원본 이미지 설명(이미지 생략): 예제 메시와 아마츄어를 선택한 Automatic Bone Weight Recalculation 설정.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 예제 메시와 아마츄어를 선택한 Automatic Bone Weight Recalculation 설정.*

---

### 웨이트 대칭 {#weight-mirror}

**기능:** 대칭 캐릭터에서 웨이트를 한쪽에서 반대쪽으로 복사합니다.

**주요 컨트롤:**

- **Mirror All Weights** — 모든 본 그룹을 반대쪽에 대칭 복사
- **Mirror Active Weight** — 활성 본 그룹만 대칭 복사
- **Axis**, **Direction** — 반사 축과 소스 방향 선택
- **Search Distance** — 반사된 정점 위치와 공간상 대응점 사이의 허용 거리
- **Select Unmatched** — 짝 없는 정점 선택. **Normalize Weights**는 이후 합계를 1.0으로 정규화

메시 토폴로지가 아니라 공간 위치를 사용합니다.

1. 대칭 버튼을 클릭하세요.
2. Adjust Last Operation에서 **Axis**를 선택하세요.
3. **Direction**을 선택하세요.
4. **Search Distance**를 설정하세요.

**Mirror Active Weight**는 Weights → BoneCraft와 Weights 툴 셸프 탭에도 있습니다.

**위치:** 웨이트 페인트 모드의 BoneCraft 탭 → Weight Mirror

영문 원본 이미지 설명(이미지 생략): Weight Mirror 작업. 클릭 후 Adjust Last Operation에서 축과 검색 옵션을 설정하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Weight Mirror 작업. 클릭 후 Adjust Last Operation에서 축과 검색 옵션을 설정하세요.*

---

### 웨이트 전달 {#weight-transfer}

**기능:** 소스 메시의 웨이트를 활성 메시로 복사합니다. 몸에 의상을 부착하거나 고해상도 메시에서 저해상도로 옮길 때 사용합니다.

**주요 컨트롤:** Adjust Last Operation의 **Normalize**는 합계를 1.0으로 유지합니다. **Select Problem Vertices**는 대응이 좋지 않은 정점을 선택합니다.

대상 메시를 웨이트 페인트 모드에서 활성 상태로 유지하세요.

1. **Source Mesh**에서 소스 메시를 선택하세요.
2. **Transfer Weights**를 클릭하세요.
3. Adjust Last Operation에서 전달 방법을 선택하세요.
4. 본 필터를 선택하세요.

결과는 평균과 최대 거리를 표시합니다.

**위치:** 웨이트 페인트 모드의 BoneCraft 탭 → Weight Transfer(Skin → Weight Tools에도 있음)

영문 원본 이미지 설명(이미지 생략): Transfer Weights 전에 Source Mesh를 선택하세요. 이 예제의 거리 필드는 초기값입니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Transfer Weights 전에 Source Mesh를 선택하세요. 이 예제의 거리 필드는 초기값입니다.*

---

### 웨이트 표 {#weight-table}

**기능:** 선택 정점의 본별 정확한 웨이트를 표시하고 정밀 값을 설정합니다.

**사용법:**

1. 웨이트 페인트 모드로 들어가세요.
2. **정점 선택 마스킹**을 켜세요.
3. 정점 하나를 선택하세요.

표에 해당 정점의 본과 웨이트가 나타납니다.

4. 본 행의 손 아이콘을 클릭하세요.
5. Adjust Last Operation에서 **Weight**를 설정하세요.

Add Influence는 선택한 본을 사용합니다. 실행 후 새 웨이트도 Adjust Last Operation에서 설정하세요. 여러 정점을 선택했다면 **Normalize All Vertices**가 모두 정규화합니다.

**위치:** 웨이트 페인트 모드의 BoneCraft 탭 → Weight Table

영문 원본 이미지 설명(이미지 생략): 여러 정점이 선택된 Weight Table. 세부 웨이트 편집에는 정점 하나를 선택하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. 여러 정점이 선택된 Weight Table. 세부 웨이트 편집에는 정점 하나를 선택하세요.*

---

### 전체 채우기 {#flood-fill}

**기능:** 선택하지 않은 정점을 포함한 메시 전체에서 활성 버텍스 그룹 웨이트를 변경합니다.

Flood Fill 전에:

1. 메시를 선택하세요.
2. 웨이트 페인트 모드로 들어가세요.
3. 필요한 버텍스 그룹을 활성화하세요.

**작업:**

- **Flood to 0.0** — 메시 전체의 활성 그룹에서 양수로 할당된 웨이트를 제거합니다. 다른 그룹은 유지합니다.
- **Flood to 1.0** — 모든 정점의 활성 그룹에 1.0을 할당합니다. 다른 양수 웨이트 합계가 1e-6을 넘으면 해당 정점의 다른 양수 웨이트를 제거합니다.
- **Flood to Custom** — 모든 정점의 활성 그룹에 양수 **Value**를 할당합니다. **Normalize**를 켜면 메시 전체 웨이트도 정규화합니다. **Value**가 0이면 할당이나 정규화를 하지 않습니다. 비우려면 **Flood to 0.0**을 사용하세요.

Weights 메뉴와 셸프에서는 고정값 버튼을 Flood to Zero와 Flood to One이라고 부릅니다.

사용자 값 채우기:

1. **Flood to Custom**을 선택하세요.
2. 즉시 Adjust Last Operation의 **Value**를 설정하세요.
3. **Normalize**를 켜거나 끄세요.

**위치:** 웨이트 페인트 모드의 BoneCraft 탭 → Skin → Weight Tools; Weights → BoneCraft와 Tool Shelf → Weights → BoneCraft에도 있음

영문 원본 이미지 설명(이미지 생략): Flood Fill 작업. 클릭 후 Adjust Last Operation에서 사용자 값을 설정하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Flood Fill 작업. 클릭 후 Adjust Last Operation에서 사용자 값을 설정하세요.*

---

### 변형 본과 컨트롤 본 {#deform-vs-control}

**기능:** 변형 본은 메시를 움직이고 컨트롤 본은 애니메이터가 움직입니다. 도구는 이를 분리하고 변형 본에 태그와 변형 본 이름을 지정하며 변형 본만 있는 스켈레톤도 내보냅니다.

**위치:** 포즈 모드의 BoneCraft 탭 → Deform vs Control

영문 원본 이미지 설명(이미지 생략): 예제 리그의 Deform과 Control 목록. 변형 본 19개이며 컨트롤 본은 없습니다.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 예제 리그의 Deform과 Control 목록. 변형 본 19개이며 컨트롤 본은 없습니다.*

---

### Delta Mush {#delta-mush}

**기능:** 관절 찝힘을 줄이는 스무딩 변형입니다. 레스트 상태의 형태를 유지하면서 모션 중 더 깨끗하게 변형합니다.

**사용법:** 오브젝트 모드의 활성 메시가 필요합니다.

1. **Add Delta Mush**를 클릭하세요.

모디파이어를 추가하고 레스트 형태에 바인딩합니다. 실행 직후 옵션을 조정하세요.

2. Adjust Last Operation에서 **Iterations**를 설정하세요.
3. **Smooth Strength**를 설정하세요.
4. **Pin Borders**를 켜거나 끄세요.
5. **Only Smooth Deform**을 켜거나 끄세요.

모디파이어가 있으면 **Rebind**, **Remove**가 나타납니다. Settings에는 반복 수, 스무딩 강도 및 경계 고정 컨트롤이 있습니다.

**위치:** BoneCraft → Skin → Delta Mush(오브젝트 모드; 메시)

영문 원본 이미지 설명(이미지 생략): Add Delta Mush로 설정을 시작합니다. 클릭 직후 옵션을 조정하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Add Delta Mush로 설정을 시작합니다. 클릭 직후 옵션을 조정하세요.*

---

### 근접 랩 {#proximity-wrap}

**기능:** 두 번째 피부처럼 메시 하나가 다른 메시 표면을 따르게 합니다. 몸에 붙는 의상에 유용합니다.

**사용법:** 오브젝트 모드의 활성 대상 메시가 필요합니다. 바인딩 때 드라이버의 아마츄어는 레스트 포즈로 두세요.

1. 대상 메시를 선택하세요.
2. 다른 **Driver Mesh**를 선택하세요.
3. **Bind Proximity Wrap**을 클릭하세요.

버튼 아래 Options에는 **Falloff Type**, **Max Distance**가 있습니다. 9.1.2는 값을 저장하지만 Surface Deform 바인딩을 변경하지는 않습니다. 바인딩 후 **Rebind**, **Unbind**가 나타납니다. Unbind는 뷰포트와 렌더에서 모디파이어를 끄지만 제거하지는 않습니다.

**위치:** BoneCraft → Skin → Proximity Wrap(오브젝트 모드; 메시)

영문 원본 이미지 설명(이미지 생략): Bind Proximity Wrap 전에 Driver Mesh를 선택하세요. Options는 접혀 있습니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Bind Proximity Wrap 전에 Driver Mesh를 선택하세요. Options는 접혀 있습니다.*

---

## 리그 컨트롤 {#rig-controls}

포즈 모드의 BoneCraft 탭에 나타납니다.

---

### 공간 전환 {#space-switch}

**기능:** 애니메이션 중 본이 따르는 공간을 바꿉니다. 소품을 든 손을 한 번 클릭으로 몸 추종에서 월드 고정으로 바꿀 수 있습니다.

**주요 컨트롤:**

- **Add Space**, Manage Spaces 아래의 **Remove Space**(X) — 본이 따를 공간(World, Origin 또는 다른 본)
- 공간마다 해당 이름의 버튼이 있으며 현재 공간에는 ● 표시. 다른 버튼을 클릭해 전환

**위치:** 포즈 모드의 BoneCraft 탭 → Space Switch

영문 원본 이미지 설명(이미지 생략): 정의된 공간이 없는 Space Switch. Add Space로 설정을 시작합니다.

*기본 패널 팝오버, BoneCraft 9.2.18. 정의된 공간이 없는 Space Switch. Add Space로 설정을 시작합니다.*

---

### Spline IK {#spline-ik}

**기능:** 본 체인이 커브를 따르게 합니다. 부드럽고 휘도는 움직임이 필요한 꼬리, 촉수, 밧줄, 긴 머리카락 및 척추에 사용합니다.

**사용법:**

1. 시작 본을 활성화하세요.
2. **Generate Spline IK**를 클릭하세요.
3. Adjust Last Operation에서 **Chain Length**를 설정하세요.
4. **Curve Resolution**을 설정하세요.
5. **Stretch**를 설정하세요.
6. **Volume Preservation**을 설정하세요.

**Remove Spline IK**는 구성을 제거합니다.

**위치:** 포즈 모드의 BoneCraft 탭 → Spline IK

영문 원본 이미지 설명(이미지 생략): Spline IK 작업. 생성 후 Adjust Last Operation에서 체인 옵션을 설정하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Spline IK 작업. 생성 후 Adjust Last Operation에서 체인 옵션을 설정하세요.*

---

### 체인 동역학 {#chain-dynamics}

**기능:** 본 체인에 물리와 비슷한 보조 모션을 추가합니다. 움직이는 부모 뒤로 늦게 따라가고 멈추면 튕깁니다. 머리카락, 꼬리 및 액세서리에 사용합니다.

**사용법:**

1. 본 체인을 선택하세요.
2. **Add Chain Dynamics**를 클릭하세요.
3. Adjust Last Operation에서 **Stiffness**를 설정하세요.
4. **Damping**을 설정하세요.
5. **Mass**를 설정하세요.
6. **Gravity Scale**을 설정하세요.

작업 아래 Settings에도 같은 매개변수가 있습니다. 구성이 있으면 **Bake**, **Remove**가 나타납니다. 충돌에는 단순화한 구를 사용하므로 오목한 표면에서는 올바르게 충돌하지 않을 수 있습니다.

**위치:** 포즈 모드의 BoneCraft 탭 → Chain Dynamics

영문 원본 이미지 설명(이미지 생략): Add Chain Dynamics로 설정을 시작하며 매개변수가 필요하면 Settings를 펼칩니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Add Chain Dynamics로 설정을 시작하며 매개변수가 필요하면 Settings를 펼칩니다.*

---

### 리본 {#ribbon}

**기능:** 부드럽게 휘고 비틀리는 Bendy Bones 리본을 만들어 입술, 눈썹, 벨트 등 부드러운 곡면에 사용합니다.

**사용법:**

1. 본 체인을 선택하세요.
2. **Generate Ribbon**을 클릭하세요.
3. Adjust Last Operation에서 **Control Bones**를 설정하세요.
4. **Ribbon Width**를 설정하세요.

**Remove Ribbon**은 구성을 제거합니다.

**위치:** 포즈 모드의 BoneCraft 탭 → Ribbon

영문 원본 이미지 설명(이미지 생략): Ribbon 작업과 체인 길이. 클릭 직후 생성된 리본을 조정하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Ribbon 작업과 체인 길이. 클릭 직후 생성된 리본을 조정하세요.*

---

### 비짐 라이브러리 {#viseme-library}

**기능:** 셰이프 키와 연결된 비짐 세트(입 모양)를 만들고 관리하며 텍스트에서 립싱크 키도 만듭니다. VRChat 매핑에는 VRChat Viseme Mapping, 새 비짐 생성에는 CATS Visemes를 사용하세요.

**주요 컨트롤:**

- **New Set**, **Delete** — 비짐 세트 생성과 제거
- 각 세트에서 비짐별 스피커 버튼으로 미리보기
- Lip Sync — 음소당 프레임 수와 스무딩을 설정하는 텍스트→비짐 키 생성

**위치:** CATS → Avatar Tools → Viseme Library(아마츄어); Lip Sync(포즈 모드)

영문 원본 이미지 설명(이미지 생략): New Set으로 시작하는 Viseme Library. Lip Sync에는 포즈 모드로 바꾸세요.

*기본 패널 팝오버, BoneCraft 9.2.18. New Set으로 시작하는 Viseme Library. Lip Sync에는 포즈 모드로 바꾸세요.*

영문 원본 이미지 설명(이미지 생략): Lip Sync 텍스트와 Generate Lip Sync. 타이밍과 스무딩은 Options를 펼치세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Lip Sync 텍스트와 Generate Lip Sync. 타이밍과 스무딩은 Options를 펼치세요.*

---

### 드리븐 키 설정 {#set-driven-key}

**기능:** Python 표현식 없이 본 변환 값 하나를 다른 값에 연결합니다. 예를 들어 컨트롤 본의 X 이동이 대상 본을 Z로 올립니다. 이 패널은 본 변환 대상을 설정합니다.

1. **Driver Bone**을 선택하세요.
2. **Driver Attribute**를 선택하세요.
3. **Target Bone**을 선택하세요.
4. **Target Attribute**를 선택하세요.
5. 본 포즈를 만드세요.
6. 각 포인트를 기록하세요.
7. **Create SDK**를 선택하세요.

**주요 컨트롤:**

- **Driver Bone**, **Driver Attribute** — 구동하는 요소
- **Target Bone**, **Target Attribute** — 구동되는 요소
- **Set Value**, **Record Point** — 커브의 한 점 기록
- **Create SDK** — 드라이버 생성

**위치:** 포즈 모드의 BoneCraft 탭 → Set Driven Key

영문 원본 이미지 설명(이미지 생략): 드리븐 키 포인트 기록 전에 구동 본과 대상 본을 선택하세요. 예제에서는 미할당 상태입니다.

*기본 패널 팝오버, BoneCraft 9.2.18. 드리븐 키 포인트 기록 전에 구동 본과 대상 본을 선택하세요. 예제에서는 미할당 상태입니다.*

---

### 리그 검증기 {#rig-validator}

**기능:** 이름, 본 누락, 깨진 컨스트레인트, 계층, 웨이트, Python이 필요한 드라이버 및 Mechanisms 규칙을 검사하고 문제를 보고합니다. `DEF-upper_arm.L` 같은 하이픈 이름은 통과합니다.

**주요 컨트롤:**

- **Run Validation** — 모든 검사 실행과 결과 목록
- **Export Report** — 결과를 파일에 저장

Task Board(BoneCraft 탭 → Overview → Task Board)는 검사가 실패하면 검증 작업을 표시합니다.

**위치:** BoneCraft 탭 → Review → Rig Validator

영문 원본 이미지 설명(이미지 생략): 검증은 컬렉션 경고 하나를 보고합니다. 예제 리그에는 부모 연결된 메시가 없어 웨이트 검사를 건너뜁니다.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 검증은 컬렉션 경고 하나를 보고합니다. 예제 리그에는 부모 연결된 메시가 없어 웨이트 검사를 건너뜁니다.*

---

### 리그 노트 {#rig-notes}

**기능:** 본에 연결한 서면 노트로 설정 내용, 기억할 사항 및 협업 메모를 남깁니다.

**주요 컨트롤:** **Add Note**와 각 노트의 **Remove**. Rig Readme는 읽기 전용 페이지로 리그 노트를 보여 줍니다.

**위치:** BoneCraft 탭 → Overview → Rig Notes, Review → Rig Readme

영문 원본 이미지 설명(이미지 생략): 포즈 모드의 Hips에 연결한 노트. Add Note는 주석을 만들고 Remove는 해당 주석을 삭제합니다.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 포즈 모드의 Hips에 연결한 노트. Add Note는 주석을 만들고 Remove는 해당 주석을 삭제합니다.*

다음: [리그 빌더](06-rig-builder.md)
