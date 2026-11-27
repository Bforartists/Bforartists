# 튜토리얼: 메커니즘으로 Crescent Rose 만들기 {#tutorial-crescent-rose-with-mechanisms}

[← 목차](index.md)

<!-- Print layout is scoped to this illustrated chapter; the shared renderer is unchanged. -->
<style>
@media print {
  h3[id^="12-crescent-rose--"] { break-before: page; break-after: avoid; }
  h2:has(+ h3[id^="12-crescent-rose--"]) { break-before: page; break-after: avoid; }
  h2 + h3[id^="12-crescent-rose--"] { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) { break-after: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) + p { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) table { break-inside: avoid; }
  [id="12-crescent-rose--what-you-built"] { break-before: page; break-after: avoid; }
}
</style>

## 만들 결과 {#what-you-will-build}

Crescent Rose는 낫과 소총이 결합된 무기입니다. 이 튜토리얼에서는 메커니즘으로 이 모델을 리깅합니다. 슬라이더 하나는 낫을 소총으로 바꾸고, 두 번째 슬라이더는 소총을 접어 수납 형태로 만듭니다.

이 튜토리얼에서는 기어 링크를 제외한 현재의 모든 관절과 링크를 사용합니다. 힌지 8개, 슬라이드 3개, 텔레스코프 1개, 피스톤 1개, 추종 링크 1개를 만들고, 시퀀스 2개와 폼 3개도 만듭니다.

이 폼들은 팬이 제작한 모델을 위한 학습용 포즈입니다. 메커니즘은 충돌을 감지하거나 실제 기계 설계에 맞는 복제품을 만들지 않습니다. 리그를 응용할 때는 부품 사이의 여유 공간을 확인하세요.

결과 파일은 `examples/crescent-rose/CrescentRose_Mechanisms.blend`입니다. 언제든 열어 작업 결과와 비교할 수 있습니다.

## 시작하기 전에 {#before-you-start}

- 파일: `examples/crescent-rose/CrescentRose_parts.blend`에는 모델이 부품 오브젝트 15개로 나뉘어 있습니다. 이 파일에서 튜토리얼을 시작하세요. `CrescentRose_Mechanisms.blend`는 완성된 리그입니다.
- 시간: 원본 FBX 준비와 메커니즘 실습에 각각 한 차례의 작업 시간을 확보하세요. 두 과정 모두 작업량이 많습니다. 단계 사이에 체크포인트를 저장하세요.
- 용어: 먼저 [메커니즘](07-mechanisms.md)의 “메커니즘이 하는 일”을 읽으세요. 부품, 관절, 링크, 핸들, 시퀀스, 폼을 설명합니다.
- 언어: 여기서 생략한 영어 원본 스크린샷에는 Bforartists와 BoneCraft 패널이 영어로 표시됩니다. BoneCraft 패널은 **언어(Language)** 환경설정을 따릅니다. Bforartists의 나머지 부분은 애플리케이션의 인터페이스 언어를 따릅니다. BoneCraft가 해당 Bforartists 언어를 지원하지 않으면 패널은 영어로 유지됩니다. 이 텍스트 전용 판의 설명은 그대로 적용됩니다.
- 시작 경로: 원본 FBX로 시작한다면 아래의 P1-P8을 진행하고, 준비된 파일을 사용한다면 1단계로 건너뛰세요. 두 경로 모두 같은 부품 15개를 사용합니다.
- 영어 원본의 과거 검증: 설명과 실제 인터페이스 캡처는 BoneCraft `9.1.2`를 사용해 기본 키맵의 Bforartists `5.2.0`에서 확인했습니다. 이 텍스트 전용 판을 위해 새로 캡처하거나 튜토리얼을 다시 실행하지는 않았습니다.

**현재 탐색 경로:** 9.2.18에서는 **BoneCraft → 메커니즘(Mechanisms)** 또는 <strong>속성(Properties) → 씬(Scene) → 메커니즘(Mechanisms)</strong>을 사용하세요. 씬 섹션이 보이지 않으면 <strong>탭(Tabs) → 씬 속성(Scene Properties) → 표시(Show)</strong>를 활성화하세요. 부품(Parts), 관절 및 링크(Joints & Links), 시퀀스(Sequences), 컨트롤(Controls)의 이름은 유지됩니다. 여기서 생략한 이전 영어 원본 스크린샷에는 이 섹션 주변의 배치가 과거 모습으로 나올 수 있습니다.

