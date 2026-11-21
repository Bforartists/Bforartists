# Primeiros passos {#getting-started}

[← Sumário](index.md)

## O que é o BoneCraft? {#what-is-bonecraft}

O BoneCraft é um complemento para o Bforartists. Ele cria rigs de personagens e objetos e prepara avatares 3D para VRChat, VRoid / VRM e MMD. Seus painéis automatizam a criação de rigs, a pintura de pesos, a nomeação de ossos, a sincronização labial, o rastreamento dos olhos e a exportação.

**O que o BoneCraft não faz:**

- Não modela nem esculpe a forma do corpo do avatar
- Não cria texturas nem materiais do zero
- Não envia diretamente para o VRChat (você ainda precisa do VRChat Creator Companion / SDK)

---

## BoneCraft e BoneForge {#bonecraft-and-boneforge}

O BoneCraft funciona somente no Bforartists, uma derivação do Blender. O BoneForge é um complemento separado para o Blender padrão, com menos ferramentas. Instale apenas um desses complementos. No Blender padrão, o BoneCraft mostra um aviso e um botão para obter o Bforartists. Ele não carrega suas ferramentas.

O BoneForge 9.0.0 e versões posteriores destinam-se ao Blender padrão. O BoneCraft é o complemento separado para o Bforartists. Ambos oferecem Auto-Rig Wizard, Quick Rig, Mannequin e as ferramentas compartilhadas CATS/Material Atlas. O BoneCraft também inclui Mechanisms, Control Picker e suas ferramentas de rig de controle para produção, detecção de juntas e exportação por perfil. Uma posição semelhante na interface não disponibiliza essas ferramentas no BoneForge.

## Início rápido na compilação fornecida {#supplied-build-quick-start}

A compilação do Bforartists fornecida originalmente inclui o BoneCraft 9.2.18. A nova prévia local inclui a versão candidata 9.2.19. Ambas ativam o BoneCraft pelas configurações de fábrica. Nessas compilações, você não instala um ZIP nem ativa o BoneCraft manualmente.

1. Abra a compilação fornecida do Bforartists.
2. Pressione **T** para mostrar a Tool Shelf à esquerda.
3. Selecione **BoneCraft** ou **Rig Builder**.
4. Pressione **N** para mostrar a barra lateral à direita.
5. Selecione **CATS** para as ferramentas de avatar e **Import / Export**.

Use os mesmos caminhos da interface e configurações deste manual. Os pacotes de ferramentas opcionais e suas dependências mantêm seus requisitos. Os rigs iniciais do Rigify e as pontes VRM/MMD ainda precisam das dependências indicadas.

