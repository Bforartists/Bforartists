# CATS 도구 {#cats-tools}

[← 목차](index.md)

오른쪽 사이드바의 **CATS → CATS**에 있습니다. **N**으로 사이드바를 표시하세요.

Preferences → Tabs → Scene Properties → Show가 켜져 있으면 **Properties → Scene**에도 나타납니다. CATS 뷰포트 스위치와 Scene Properties 스위치는 각 사본을 독립적으로 제어합니다.

도구는 [CATS 파이프라인](04-cats-pipeline.md)을 따릅니다. 섹션 위쪽에서 처리할 아마츄어를 선택하세요.

9.1의 여러 패널은 작업 버튼 아래 접이식 영역에 선택적 설정을 둡니다. 필수 입력은 버튼 위에 남으며 Fix Model 정리 스위치, Translate Bone Names 소스 언어, 입 모양 및 눈 본 등이 해당합니다.

Adjust Last Operation을 쓰는 본 도구는 즉시 실행됩니다. 실행 후 그곳에서 옵션을 조정하세요. 버튼이나 옵션에 포인터를 올려 툴팁을 읽으세요.

---

## 모델 정리 {#fix-model}

**파이프라인 단계:** 1(권장 정리 검토)

**기능:** 선택한 메시에서 켜진 정리 작업을 실행합니다. 깨끗한 아바타에는 필요하지 않을 수 있습니다.

**옵션(각각 끌 수 있음):**

- 모디파이어 적용
- Remove doubles — 같은 위치의 중복 정점 병합
- 노멀 재계산 — 뒤집힌 표면 수정
- 느슨한 지오메트리 제거 — 몸에 붙어 있지 않은 면
- 빈 버텍스 그룹 제거
- 제로 웨이트 본 제거 — 정점을 전혀 움직이지 않는 본
- VRChat이 사용할 수 없는 컨스트레인트와 강체 제거

1. 정리 옵션을 검토하세요.

2. 아바타에 필요한 작업만 켜세요.

3. 파일 체크포인트를 저장하세요.

4. **Fix Model**로 선택한 메시에서 켜진 작업을 한 번에 실행하세요.

5. 계속하기 전에 결과를 확인하세요.

영문 원본 이미지 설명(이미지 생략): Fix Model 옵션과 작업. 첫 파이프라인 단계 전에 선택을 검토하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Fix Model 옵션과 작업. 첫 파이프라인 단계 전에 선택을 검토하세요.*

---

## 본 이름 번역 {#translate-bone-names}

**기능:** 알려진 본 이름의 내장 사전으로 오프라인에서 영어 VRChat 이름으로 번역합니다.

**지원 언어:** 일본어(日本語, MMD와 여러 커뮤니티 모델에 가장 흔함), 중국어(中文), 한국어, 포르투갈어(Português), 스페인어(Español), 프랑스어(Français).

**주요 컨트롤:**

1. 소스 이름의 **Language**를 선택하세요.

2. **Translate Bone Names**를 선택하세요.

Language는 인터페이스가 아니라 모델의 본 이름 언어입니다. 일본어 MMD 모델이면 Bforartists UI 언어와 관계없이 Japanese를 선택하세요.

영문 원본 이미지 설명(이미지 생략): Translate Bone Names 전에 소스 이름 언어를 선택하세요. 이 예제는 아직 일치하는 이름을 감지하지 않았습니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Translate Bone Names 전에 소스 이름 언어를 선택하세요. 이 예제는 아직 일치하는 이름을 감지하지 않았습니다.*

---

## 메시 결합 {#join-meshes}

**기능:** 아바타의 메시 오브젝트를 하나로 합칩니다. VRChat은 아바타당 메시 하나일 때 성능이 가장 좋습니다. 소스 셰이프 키가 서로 다르면 CATS가 누락된 키를 중립 모양으로 채워 일관된 한 세트를 만듭니다.

