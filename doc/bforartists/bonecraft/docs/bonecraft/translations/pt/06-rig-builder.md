# Construtor de rigs {#rig-builder}

[← Sumário](index.md)

Para uma demonstração narrada dos dois tipos de rig, consulte o [tutorial de IK/FK para iniciantes e o arquivo de prática](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md).

## Construir um novo rig {#building-a-new-rig}

O Rig Builder cria um novo rig para um personagem. Sua aba **Rig Builder** fica na estante de ferramentas à esquerda. Pressione **T** para mostrar a estante. Quando Preferences → Tabs → Scene Properties → Show está ativado, o Rig Builder também aparece na aba **Scene** do editor **Properties**. Uma estante estreita usa uma disposição compacta com rótulos curtos. O Auto-Rig Wizard aparece primeiro, seguido de Quick Rig e Mannequin. O menu Add → Armature da viewport também oferece o assistente e Quick Rig.

---

### Assistente de rig automático {#auto-rig-wizard}

**O que faz:** Um guia passo a passo que posiciona marcadores na malha e cria, a partir deles, um rig completo com pesos. É a principal maneira de criar o rig de um personagem do zero.

O [Guia 1](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat) apresenta cada etapa.

**Etapas:** Select Mesh → Rig Type → Body Markers → Finger Markers → Face Markers → Review → Generate

**Controles principais:**

- **Start Auto-Rig** abre o assistente. **Back** e **Cancel** ficam no topo. **Next** fica na parte inferior das etapas de malha, tipo de rig e marcadores. A revisão usa **Generate Rig** no lugar de Next. A etapa final usa **Close Wizard**
- A lista de malhas — clique na sua malha aqui. A etapa seguinte oferece **Body + Face**, **Body Only** ou **Face Only** (para uma armadura existente)
- **Detect Markers** (em Smart Detection) — percorre os membros da malha e posiciona cada marcador do corpo com uma classificação de confiança. **Accept High** mantém os marcadores de alta confiança. **Reset Low** limpa os de baixa confiança
- **Guess Markers from Mesh** e **Guess Precision** (corpo), **Guess Finger Markers** (os marcadores dos dedos são posicionados com base na forma da mão) e **Guess Face Markers**
- Finger Detail — quantos dedos criar, de "0 — No Fingers" a "5 — Full Human Hand"
- A linha de cada marcador: **Place Marker** (ícone de seta), **Confirm Marker** (marca de seleção) e **Reset Marker** (seta circular). Os marcadores da esquerda e da direita também têm **Toggle Symmetry** como primeiro ícone
- **Mirror L to R** e **Mirror R to L** — copiam os marcadores confirmados para o outro lado da linha central
- **Confirm All Placed** — confirma todos os marcadores posicionados na etapa
- **Generate Rig** — cria o rig com os marcadores confirmados. A última etapa oferece **Build Control Rig** (veja abaixo) e **Close Wizard**

**O que Generate Rig cria:**

- Um rig corporal com os segmentos de coluna e pescoço escolhidos e braços e pernas IK/FK, somente IK ou somente FK (a opção **Kinematics**)
- Ossos dos dedos conforme a quantidade escolhida
- Para **Body + Face**: um rig facial, com formas de controle quando **Generate Control Shapes** está ativado
- Pesos de deformação com a qualidade escolhida. Malhas densas recebem pesos por meio de uma malha proxy mais leve; assim, um personagem de 678,000 vértices (seiscentos e setenta e oito mil) leva cerca de um minuto, em vez de falhar silenciosamente.

**Build Control Rig:** a etapa de revisão também mostra **Twist Bones**, **Skirt Bones**, **Face Controls** e **Joint Correctives**. Generate Rig não aplica essas opções. Elas pertencem ao rig de controle do motor. Esse rig inclui ossos de torção, ossos de saia que acompanham as pernas, controles para direcionar os olhos e piscar e chaves de forma corretivas das articulações. Depois de Generate Rig, a última etapa oferece **Build Control Rig**. Esse comando cria o rig de controle na armadura gerada, com as opções selecionadas. Antes de **Close Wizard**, clique em **Build Control Rig**. Fechar o assistente redefine suas opções. O painel Control Layer (Rig Tools) só aparece em um rig criado dessa maneira.

**Onde encontrar:** Rig Builder → Auto-Rig Wizard

**Posicionar vários marcadores com a ferramenta da viewport:**

1. Inicie o assistente.
2. Avance até uma etapa de marcadores do corpo, dos dedos ou do rosto.
3. No Modo de Objeto, ative Place Rig Markers na barra de ferramentas da viewport.

O cabeçalho da ferramenta indica o próximo marcador não confirmado e mostra os bloqueios de eixo e uma opção de espelhamento.

4. Clique na malha do assistente para posicionar e confirmar esse marcador.
5. Quando a ferramenta indicar que a etapa terminou, pressione **Next** no assistente.

A simetria segue as configurações do assistente. Os botões Place de cada marcador continuam funcionando. Clicar em outro lugar não posiciona um marcador.

---

### Rig rápido {#quick-rig}

**O que faz:** Adiciona o Basic Humanoid do BoneCraft ou um dos metarigs do Rigify com um clique. Basic Humanoid tem 19 ossos e não precisa do Rigify. Quick Rig é mais rápido que o assistente, mas se adapta menos à malha.

