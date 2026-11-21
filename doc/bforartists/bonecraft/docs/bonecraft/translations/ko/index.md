# BoneCraft 설명서 {#bonecraft-manual}

<!-- Print footer for exported PDFs. -->
<style>
@media print {
  p:has(> img):has(+ p > em:only-child) {
    break-after: avoid;
  }
  p:has(> img) + p:has(> em:only-child) {
    break-before: avoid;
    break-inside: avoid;
  }
  section.chapter > p:last-child {
    break-before: avoid;
  }
  @page {
    @bottom-center {
      content: "페이지 " counter(page) " / " counter(pages);
      font-family: "Segoe UI", sans-serif;
      font-size: 9pt;
      color: #555;
    }
  }
}
</style>

**BoneCraft 9.2.19 로컬 후보 버전.** BoneCraft는 Bforartists용 리깅 및 아바타 툴킷입니다.

이 텍스트 전용 판은 BoneCraft 9.2.19 후보 버전의 컨트롤, 탐색 및 패널 수정을 다룹니다. 12개 장과 워크숍의 서면 지침을 모두 유지합니다. 스크린샷 파일은 생략하며, 영문 원본의 이미지 설명과 그림 설명은 참고 문구로 유지합니다.

원래 제공된 Bforartists 빌드에는 BoneCraft 9.2.18이 포함되어 있습니다. 새 로컬 미리보기에는 9.2.19 후보 버전이 포함됩니다. 두 빌드 모두 팩토리 설정에서 BoneCraft를 활성화하므로 ZIP을 설치할 필요가 없습니다.

**BoneCraft**와 **Rig Builder**는 왼쪽 툴 셸프(**T**)에서, **CATS**는 오른쪽 사이드바(**N**)에서 여세요. [제공된 빌드 빠른 시작](01-start.md#supplied-build-quick-start)을 참고하세요.

인터페이스 경로와 설정은 같습니다. 선택적 도구와 의존 패키지의 요구 사항도 그대로 적용됩니다. 이 지침은 로컬 기여 미리보기를 설명합니다. 공식 Bforartists 5.2.3 패키지에는 이 번들이 포함되지 않습니다. 독립형 사용자는 [BoneCraft 설치](01-start.md#installing-bonecraft)를 따르세요.

소스 검토 범위는 MMD 설치, 머티리얼 아틀라스 준비, 내보내기 이름, 모드 복원, 저장된 메커니즘 형태 및 현재 패널 수정입니다.

설치와 인터페이스 위치는 [시작하기](01-start.md)를 읽으세요. 로컬 9.2.19 후보 버전까지의 변경 사항은 [새로운 기능](11-whats-new.md)을 읽으세요.

영문 원본 워크숍은 과거 검증 기록과 스크린샷 버전 표시를 유지합니다. 이 텍스트 전용 판은 이미지를 생략하고 서면 이미지 설명과 그림 설명을 유지합니다. 모든 튜토리얼을 9.2.19에서 다시 실행했다고 주장하지 않습니다.

이 판은 확장된 6장 워크숍과 12장을 포함하여 현재 영문 12개 장을 모두 따릅니다. 이전 번역 목차와 불완전한 장은 과거 선행본이며 이 판의 범위를 정하지 않습니다.

공개된 독립형 릴리스는 여전히 9.2.18입니다. 로컬 9.2.19 후보 버전은 공개되지 않았습니다. 해당 릴리스는 [9.2.18 릴리스 노트](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md)를 읽으세요.

영문 원본 Crescent Rose 튜토리얼에는 FBX 준비 8단계, Mechanisms 30단계 및 9.1.2 인터페이스를 기준으로 확인한 주석 달린 스크린샷 52개가 포함됩니다. 이 텍스트 전용 판은 이미지 파일을 생략하고 서면 단계, 이미지 설명 및 그림 설명을 유지합니다.

## 장 {#chapters}

보충 영상: [IK/FK 초보자 실습 안내와 연습 파일](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md).

아래의 장 링크를 사용하세요. 설명서를 다시 빌드하면 PDF 페이지 구성이 달라집니다.

1. [시작하기](01-start.md) — BoneCraft 소개, 설치 및 기능 위치.
2. [가이드 1–7](02-guides-a.md) — 첫 아바타, VRoid, MMD, 본 이름, 휴머노이드 매핑, 머리카락, 의상.
3. [가이드 8–13](03-guides-b.md) — 립싱크, 성능, 포즈, 리그 합치기, 업로드 문제, CATS.
4. [CATS 파이프라인](04-cats-pipeline.md) — 여섯 단계, 기록 및 순서가 중요한 이유.
5. [리그 도구](05-rig-tools.md) — 리그 UI, 애니메이션, 웨이트 및 리그 제어 도구.
6. [리그 빌더](06-rig-builder.md) — 새 리그 만들기, Simple Human → 마네킹 → Auto-Rig → IK/FK의 서면 워크숍 및 본 병합.
7. [Mechanisms(메커니즘)](07-mechanisms.md) — 소품과 기계를 위한 조인트와 링크: 힌지, 슬라이드, 기어, 시퀀스.
8. [VRChat 도구](08-vrchat.md) — VRChat, VRM, MMD 도구, I/O 허브 및 작업 보드.
9. [CATS 도구](09-cats.md) — 모든 CATS 도구를 하나씩 설명.
10. [빠른 해결과 용어집](10-reference.md) — 자주 생기는 문제 및 이 설명서의 용어.
11. [새로운 기능](11-whats-new.md) — 버전별 변경 사항.
12. [튜토리얼: Mechanisms로 Crescent Rose 만들기](12-crescent-rose.md) — 변형하는 낫 겸 소총을 단계별로 리깅하는 실습 예제. 서면 지침과 영문 원본 이미지 설명을 유지합니다.