**주요 컨트롤:** 메시 목록, 새로 고침 버튼, **Join Meshes**.

**사용 시점:** 의상과 액세서리를 부착하고 웨이트를 지정한 뒤.

1. 소스 메시를 확인하세요.

2. 결합 전에 소스 메시에 필요한 정리 작업을 선택하세요.

3. 파일 체크포인트를 저장하세요.

4. 목록 갱신이 필요하면 옆의 버튼으로 새로 고치세요.

5. **Join Meshes**를 선택하세요.

6. 결합된 메시, 셰이프 키 및 웨이트를 확인하세요.

영문 원본 이미지 설명(이미지 생략): Refresh Mesh List 후 폴리곤 여섯 개인 선택 메시 하나가 목록에 있습니다. Join Meshes 전에 검토하세요.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. Refresh Mesh List 후 폴리곤 여섯 개인 선택 메시 하나가 목록에 있습니다. Join Meshes 전에 검토하세요.*

---

## 머티리얼 아틀라스 결합기 {#material-atlas-combiner}

**파이프라인 단계:** 2(선택)

**기능:** 여러 머티리얼을 하나의 텍스처 시트(아틀라스)로 베이크합니다. 머티리얼 수가 적으면 VRChat 성능 등급이 좋아집니다.

**위치:** **CATS → CATS → Material Atlas**. **1. Choose Target**, **2. Choose Materials and Textures**, **3. Bake and Review**로 나뉩니다.

### 분석과 소스 선택 {#analyze-and-choose-sources}

영문 원본 이미지 설명(이미지 생략): 분석 전의 Material Atlas. 대상을 선택하고 백업을 유지한 뒤 Analyze Materials를 사용하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. 분석 전의 Material Atlas. 대상을 선택하고 백업을 유지한 뒤 Analyze Materials를 사용하세요.*

**Target**은 **Active Avatar**, **Selected Meshes**, **Visible Scene**을 제공합니다. Active Avatar는 활성 아마츄어의 자식 메시를 사용하며 활성 아마츄어가 없으면 활성 메시를 사용합니다. Visible Scene은 보이는 메시를 사용합니다. 특정 집합에는 Selected Meshes를 선택하세요.

1. 파일 사본을 저장하세요.

2. **Target**에서 필요한 범위를 선택하세요.

3. **Preserve Backup Duplicate**를 켜 두세요.

4. **Analyze Materials**를 선택하세요.

5. 아틀라스 그룹을 선택하세요.

6. 그 그룹을 베이크하려면 확인란을 켜세요.

7. **Materials to combine**에서 포함할 머티리얼을 켜세요.

8. **Texture images**에서 포함할 이미지를 켜세요.

9. 켜진 그룹마다 소스 검토를 반복하세요.

**Analyze Materials**는 소스 목록을 만듭니다. 그룹이 생기면 이름이 **Refresh Analysis**로 바뀝니다. 새로 고치면 목록과 선택을 다시 만들므로 재검토하세요.

각 목록에는 **Select All**, **Deselect All**이 있습니다. 활성 그룹의 해당 목록 **Include** 확인란만 바꾸며 강조된 행을 바꾸지 않습니다. 머티리얼과 텍스처 목록은 독립적이고 다른 그룹의 선택도 유지합니다. 누락된 텍스처는 선택하지 않으며 일괄 선택으로 꺼진 그룹을 켜지 않습니다.

같은 작업은 **Object → Atlas Source Selection**에도 있습니다. 소스 선택을 바꾸기 전에 보류 중인 아틀라스 미리보기를 Accept 또는 Revert하세요.

켜진 그룹에는 머티리얼이 두 개 이상 선택되어야 합니다. 꺼진 그룹과 단일 머티리얼 그룹은 건너뜁니다. 제외된 머티리얼 슬롯과 공유 참조는 별도로 유지됩니다. 이미지 제외는 해당 이미지의 베이크만 생략하며 머티리얼 전체를 제외하지는 않습니다.