Estas instruções descrevem a prévia local da contribuição. O pacote oficial do Bforartists 5.2.3 não inclui esse conjunto. Consulte a [proposta de contribuição](https://github.com/Bforartists/Bforartists/pull/7067) para conhecer seu histórico de revisão.

## Instalar o BoneCraft {#installing-bonecraft}

Use esta seção para o ZIP independente do Toolkit. Quem usa a compilação fornecida pode começar pelas abas já disponíveis, descritas acima.

O ZIP público vinculado é a versão 9.2.18. Até a publicação, use a prévia local para as correções da versão candidata 9.2.19.

**Você precisa de:**

- Bforartists (o BoneCraft foi testado no Bforartists 5.2)
- O arquivo independente [BoneCraft-BFA-9.2.18.zip](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/bonecraft-v9.2.18/BoneCraft-BFA-9.2.18.zip)

**Etapas:**

Para atualizar:

1. Salve seu trabalho.

2. Desative o complemento BoneCraft independente anterior.

3. Remova o complemento BoneCraft independente anterior.

4. Reinicie o Bforartists antes de instalar o novo ZIP.

Para a primeira instalação, comece aqui:

1. Abra o Bforartists.
2. Abra **Edit** → **Preferences** → **Add-ons**.
3. Selecione **Install from Disk…**.

4. Selecione o arquivo `.zip` do BoneCraft.

5. Ative a caixa de seleção ao lado do BoneCraft.
6. Confirme que Preferences informa **9.2.18** para o ZIP publicado vinculado.

7. Expanda a entrada do BoneCraft para ver **Language**, **Tabs**, **Shelf Width**, **Show Helpers** e **Tools**.

Essas etapas instalam o ZIP independente do Toolkit. Use o início rápido da compilação fornecida quando ela já incluir o BoneCraft. Evite ativar cópias independentes e integradas duplicadas.

**Você deve ver:** as abas BoneCraft e Rig Builder na Tool Shelf à esquerda (pressione **T**) e a aba CATS na barra lateral à direita (pressione **N**).

## Onde fica cada coisa {#where-things-are}

Cada aba contém um grupo de trabalho. Setup Rigging, Skin, Review, Avatar Tools e Facial são seções expansíveis dentro das abas. Os caminhos abaixo usam os rótulos da interface em inglês. Os rótulos traduzidos dependem da preferência Language.

| Aba | Local padrão | Seções |
| --- | --- | --- |
| Rig Builder | Tool Shelf à esquerda (T) | Auto-Rig Wizard, Quick Rig - armaduras prontas, Mannequin |
| BoneCraft | Tool Shelf à esquerda (T) | Overview, Setup Rigging, Skin, Mechanisms, Review |
| CATS | Barra lateral à direita (N) | CATS, Avatar Tools, VRChat Tools, Import / Export |

Descrição da imagem do original em inglês (imagem omitida): BoneCraft está selecionado na Tool Shelf à esquerda e CATS na barra lateral à direita. Pressione T ou N para mostrar esses lados.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. BoneCraft está selecionado na Tool Shelf à esquerda e CATS na barra lateral à direita. Pressione T ou N para mostrar esses lados.*

| Ferramenta | Abra este caminho |
| --- | --- |
| Bone Merge | BoneCraft → Setup Rigging → Bone Merge |
| Delta Mush / Proximity Wrap | BoneCraft → Skin → Delta Mush / Proximity Wrap |
| Viseme Library / Lip Sync | CATS → Avatar Tools → Viseme Library → Lip Sync |
| VRChat Viseme Mapping / Face Tracking | CATS → VRChat Tools → Facial |
| Humanoid / Hair | CATS → Avatar Tools → Set Up Humanoid Bones / Add Hair Physics |
| Exportação para VRChat | CATS → Import / Export → Game Engine Export → Unity / VRChat |
| Exportação para Unreal e Bone Names | CATS → Import / Export → Game Engine Export → Unreal Engine 5 |
| Exportação por perfil validada | CATS → Import / Export → Game Export → Export (Profile) |
| Material Atlas | CATS → CATS → Material Atlas → Analyze Materials / Refresh Analysis → Bake Checked Sources |
| VRM / MMD / I/O Hub | CATS → Import / Export → VRM / VRoid, MMD / PMX, Game Engine Export |
| Desempenho / Roupas / Nomes | CATS → VRChat Tools → Check Performance / Attach Clothing / VRChat Naming Extras |

Para os controles de rig e da biblioteca de visemas, selecione uma armadura. Para Delta Mush e Proximity Wrap, selecione uma malha no modo Objeto. Lip Sync exige uma armadura no modo Pose. Expanda o triângulo da seção para mostrar seus botões. Os grupos Options contêm configurações opcionais. Se uma ferramenta executar imediatamente, ajuste-a em Adjust Last Operation antes de outra operação.

Os três fluxos de trabalho faciais têm finalidades diferentes. A geração de visemas do CATS cria chaves de forma da boca. Viseme Library / Lip Sync armazena poses e insere chaves de animação. Facial mapeia chaves de forma existentes para o VRChat ou configura o rastreamento facial.

Os controles de empacotamento UV ficam em **CATS → CATS → Material Atlas → Advanced Options → UV Packing**. Instruções anteriores chamam esse grupo de Override Inherited Settings. O BoneCraft fornece os auxiliares UV compartilhados do atlas, não o complemento independente UVToolkit completo.

**Starter Rigs:**

1. Ative **Starter Rigs** no menu de catálogos da prateleira inferior de assets.

2. Se necessário, selecione **All** nas bibliotecas.

A versão 9.2.5 removeu os antigos controles Starter Rigs do canto superior esquerdo. **Add → Armature → Starter Rig Catalog** oferece ajuste e geração com verificações de dependências.

**Mover uma aba:**

1. Abra **Edit** → **Preferences** → **Add-ons** → BoneCraft → **Tabs**.

2. Selecione **Left** ou **Right** para a aba.

Cada aba também tem um controle de exibição. As alterações se aplicam imediatamente. Quando uma aba está oculta, seus botões Left e Right ficam cinza, mas continuam funcionando.

**Editor de Propriedades:** **Scene Properties**, em Preferences → Tabs, começa ativado. Ele mostra Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools e Import / Export na aba Cena do editor de Propriedades.

Selecione **Show** para ocultar ou mostrar essas seções. Azul significa que as seções estão visíveis. Esse controle não altera as abas da viewport nem a aba de dados da Armadura.

Com uma armadura selecionada, as ferramentas de armadura do BoneCraft também aparecem na aba de dados da Armadura. Essas ferramentas não seguem os controles de visibilidade. Rig Builder, Mechanisms e as seções CATS usam a aba Cena.

Para remover uma ferramenta de todos os locais, desative seu pacote em **Tools**. Como alternativa, desative o complemento.

**Shelf Width:** Widen Narrow Shelves começa ativado. Ele amplia uma vez as prateleiras que contêm abas do BoneCraft quando a largura fica abaixo do mínimo Left ou Right. Na escala de interface 1×, os padrões são 240 pixels para Left e 260 pixels para Right. Se depois você arrastar uma prateleira para deixá-la mais estreita, ela mantém a largura escolhida. Para controlar as larguras manualmente, desative o controle. Seus campos de largura ficam inativos.

Descrição da imagem do original em inglês (imagem omitida): Tabs coloca BoneCraft e Rig Builder à esquerda e CATS à direita. Shelf Width e Show Helpers ficam abaixo.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Tabs coloca BoneCraft e Rig Builder à esquerda e CATS à direita. Shelf Width e Show Helpers ficam abaixo.*

**Menus e abas integradas da Tool Shelf:** você também pode acessar as ferramentas pelos menus do cabeçalho da Viewport 3D:

| Local | Ferramentas |
| --- | --- |
| Add → Armature | Quick Rig, Auto-Rig Wizard, Mannequin for Active Rig |
| Pose → BoneCraft (modo Pose) | Ferramentas de pose, seletor de controles, coleções de ossos, configuração e verificações do rig |
| Weights → BoneCraft (modo Pintura de pesos) | Preenchimento, espelhamento e normalização de pesos |
| Object → Mechanisms (modo Objeto) | Adicionar peças, juntas e vínculos; testar movimento |
| Tool Shelf → Pose ou Weights → BoneCraft | Botões para operações comuns de pose ou pesos |

Os botões Pose e Weights da prateleira mostram texto em uma prateleira larga. Uma prateleira estreita mostra uma grade de ícones. Passe o ponteiro sobre um ícone para ler sua dica. Esses locais usam as mesmas ferramentas das abas do BoneCraft. Somente os pacotes de ferramentas ativados ficam disponíveis.

**Ferramentas da viewport:** Place Rig Markers posiciona o próximo marcador do Auto-Rig Wizard quando você clica na malha. Build Mechanism inicia uma junta ou vínculo guiado quando você clica em uma peça. Consulte [Construtor de Rig](06-rig-builder.md#auto-rig-wizard) e [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each) para a configuração e os controles.

**Execute primeiro e ajuste depois:** Quick Rig, Fit Dropped Rig, Weight Mirror, Weight Transfer, Flood to Custom, Ribbon, Spline IK e Delta Mush executam imediatamente.

1. Selecione a ferramenta.

2. Ajuste imediatamente suas opções no painel Adjust Last Operation da viewport.

3. Conclua os ajustes antes de outra operação.

Outros painéis contêm configurações opcionais em um grupo abaixo dos botões de ação. Para usar essas configurações, expanda o grupo. Se um painel exigir outra seleção, ele pode permanecer visível e explicar o que selecionar.

**Show Helpers:** o BoneCraft explica as seções com linhas curtas de “o que faz / quando usar” e notas “Como funciona”. Para ocultar essas notas, desative **Show Helpers** nas preferências do complemento. Em Avatar Tools, **Compact Mode** controla a mesma opção.

**Language:** a configuração **Language** nas preferências do complemento muda os próprios painéis do BoneCraft para English, 日本語, 한국어, 中文, Français, Português ou Español.

Descrição da imagem do original em inglês (imagem omitida): a prévia local informa BoneCraft 9.2.19 e English como Language.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. A prévia local informa BoneCraft 9.2.19 e English como Language.*

**Revise primeiro a limpeza:**

1. Inspecione as opções de Fix Model.

2. Selecione as operações de que seu avatar precisa.

3. Salve um ponto de restauração do arquivo antes das alterações.

4. Após a operação, inspecione o resultado.

Pipeline Status e Operation Ledger registram o progresso. Consulte [O pipeline do CATS](04-cats-pipeline.md).

**Painel rápido:** pressione **Ctrl+Shift+R** na Viewport 3D para abrir o painel de rig do BoneCraft em uma janela flutuante sob o ponteiro.

---

## Por onde começar? {#where-should-i-start}

Selecione o guia para sua tarefa:

> **Criar o rig de um modelo novo em FBX, OBJ ou Blender para o VRChat.**
> → Vá para [Guia 1: Leve seu primeiro avatar para o VRChat](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat)

> **Preparar um avatar VRM exportado do VRoid Studio.**
> → Vá para [Guia 2: Leve um avatar VRoid para o VRChat](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)

> **Preparar um modelo MMD (arquivo PMX) para o VRChat.**
> → Vá para [Guia 3: Leve um avatar MMD para o VRChat](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)

> **Corrigir nomes de ossos que impedem o envio de um avatar com rig.**
> → Vá para [Guia 4: Corrija os nomes dos ossos do seu avatar](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

> **Preparar sincronização labial, rastreamento dos olhos e malha de um avatar com rig para o VRChat.**
> → Vá para [Guia 13: Prepare seu avatar para o VRChat com CATS](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)

> **Encontrar a solução para um problema específico.**
> → Vá para o [Índice de soluções rápidas](10-reference.md#quick-fix-index)

Próximo: [Guias 1–7](02-guides-a.md)