**Controles principais:**

- O botão Basic Humanoid e os metarigs do Rigify. Para usar uma predefinição do Rigify quando ele está desativado, selecione **Enable Rigify** primeiro
- Um botão de rig adiciona seu rig imediatamente. Adjust Last Operation contém ajuste à malha, pesos automáticos, **Add IK/FK Controllers** e **Initial Pose**
- **T-Pose** e **A-Pose** — alternam a pose de repouso do rig selecionado
- Expanda Troubleshooting para acessar **Diagnose Quick Rig (print to console)**. Com uma armadura que não seja um metarig ativa, também aparece **Inspect Active Rig Controls**
- Com um metarig do Rigify ativo, Troubleshooting mostra **Generate Control Rig (active metarig)** no lugar de Inspect Active Rig Controls. Esse comando gera o rig de controle do Rigify

**O catálogo inicial BoneCraft Rigs:** os nove rigs iniciais incluídos compartilham um catálogo **Starter Rigs** na estante nativa de recursos inferior.

1. Abra o menu de catálogos à esquerda da estante.
2. Selecione **All** para as bibliotecas.
3. Ative **Starter Rigs** uma vez para adicionar sua aba ao lado das abas de catálogos existentes.
4. Selecione essa aba para explorar os rigs iniciais.

**Add → Armature → Starter Rig Catalog** abre o menu de ajuste e adição de um rig inicial, com tratamento das dependências.

Basic Humanoid não precisa do Rigify. As outras miniaturas têm o rótulo **Rigify**. Quando o Rigify está inativo, selecionar ou soltar uma delas no menu do catálogo oferece **Enable Rigify & Add Rig** e Cancel. Aceitar ativa o Rigify instalado e continua com esse rig inicial. Cancelar não adiciona nada. **Quick Rig** também oferece **Enable Rigify**. O menu de contexto do catálogo oferece essa opção quando o Rigify está indisponível. Uma dependência ou predefinição ausente produz uma explicação. O menu não adiciona um rig substituto quando a versão instalada não inclui a predefinição.

A estante nativa de recursos inferior importa recursos de armaduras. Use **Add → Armature → Starter Rig Catalog** para o fluxo com tratamento de dependências descrito abaixo.

Com uma malha selecionada, a ferramenta ajusta o rig inicial a ela ao adicioná-lo. No menu, clique em uma miniatura para adicionar um rig inicial ou arraste-a para a viewport. Os pesos automáticos e a geração de controles começam desativados. Ajuste essas opções depois em **Adjust Last Operation**.

Se nenhuma malha estava selecionada:

1. Selecione o novo rig inicial.
2. Em Quick Rig, selecione a **Mesh**.
3. Clique em **Fit Dropped Rig**.

O ajuste dimensiona e posiciona o esqueleto. Antes de gerar controles ou pesos:

1. Inspecione a posição das articulações.
2. Edite a posição das articulações conforme necessário.

Arrastar para fora da viewport, pressionar Esc ou clicar com o botão direito cancela sem adicionar nada.

**Onde encontrar:** Rig Builder → Quick Rig; Add → Armature → Quick Rig também adiciona os rigs prontos

---

### Manequim {#mannequin}

**O que faz:** Cria uma malha de pré-visualização ao redor de um rig existente para inspecionar sua deformação sem uma malha de personagem pronta. Se ainda não houver um rig, adicione um com Quick Rig. Antes de usar Mannequin, selecione a armadura ou uma malha vinculada a ela como filha. O manequim serve apenas para pré-visualização: substitua-o pela sua própria malha antes do uso final.

**Controles principais:**

- **Quick Mannequin** — cria uma pré-visualização com valores padrão fixos, substituindo o manequim anterior desse rig
- **Add Mannequin** — cria uma pré-visualização com as configurações da cena. Por padrão, substitui um manequim existente. Replace Existing fica em Adjust Last Operation depois do clique
- **Regenerate** — recria a pré-visualização existente com suas configurações salvas
- **Remove** — exclui a malha do manequim e mantém a armadura
- Options, abaixo dos botões, contém **Mode**, **Body Type**, densidade e **Radius Scale**. Advanced, dentro de Options, contém as escalas por região e as configurações de saída. Para usar configurações de cena alteradas, clique em **Add Mannequin** novamente

**Onde encontrar:** Rig Builder → Mannequin

---

## Oficina do manequim: instruções em texto {#illustrated-mannequin-workshop}

<!-- Keep each illustrated step together and preserve the manual's print scale. -->
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

Siga estas três partes em ordem:

1. [A — De Simple Human a manequim](#part-a-simple-human-to-mannequin).
2. [B — Manequim sem rig pelo Auto-Rig](#part-b-rigless-mannequin-through-auto-rig).
3. [C — Testar os pesos e usar IK/FK](#part-c-test-weights-and-use-ikfk).

A fonte em inglês fornece uma captura real da interface para cada etapa numerada da oficina; os números vermelhos correspondem às legendas. Essas capturas foram feitas com a **versão BoneCraft 9.1.2** no `Bforartists 5.2.0`. Esta edição somente em texto omite as imagens e mantém as etapas escritas, as descrições das imagens e as legendas. A disposição dos painéis e os atalhos do Blender podem ser diferentes. Use os comandos nomeados como referência.

As capturas da fonte em inglês, omitidas aqui, mantêm seus rótulos da captura em 9.1.2. A navegação atual é **Rig Builder → Quick Rig**, **Rig Builder → Auto-Rig Wizard** e **BoneCraft → Skin → Weight Tools**. Starter Rigs agora usa a aba de catálogo nativa inferior. Esta edição somente em texto não afirma uma nova repetição em 9.2.18 ou 9.2.19.

Este exercício produz uma pré-visualização simples de cápsulas para aprender rigging. A cabeça, as mãos e o tronco são formas provisórias. Não se trata de um modelo de personagem pronto. Comece em um arquivo novo. Mantenha os dois pontos de restauração salvos para repetir a conversão sem perder o metarig original.

O repositório inclui os dois pontos de restauração em `examples/mannequin/`: `SimpleHuman_Mannequin.blend` é o resultado neutro da Parte A, e `Mannequin_AutoRig.blend` é o exemplo concluído e posado da Parte C, com pesos corrigidos.

### Parte A: de Simple Human a manequim {#part-a-simple-human-to-mannequin}

#### A1. Ativar o Rigify {#a1-enable-rigify}

1. Comece em uma cena nova.
2. Abra **Scene Properties → Rig Builder → Quick Rig**.
3. Se as predefinições do Rigify estiverem indisponíveis, clique em **Enable Rigify**.

Este tutorial usa o metarig `Simple Human` do Rigify. **BoneCraft Basic Humanoid (19 ossos)** é outra predefinição.

Descrição da imagem da fonte em inglês (imagem omitida): A1: Ativar o Rigify

*1 — Scene Properties. 2 — Enable Rigify.*

#### A2. Adicionar Simple Human {#a2-add-simple-human}

Clique em `Simple Human` em Quick Rig. O resultado é um metarig editável, ainda não uma malha. Ele tem 29 ossos nesta versão.

Descrição da imagem da fonte em inglês (imagem omitida): A2: Adicionar Simple Human

*1 — Predefinição Simple Human.*

#### A3. Inspecionar o metarig {#a3-inspect-the-metarig}

1. Mova o ponteiro para a viewport.
2. Pressione `Numpad 1` para a vista ortográfica frontal.
3. Confira se o esqueleto inteiro está visível.
4. Use a roda do mouse para enquadrar o esqueleto.

O novo metarig pode começar no Modo de Pose.

Descrição da imagem da fonte em inglês (imagem omitida): A3: Inspecionar o metarig

*1 — Vista frontal. 2 — Esqueleto Simple Human.*

#### A4. Voltar ao Modo de Objeto {#a4-return-to-object-mode}

Antes de alterar a pose de repouso ou gerar o manequim:

1. Na lista de modos da viewport, selecione **Object Mode**.
2. Mantenha `SimpleHumanArmature` selecionado.

Descrição da imagem da fonte em inglês (imagem omitida): A4: Voltar ao Modo de Objeto

*1 — Lista de modos. 2 — Object Mode.*

#### A5. Usar uma pose em T {#a5-use-a-t-pose}

Em Quick Rig, clique em **T-Pose**. Os braços se estendem horizontalmente. Para um corpo personalizado, ajuste o metarig no Modo de Edição antes de gerar sua pré-visualização. Neste exercício, mantenha simétricas as articulações da esquerda e da direita.

Descrição da imagem da fonte em inglês (imagem omitida): A5: Usar uma pose em T

*1 — Comando T-Pose.*

#### A6. Gerar o manequim {#a6-generate-the-mannequin}

1. Expanda **Mannequin → Options**.
2. Defina `Mode: Universal`.
3. Defina `Body Type: Neutral`.
4. Selecione **Medium**.
5. Defina `Radius Scale: 1.00`.
6. Em Advanced, mantenha as escalas por região em 1.00.
7. Selecione `Joined (non-manifold)`.
8. Selecione **Flat colour**.
9. Ative **Joint Smoothing**.
10. Deixe Unified Volume desativado.
11. Clique em **Add Mannequin**.

A captura omitida da fonte em inglês mostra a malha de cápsulas resultante. Add usa as opções atuais. Regenerate reutiliza as configurações salvas do manequim.

Descrição da imagem da fonte em inglês (imagem omitida): A6: Gerar o manequim

*1 — Add Mannequin. 2 — Universal e configurações do corpo. 3 — Saída Joined e suavização.*

#### A7. Experimentar uma pose de osso {#a7-try-a-bone-pose}

Na vista frontal, o lado esquerdo do personagem fica à sua direita.

1. Selecione a armadura.
2. Mude para **Pose Mode**.
3. Clique no osso do antebraço esquerdo.
4. Com a ferramenta de rotação, gire ligeiramente o osso.

O manequim vinculado acompanha o movimento. Trata-se de uma pré-visualização com pesos no metarig. Ela ainda não tem os controles de animação usados na Parte C.

Descrição da imagem da fonte em inglês (imagem omitida): A7: Experimentar uma pose de osso

*1 — Pose Mode. 2 — Antebraço selecionado e seu gizmo de transformação.*

#### A8. Restaurar e salvar a pré-visualização {#a8-restore-and-save-the-preview}

1. Com o ponteiro na viewport, selecione todos os ossos de pose.
2. Pressione **F3**.
3. Procure `Clear Pose Transforms`.
4. Selecione **All**.
5. Confirme que o manequim voltou à pose em T.
6. Abra **File → Save As**.
7. Salve o arquivo como `SimpleHuman_Mannequin.blend`.

Mantenha esse ponto de restauração antes de continuar.

Descrição da imagem da fonte em inglês (imagem omitida): A8: Restaurar e salvar a pré-visualização

*1 — Busca por Clear Pose Transforms. 2 — All redefine os ossos de pose selecionados.*

### Parte B: manequim sem rig pelo Auto-Rig {#part-b-rigless-mannequin-through-auto-rig}

#### B1. Selecionar a malha do manequim {#b1-select-the-mannequin-mesh}

Continue a partir do ponto de restauração neutro da Parte A. Esta parte remove deliberadamente o rig do manequim antes de executar o assistente.

1. Mude para **Object Mode**.
2. No Outliner, selecione `SimpleHumanArmature_Mannequin`.

Para preservar a Parte A, salve o resultado com outro nome de arquivo.

Descrição da imagem da fonte em inglês (imagem omitida): B1: Selecionar a malha do manequim

*1 — Selecione a malha, não a armadura.*

#### B2. Consolidar a pré-visualização em uma malha {#b2-bake-the-preview-into-a-mesh}

Mantenha o manequim na pose em T restaurada. Deixe apenas o manequim selecionado.

1. Pressione **F3**.
2. Procure `Convert Mesh`.
3. Execute `Convert Mesh`.

Isso mantém a geometria neutra visível e remove o modificador Armature.

Descrição da imagem da fonte em inglês (imagem omitida): B2: Consolidar a pré-visualização em uma malha

*1 — Comando Convert Mesh.*

#### B3. Remover o vínculo de parentesco {#b3-clear-the-parent}

1. Pressione **Alt+P**.
2. Selecione `Clear and Keep Transformation`.

Isso desvincula a malha do metarig antigo sem movê-la.

Descrição da imagem da fonte em inglês (imagem omitida): B3: Remover o vínculo de parentesco

*1 — Clear and Keep Transformation.*

#### B4. Remover os pesos antigos {#b4-remove-the-old-weights}

Esta ação se destina a esta malha descartável de treinamento. Os grupos pertencem ao metarig antigo. O assistente criará novos grupos.

1. Abra **Object Data Properties → Vertex Groups**.
2. No menu suspenso da lista, selecione `Delete All Groups`.

Descrição da imagem da fonte em inglês (imagem omitida): B4: Remover os pesos antigos

*1 — Menu Vertex Groups. 2 — Delete All Groups.*

#### B5. Verificar o ponto de restauração sem rig {#b5-verify-the-rigless-checkpoint}

1. Oculte o antigo `SimpleHumanArmature` com seu ícone de olho no Outliner.
2. Confira se o manequim continua visível.
3. Confira se o painel Modifiers não tem um modificador Armature.
4. Confira se a lista Vertex Groups está vazia.

Essa é a entrada do manequim sem rig. O BoneCraft 9.1.2 gera manequins a partir de uma armadura. Desvincular essa pré-visualização fornece uma malha de treinamento sem rig.

Descrição da imagem da fonte em inglês (imagem omitida): B5: Verificar o ponto de restauração sem rig

*1 — Oculte o metarig antigo. 2 — Pilha de modificadores vazia.*

#### B6. Ativar a aba Rig Builder da viewport {#b6-enable-the-viewport-rig-builder-tab}

No aplicativo 9.1.2 testado, Place Marker iniciado por Scene Properties não aceitava cliques na viewport. Use a aba da viewport para posicionar os marcadores.

1. Abra **Edit → Preferences → Add-ons → BoneCraft → Tabs**.
2. Ative **Rig Builder**.
3. Selecione **Left**.
4. Feche Preferences.
5. Coloque o ponteiro sobre a viewport.
6. Se a estante de ferramentas à esquerda estiver oculta, pressione **T**.

Descrição da imagem da fonte em inglês (imagem omitida): B6: Ativar a aba Rig Builder da viewport

*1 — Ative Rig Builder. 2 — Posicionamento na estante de ferramentas à esquerda.*

#### B7. Iniciar o Auto-Rig {#b7-start-auto-rig}

Com o manequim sem rig selecionado, clique em **Start Auto-Rig**. A captura omitida da fonte em inglês mostra o botão equivalente em Scene Properties. A aba Rig Builder da viewport, ativada na etapa anterior, tem o mesmo comando no topo.

Descrição da imagem da fonte em inglês (imagem omitida): B7: Iniciar o Auto-Rig

*1 — Start Auto-Rig.*

#### B8. Escolher a malha de entrada {#b8-choose-the-input-mesh}

Não selecione um widget ou outro objeto de pré-visualização.

1. Em `Select Mesh`, selecione o manequim.
2. Verifique a indicação de malha selecionada.
3. Clique em **Next**.

Descrição da imagem da fonte em inglês (imagem omitida): B8: Escolher a malha de entrada

*1 — Manequim de entrada. 2 — Next.*

#### B9. Escolher um rig corporal com os dois métodos {#b9-choose-a-body-rig-with-both-methods}

Este manequim de cápsulas não tem topologia facial; portanto, Body + Face é desnecessário.

1. Selecione **Body Only**.
2. Selecione `Kinematics: IK + FK`.
3. Mantenha **Generate Control Shapes** ativado.
4. Clique em **Next**.

Descrição da imagem da fonte em inglês (imagem omitida): B9: Escolher um rig corporal com os dois métodos

*1 — Body Only. 2 — IK + FK. 3 — Next.*

#### B10. Detectar os marcadores iniciais do corpo {#b10-detect-initial-body-markers}

As estimativas da detecção são um ponto de partida. Não as aceite sem conferi-las.

1. Para este manequim simétrico, mantenha **Mirror Symmetry** ativado.
2. Em Body Markers, clique em **Detect Markers**, em Smart Detection.

Descrição da imagem da fonte em inglês (imagem omitida): B10: Detectar os marcadores iniciais do corpo

*1 — Detect Markers. 2 — Mirror Symmetry.*

#### B11. Revisar as posições detectadas {#b11-review-the-detected-positions}

Esta pré-visualização segmentada produz várias estimativas de baixa confiança. Antes de gerar:

1. Confira o topo da cabeça, a base do pescoço, a pelve, os punhos e os tornozelos em relação à malha visível.
2. Revise os pontos principais e os pontos de precisão opcionais.
3. Corrija os pontos conforme necessário.

Os rótulos de confiança descrevem a detecção original. Uma marca verde no início de uma linha indica que a posição atual está confirmada.

Descrição da imagem da fonte em inglês (imagem omitida): B11: Revisar as posições detectadas

*1 — Resumo de confiança da detecção. 2 — Linhas dos marcadores do corpo.*

#### B12. Posicionar um punho na malha {#b12-place-a-wrist-on-the-mesh}

Na vista frontal, o punho esquerdo do personagem fica à direita da tela.

1. Se o marcador já estiver confirmado, redefina sua linha para exibir o botão de posicionamento.
2. Na aba **Rig Builder** da viewport, clique no conta-gotas **Place Marker** de Wrist Left.
3. Clique na superfície do punho na viewport.

Descrição da imagem da fonte em inglês (imagem omitida): B12: Posicionar um punho na malha

*1 — Controle de posicionamento de Wrist Left. 2 — Clique na superfície do punho.*

#### B13. Conferir o punho espelhado e os tornozelos {#b13-check-the-mirrored-wrist-and-ankles}

1. Verifique se as duas linhas dos punhos mostram marcas verdes e coordenadas X opostas.
2. Repita o posicionamento de `Ankle Left` na articulação, não na ponta do pé.

A simetria fornece Ankle Right. Confira a simetria em relação à malha. Não copie as coordenadas do exemplo para um personagem de outro tamanho.

Descrição da imagem da fonte em inglês (imagem omitida): B13: Conferir o punho espelhado e os tornozelos

*1 — Par de punhos confirmado. 2 — Punho espelhado na malha.*

#### B14. Refinar os ombros e cotovelos {#b14-refine-shoulders-and-elbows}

1. Role até Precision Markers.
2. Redefina `Shoulder Left`.
3. Posicione `Shoulder Left` no pivô do braço.
4. Redefina `Elbow Left`.
5. Posicione `Elbow Left` no espaço do cotovelo.
6. Confirme os correspondentes espelhados.
7. Mantenha o punho na extremidade do antebraço junto à mão.

Esses pontos determinam a cadeia do braço. Corrija um ombro ou cotovelo estimado na cápsula errada.

Descrição da imagem da fonte em inglês (imagem omitida): B14: Refinar os ombros e cotovelos

*1 — Linhas dos marcadores de ombro e cotovelo. 2 — Ombro. 3 — Cotovelo.*

#### B15. Refinar os quadris e joelhos {#b15-refine-hips-and-knees}

1. Posicione `Hip Left` no topo da coxa.
2. Posicione `Knee Left` no espaço entre a coxa e a canela.
3. Confira o lado oposto fornecido pela simetria.
4. Mantenha a pelve na linha central, entre os quadris.

Descrição da imagem da fonte em inglês (imagem omitida): B15: Refinar os quadris e joelhos

*1 — Linhas de quadril e joelho. 2 — Superfície do quadril. 3 — Espaço do joelho.*

#### B16. Conferir a profundidade e os dedos dos pés de lado {#b16-check-depth-and-toes-from-the-side}

1. Com o ponteiro sobre a viewport, pressione `Numpad 3`.
2. Confira os pontos tanto na vista ortográfica direita quanto na frontal.
3. Posicione `Toe Left` perto da frente do pé.
4. Verifique seu correspondente espelhado.

Um marcador pode parecer correto de frente e, ainda assim, estar muito à frente ou atrás do corpo.

Descrição da imagem da fonte em inglês (imagem omitida): B16: Conferir a profundidade e os dedos dos pés de lado

*1 — Vista ortográfica direita. 2 — Linha do marcador do dedo do pé. 3 — Superfície do pé.*

#### B17. Posicionar os calcanhares {#b17-place-the-heels}

1. Se um calcanhar foi estimado incorretamente, redefina esse calcanhar.
2. Na vista lateral, posicione `Heel Left` perto da parte de trás do pé.
3. Verifique Heel Right.

Esses marcadores são opcionais. Deixar os dois em zero produziu um aviso de proximidade na versão testada. Posicioná-los nos pés eliminou esse aviso.

Descrição da imagem da fonte em inglês (imagem omitida): B17: Posicionar os calcanhares

*1 — Par de calcanhares confirmado. 2 — Localização do calcanhar.*

#### B18. Confirmar e continuar {#b18-confirm-and-continue}

1. Revise o topo da cabeça, a base do pescoço e a pelve, além de cada par de pontos.
2. Clique em **Confirm All Placed**.
3. Clique em **Next**.

As marcas verdes ao lado dos nomes mostram o estado de confirmação. Os rótulos de confiança originais REVIEW/ADJUST podem continuar visíveis em 9.1.2.

Descrição da imagem da fonte em inglês (imagem omitida): B18: Confirmar e continuar

*1 — Confirm All Placed. 2 — Next.*

#### B19. Pular os dedos nesta malha {#b19-skip-fingers-for-this-mesh}

Este manequim tem cápsulas nas mãos, mas não tem geometria para os dedos.

1. Selecione `0 — No Fingers`.
2. Clique em **Next**.

Para uma malha de mão real:

1. Selecione a quantidade adequada de dedos.
2. Posicione os marcadores dos dedos.

Descrição da imagem da fonte em inglês (imagem omitida): B19: Pular os dedos nesta malha

*1 — No Fingers. 2 — Next.*

#### B20. Revisar e gerar {#b20-review-and-generate}

Antes de continuar, exija **All checks passed**. Estas configurações se aplicam a este manequim simples de treinamento. Não são requisitos universais de exportação.

1. Selecione **IK + FK**.
2. Ative as formas de controle.
3. Defina `Spine Segments: 3`.
4. Defina `Neck Segments: 1`.
5. Selecione `No Fingers`.
6. Selecione **Game Ready**.
7. Desative Twist Bones.
8. Desative Skirt Bones.
9. Desative Preserve Volume.
10. Desative Joint Correctives.
11. Clique em **Generate Rig**.

Descrição da imagem da fonte em inglês (imagem omitida): B20: Revisar e gerar

*1 — Verificações dos marcadores. 2 — Configurações de geração. 3 — Generate Rig.*

#### B21. Criar os controles de animação {#b21-build-the-animator-controls}

Depois da geração, clique em **Build Control Rig**. Generate Rig fornece o rig corporal e os pesos. Build Control Rig adiciona a camada de controle usada abaixo. A malha de entrada já está presente, mesmo que o painel de conclusão mostre sua oferta genérica de manequim. Não clique em Quick Mannequin novamente.

Descrição da imagem da fonte em inglês (imagem omitida): B21: Criar os controles de animação

*1 — Build Control Rig.*

#### B22. Concluir o assistente {#b22-finish-the-wizard}

1. Aguarde a mensagem de conclusão do rig de controle.
2. Clique em **Close Wizard**.
3. Mantenha o antigo metarig Simple Human oculto.

A nova armadura aparece no Outliner. O novo rig deve deformar a malha. Ossos visíveis, por si só, não comprovam que a deformação funciona.

Descrição da imagem da fonte em inglês (imagem omitida): B22: Concluir o assistente

*1 — O botão de construção agora está desativado. 2 — Close Wizard.*

### Parte C: testar os pesos e usar IK/FK {#part-c-test-weights-and-use-ikfk}

A armadura gerada tem este nome de objeto na versão testada (use-o no Outliner e na ferramenta de pesos):

```text
BoneForge_Rig
```

`FK (Forward Kinematics)` propaga rotações pela hierarquia. A rotação do braço afeta o antebraço e depois a mão. É adequada para movimentos amplos e membros que se movem livremente. `IK (Inverse Kinematics)` começa por uma extremidade. Ao mover um alvo do punho ou do tornozelo, o solucionador dobra a cadeia para alcançá-lo. É adequada para pés apoiados e mãos que precisam tocar uma superfície.

| Tarefa | Controle a usar | O que observar |
|---|---|---|
| Balançar um braço | Controles FK do ombro e do cotovelo | Os controles filhos acompanham seu pai |
| Posicionar uma mão | Alvo IK do punho | Ombro e cotovelo são resolvidos em direção ao alvo |
| Apoiar um pé | Alvo IK do tornozelo dessa perna | Mova o corpo enquanto o alvo alcançável permanece no lugar |
| Direcionar a dobra de um cotovelo ou joelho | Controle de polo IK | O polo define a direção da dobra; não é o alvo do punho/tornozelo |
| Mudar de método | Botões IK/FK do membro | Confira a pose ajustada antes de inserir chaves de animação |

O exercício abaixo compara um braço nos dois modos. Cada membro tem sua própria alternância. `Bake IK / Bake FK` são ferramentas de conversão de animação. Uma troca para uma única pose não substitui a consolidação nem a inserção de chaves de uma animação. Consulte [Camada de controle](05-rig-tools.md#control-layer-ikfk) para os outros controles.

#### C1. Abrir a camada de controle {#c1-open-the-control-layer}

1. Selecione a **armadura gerada**.
2. Selecione **Pose Mode**.
3. Abra **BoneCraft → Review → Control Layer**.
4. Selecione **arm-L → FK**.

Cada braço e perna tem sua própria alternância IK/FK. Esquerda e direita se referem ao personagem. Na vista frontal, arm-L aparece à sua direita.

Descrição da imagem da fonte em inglês (imagem omitida): C1: Abrir a camada de controle

*1 — Pose Mode. 2 — Control Layer e alternância de arm-L.*

#### C2. Mostrar os controles de animação {#c2-show-the-animator-controls}

1. Abra **Object Data Properties → Bone Collections** da armadura.
2. Selecione a estrela Solo de `Controls`.
3. Selecione a estrela Solo de **FK**.
4. Se a malha ocultar os controles, ative **In Front** em Viewport Display.
5. Ao usar os alvos mais adiante, inclua **IK**.

As seleções Solo isolam essas formas de controle. Essa lista nativa de coleções também funciona se o painel Collections do BoneCraft não for desenhado neste aplicativo.

Descrição da imagem da fonte em inglês (imagem omitida): C2: Mostrar os controles de animação

*1 — Estrelas Solo de Controls e FK. 2 — In Front.*

#### C3. Selecionar o controle FK do antebraço {#c3-select-the-forearm-fk-control}

1. Na vista frontal, clique no controle circular no cotovelo esquerdo do personagem.
2. Confira se o nome da seleção na viewport é **forearm.fk-L**.

Um controle FK do antebraço gira ao redor do cotovelo. Selecionar o controle do ombro giraria o braço e seus filhos.

Descrição da imagem da fonte em inglês (imagem omitida): C3: Selecionar o controle FK do antebraço

*1 — Controle forearm.fk-L selecionado. 2 — FK está ativo para arm-L.*

#### C4. Girar e inspecionar a deformação {#c4-rotate-and-inspect-the-deformation}

O objetivo é uma rotação de aproximadamente `−45°` em torno do **Y** global neste exemplo em vista frontal. Use um dos métodos:

- Com a ferramenta de rotação, gire o controle FK selecionado.
- Para o mapa de teclas do Bforartists mostrado, siga estas etapas:

1. Pressione **Ctrl+E**.
2. Pressione **Y**.
3. Digite **-45**.
4. Pressione **Enter**.

O atalho padrão de rotação do Blender é **R**. A captura omitida da fonte em inglês mostra deliberadamente o problema inicial dos pesos: a cápsula do braço se inclina junto com o antebraço. Não aceite esse resultado como um rig pronto.

Descrição da imagem da fonte em inglês (imagem omitida): C4: Girar e inspecionar a deformação

*1 — Movimento incorreto do braço durante o teste FK.*

#### C5. Recalcular os pesos do manequim {#c5-recalculate-the-mannequin-weights}

Se o teste de pose acima falhar, siga estas etapas:

1. Mude para **Object Mode**.
2. Selecione a malha.
3. Abra **BoneCraft → Skin → Weight Tools → Automatic Bone Weight Recalculation**.
4. Defina Mesh to Reweight como o manequim.
5. Defina Existing Armature como a **armadura gerada**.
6. Selecione **Body**.
7. Selecione `Body Method: Bone Heat`.
8. Defina `New Weight Strength: 1.00`.
9. Defina `Smooth Passes: 0`.
10. Defina `Max Bones per Vertex: 0`.
11. Defina `Minimum Weight: 0.001`.
12. Mantenha **Keep Weight Backup** ativado.
13. Execute **Automatic Bone Weight Recalculation**.

Isso corrigiu a pré-visualização segmentada na versão testada.

Descrição da imagem da fonte em inglês (imagem omitida): C5: Recalcular os pesos do manequim

*1 — Malha e armadura. 2 — Bone Heat. 3 — Configurações de substituição e cópia de segurança. 4 — Recalcular.*

#### C6. Verificar a dobra FK corrigida {#c6-verify-the-repaired-fk-bend}

1. Selecione novamente a armadura gerada.
2. Volte para **Pose Mode**.

O braço agora deve permanecer horizontal do ombro ao cotovelo, enquanto o antebraço se eleva a partir do cotovelo. O objeto oculto `WEIGHTS_BACKUP_…` preserva os pesos antigos. Antes de animar seu próprio personagem, teste também os outros membros. Um esqueleto gerado, por si só, não comprova que a deformação por pesos está correta.

Descrição da imagem da fonte em inglês (imagem omitida): C6: Verificar a dobra FK corrigida

*1 — O braço permanece no lugar. 2 — O antebraço dobra no cotovelo.*

#### C7. Mudar o mesmo braço para IK {#c7-switch-the-same-arm-to-ik}

Clique em **arm-L → IK**. A troca ajusta o alvo à pose atual, de modo que o braço deve continuar elevado. Se os alvos estiverem ocultos, adicione **IK** às coleções Solo visíveis. A troca muda quais controles conduzem a cadeia. Ela não registra uma nova animação.

Descrição da imagem da fonte em inglês (imagem omitida): C7: Mudar o mesmo braço para IK

*1 — Alternância IK de arm-L. 2 — Pose mantida durante a troca.*

#### C8. Selecionar o alvo IK do punho {#c8-select-the-wrist-ik-target}

1. Clique no controle do punho.
2. Confira se o nome da seleção é **forearm.ik-L**.

Apesar de seu nome mencionar o antebraço, este é o alvo da extremidade da cadeia do braço. Mova esse alvo para posicionar a mão. O solucionador muda os ângulos do ombro e do cotovelo para alcançar o alvo.

Descrição da imagem da fonte em inglês (imagem omitida): C8: Selecionar o alvo IK do punho

*1 — Alvo do punho selecionado. 2 — Nome da seleção.*

#### C9. Mover o alvo e comparar {#c9-move-the-target-and-compare}

Mantenha o alvo ao alcance do braço. O objetivo é mover ligeiramente o alvo do punho para dentro, ao longo do **X** global. Neste exemplo, `−0.15 m` cria uma dobra visivelmente diferente. Use um dos métodos:

- Arraste a seta X da ferramenta de movimento.
- Para o mapa de teclas mostrado, siga estas etapas:

1. Pressione **Ctrl+W**.
2. Pressione **X**.
3. Digite `-0.15`.
4. Pressione **Enter**.

O atalho padrão de movimento do Blender é **G**. Compare o braço inteiro com o exemplo FK. A extremidade conduz o movimento e os dois segmentos do braço acompanham.

Descrição da imagem da fonte em inglês (imagem omitida): C9: Mover o alvo e comparar

*1 — Extremidade do punho. 2 — Resposta da cadeia. 3 — Exemplo de movimento em X.*

#### C10. Voltar ao modo anterior e salvar o exemplo {#c10-switch-back-and-save-the-example}

1. Clique novamente em **arm-L → FK**.

Os controles FK se ajustam à pose IK atual.

2. Verifique se a malha não dá um salto.
3. Abra **File → Save As**.
4. Salve `Mannequin_AutoRig.blend`.

A captura omitida da fonte em inglês mostra o exemplo salvo com FK ativo. Para uma cópia neutra de treinamento:

1. Mantenha os quatro membros em FK.
2. Selecione todos os controles de pose visíveis.
3. Pressione **F3**.
4. Procure `Clear Pose Transforms`, como na Parte A.
5. Selecione **All**.
6. Salve a cópia neutra com outro nome.

Descrição da imagem da fonte em inglês (imagem omitida): C10: Voltar ao modo anterior e salvar o exemplo

*1 — FK ativo novamente. 2 — Pose preservada. 3 — Nome do arquivo salvo.*

**Verificação de conclusão:** A pré-visualização do metarig original continua salva. O manequim desvinculado tem um novo rig corporal e controles. Os pesos da pré-visualização estão corrigidos. Você comparou uma rotação FK com um movimento de alvo IK. Mantenha o rig salvo como exemplo de aprendizado. Para produção, substitua a pré-visualização por uma geometria de personagem adequada.

---

### Transferência de animação {#animation-retargeting}

A transferência de animação de um esqueleto para outro é explicada em [Ferramentas de rig: Retarget](05-rig-tools.md#retarget).

Consulte a [imagem de Retarget](05-rig-tools.md#retarget) para os controles de clipe.

---

## Mesclar ossos {#bone-merge}

**O que faz:** Combina duas armaduras em uma — por exemplo, um rig corporal e um rig de roupa ou cabelo — mantendo todos os pesos.

O [Guia 11](03-guides-b.md#guide-11-merge-two-rigs-together) apresenta cada etapa.

**As três fases:**

- Scope — seleção das duas armaduras e revisão de suas diferenças
- Rename — resolução de conflitos de nomes e identificação de novos ossos
- Merge — pré-visualização seguida da mesclagem final

**Controles principais:**

- **Base** — a armadura que permanece. A outra armadura é mesclada a ela e depois ocultada
- **Analyze** — compara os dois esqueletos. **Acknowledge Scope — Proceed to Rename** abre a fase 2
- **Normalize Both Armatures** — renomeia os ossos padrão dos dois rigs conforme um único padrão de nomes (Mixamo Prefixed, Mixamo Stripped ou personalizado)
- **Auto-Propose Renames** — sugere nomes para os ossos próprios do rig que será mesclado
- **Apply Rename** — renomeia uma entrada (uma etapa de desfazer). **Apply Batch Pattern** renomeia várias com um padrão (com `{bone}`, `{side}` e `{index}`)
- **Mark as Unique** — mantém um osso como um novo osso em vez de mesclá-lo
- **Verify Rename — Proceed to Merge** — abre a fase 3
- **Run Merge Preview** — informa o que a mesclagem faria, sem alterar nada
- **Merge Armatures** — cria cópias de segurança das duas armaduras e as mescla

**Onde encontrar:** BoneCraft → Setup Rigging → Bone Merge

Descrição da imagem da fonte em inglês (imagem omitida): Bone Merge começa na fase 1: Scope. As fases posteriores permanecem bloqueadas até as verificações anteriores terminarem.

*Menu de painel nativo, BoneCraft 9.2.18. Bone Merge começa na fase 1: Scope. As fases posteriores permanecem bloqueadas até as verificações anteriores terminarem.*

Próximo: [Mecanismos](07-mechanisms.md)