투명 및 발광 머티리얼은 별도 그룹으로 시작합니다. 그리기 순서를 보존하기 위해 Alpha Blend 그룹은 처음에 꺼져 있습니다. 순서 변경 가능성을 수용한다면 켜세요.

**Source Details**는 처음에 꺼져 있습니다. 켜면 메시 진단, 셰이프 키와 UV 경고, 머티리얼 크기, 텍스처 역할 및 중복 소스 그룹을 볼 수 있습니다. 머티리얼의 **Override Size**는 크기 선택을 표시합니다. 사용자 크기는 **Width**, **Height**, 색상 전용 머티리얼은 **Fallback** 크기를 사용합니다.

그룹 목록에는 **Resolution**과 추가/제거 컨트롤이 있습니다. **Add Group**, **Remove Group**은 그룹만 관리하며 자체적으로 베이크하지 않습니다.

영문 원본 이미지 설명(이미지 생략): 예제 메시 두 개의 분석 소스. UV 경고와 함께 그룹, 머티리얼 및 이미지 확인란을 검토하세요.

*BoneCraft 9.2.19 후보 버전. 기본 Bforartists 5.2.3 테스트 빌드, Blender 5.4 Alpha. 예제 메시 두 개의 분석 소스. UV 경고와 함께 그룹, 머티리얼 및 이미지 확인란을 검토하세요.*

### 베이크와 검토 {#bake-and-review}

1. 소스 목록 검토 후 **Bake Checked Sources**를 선택하세요.

2. 사전 검사 요약을 읽으세요.

3. 보고된 소스나 설정 오류를 수정하세요.

4. 계획된 변경이 맞으면 베이크를 확인하세요.

5. 아틀라스, 투명도, 셰이프 키 및 내보낸 UV 채널을 확인하세요.

6. 결과가 맞으면 **Accept — Delete Backup**을 선택하세요.

원래 결과가 필요하면 대신 **Revert — Restore Originals**를 선택하세요. Accept는 백업을 삭제합니다. Revert는 원래 오브젝트, 머티리얼, 표시 상태를 복원하며 머티리얼 수 결과도 초기화합니다.

영문 원본 이미지 설명(이미지 생략): 예제 메시 두 개에서 베이크한 2048픽셀 Opaque 그룹 하나. 패널은 여전히 머티리얼 2에서 2, Excellent 등급을 보고합니다. Accept나 Revert 전에 UV 경고를 확인하세요.

*BoneCraft 9.2.19 후보 버전. 공식 Bforartists 5.2.3, Blender 5.3 Alpha. 예제 메시 두 개에서 베이크한 2048픽셀 Opaque 그룹 하나. 패널은 여전히 머티리얼 2에서 2, Excellent 등급을 보고합니다. Accept나 Revert 전에 UV 경고를 확인하세요.*

**Preserve Backup Duplicate**는 처음에 켜져 있으며 검토와 Revert를 위한 아틀라스 이전의 보이는 사본을 유지합니다. 끄면 아틀라스 생성 후 원본을 제거하고 복원 백업이 없습니다. 끄기 전에 별도 파일을 저장하세요.

다른 분석이나 베이크 전에 현재 미리보기를 Accept 또는 Revert하세요. 분석한 오브젝트, 머티리얼 슬롯 또는 렌더 분류가 바뀌면 백업 생성 전에 사전 검사에서 취소할 수 있습니다.

다시 베이크하기 전:

1. **Refresh Analysis**를 선택하세요.

2. 다시 만든 선택을 검토하세요.

**Smart Combine Materials**는 분석이 없을 때의 초기 자동 단축 경로입니다. **Auto Analyze**가 켜져 있으면 베이크 전에 분석을 다시 만듭니다. 자동 재분석 없이 검토한 선택을 베이크하려면 **Bake Checked Sources**를 사용하세요. 이전 지침에서는 이를 **Bake Atlas**라고 부릅니다.

