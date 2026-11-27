# Manual do BoneCraft {#bonecraft-manual}

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
      content: "Página " counter(page) " de " counter(pages);
      font-family: "Segoe UI", sans-serif;
      font-size: 9pt;
      color: #555;
    }
  }
}
</style>

**BoneCraft 9.2.19, versão candidata local.** O BoneCraft é um kit de ferramentas de rigging e avatares para o Bforartists.

Esta edição somente de texto abrange os controles, a navegação e as correções de painéis da versão candidata BoneCraft 9.2.19. Ela mantém os 12 capítulos e as instruções escritas das oficinas. Os arquivos de capturas de tela foram omitidos; as descrições de imagens e as legendas do original em inglês são mantidas como notas.

A compilação do Bforartists fornecida originalmente inclui o BoneCraft 9.2.18. A nova prévia local inclui a versão candidata 9.2.19. Ambas ativam o BoneCraft pelas configurações de fábrica. Essas compilações não exigem instalação por ZIP.

Para **BoneCraft** e **Rig Builder**, abra a Tool Shelf à esquerda (**T**). Para **CATS**, abra a barra lateral à direita (**N**). Consulte [Início rápido na compilação fornecida](01-start.md#supplied-build-quick-start).

Os caminhos da interface e as configurações são os mesmos. As ferramentas opcionais e suas dependências mantêm seus requisitos. Estas instruções descrevem a prévia local da contribuição. O pacote oficial do Bforartists 5.2.3 não inclui esse conjunto. Quem usa a versão independente deve seguir [Instalar o BoneCraft](01-start.md#installing-bonecraft).

A revisão do código-fonte abrange a instalação de MMD, a preparação do atlas de materiais, os nomes de exportação, a restauração de modos, as formas salvas dos mecanismos e as correções atuais de painéis.

Para a instalação e o mapa da interface, leia [Primeiros passos](01-start.md). Para as alterações até a versão candidata local 9.2.19, leia [Novidades](11-whats-new.md).

As oficinas do original em inglês mantêm suas verificações históricas e os rótulos de versão das capturas de tela. Esta edição somente de texto omite essas imagens e mantém suas descrições escritas e legendas. Ela não afirma que todos os tutoriais foram repetidos com a versão 9.2.19.

Esta edição segue os 12 capítulos atuais em inglês, incluindo a oficina ampliada do capítulo 6 e o capítulo 12. Os índices traduzidos anteriores e os capítulos incompletos são predecessores históricos, não definem o escopo desta edição.

A versão independente publicada continua sendo a 9.2.18. A versão candidata local 9.2.19 ainda não foi publicada. Leia as [notas da versão 9.2.18](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md) para essa versão.

O tutorial de Crescent Rose do original em inglês inclui oito etapas de preparação do FBX, 30 etapas de Mechanisms e 52 capturas de tela anotadas, verificadas na interface 9.1.2. Esta edição somente de texto mantém as etapas escritas, as descrições de imagens e as legendas, omitindo os arquivos de imagem.

## Capítulos {#chapters}

Suplemento em vídeo: [Introdução ao IK/FK e arquivo de prática](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md).

Use os links dos capítulos abaixo. A paginação do PDF muda quando o manual é recompilado.

1. [Primeiros passos](01-start.md) — o que é o BoneCraft, como instalá-lo e onde fica cada coisa.
2. [Guias 1–7](02-guides-a.md) — primeiro avatar, VRoid, MMD, nomes de ossos, mapeamento humanoide, cabelo, roupas.
3. [Guias 8–13](03-guides-b.md) — sincronização labial, desempenho, poses, mesclagem de rigs, problemas de envio, CATS.
4. [O pipeline do CATS](04-cats-pipeline.md) — as seis fases, o registro e por que a ordem importa.
5. [Ferramentas de rig](05-rig-tools.md) — interface do rig, animação, pesos e ferramentas de controle do rig.
6. [Construtor de Rig](06-rig-builder.md) — criação de um rig novo, oficina escrita Simple Human → manequim → Auto-Rig → IK/FK e Bone Merge.
7. [Mechanisms](07-mechanisms.md) — juntas e vínculos para objetos e máquinas: dobradiças, deslizamentos, engrenagens, sequências.
8. [Ferramentas do VRChat](08-vrchat.md) — ferramentas do VRChat, VRM e MMD, hub de E/S e quadro de tarefas.
9. [Ferramentas do CATS](09-cats.md) — cada ferramenta do CATS, uma por uma.
10. [Soluções rápidas e glossário](10-reference.md) — problemas comuns e os termos usados neste manual.
11. [Novidades](11-whats-new.md) — alterações por versão.
12. [Tutorial: Crescent Rose com Mechanisms](12-crescent-rose.md) — exemplo prático: criar o rig de uma foice-fuzil transformável, passo a passo, com instruções escritas e as descrições de imagens do original em inglês preservadas.