이 텍스트 전용 판은 영어 원본의 9.1.2 캡처와 재실행 검증 범위를 그대로 유지하며, 이미지는 생략합니다. 9.2.18 소스 검토가 튜토리얼을 새로 실행한 검증을 대신하지는 않습니다. 예전에 저장한 폼도 계속 읽고 사용할 수 있습니다. 폼을 열거나 적용해도 그 값이 다시 저장되지는 않습니다. [폼](07-mechanisms.md#forms)을 참고하세요.

영어 원본 이미지는 빨간 번호 표시로 클릭하거나 값을 입력하거나 확인할 위치를 가리킵니다. 이 텍스트 전용 판에서는 해당 이미지를 생략하고, 이미지 설명과 조작 번호 설명은 유지합니다. 본문의 단계와 조작 번호 설명을 순서대로 따르세요(1, 다음 2, 다음 3). 이 번호는 영어 원본의 주석을 가리키며 이미지마다 다시 시작합니다. 원본 증거에서 상자는 확인할 결과를, 원은 사용할 부품이나 버튼을 표시합니다.

## 원본 FBX 준비하기(P1-P8) {#prepare-the-original-fbx-p1-p8}

`CrescentRose_parts.blend`를 사용한다면 이 섹션을 건너뛰세요.

1. 새 파일에서 작업하세요.

2. 원본 FBX와 해당 `CrescentRoseTextures` 폴더를 함께 두세요.

이 단계들은 기본 키맵을 사용하는 Bforartists 5.2.0에서 재실행했습니다. 화면의 모드 메뉴를 사용하세요. 이 키맵에서 Tab은 편집 모드로 전환하는 대신 오버레이를 켜거나 끌 수 있습니다.

### P1 - FBX 가져오기 {#p1---import-the-fbx}

이 절차에는 Legacy 가져오기를 사용하세요.

1. 빈 씬에서 시작하세요.

2. <strong>파일(File) > 가져오기(Import) > FBX (.fbx) (Legacy)</strong>를 선택하세요.

3. `CrescentRose.fbx`를 선택하세요.

4. 가져오기 배율(Scale)은 `1.00`으로 유지하세요.

5. FBX 가져오기(Import FBX)를 선택하세요.

6. Numpad 3을 눌러 오른쪽 뷰로 전환하세요.

7. Home을 눌러 가져온 오브젝트가 화면에 들어오게 하세요.

아웃라이너에는 루트와 재질별 메시 3개인 `Black01`, `Blades01`, `Red01`이 있습니다.

영어 원본 이미지 설명(이미지 생략): P1: 배율 1.00의 Legacy FBX 가져오기 옵션

*1: CrescentRose.fbx를 선택합니다. 2: 배율을 1.00으로 유지합니다. 3: Import FBX를 클릭합니다. Legacy 가져오기를 사용하세요.*

### P2 - 배치를 유지하고 크기 설정하기 {#p2---preserve-placement-and-set-the-size}

가져온 무기의 높이는 약 `0.32 m`입니다. 준비된 파일에는 이미 배율이 적용되어 있습니다. 가져온 메시에는 이 크기 조절 절차를 한 번만 수행하세요.

1. 오브젝트 모드로 전환하세요.

2. 메시 3개를 모두 선택하세요.

3. <strong>오브젝트(Object) > 부모(Parent) > 변환을 유지하고 해제(Clear and Keep Transformation)</strong>를 선택하세요.

4. 이제 사용하지 않는 루트를 작업 씬에서 제거하세요.

5. 메시 3개가 모두 선택된 상태에서 <strong>오브젝트(Object) > 적용(Apply) > 회전 및 배율(Rotation & Scale)</strong>을 선택하세요.

6. 이 Bforartists 키맵에서 Ctrl+R을 눌러 크기 조절을 시작하세요.

7. `6.25`를 입력해 메시 3개를 함께 확대하세요.

8. 배율을 확정하세요.

9. <strong>오브젝트(Object) > 적용(Apply) > 회전 및 배율(Rotation & Scale)</strong>을 다시 선택하세요.

이제 전체 무기의 높이는 약 `1.997 m`입니다.

영어 원본 이미지 설명(이미지 생략): P2: 배치를 유지하면서 부모 관계 해제하기

*1: F3을 누르고 Clear Parent Keep Transform을 검색합니다. 2: Clear and Keep Transformation을 선택합니다. 루트를 제거하기 전에 메시 3개 모두에 반복하세요.*

영어 원본 이미지 설명(이미지 생략): P2: 가져온 무기에 회전과 배율 적용하기

*1: 메시 3개를 함께 6.25배로 확대한 뒤 Rotation & Scale을 적용합니다. 회전 값은 0이어야 합니다. 2: 모든 축의 배율은 1이어야 합니다.*

개별 오브젝트의 치수(Dimensions) 필드는 해당 재질 메시만 측정합니다. 무기의 크기는 전체를 합친 상태의 맨 아래부터 맨 위까지 확인하세요. 분리하기 전에 오브젝트 3개 모두 회전이 0이고 배율이 1이어야 합니다.

### P3 - 재질 연결하기 {#p3---connect-the-materials}

1. 셰이딩(Shading) 작업 공간으로 전환하세요.

2. 재질 미리 보기(Material Preview)를 선택하세요.

재질 3개는 각각 `CrescentRoseTextures`의 이미지 4개를 사용합니다.

| 이미지 | 색 공간 |
|---|---|
| `BaseColor` | **sRGB** |
| `Metallic` | `Non-Color` |
| `Roughness` | `Non-Color` |
| `Normal` | `Non-Color` |

재질마다 이미지를 하나씩 처리하세요.

1. `CrescentRoseTextures`에서 일치하는 이미지를 불러오세요.

2. 표에 따라 해당 이미지의 색 공간을 설정하세요.

3. BaseColor, Metallic, Roughness 이미지의 경우 이미지 텍스처(Image Texture)의 Color를 Principled BSDF의 해당 입력에 연결하세요.

Normal 이미지마다 다음 별도 연결 절차를 따르세요.

1. **노멀 맵(Normal Map)** 노드를 삽입하세요.

2. Normal Map 노드는 `Tangent Space`로 유지하세요.

3. Normal 이미지의 Color를 Normal Map의 Color에 연결하세요.

4. Normal Map의 Normal을 Principled BSDF의 Normal에 연결하세요.

기존 UV는 유지하세요.

영어 원본 이미지 설명(이미지 생략): P3: 검은 재질에 연결된 텍스처 맵 4개와 Tangent Space Normal Map

*1: BaseColor의 Color를 BSDF의 Base Color에 연결합니다. 2: BaseColor는 sRGB로 유지합니다. 3: 모든 데이터 맵은 Non-Color로 설정합니다. 4: Tangent Space를 사용해 Normal 이미지 > Normal Map > BSDF Normal 순서로 연결합니다.*

영어 원본 이미지 설명(이미지 생략): P3: 재질 미리 보기의 재질 3개

*1: 칼날 재질을 확인합니다. 2: 재질 미리 보기에서 빨강/검정 몸체 재질을 확인합니다. 텍스처 누락을 나타내는 분홍색이 없어야 합니다.*

검정, 칼날, 빨강 재질에 모두 같은 절차를 적용합니다. 이미지를 선택할 때마다 색 공간을 확인하세요. 색 공간은 이미지에 속하는 설정입니다. 무기가 빨강, 검정, 금속 재질로 보여야 하며, 텍스처 누락을 나타내는 분홍색이 없어야 합니다.

### P4 - 연결되지 않은 조각 분리하기 {#p4---separate-loose-pieces}

1. 재질별 메시 3개를 모두 선택하세요.

2. 뷰포트 모드 메뉴에서 <strong>편집 모드(Edit Mode)</strong>를 선택하세요.

3. 모든 지오메트리를 선택하세요.

4. <strong>메시(Mesh) > 분리(Separate) > 연결되지 않은 부분별(By Loose Parts)</strong>을 선택하세요.

5. 오브젝트 모드로 돌아가세요.

이제 메시 오브젝트가 **37**개입니다. 자동으로 붙는 숫자 접미사는 다를 수 있습니다. 위치와 모양으로 오브젝트를 구분하세요.

영어 원본 이미지 설명(이미지 생략): P4: 편집 모드에서 By Loose Parts 선택하기

*1: 편집 모드로 전환해 모든 지오메트리를 선택합니다. 2: F3을 누르고 Separate Loose를 검색한 뒤 By Loose Parts를 선택합니다.*

영어 원본 이미지 설명(이미지 생략): P4: 분리된 조각 37개

*1: 분리 후 오브젝트의 총수가 37인지 확인합니다. 2: 아웃라이너에서 모양과 위치로 조각을 선택합니다. 접미사는 다를 수 있습니다.*

### P5 - 함께 움직일 그룹 15개 합치기 {#p5---join-the-15-moving-groups}

표에는 원본의 모든 분리된 메시 조각이 나와 있습니다. 재질 이름은 외관을 설명하며, 최종 오브젝트 이름을 뜻하지는 않습니다.

| 최종 오브젝트 | 합칠 조각 | 합친 후 메시 정점 수 |
|---|---|---:|
| `BladeTip` | 검은색 끝 관절 노브와 금속 끝 가시 | 252 |
| `Blade2` | 두 번째 마디의 금속 판 2개와 빨간 덮개 2개 | 1000 |
| `Blade1` | 머리에 가장 가까운 첫 번째 마디의 금속 판 2개 | 512 |
| `HeadMount` | 검은색 뒤 블록, 위쪽 캡과 중심부, 빨간 내부 판 2개와 얇은 위쪽 덮개 2개 | 1395 |
| `PlateL` | 음의 X 쪽에 있는 빨간 머리 외부 판 1개 | 676 |
| `PlateR` | 양의 X 쪽에 있는 빨간 머리 외부 판 1개 | 676 |
| `RearSpike` | 금속 가시 칼날 2개, 빨간 피벗 캡 2개, 빨간 장착 판 2개 | 1194 |
| `Receiver` | 검은 몸체와 작은 노브, 노리쇠 위의 금속 링, 긴 빨간 하우징 | 2609 |
| `Grip` | 리시버 아래의 빨간 손잡이 블록 | 194 |
| `Magazine` | 몸체 아래의 검은 관 | 96 |
| `Bolt` | 빨간 노리쇠 실린더와 손잡이 조각 2개 | 362 |
| `Pole` | 금속 아래 자루와 빨간 칼라 | 148 |
| `ButtSpike` | 맨 아래의 금속 가시 | 110 |
| `StrutBase` | 리시버와 머리 사이의 얇은 빨간 막대 | 34 |
| `StrutRod` | 그 막대를 감싸는 홈이 있는 검은 슬리브 | 108 |

외부 판을 Blade1에 합치지 마세요. 스트럿 부품 2개를 서로 합치지 마세요. 스트럿은 이미 두 조각으로 나뉘어 있으므로 이등분할 필요가 없습니다.

칼날 끝에서 안쪽으로 진행한 다음 리시버와 자루로 넘어가세요. 함께 움직일 그룹마다 다음 절차를 따르세요.

1. 함께 움직여야 하는 조각을 선택하세요.

2. 양쪽에 짝을 이루는 조각은 뷰를 회전해 둘 다 선택하세요.

3. 합치기 전에 선택 상태를 확인하세요.

4. **오브젝트(Object) > 합치기(Join)**(Ctrl+J)를 선택하세요.

5. 아웃라이너에서 합친 오브젝트의 이름을 바꾸세요.

총 **메시 15개, 정점 9,366개**가 되어야 합니다. 2단계에서는 완성된 부품 이름과 나중에 설정할 부모 관계를 다시 정리합니다.

영어 원본 이미지 설명(이미지 생략): P5: 아웃라이너에서 이름을 지정한 이동 그룹 15개

*1: 아웃라이너에서 합친 그룹 각각의 이름을 표의 15개 이름과 일치하도록 바꿉니다.*

영어 원본 이미지 설명(이미지 생략): P5: 합치기 전에 선택한 Blade1 원본 판 2개

*1: 양쪽에 있는 금속 Blade1 판 2개를 선택합니다. 2: 오브젝트가 둘 다 선택되었는지 확인한 뒤 Join을 사용하고 결과의 이름을 Blade1로 바꿉니다.*

영어 원본 이미지 설명(이미지 생략): P5: 오브젝트 메뉴의 Join 명령

*1: 한 그룹의 조각만 선택한 뒤 Object를 엽니다. 2: Join(Ctrl+J)을 선택합니다. 이 메뉴 설명은 명령의 위치를 알려 줍니다. 위에서 설명한 조각 2개 선택 상태를 사용하세요.*

### P6 - 원점을 중앙에 배치하기 {#p6---centre-the-origins}

1. 오브젝트 모드로 전환하세요.

2. 메시 15개를 모두 선택하세요.

3. <strong>오브젝트(Object) > 원점 설정(Set Origin) > 원점을 지오메트리로(Origin to Geometry)</strong>를 선택하세요.

4. 작업 옵션의 중심(Center)을 `Bounds Center`로 설정하세요.

5. 회전이 0이고 배율이 1인지 확인하세요.

오브젝트에는 아직 부모도 아마추어도 없습니다. 이 원점 설정은 준비 과정입니다. 6단계에서는 메커니즘의 피벗을 실제 관절 위치로 옮깁니다.

영어 원본 이미지 설명(이미지 생략): P6: Object > Set Origin > Origin to Geometry

*1: Object를 엽니다. 2: Set Origin에 포인터를 올립니다. 3: Origin to Geometry를 선택하고 작업 옵션에서 Bounds Center를 설정합니다.*

영어 원본 이미지 설명(이미지 생략): P6: 중앙에 배치된 Blade1 원점과 적용된 변환

*1: 주황색 원점이 메시 중앙에 있습니다. 2: 회전이 0인지 확인합니다. 3: 배율이 1인지 확인합니다. 메커니즘 피벗은 나중에 옮깁니다.*

### P7 - 텍스처 크기를 줄이고 패킹하기 {#p7---resize-and-pack-the-textures}

**사용하는 맵은 12개**이며, 재질마다 4개입니다. 원본 JPEG를 덮어쓰지 마세요. 사용하는 맵마다 다음 절차를 따르세요.

1. 이미지 에디터에서 맵을 선택하세요.

2. <strong>이미지(Image) > 크기 조절(Resize)</strong>을 선택하세요.

3. 너비를 **1024**로 설정하세요.

4. 높이를 **1024**로 설정하세요.

5. 크기 조절을 확정하세요.

6. <strong>이미지(Image) > 패킹(Pack)</strong>을 선택하세요.

패킹하면 크기를 조절한 픽셀이 blend 파일 안에 보존됩니다. 모든 맵을 처리한 뒤 재질 미리 보기를 확인하세요.

영어 원본 이미지 설명(이미지 생략): P7: 1024 x 1024로 크기를 조절한 텍스처를 이미지 메뉴에서 패킹하기

*1: Image > Resize를 선택하고 너비와 높이에 1024를 입력합니다. 2: 결과 치수가 1024 x 1024인지 확인합니다. 3: Pack을 선택합니다. 사용하는 맵 12개 모두에 반복하세요.*

### P8 - 준비된 파일을 저장하고 다시 열기 {#p8---save-and-reopen-the-prepared-file}

1. 작업 사본을 `CrescentRose_parts.blend`로 저장하세요.

2. 그 파일을 다시 여세요.

3. 이름을 지정한 메시 15개, 해당 변환, 빨강/검정 재질을 확인하세요.

4. 오른쪽 뷰를 다시 선택하세요.

5. Home을 누르세요.

6. 1단계로 이어 가세요.

원본 텍스처 디렉터리가 없어도 맵 12개를 모두 사용할 수 있어야 합니다.

영어 원본 이미지 설명(이미지 생략): P8: 텍스처가 적용된 무기가 그대로 유지된 준비 파일을 다시 열기

*1: File을 열어 Save As로 저장한 뒤 Open으로 작업 사본을 다시 불러옵니다. 2: 이름을 지정한 메시 15개가 유지되는지 확인합니다. 3: 재질을 확인합니다. 제목 표시줄에서 다시 연 파일의 이름을 확인할 수 있습니다.*

## A. 파일 열기 {#a-open-the-file}

### 1단계 — 부품 파일 열기 {#step-1--open-the-parts-file}

1. `examples/crescent-rose/CrescentRose_parts.blend`를 여세요.

2. 뷰포트에서 재질 미리 보기 셰이딩을 선택하세요.

3. Numpad 3을 눌러 오른쪽 뷰로 전환하세요.

4. Home을 눌러 무기가 화면에 들어오게 하세요.

칼날은 왼쪽을 향하고 맨 아래 가시는 아래를 향합니다.

영어 원본 이미지 설명(이미지 생략): 1단계: 오른쪽 뷰의 부품 파일

*1: Material Preview를 클릭합니다. 2: 뷰에 Right Orthographic이 표시될 때까지 Numpad 3을 누르고, Home을 눌러 무기가 화면에 들어오게 합니다.*

**확인할 모습:** 높이 약 2 m의 빨강과 검정 낫이 보이고, 아무것도 선택되어 있지 않습니다.

### 2단계 — 부품 살펴보기 {#step-2--meet-the-parts}

아웃라이너에는 오브젝트 15개가 나열됩니다. 각각은 하나의 덩어리로 움직이는 부품입니다.

| 오브젝트 | 설명 | 붙어서 함께 움직일 대상 |
|---|---|---|
| `Receiver` | 조준경, 방아쇠, 가늠자가 달린 소총 몸체 | 리그 |
| `Grip` | 리시버 아래의 손잡이 | `Receiver` |
| `Magazine` | 원통형 탄창 | `Receiver` |
| `Bolt` | 노리쇠 | `Receiver` |
| `Pole` | 아래 자루와 칼라 | `Receiver` |
| `ButtSpike` | 맨 아래의 가시 | `Pole` |
| `HeadMount` | 칼날이 매달린 머리 블록 | `Receiver` |
| `Blade1` | 머리에 가장 가까운 첫 번째 칼날 마디 | `HeadMount` |
| `Blade2` | 두 번째 마디 | `Blade1` |
| `BladeTip` | 끝부분 | `Blade2` |
| `RearSpike` | 머리 뒤쪽의 가시 | `HeadMount` |
| `PlateL`, `PlateR` | 머리의 바깥쪽 측면 판 | `HeadMount` |
| `StrutBase` | 리시버와 머리 사이의 얇은 막대 | `Receiver` |
| `StrutRod` | 그 막대를 감싸는 홈이 있는 슬리브 | `HeadMount` |

영어 원본 이미지 설명(이미지 생략): 2단계: 아웃라이너의 부품 오브젝트 15개

*1: 칼날 마디 3개를 구분합니다. 2: 몸체, 머리, 자루의 이름을 표와 대조합니다. 3: StrutBase와 StrutRod는 별도 오브젝트로 유지하세요.*

원본 FBX를 사용한다면 위의 P1-P8을 따르세요. 그 인터페이스 조작으로 제공된 준비 파일을 만들었습니다. 저장소의 준비 스크립트에는 참고용 그룹 표가 있습니다.

### 3단계 — 메커니즘 찾기 {#step-3--find-mechanisms}

왼쪽 도구 선반(Tool Shelf)이 보이지 않는다면 다음을 수행하세요.

1. 뷰포트 위에 포인터를 놓고 T를 누르세요.

2. 영역 전환(Region Toggle) 메뉴에서 도구(Tools)를 선택하세요.

그다음 다음 절차를 따르세요.

1. 왼쪽 도구 선반에서 BoneCraft 탭을 여세요.

2. <strong>메커니즘(Mechanisms)</strong>을 펼치세요.

3. 선반의 오른쪽 가장자리를 드래그해 패널 글자가 읽히도록 넓히세요.

BoneCraft 환경설정에서 씬 속성을 표시(Show)로 설정하면 <strong>속성(Properties) > 씬(Scene)</strong>에도 같은 섹션이 나타납니다. 생략된 영어 원본 스크린샷은 도구 선반을 사용합니다.

메시가 활성 상태이고 리그가 없으면 맨 위에 <strong>선택 항목에서 부품 추가(Add Parts from Selection)</strong>가 나타납니다. 사용하기 전에 4단계 설명에 따라 부품을 모두 선택하세요. 번호가 붙은 하위 섹션은 부품을 추가한 뒤 사용할 수 있습니다.

영어 원본 이미지 설명(이미지 생략): 3단계: BoneCraft 탭의 메커니즘 섹션

*1: BoneCraft 탭을 클릭합니다. 2: Mechanisms를 펼칩니다. 3: Add Parts from Selection을 찾습니다. 사용하기 전에 메시를 선택하세요.*

## B. 부품 {#b-parts}

### 4단계 — 선택 항목에서 부품 추가 {#step-4--add-parts-from-selection}

1. 뷰포트 위에 포인터를 놓고 A를 눌러 오브젝트 15개를 모두 선택하세요.

2. <strong>선택 항목에서 부품 추가(Add Parts from Selection)</strong>를 선택하세요.

영어 원본 이미지 설명(이미지 생략): 4단계: 부품을 모두 선택한 상태의 Add Parts from Selection

*1: 뷰포트에 포인터를 놓고 A를 눌러 메시 15개를 선택합니다. 2: Add Parts from Selection을 클릭합니다.*

**확인할 모습:** 아웃라이너에 새 아마추어 “Mechanism Rig”가 나타나고 그 아래에 부품이 배치됩니다. 메시 오브젝트는 선택된 상태를 유지합니다. <strong>1. 부품(Parts)</strong>에 부품 15개가 나열됩니다. BoneCraft 탭은 이제 리그의 접을 수 있는 개요(Overview)로 시작합니다.

### 5단계 — 함께 움직일 대상 설정 {#step-5--rides-on}

부품은 자신이 붙어 있는 부품을 따라 움직입니다.

1. <strong>1. 부품(Parts)</strong>에서 `Blade1`을 선택하세요.

2. 목록 아래의 “Rides on” 메뉴를 여세요.

3. `HeadMount`를 선택하세요.

4. 2단계 표에 따라 부품마다 반복하세요.

`Receiver`는 “the rig”를 유지합니다.

영어 원본 이미지 설명(이미지 생략): 5단계: HeadMount를 따라 움직이는 Blade1

*1: Parts 목록에서 Blade1을 선택합니다. 2: Rides on을 열고 HeadMount를 선택합니다. 부모 관계 표에 따라 반복하세요.*

### 6단계 — 피벗 {#step-6--pivots}

힌지는 해당 부품의 피벗을 중심으로 회전합니다. 칼날 마디, 머리, 손잡이는 중심이 아니라 관절 위치에서 회전해야 합니다. 피벗의 좌우 방향 위치를 유지하려면 정사영 측면 뷰에서 작업하세요.

1. 목록에서 `Blade1`을 선택하세요.

2. <strong>피벗 편집(Edit Pivot)</strong>을 선택하세요.

3. 마커를 선택하세요.

4. Bforartists에서 이동하려면 Ctrl+W를 누르세요.

5. 마디와 머리가 만나는 곳을 클릭하세요.

6. <strong>피벗 적용(Apply Pivot)</strong>을 선택하세요.

7. 아래 부품에도 피벗 설정 절차를 반복하세요.

| 부품 | 피벗 위치 |
|---|---|
| `Blade2` | `Blade1`과 만나는 곳 |
| `BladeTip` | `Blade2`와 만나는 곳 |
| `HeadMount` | 스트럿과 만나는 맨 아래 지점 |
| `Grip` | 위쪽 가장자리 |
| `RearSpike` | 머리와 만나는 곳 |
| `PlateL` 및 `PlateR` | Blade1과 머리가 만나는 둥근 볼트의 중심 |
| `StrutBase` | 맨 아래 |
| `StrutRod` | 맨 위 |

생략된 영어 원본 스크린샷의 마커 위치는 참고용입니다. 몇 밀리미터 정도 차이가 나도 눈에 띄는 차이는 없습니다.

영어 원본 이미지 설명(이미지 생략): 6단계: 부품을 선택하고 Edit Pivot 클릭하기

*1: Parts에서 Blade1을 선택합니다. 2: Edit Pivot을 클릭한 뒤 다음 설명처럼 마커를 이동하고 적용합니다.*

영어 원본 이미지 설명(이미지 생략): 6단계: 관절 위치의 Blade1 피벗 마커와 Apply Pivot

*1: Ctrl+W로 피벗 마커를 칼날 관절 위치로 옮깁니다. 2: Apply Pivot을 클릭해 그 위치를 유지합니다.*

## C. 머리 {#c-the-head}

### 7단계 — 관절 추가 → 힌지 {#step-7--add-joint--hinge}

가리는 물체를 숨겨야 한다면 가이드 시작 전에 숨기세요.

<strong>관절 추가(Add Joint) → 힌지(Hinge)</strong>를 여세요. 가이드식 빌드의 헤더와 상태 표시줄에서 각 단계를 설명합니다.

영어 원본 이미지 설명(이미지 생략): 7단계: Add Joint 메뉴의 Hinge

*1: Add Joint를 엽니다. 2: Hinge를 클릭합니다. 이제 가이드식 빌드가 부품 선택을 기다립니다.*

### 8단계 — 머리 클릭하기 {#step-8--click-the-head}

헤더에 “회전할 부품을 클릭하세요(click the part that turns)”가 표시됩니다. 오른쪽 뷰에서는 외부 판이 머리를 가립니다. 원본의 원 표시 위치인 판 뒤쪽의 머리 뒷블록을 클릭하세요.

헤더에 `PlateR`이 표시된다면 다음을 수행하세요.

1. Esc를 누르세요.

2. <strong>관절 추가(Add Joint) > 힌지(Hinge)</strong>를 다시 시작하세요.

3. 머리의 더 뒤쪽을 클릭하세요.

가이드가 활성화된 동안에는 일반 키보드 단축키도 가이드에서 처리합니다.

영어 원본 이미지 설명(이미지 생략): 8단계: 머리 뒷블록 클릭하기

*1: 빨간 외부 판 뒤에 있는 HeadMount의 검은 뒷블록을 클릭합니다. 가이드에 HeadMount가 표시되는지 확인하세요.*

### 9단계 — X를 누른 뒤 Enter 누르기 {#step-9--press-x-then-enter}

헤더에서 축을 지정하라고 안내합니다.

1. X를 누르세요.

2. 반복되는 미리 보기를 확인하세요.

3. Enter를 눌러 힌지를 유지하세요.

머리가 좌우 방향 축을 중심으로 회전합니다.

영어 원본 이미지 설명(이미지 생략): 9단계: 축 지정 단계

*1: 축 안내에 따라 X를 누르고 Enter를 누릅니다. 2: 확정하기 전에 머리가 피벗을 중심으로 회전하는 모습을 확인하세요.*

**확인할 모습:** <strong>2. 관절 및 링크(Joints & Links)</strong>에 `HeadMount Hinge`가 있고, <strong>4. 컨트롤(Controls)</strong>에 해당 슬라이더가 있습니다. 이 슬라이더는 오브젝트 모드에서 사용하세요.

뷰포트의 본 핸들을 사용하려면 다음을 수행하세요.

1. 아마추어를 선택하세요.

2. 포즈 모드로 전환하세요.

### 10단계 — 제한 {#step-10--limits}

1. 목록에서 `HeadMount Hinge`를 선택하세요.

2. <strong>최솟값(Min)</strong>을 0으로 설정하세요.

3. <strong>최댓값(Max)</strong>을 120으로 설정하세요.

양수 값은 머리를 아래쪽과 뒤쪽으로 회전시킵니다. 이동 제한은 120도로 유지하세요. Rifle 시퀀스에서는 칼날 힌지와 함께 90도 목표를 사용합니다.

영어 원본 이미지 설명(이미지 생략): 10단계: Min 0, Max 120

*1: HeadMount Hinge를 선택합니다. 2: Min을 0으로 설정합니다. 3: Max를 120으로 설정합니다. 숫자를 두 번 클릭해 값을 입력한 뒤 Enter를 누르세요.*

### 11단계 — 테스트 {#step-11--test}

행의 재생 버튼을 클릭하세요. 머리가 120°까지 움직였다가 돌아오고, 원래 포즈가 복원됩니다.

영어 원본 이미지 설명(이미지 생략): 11단계: 힌지 행의 Test

*1: HeadMount Hinge 행의 작은 재생 삼각형을 클릭합니다. 왕복 움직임을 확인하세요.*

## D. 칼날 체인 {#d-the-blade-chain}

### 12단계 — 힌지 3개 더 만들기 {#step-12--three-more-hinges}

`Blade1`, `Blade2`, `BladeTip` 각각에 7~10단계를 반복하세요.

1. <strong>관절 추가(Add Joint) → 힌지(Hinge)</strong>를 여세요.

2. 마디를 클릭하세요.

3. X를 누르세요.

4. Enter를 누르세요.

5. <strong>최댓값(Max)</strong>을 120으로 설정하세요.

각 마디는 이전 마디를 따라 움직입니다. 힌지 3개가 하나의 체인을 이룹니다.

영어 원본 이미지 설명(이미지 생략): 12단계: 목록의 칼날 마디 힌지 3개와 별도의 머리 힌지

*1: Blade1, Blade2, BladeTip의 칼날 힌지를 각각 만들고 선택합니다. 2: 각 힌지의 Max를 120으로 설정하고 축은 X를 사용하세요.*

### 13단계 — 체인 시험하기 {#step-13--try-the-chain}

1. 공간을 확보하려면 <strong>2. 관절 및 링크(Joints & Links)</strong>를 접으세요.

2. <strong>4. 컨트롤(Controls)</strong>을 펼치세요.

3. 오브젝트 모드에서 `Blade1 Hinge`, `Blade2 Hinge`, `BladeTip Hinge`를 각각 60도로 설정하세요.

각 값은 다음과 같이 입력하세요.

1. 숫자 필드를 두 번 클릭하세요.

2. Ctrl+A를 누르세요.

3. 값을 입력하세요.

4. Enter를 누르세요.

뒤쪽 마디가 앞쪽 마디와 함께 움직이며 체인이 말립니다. 계속하기 전에 세 값을 모두 0으로 되돌리세요.

영어 원본 이미지 설명(이미지 생략): 13단계: 컨트롤에서 칼날 힌지 3개를 60도로 설정한 상태

*1: 칼날 슬라이더 3개에 각각 60을 입력합니다. 2: 체인이 함께 말리는지 확인합니다. 슬라이더 3개를 모두 0으로 되돌리세요.*

## E. 측면 판과 스트럿 {#e-plates-and-strut}

### 14단계 — 측면 판에 힌지 만들기 {#step-14--hinges-on-the-plates}

오른쪽 뷰에서는 `PlateL`이 머리 뒤에 가려집니다.

1. 같은 절차로 `PlateR`에 힌지를 추가하세요.

2. <strong>최댓값(Max)</strong>을 30으로 설정하세요.

3. Ctrl+Numpad 3을 눌러 왼쪽 뷰로 전환하세요.

4. `PlateL`에 힌지를 추가하세요.

5. <strong>최댓값(Max)</strong>을 30으로 설정하세요.

6. Numpad 3을 눌러 오른쪽 뷰로 돌아가세요.

영어 원본 이미지 설명(이미지 생략): 14단계: PlateL Hinge와 PlateR Hinge

*1: PlateR과 PlateL 힌지를 모두 만듭니다. PlateL은 반대쪽 측면 뷰에서 선택하세요. 2: 각 Max를 30으로 설정합니다.*

### 15단계 — 링크 추가 → 추종 {#step-15--add-link--follow}

핸들 하나로 양쪽 판을 움직여야 합니다. 가이드를 시작하기 전에 뷰를 설정하세요.

1. Numpad 1을 눌러 정면 뷰로 전환하세요.

2. `Blade2`를 선택하세요.

3. F3 > Frame Selected로 머리를 가까이 보세요.

바깥쪽 판 2개가 왼쪽과 오른쪽 가장자리에 나타납니다.

1. <strong>링크 추가(Add Link) > 추종(Follow)</strong>을 여세요.

2. 왼쪽 가장자리의 `PlateL`을 선행 부품으로 클릭하세요.

3. 오른쪽 가장자리의 `PlateR`을 따라가는 부품으로 클릭하세요.

4. Enter를 누르세요.

영어 원본 이미지 설명(이미지 생략): 15단계: 추종 링크를 지정할 수 있도록 정면 뷰에서 양쪽 외부 판을 보이게 하기

*1: 선행 부품인 PlateL을 먼저 클릭합니다. 2: 따라가는 부품인 PlateR을 두 번째로 클릭합니다. Enter를 누르세요.*

### 16단계 — 범위 {#step-16--ranges}

1. 새 추종 링크를 선택하세요.

2. 자동으로 채워진 **원본 범위(Source Range)** 0…30과 **대상 범위(Target Range)** 0…30을 확인하세요.

3. <strong>이름(Name)</strong>에서 링크 이름을 `PlateR Follow`로 바꾸세요.

영어 원본 이미지 설명(이미지 생략): 16단계: Source Range와 Target Range

*1: 링크 이름을 PlateR Follow로 지정합니다. 2: Source Range가 0~30인지 확인합니다. 3: Target Range가 0~30인지 확인합니다.*

### 17단계 — 링크 추가 → 피스톤 {#step-17--add-link--piston}

머리가 접히는 동안 스트럿은 리시버와 머리 사이를 향해야 합니다. 가이드가 활성화된 동안에는 뷰 탐색 단축키도 가이드에서 처리합니다. 가이드를 시작하기 전에 다음을 수행하세요.

1. Numpad 3을 눌러 오른쪽 뷰로 전환하세요.

2. 아웃라이너에서 `StrutRod`를 선택하세요.

3. F3 > Frame Selected로 확대해 보세요.

4. <strong>링크 추가(Add Link) > 피스톤(Piston)</strong>을 여세요.

영어 원본 이미지 설명(이미지 생략): 17단계: Add Link 메뉴의 Piston

*1: StrutRod가 화면에 들어오게 한 뒤 Add Link를 엽니다. 2: Piston을 선택합니다. 가이드에서 먼저 실린더를 지정하라고 안내합니다.*

### 18단계 — 실린더와 로드 {#step-18--the-cylinder-and-the-rod}

가이드의 실린더/로드 역할은 링크의 양 끝을 설명합니다. 모델의 오브젝트 이름은 원래 조각을 설명합니다. `StrutBase`는 슬리브의 홈 사이로 드러난 얇은 빨간 막대입니다. `StrutRod`는 검은 슬리브입니다.

1. 확대된 뷰에서 `StrutBase`를 실린더 부품으로 먼저 클릭하세요.

2. `StrutRod`를 로드 부품으로 두 번째로 클릭하세요.

3. Enter를 눌러 확정하세요.

4. 링크 이름을 `Head Strut`으로 바꾸세요.

5. <strong>늘이기(Stretch)</strong>는 비활성 상태로 유지하세요.

1. 컨트롤에서 `HeadMount Hinge` 값을 바꾸세요.

2. 스트럿을 확인하세요.

3. 값을 0으로 되돌리세요.

**확인할 모습:** 스트럿이 머리를 따라 움직입니다. 두 부품이 서로를 향합니다.

영어 원본 이미지 설명(이미지 생략): 18단계: 드러난 빨간 실린더, 이어서 검은 슬리브를 지정하는 피스톤 가이드

*1: 드러난 빨간 StrutBase를 먼저 클릭합니다. 2: 검은 StrutRod 슬리브를 두 번째로 클릭합니다. Enter를 누르세요.*

영어 원본 이미지 설명(이미지 생략): 18단계: Stretch를 끈 Head Strut 설정

*1: 링크 이름을 Head Strut으로 바꿉니다. 2: Stretch는 선택하지 않은 상태로 두세요. 그런 다음 HeadMount Hinge를 시험하고 0으로 되돌립니다.*

## F. 소총 {#f-the-rifle}

### 19단계 — 손잡이와 뒤쪽 가시에 힌지 만들기 {#step-19--grip-and-rear-spike-hinges}

`Grip`과 `RearSpike` 각각에 다음을 수행하세요.

1. <strong>관절 추가(Add Joint) → 힌지(Hinge)</strong>를 여세요.

2. 부품을 클릭하세요.

3. X를 누르세요.

4. Enter를 누르세요.

5. <strong>최솟값(Min)</strong>을 0으로 설정하세요.

6. <strong>최댓값(Max)</strong>을 90으로 설정하세요.

그다음 다음 절차를 따르세요.

1. 목록에서 `RearSpike Hinge`를 선택하세요.

2. 축 X(Axis X)를 -1로 설정하세요.

3. Y와 Z는 0으로 유지하세요.

4. Grip은 양의 X로 유지하세요.

5. 관절 목록에 `Grip Hinge`와 `RearSpike Hinge`가 나타나는지 확인하세요.

RearSpike의 X축을 반대로 하면 Compact 형태에서 접힌 머리 쪽으로 접힙니다. 이 컨트롤은 25단계의 수납 형태를 위해 손잡이와 뒤쪽 가시를 접습니다.

영어 원본 이미지 설명(이미지 생략): 19단계: Grip Hinge, Max 90

*1: Grip Hinge를 선택합니다. 2: Axis X를 1, Y와 Z를 0으로 유지합니다. 3: Max를 90으로 설정하고 Min은 0으로 유지하세요.*

영어 원본 이미지 설명(이미지 생략): 19단계: Axis X -1, Max 90의 RearSpike Hinge

*1: RearSpike Hinge를 선택합니다. 2: Axis X를 -1로 설정합니다. 3: Max를 90으로 설정하고 Min은 0으로 유지하세요.*

### 20단계 — 탄창과 노리쇠에 슬라이드 만들기 {#step-20--magazine-and-bolt-slides}

먼저 `Magazine`에, 다음으로 `Bolt`에 다음을 수행하세요.

1. <strong>관절 추가(Add Joint) → 슬라이드(Slide)</strong>를 여세요.

2. 부품을 클릭하세요.

3. Z를 누르세요.

4. Enter를 누르세요.

5. <strong>최댓값(Max)</strong>을 Magazine은 0.04, Bolt는 0.06으로 설정하세요.

슬라이드는 씬 단위를 사용합니다. 0.06은 6 cm입니다.

영어 원본 이미지 설명(이미지 생략): 20단계: Z축, Max 0.04의 Magazine Slide

*1: Add Joint > Slide를 사용한 뒤 Magazine Slide를 선택합니다. 2: Z축을 사용합니다(Z = 1, X = Y = 0). 3: Max를 0.04로 설정하고 Min은 0으로 유지하세요.*

영어 원본 이미지 설명(이미지 생략): 20단계: Z축, Max 0.06의 Bolt Slide

*1: Add Joint > Slide를 사용한 뒤 Bolt Slide를 선택합니다. 2: Z축을 사용합니다(Z = 1, X = Y = 0). 3: Max를 0.06으로 설정하고 Min은 0으로 유지하세요.*

### 21단계 — 자루 슬라이드 {#step-21--pole-slide}

1. <strong>관절 추가(Add Joint) → 슬라이드(Slide)</strong>를 여세요.

2. `Pole`을 클릭하세요.

3. Z를 누르세요.

4. Enter를 누르세요.

5. <strong>최댓값(Max)</strong>을 0.6으로 설정하세요.

6. <strong>4. 컨트롤(Controls)</strong>에서 `Pole Slide`를 0.6으로 설정하세요.

7. 안으로 들어간 자루를 확인하세요.

8. 컨트롤을 0으로 되돌리세요.

양수 값은 자루를 위로 움직여 리시버 안으로 넣습니다.

영어 원본 이미지 설명(이미지 생략): 21단계: Z축, Max 0.6의 Pole Slide 설정

*1: Add Joint > Slide를 사용한 뒤 Pole Slide를 선택합니다. 2: Z축을 사용합니다(Z = 1, X = Y = 0). 3: Max를 0.6으로 설정하고 Min은 0으로 유지하세요.*

### 22단계 — 자루 텔레스코프 {#step-22--pole-telescope}

1. <strong>관절 추가(Add Joint) → 텔레스코프(Telescope)</strong>를 여세요.

2. `Pole`을 베이스로 클릭하세요.

3. `ButtSpike`를 마디로 클릭하세요.

4. Enter를 누르세요.

5. Z를 누르세요.

6. Enter를 누르세요.

7. <strong>길이(Length)</strong>를 0.2로 설정하세요.

8. 별도의 컨트롤을 시험하세요.

9. 컨트롤을 0으로 되돌리세요.

이 컨트롤은 가시를 양의 Z 방향으로 최대 20 cm 올려 이 모델의 자루 안으로 넣습니다.

영어 원본 이미지 설명(이미지 생략): 22단계: Pole을 베이스, ButtSpike를 마디로 지정하는 텔레스코프 가이드

*1: Pole을 베이스로 클릭합니다. 2: ButtSpike를 마디로 클릭합니다. Enter, Z, Enter 순서로 누르세요.*

영어 원본 이미지 설명(이미지 생략): 22단계: Z축, Length 0.2의 Pole Telescope 설정

*1: Pole Telescope를 선택합니다. 2: 축이 Z인지 확인합니다. 3: Length에 0.2를 입력하고 컨트롤을 시험한 뒤 0으로 되돌립니다.*

## G. 시퀀스 {#g-sequences}

### 23단계 — 시퀀스 추가 {#step-23--add-sequence}

1. <strong>3. 시퀀스(Sequences)</strong>에서 <strong>시퀀스 추가(Add Sequence)</strong>를 선택하세요.

2. 목록에서 시퀀스 이름을 두 번 클릭하세요.

3. `Scythe to Rifle`을 입력하세요.

4. Enter를 누르세요.

영어 원본 이미지 설명(이미지 생략): 23단계: Add Sequence

*1: Add Sequence를 클릭합니다. 2: 새 이름을 두 번 클릭해 Scythe to Rifle을 입력합니다. Enter를 누르세요.*

### 24단계 — 동작 그룹 기록하기 {#step-24--record-a-motion-group}

1. <strong>슬라이더를 끝으로 이동(Move Slider to End)</strong>을 선택하세요.

시퀀스 슬라이더가 `100%`로 이동합니다. 버튼이 Record Step 1로 바뀝니다.

1. <strong>4. 컨트롤(Controls)</strong>에서 `BladeTip Hinge`를 70으로 설정하세요.

2. `Blade2 Hinge`를 120으로 설정하세요.

3. Record Step 1을 선택하세요.

움직인 핸들마다 하나씩, 대상 항목 2개가 저장됩니다. 두 관절 슬라이더는 모두 0으로 되돌아갑니다.

영어 원본 이미지 설명(이미지 생략): 24단계: 첫 그룹의 포즈를 만들기 전 Move Slider to End

*1: Move Slider to End를 한 번 클릭합니다. 버튼이 Record Step 1로 바뀝니다.*

영어 원본 이미지 설명(이미지 생략): 24단계: Blade2 120도, BladeTip 70도에서 Record Step 1

*1: Blade2 = 120과 BladeTip = 70을 입력합니다. 2: Record Step 1을 클릭합니다. 두 대상이 저장되고 관절 슬라이더가 초기화됩니다.*

*나머지 동작 그룹.* 캡처할 때마다 기록 준비 상태가 유지됩니다. 준비 상태를 다시 켜지 마세요. 아래의 나머지 그룹마다 다음을 수행하세요.

1. 표에 나온 값으로 해당 그룹의 핸들 포즈를 설정하세요.

2. 표시된 Record Step 버튼을 선택하세요.

| 동작 그룹 | 이 핸들의 포즈 설정 | 앞 그룹들을 기록한 뒤의 기록 버튼 |
|---|---|---|
| 2 | `Blade1 Hinge` 10 및 `PlateL Hinge` 30 | Record Step 3 |
| 3 | `HeadMount Hinge` 90 | Record Step 5 |
| 4 | `Pole Slide` 0.6 | Record Step 6 |

버튼 번호는 저장된 대상 항목 수에 1을 더한 값입니다. 핸들 2개를 기록하면 번호가 2만큼 증가합니다. 기록 버튼을 클릭한 횟수를 세는 것은 아닙니다. 동작 그룹 4개로 대상 항목 6개가 만들어집니다. 움직일 핸들을 바꿨다면 화면에 표시되는 버튼 번호를 따르세요.

### 25단계 — 단계 설정 {#step-25--the-steps}

기록된 대상마다 시퀀스 아래에 항목이 생깁니다. 각 항목에는 **대상(Target)**, 이징, **시작(Start)**, <strong>끝(End)</strong>이 표시됩니다. Start/End 필드는 0-1을 사용하고, 컨트롤 슬라이더는 0-100%를 표시합니다.

| 동작 | 시작 | 끝 |
|---|---:|---:|
| 칼날이 먼저 접힘 | 0 | 0.25 |
| 측면 판과 첫 번째 마디가 뒤따름 | 0.25 | 0.5 |
| 머리가 세 번째로 접힘 | 0.5 | 0.8 |
| 자루가 마지막에 움직임 | 0.8 | 1 |

같은 동작 그룹에 속한 항목은 Start와 End 값을 동일하게 사용합니다. `Scythe to Rifle`의 각 항목에 다음을 수행하세요.

1. <strong>시작(Start)</strong>을 표에서 해당 동작 그룹의 시작 값으로 설정하세요.

2. <strong>끝(End)</strong>을 표에서 해당 동작 그룹의 끝 값으로 설정하세요.

3. 항목은 `Ease In Out`으로 유지하세요.

각 단계의 구간 전에는 시작 값을 유지하고, 구간 후에는 끝 값을 유지합니다.

시퀀스 하나를 완성할 때마다 캡처 배너에서 <strong>취소(Cancel)</strong>를 선택하세요. Cancel은 기록을 끝내고 저장된 항목은 유지하며, 해당 시퀀스 슬라이더를 0으로 되돌립니다. 기록 준비 상태에서는 겹침 경고가 다음에 기록할 구간을 설명합니다. 빈 그룹을 추가로 만들지 마세요.

두 번째 시퀀스에는 24단계의 기록 절차를 사용하세요.

1. `Rifle to Compact`를 추가하세요.

2. <strong>슬라이더를 끝으로 이동(Move Slider to End)</strong>을 한 번 선택해 기록 준비 상태로 만드세요.

3. 첫 그룹에서는 `Grip Hinge`를 90으로 설정하세요.

4. `RearSpike Hinge`를 90으로 설정하세요.

5. Record Step 1을 선택하세요.

6. 첫 그룹의 각 항목에 다음을 수행하세요.

    1. <strong>시작(Start)</strong>을 0으로 설정하세요.

    2. <strong>끝(End)</strong>을 0.5로 설정하세요.

7. 두 번째 그룹에서는 `Magazine Slide`를 0.04로 설정하세요.

8. `Bolt Slide`를 0.06으로 설정하세요.

9. Record Step 3을 선택하세요.

10. 두 번째 그룹의 각 항목에 다음을 수행하세요.

    1. <strong>시작(Start)</strong>을 0.5로 설정하세요.

    2. <strong>끝(End)</strong>을 1로 설정하세요.

11. 각 항목은 `Ease In Out`으로 유지하세요.

12. 캡처 배너에서 <strong>취소(Cancel)</strong>를 선택해 기록을 끝내세요.

그룹마다 항목 2개가 만들어집니다. 두 번째 그룹에서는 기록 버튼이 Record Step 1에서 Record Step 3으로 바뀝니다.

영어 원본 이미지 설명(이미지 생략): 25단계: Scythe to Rifle의 대상 6개와 시간 구간

*1: Target은 기록된 관절 값입니다. 2: Ease In Out을 선택합니다. 3: Start를 입력합니다. 4: End를 입력합니다. 설명된 값을 사용해 항목 6개 모두에 이 필드를 반복해서 설정하세요.*

영어 원본 이미지 설명(이미지 생략): 25단계: Rifle to Compact의 대상 4개와 시간 구간

*1: Grip과 RearSpike는 Target 90, Start 0, End 0.5를 사용합니다. 2: Magazine과 Bolt는 0.04 / 0.06, Start 0.5, End 1을 사용합니다. Ease In Out은 유지하세요.*

영어 원본 이미지 설명(이미지 생략): 25단계: 캡처 배너의 Cancel로 기록 끝내기

*1: 시퀀스를 완성한 뒤 이 캡처 배너에서 Cancel을 클릭해 기록을 끝냅니다. 항목은 유지되고 시퀀스는 0으로 돌아갑니다.*

### 26단계 — 시퀀스 테스트 {#step-26--test-the-sequence}

단계 기록 버튼 옆의 <strong>테스트(Test)</strong>는 슬라이더를 0%에서 100%로, 다시 0%로 움직입니다. 그런 다음 테스트 전의 슬라이더 값으로 복원합니다.

1. Scythe 형태에서 `Scythe to Rifle`의 <strong>테스트(Test)</strong>를 선택하세요.

2. 첫 시퀀스가 100%인 상태에서 `Rifle to Compact`의 <strong>테스트(Test)</strong>를 선택하세요.

3. 테스트 후 두 시퀀스를 모두 0%로 되돌리세요.

영어 원본 이미지 설명(이미지 생략): 26단계: 접히는 동안의 시퀀스 Test 버튼

*1: 기록 버튼 옆의 Test를 클릭합니다. 2: 접혔다가 돌아오는 모습을 확인합니다. Scythe to Rifle이 100%인 상태에서 Compact를 테스트하세요.*

**확인할 모습:** 칼날이 말리고, 측면 판이 닫히고, 머리가 리시버를 따라 아래로 접히며, 자루가 위로 들어갑니다. 그런 다음 모두 원래대로 돌아갑니다.

## H. 폼 {#h-forms}

### 27단계 — 폼 저장 {#step-27--save-form}

개별 관절 슬라이더는 모두 0으로 유지하세요. 움직임은 시퀀스가 만듭니다. 선택한 시퀀스를 끝으로 설정하면 기록 준비 상태가 다시 켜질 수 있습니다. 폼을 저장해도 단계가 추가로 기록되지는 않습니다. 다른 대상을 추가하려는 경우가 아니라면 Record Step을 선택하지 마세요.

<strong>4. 컨트롤(Controls)</strong>에서 다음을 수행하세요.

1. 모든 슬라이더가 0인 상태에서 <strong>폼 저장(Save Form)</strong>을 선택하세요.

2. 새 목록 항목을 두 번 클릭하세요.

3. 이름을 `Scythe`로 지정하세요.

4. `Scythe to Rifle`을 `100%`로 설정하세요.

5. <strong>폼 저장(Save Form)</strong>을 선택하세요.

6. 같은 이름 지정 절차로 새 항목의 이름을 `Rifle`로 지정하세요.

7. `Rifle to Compact`도 `100%`로 설정하세요.

8. <strong>폼 저장(Save Form)</strong>을 선택하세요.

9. 새 항목의 이름을 `Compact`로 지정하세요.

기록 준비 상태를 해제하려면 다음을 수행하세요.

1. 폼 목록에서 `Scythe`를 선택하세요.

2. <strong>폼으로 이동(Go to Form)</strong>을 선택하세요.

두 시퀀스가 모두 0으로 돌아갑니다. Rifle이나 Compact로 이동하면 선택된 시퀀스가 100%이므로 기록 준비 상태가 다시 켜질 수 있습니다.

영어 원본 이미지 설명(이미지 생략): 27단계: 모든 슬라이더가 0인 상태의 Save Form

*1: 두 시퀀스와 모든 관절이 0인 상태로 시작합니다. 2: Save Form을 클릭합니다. 3: 새 목록 항목을 두 번 클릭해 Scythe로 이름을 지정합니다. Rifle과 Compact에도 반복하세요.*

### 28단계 — 폼으로 이동 {#step-28--go-to-form}

1. 목록에서 폼을 선택하세요.

2. <strong>폼으로 이동(Go to Form)</strong>을 선택하세요.

<strong>이동 및 키 삽입(Go and Key)</strong>은 현재 프레임에 모든 컨트롤의 키도 삽입합니다. 이 키로 변형 동작을 애니메이션화합니다.

영어 원본 이미지 설명(이미지 생략): 28단계: Rifle을 선택한 상태의 Go to Form

*1: 저장한 폼을 선택합니다. 2: Go to Form을 클릭합니다. Go and Key는 애니메이션 키도 삽입합니다.*

### 29단계 — 소총 {#step-29--the-rifle}

영어 원본 이미지 설명(이미지 생략): 29단계: Rifle 폼

*1: Rifle을 선택합니다. 2: Go to Form을 클릭합니다. 3: 시퀀스 백분율이 원본 이미지에 나온 포즈와 맞는지 확인합니다.*

### 30단계 — 수납 형태 {#step-30--compact}

영어 원본 이미지 설명(이미지 생략): 30단계: Compact 폼

*1: Compact를 선택합니다. 2: Go to Form을 클릭합니다. 3: 시퀀스 백분율이 원본 이미지에 나온 포즈와 맞는지 확인합니다.*

1. `Scythe`로 돌아가세요.

2. 파일을 저장하세요.

## 완성한 구성 {#what-you-built}

| 레코드 | 본 | 기능 |
|---|---|---|
| 부품 15개 | `MCH-<part>` 및 `DEF-<part>` | 각 부품의 메시는 해당 `DEF-` 본을 부모로 사용 |
| 힌지 8개, 슬라이드 3개, 텔레스코프 1개 | `CTRL-<part>` | 핸들로 사용되며, <strong>4. 컨트롤(Controls)</strong>의 슬라이더에 그 값이 표시됨 |
| 피스톤 1개 | `MCH-<part>-aim` 및 `MCH-<part>-target` | 스트럿의 두 부품이 서로를 향하게 유지 |
| 추종 링크 1개 | 없음 | `PlateR`이 `PlateL`과 함께 회전 |
| 시퀀스 2개 | `CTRL-SEQ-<name>` | 각각 슬라이더 1개 |
| 폼 3개 | 없음 | 저장된 슬라이더 값 |

갱신된 예제는 보고된 문제 없이 리그 검사기(Rig Validator)를 통과했습니다. Auto Run Python Scripts를 끈 상태에서 개별 컨트롤 모두와 폼 3개를 포함한 다시 불러오기 검사도 통과했습니다.

## 다음에 해 볼 작업 {#try-next}

추종 링크의 매핑을 편집하려면 다음을 수행하세요.

1. `PlateR Follow`에서 <strong>커브(Curve)</strong>를 활성화하세요.

2. 그래프 에디터에서 매핑 모양을 바꾸세요.

다른 포즈를 만들려면 칼날을 접고 머리를 올린 상태에서 네 번째 폼인 `Carry`를 저장하세요.

애니메이션을 만들고 내보내려면 다음을 수행하세요.

1. <strong>이동 및 키 삽입(Go and Key)</strong>으로 여러 프레임에 폼의 키를 삽입하세요.

2. `DEF-` 본을 내보내세요([VRChat 도구](08-vrchat.md) 참고).

## 기어 링크 {#gear-link}

Crescent Rose에는 맞물리는 기어 쌍이 없으므로 이 리그에는 기어 링크가 없습니다. 기어 링크는 다른 힌지가 회전할 때 톱니 수 비율에 따라 한 힌지를 회전시킵니다. 크랭크와 바퀴, 또는 회전을 슬라이드 이동으로 바꾸는 랙이 그 예입니다. [기어 링크](07-mechanisms.md#gear-link)를 참고하세요.

## 제작자 및 이용 조건 {#credits}

Crescent Rose 모델 제작자: amandangm, https://sketchfab.com/3d-models/crescent-rose-dcb6bfbb3b824c01a182fa131fe35824, CC BY 4.0. 이 튜토리얼에서는 모델을 분리하고 크기를 조절한 뒤 리깅한 버전을 사용합니다. Crescent Rose는 Rooster Teeth Productions의 디자인입니다. 이 자산은 팬이 만든 튜토리얼용 자산입니다.

[← 목차](index.md)