**베이크가 시작되지 않는 경우:** 아틀라스 베이크에는 Cycles가 필요합니다. 사용할 수 없다고 보고하면 Cycles가 포함된 전체 빌드를 사용하세요.

### 고급 옵션 {#advanced-options}

**Advanced Options**는 이전 Override Inherited Settings라는 이름을 대체합니다. 선택적 작업 흐름, 베이크, UV 및 출력 컨트롤이 있습니다.

| 설정 | 용도 |
| --- | --- |
| Auto Analyze | 자동 Smart Combine 단축 경로용 그룹 재생성. |
| Debug Report / Copy Debug Report | 진단을 켜고 문제 해결용 최신 보고서 복사. |
| Albedo (Color) | 필수 기본 색상 베이크 패스. 켜 두세요. |
| Normal Map / Emission / Roughness | 선택적 별도 출력 패스. 지원 소스 데이터와 결과 확인. |
| Metallic / Pack ORM Channels | 이 빌드의 사전 검사가 차단하므로 꺼 두세요. |
| Packing Preset / Bake Padding / UV Margin | 아틀라스 아일랜드 사이 패딩과 간격 설정. |
| Pixel Art No-Bleed / Preserve Island Orientation | 패딩 동작과 지원되는 아일랜드 방향 처리 제어. |
| UV Method / UV Seed / Rotation Step | 패킹과 변형 선택. 사용하는 방법에서만 시드와 회전 컨트롤 표시. |
| Keep Source UV Maps | 출력 메시의 소스 UV 레이어 유지. 처음에는 꺼짐. |
| Fallback Size | 이미지 없는 색상 전용 머티리얼의 아틀라스 배정 크기. |
| Format Output | PNG, TGA, EXR 선택. EXR은 1.0을 넘는 발광을 보존하며 PNG와 TGA는 제한. |
| Material Output Type / Surface Output | 생성 머티리얼의 렌더 유형과 표면 셰이더 선택. |
| Path Output | 출력 텍스처 폴더 설정. |

**Keep Source UV Maps**가 꺼져 있으면 최종 아틀라스 메시는 FBX, Unity, VRChat용 `atlas_uv`를 UV0으로 사용합니다. 켜면 `atlas_uv`가 UV1에 남을 수 있습니다. 소스 맵을 유지할 때 엔진 UV 채널을 확인하세요. 작성된 UV 없는 색상 전용 메시도 생성 아틀라스 UV 레이어를 받습니다.

### 보존과 한계 {#preservation-and-limits}

결합기는 베이크 중 연결된 Principled 틴트, 텍스처 매핑 및 알파를 보존합니다. 렌더에서 숨긴 메시에는 임시 베이크 사본을 사용합니다. 제외된 머티리얼 참조는 다른 오브젝트와 공유된 상태를 유지합니다. 조립 중 지오메트리 위치, 셰이프 키 및 부모 연결은 보호됩니다.

VRM / MToon 머티리얼은 전용 대체 경로를 유지합니다. 투명도 분류는 실제 알파 그래프와 텍스처 알파를 고려합니다. DITHERED 렌더 설정만으로 투명으로 분류하지 않습니다. 베이크 후 문제 타일이 마젠타로 보일 수 있으므로 수락 전에 확인하세요.

기록된 수정에는 생성한 테스트 예제를 사용한 호스트 검사가 있습니다. 모든 실제 아바타나 셰이더 그래프를 인증하지는 않습니다. 파일 브라우저 표시, 실제 창 배치 및 대화형 실행 취소/다시 실행에는 기록된 테스트 한계가 적용됩니다. 과거 [수정 기록](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md)과 [9.2.15 UI 검토](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md)를 참고하세요.

**계보와 기여:** 이 작업 흐름은 CATS 통합 계보를 이어가며 원본 Cats Blender Plugin을 명시합니다. Material Combiner 계보는 Grim-es/material-combiner-addon에 기여를 돌립니다. UV 흐름은 Alexander Belyakov의 UV Toolkit과 oRazeD/UVToolkit 보관 저장소에서 영감을 받았습니다. BoneCraft는 자체 아틀라스 UV 도우미를 구현하며 UVToolkit 소스는 포함하지 않습니다.

---

## 비짐 {#visemes}

**파이프라인 단계:** 3

**기능:** 세 기본 입 모양에서 VRChat 비짐 15개를 생성합니다.

**생성 전:** **A Shape**, **O Shape**, **CH Shape** 각각에 기존 입 셰이프 키를 소스로 할당해야 합니다.

**수동 소스 선택:**

1. **A Shape**에서 소스 키를 선택하세요.

2. **O Shape**에서 소스 키를 선택하세요.

3. **CH Shape**에서 소스 키를 선택하세요.

**자동 대안:** 대신 **Auto-Detect**를 선택하세요.

**어느 방법이든 소스 선택 후:**

1. 세 필드 모두 기존 키 이름인지 확인하세요.

2. 필요하면 버튼 아래 Options를 펼치세요.

3. 필요하면 기존 비짐 덮어쓰기 여부를 바꾸세요.

4. **Generate Visemes**를 선택하세요.

[가이드 13, 2단계](03-guides-b.md#phase-2--viseme-generation)를 참고하세요.

영문 원본 이미지 설명(이미지 생략): CATS Visemes. Generate Visemes 전에 A, O, CH 소스를 고르거나 Auto-Detect를 사용하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. CATS Visemes. Generate Visemes 전에 A, O, CH 소스를 고르거나 Auto-Detect를 사용하세요.*

---

## 눈 추적 {#eye-tracking}

**파이프라인 단계:** 4(Fix Model 후 실행)

Auto-Detect는 흔한 눈 본 이름을 검색하며 메시 지오메트리나 본 위치를 사용하지 않습니다.

1. **Left Eye**, **Right Eye**를 확인하세요.

2. 할당이 없으면 수동으로 본을 선택하세요.

본 이름을 바꾸면:

1. 감지를 다시 실행하세요.

2. 양쪽 할당을 다시 확인하세요.

움직임이 틀리면 본 방향, 컨스트레인트 및 내보낸 아바타를 확인하세요.

**기능:** 눈 본을 찾아 VRChat 요구 이름 `LeftEye`, `RightEye`로 바꾸고 눈 움직임용 회전 컨스트레인트를 만듭니다.

**주요 컨트롤:**

- **Auto-Detect** — 흔한 좌우 눈 본 이름 검색
- **Left Eye**, **Right Eye** — 직접 고르는 눈 본
- **Up Limit**, **Down Limit**, **Side Limit** — 눈이 회전할 수 있는 도 단위 범위
- **Create Eye Tracking** — 본 이름 변경과 컨스트레인트 생성

영문 원본 이미지 설명(이미지 생략): 본 감지 전의 Eye Tracking. 예제 한계는 위 30도, 아래 20도, 옆 30도입니다.

*기본 테스트 빌드 팝오버, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 본 감지 전의 Eye Tracking. 예제 한계는 위 30도, 아래 20도, 옆 30도입니다.*

---

## 포즈와 셰이프 키 {#pose--shape-keys}

**파이프라인 단계:** 5(선택)

### Pose to Shape Key {#pose-to-shape-key}

현재 버튼은 선택한 메시의 **현재 셰이프 키 혼합**을 저장하며 아마츄어 본 변형을 베이크하지 않습니다.

1. 오브젝트 모드로 바꾸세요.

2. 대상 메시를 선택하세요.

3. 기존 셰이프 키 값을 저장할 혼합으로 설정하세요.

4. **Pose to Shape Key**를 선택하세요.

5. 이름을 입력하세요.

6. 작업을 확인하세요.

7. 원래 셰이프 키 값을 0으로 되돌리세요.

8. 새 키만 확인하세요.

새 키는 1로 설정되지만 기존 키도 활성 상태로 남습니다. 원래 값을 활성 상태로 두면 변형이 다시 더해집니다.

### 본으로 변형한 포즈 저장 {#save-a-bone-deformed-pose}

본 변형을 저장할 때는 다음 기본 작업 흐름을 사용하세요. 모디파이어가 메시 토폴로지를 보존해야 합니다.

**Save as Shape Key**는 Armature 모디파이어를 유지하고 **Apply as Shape Key**는 제거합니다.

1. 아마츄어 포즈를 만드세요.

2. 파일 체크포인트를 저장하세요.

3. 오브젝트 모드로 돌아오세요.

4. 변형된 메시를 선택하세요.

5. **Properties → Modifiers**를 여세요.

6. Armature 모디파이어의 드롭다운 메뉴를 여세요.

7. **Save as Shape Key**를 선택하세요.

8. 본 포즈를 초기화하세요.

9. 기존 셰이프 키 값을 초기화하세요.

10. 새 키 값을 1로 설정하세요.

11. 새 키만 검토하세요.

본 포즈나 소스 혼합이 남아 있으면 변형이 다시 더해집니다. 이 기본 작업은 BoneCraft의 Pose To Shape 파이프라인 완료 표시를 갱신하지 않습니다.

영문 원본 이미지 설명(이미지 생략): 기본 Armature 모디파이어 메뉴는 Save as Shape Key와 Apply as Shape Key를 별도로 제공합니다.

*로컬 미리보기, BoneCraft 9.2.19 후보 버전. Bforartists 5.2.3, Blender 5.4 Alpha. 실행 전 기본 Armature 모디파이어 메뉴. Save as Shape Key는 모디파이어를 유지하며 이 그림은 저장된 포즈 결과가 아닙니다.*

### Shape Key to Basis {#shape-key-to-basis}

활성 비-Basis 셰이프 키를 새 Basis로 만들고 다른 키를 새 Basis에 상대적으로 조정합니다.

1. 실행 전에 파일 체크포인트를 저장하세요.

2. 실행 후 나머지 키를 검토하세요.

영문 원본 이미지 설명(이미지 생략): Pose to Shape Key는 현재 키 혼합을 저장하며 Shape Key to Basis는 활성 키를 새 Basis로 만듭니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Pose to Shape Key는 현재 키 혼합을 저장하며 Shape Key to Basis는 활성 키를 새 Basis로 만듭니다.*

---

## 변환과 FBT {#transforms--fbt}

**파이프라인 단계:** 6(마지막)

### 모든 변환 적용 {#apply-all-transforms}

메시와 아마츄어의 위치, 회전, 스케일을 적용하고 변환 채널을 초기화합니다. 이전 도구도 계속 사용할 수 있습니다.

1. 실행 전에 파일 체크포인트를 저장하세요.

2. 아바타를 전후 비교하세요.

내보내기 후 크기가 다르면 메시 변환, 아마츄어 변환 및 내보내기/가져오기 스케일을 확인하세요.

### FBT 수정 {#fix-fbt}

전신 추적용 변환 보정으로 루트 본을 바닥 높이로 옮깁니다.

### FBT 제거 {#remove-fbt}

Fix FBT 보정을 제거합니다.

영문 원본 이미지 설명(이미지 생략): 마지막 파이프라인 작업인 Apply All Transforms, Fix FBT 및 Remove FBT.

*기본 패널 팝오버, BoneCraft 9.2.18. 마지막 파이프라인 작업인 Apply All Transforms, Fix FBT 및 Remove FBT.*

---

## 본 도구 {#bone-tools}

- **Create Root Bone** — 계층 맨 아래에 **Root Name**으로 지정한 루트 본 추가
- **Merge Bones** — **Merge Threshold**보다 짧은 본을 부모에 병합
- **Duplicate Bones** — 선택 본 복제

영문 원본 이미지 설명(이미지 생략): Create Root Bone, Merge Bones 및 Duplicate Bones. 실행 후 루트 이름과 임계값을 조정하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Create Root Bone, Merge Bones 및 Duplicate Bones. 실행 후 루트 이름과 임계값을 조정하세요.*

---

## 아마츄어 도구 {#armature-tools}

**기능:** 의상 아마츄어를 몸에 합치는 것처럼 한 아마츄어를 다른 아마츄어에 병합합니다.

**주요 컨트롤:**

- **Base / Root** — 남길 아마츄어. 결과는 그 이름 유지
- **Incoming** — Base로 병합할 아마츄어. 같은 이름 본은 Base에 병합
- Naming Prep — 병합 전 양쪽 본 이름 맞추기. Mixamo 외의 모든 리그에도 작동
- 본 자동 부모 연결과 이후 메시 결합 옵션
- **Merge Incoming Into Base** — 병합 실행

Naming Prep 사용:

1. Mixamo Prefixed를 선택하세요.

2. **Normalize Merge Names**를 선택하세요.

3. Mixamo Stripped를 선택하세요.

4. **Normalize Merge Names**를 다시 선택하세요.

양쪽 리그가 같은 이름으로 끝납니다.

미리보기와 단계별 병합은 Bone Merge를 사용하세요([리그 빌더](06-rig-builder.md#bone-merge) 참고).

영문 원본 이미지 설명(이미지 생략): Base와 Incoming을 선택하고 Naming Prep을 검토한 뒤 Merge Incoming Into Base를 실행하세요.

*기본 패널 팝오버, BoneCraft 9.2.18. Base와 Incoming을 선택하고 Naming Prep을 검토한 뒤 Merge Incoming Into Base를 실행하세요.*

---

## 메시 도구 {#mesh-tools}

- **Separate by Materials** — 머티리얼별 메시
- **Separate by Loose Parts** — 연결된 조각별 메시
- **Separate by Shape Keys** — 셰이프 키가 움직이는 부분 분리

영문 원본 이미지 설명(이미지 생략): 머티리얼, 분리된 조각 또는 셰이프 키로 메시를 분리합니다.

*기본 패널 팝오버, BoneCraft 9.2.18. 머티리얼, 분리된 조각 또는 셰이프 키로 메시를 분리합니다.*

---

## 스마트 자동 웨이트 {#smart-automatic-weights}

**Smart Automatic Weights**는 스마트 기본값과 숨겨진 백업이 있는 대화상자를 엽니다.

1. 대상 메시와 아마츄어를 확인하세요.

2. 기존 리그에서 웨이트를 재계산하려면 Body를 선택하세요.

3. 웨이트가 있는 소스 메시에서 전달하려면 대신 Clothing을 선택하세요.

**Advanced Recalculation**은 **BoneCraft → Skin → Weight Tools** 위치 안내를 펼치며 전체 컨트롤을 여기서 열지는 않습니다. [리그 도구](05-rig-tools.md#automatic-bone-weight-recalculation)를 참고하세요.

영문 원본 이미지 설명(이미지 생략): Smart Automatic Weights가 설정 대화상자를 엽니다. Advanced Recalculation은 전체 웨이트 컨트롤 위치를 안내합니다.

*기본 패널 팝오버, BoneCraft 9.2.18. Smart Automatic Weights가 설정 대화상자를 엽니다. Advanced Recalculation은 전체 웨이트 컨트롤 위치를 안내합니다.*

---

## 파이프라인 상태와 작업 기록 {#pipeline-status-and-operation-ledger}

Pipeline Status는 여섯 단계의 완료 여부를 표시합니다. Operation Ledger는 각 CATS 작업의 시간과 결과(Changed, Clean, Failed)를 나열합니다. **Copy**는 클립보드로 복사하고 **Clear**는 기록을 비웁니다. [CATS 파이프라인](04-cats-pipeline.md)을 참고하세요.

다음: [빠른 해결과 용어집](10-reference.md)
