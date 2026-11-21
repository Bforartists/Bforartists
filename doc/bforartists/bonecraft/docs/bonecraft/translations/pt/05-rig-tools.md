# Ferramentas de rig {#rig-tools}

[← Sumário](index.md)

Este capítulo explica as ferramentas de rigging, animação e pesos do BoneCraft. Consulte-o para conhecer detalhes dos recursos ou situações que os guias não abordam.

Cada entrada explica a finalidade da ferramenta, seus usos, controles principais e localização. A linha "Onde encontrar" indica o modo necessário. Os controles de rig exigem Pose Mode. Weight Mirror e Weight Transfer exigem Weight Paint. Delta Mush exige Object Mode. Quando uma ferramenta não pode ser executada, algumas seções continuam visíveis com uma mensagem sobre a seleção.

Desde a versão 9.1, muitas ferramentas são executadas imediatamente e mostram suas opções no painel Adjust Last Operation. Altere essas opções logo após o clique, antes de executar outra operação. Operações comuns têm atalhos nos menus Pose → BoneCraft e Weights → BoneCraft. As abas Pose e Weights da Tool Shelf do Bforartists também têm painéis de botões do BoneCraft. [Primeiros passos](01-start.md#where-things-are) lista esses pontos de acesso.

As imagens mostram exemplos de rigs e configurações das ferramentas. Siga o caminho de cada ferramenta para abrir seus controles.

Para exportar para engines, use [Ferramentas VRChat: exportação para engines de jogos](08-vrchat.md#game-engine-export). As predefinições de **Bone Names** alteram cópias de exportação. Sua finalidade é diferente da das ferramentas que renomeiam o rig de trabalho.

---

## Ferramentas de interface do rig {#rig-ui-tools}

Estas ferramentas controlam a visibilidade e a organização dos ossos e oferecem acesso rápido durante o trabalho com armatures.

---

### Coleções de ossos {#bone-collections}

**O que faz:** Mostra as coleções de ossos do esqueleto em linhas. Clique no nome de uma coleção para selecionar seus ossos. O ícone de olho mostra ou oculta a coleção.

> Uma coleção de ossos é um grupo nomeado de ossos, por exemplo, "IK Controls", "Face Bones" e "Deform Bones". Ocultar uma coleção oculta esses ossos na viewport, permitindo que você se concentre em uma parte do rig.

**Controles principais:**

- Cada linha: cor de destaque, **Toggle Collection Visibility** (ícone de olho), nome da coleção, **Solo Collection** e **Rename Collection Display**. O nome da coleção seleciona seus ossos. **Rename Collection Display** define um nome de exibição personalizado para a linha. Para identificar um botão que mostra apenas um ícone, passe o ponteiro sobre ele para ver a dica
- **Show All Collections** e **Hide All Collections** (ícones de olho aberto e fechado acima da lista) — mostram ou ocultam tudo de uma vez
- Seções — agrupam várias coleções sob um cabeçalho recolhível

**Onde encontrar:** aba BoneCraft → Review → Collections

Descrição da imagem da fonte em inglês (imagem omitida): Coleções de ossos e seus controles de visibilidade, seleção, isolamento e nome de exibição.

*Popover nativo da versão de teste, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Coleções de ossos e seus controles de visibilidade, seleção, isolamento e nome de exibição.*

---

### Favoritos de visibilidade {#visibility-bookmarks}

**O que faz:** Salva quais coleções de ossos estão visíveis, permitindo alternar de uma vez entre visualizações salvas.

**Exemplo de uso:** "Face Only" pode armazenar uma visualização apenas dos ossos do rosto para trabalhar nas expressões. "Full Rig" pode armazenar uma visualização de todos os ossos para pintar pesos. Um clique alterna entre as visualizações salvas.

**Controles principais:** cada posição é uma linha.

- Nome do favorito — clique nele para aplicar a visualização salva
- **Save Bookmark** — salva a visibilidade atual nessa posição. Para ver a dica, passe o ponteiro sobre o ícone
- Amostra de cor — identifica o favorito por cor
- **Clear Bookmark** e **Remove Bookmark** (ícones de fechar) — esvaziam a posição ou removem uma posição adicionada
- **Add Bookmark** — adiciona uma posição

**Favoritos padrão:** FK Arms, IK Body, Face Only, Full Rig

**Onde encontrar:** aba BoneCraft → Review → Collections → Visibility Bookmarks

Descrição da imagem da fonte em inglês (imagem omitida): Visibility Bookmarks com uma visualização Full Rig salva e três posições disponíveis.

*Popover nativo da versão de teste, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Visibility Bookmarks com uma visualização Full Rig salva e três posições disponíveis.*

---

### Painel rápido por atalho {#hotkey-quick-panel}

**O que faz:** Abre o painel de rig do BoneCraft (coleções e favoritos) como um pop-up na posição do cursor.

**Como usar:**

1. Na viewport 3D, pressione **Ctrl+Shift+R**.
2. Para fechar o pop-up, clique fora dele.

**Onde encontrar:** atalho **Ctrl+Shift+R** na viewport 3D (não tem um painel próprio)

O painel rápido usa os [controles de favoritos descritos acima](#visibility-bookmarks).

---

## Ferramentas de animação {#animation-tools}

---

### Biblioteca de poses {#pose-library}

**O que faz:** Armazena poses nomeadas com miniaturas, que você pode aplicar ao rig com um clique.

**Controles principais:**

- **Save** — armazena as posições atuais dos ossos como uma pose nomeada, com uma miniatura da viewport
- **Apply** — posiciona os ossos imediatamente na pose salva
- **Blend** — aplica a pose com intensidade parcial, misturada à posição atual
- **Mirror** — aplica a pose com os lados esquerdo e direito invertidos
- **Delete**, **Rename** e **Category** — gerenciam a lista. **Filter** mostra uma categoria
- **Export** e **Import** — salvam em um arquivo `.bfpose` ou carregam dele

Blend é aplicado imediatamente. Depois de clicar em Blend, ajuste a intensidade da mistura em Adjust Last Operation.

**Onde encontrar:** aba BoneCraft → Review → Pose Library

Descrição da imagem da fonte em inglês (imagem omitida): Uma pose de exemplo salva disponibiliza Apply, Mirror, Blend e os controles da biblioteca.

*Popover do painel nativo, BoneCraft 9.2.18. Uma pose de exemplo salva disponibiliza Apply, Mirror, Blend e os controles da biblioteca.*

---

### Seletor de controles {#control-picker}

**O que faz:** Um mapa clicável dos controles do rig. Clique em uma forma para selecionar seu osso. O seletor destaca os controles selecionados.

**Controles principais:**

- **Generate Picker** — cria o layout a partir do rig
- **Edit Layout** — edição do layout. A linha de cada controle tem ícones para **Move Picker Control**, **Resize Picker Control** e **Relabel Picker Control**. **Snap** alinha os controles a uma grade. **Rebuild Layout** reconstrói o layout
- **Mirror Selection** — seleciona os controles espelhados
- **Pop-up Picker** — abre o seletor em uma janela flutuante, que também oferece **Add Selection Set**

**Onde encontrar:** aba BoneCraft → Review → Control Picker

Descrição da imagem da fonte em inglês (imagem omitida): O Control Picker gerado mostra controles de exemplo, edição do layout, seleção espelhada e a ação para abrir o seletor em pop-up.

*Popover do painel nativo, BoneCraft 9.2.18. O Control Picker gerado mostra controles de exemplo, edição do layout, seleção espelhada e a ação para abrir o seletor em pop-up.*

---

### Camada de controle (IK/FK) {#control-layer-ikfk}

Para uma comparação prática por escrito, siga [Testar pesos e usar IK/FK](06-rig-builder.md#part-c-test-weights-and-use-ikfk).

**O que faz:** Controla os membros de um rig criado por **Build Control Rig**. Alterna um membro entre IK e FK sem saltos. Também converte animação IK em FK, ou FK em IK, ao longo de um intervalo de quadros.

**Controles principais:**

- **IK** e **FK** — alternam o membro e ajustam os novos controles à posição atual dele. O cotovelo ou joelho não salta
- **Bake IK** e **Bake FK** — convertem a animação de um intervalo de quadros para IK ou FK
- **Pole Follow**, **Pin** e **Lock-Free**, além de **Global Rig Scale**, que preserva os bloqueios protegidos

**Onde encontrar:** aba BoneCraft → Review → Control Layer (com um rig criado por **Build Control Rig** selecionado; consulte [Criador de rigs](06-rig-builder.md))

Descrição da imagem da fonte em inglês (imagem omitida): Control Layer mostra alternâncias IK/FK dos membros, ações de consolidação e configurações do rig.

*Captura histórica da oficina. Control Layer mostra alternâncias IK/FK dos membros, ações de consolidação e configurações do rig.*

---

### Ferramentas Rigify {#rigify-tools}

**O que faz:** Detecta um rig de controle Rigify e conecta o painel de coleções, os favoritos e os controles deslizantes de propriedades do BoneCraft aos controles padrão do Rigify.

> Rigify é o sistema integrado do Bforartists para gerar rigs prontos para animação. Se você criou seu rig com Rigify, isto conecta a interface do BoneCraft aos controles IK/FK do Rigify.

**Controles principais:**

- **Auto-Enhance** — configura os painéis do BoneCraft para o rig Rigify selecionado
- **Re-run Enhancement** — os reconstrói do zero
- **Enable Rigify** fica em Quick Rig. A seção recolhível Troubleshooting contém **Generate Control Rig (active metarig)** (consulte [Criador de rigs](06-rig-builder.md))
- Rigify Properties — controles deslizantes de IK/FK, estiramento, espaço do pai e acompanhamento da cabeça/pescoço do rig

**Onde encontrar:** aba BoneCraft → Setup Rigging → Rigify Tools (e a seção Rigify Properties)

Descrição da imagem da fonte em inglês (imagem omitida): Rigify Tools mostra o ponto de entrada para seus aprimoramentos. Selecione um rig Rigify gerado para usar os controles aplicáveis.

*Popover do painel nativo, BoneCraft 9.2.18. Rigify Tools mostra o ponto de entrada para seus aprimoramentos. Selecione um rig Rigify gerado para usar os controles aplicáveis.*

---

### Redirecionamento de animação {#retarget}

**O que faz:** Transfere animação entre esqueletos, como um clipe de captura de movimento para seu avatar. Faz a correspondência dos ossos por nome e direção para preservar a orientação dos membros. A correspondência flexível das clavículas evita rotação excessiva dos ombros.

**Controles principais:**

- **Import Clip** e **Browse Library** — carregam um clipe ou definem uma pasta de biblioteca. Clique no nome de um clipe para selecioná-lo
- **Auto-Match Bones** (marca de verificação na linha de um clipe) — associa ossos de origem e destino. A lista Bone Mapping mostra os pares
- **Preview** e **Stop Preview** — permitem experimentar o resultado
- **Apply** — consolida o clipe no rig

**Onde encontrar:** aba BoneCraft → Setup Rigging → Retarget

Descrição da imagem da fonte em inglês (imagem omitida): Retarget começa com Import Clip e Browse Library. O mapeamento e a prévia do clipe aparecem depois que um clipe é carregado.

*Popover do painel nativo, BoneCraft 9.2.18. Retarget começa com Import Clip e Browse Library. O mapeamento e a prévia do clipe aparecem depois que um clipe é carregado.*

---

### Chaves de forma corretivas {#corrective-shape-keys}

**O que faz:** Chaves de forma que são ativadas quando um osso atinge determinado ângulo, corrigindo pinçamentos ou colapsos em poses extremas.

**Exemplo de uso:** O cotovelo do personagem colapsa quando totalmente dobrado. Uma correção esculpida para o cotovelo, vinculada ao osso do braço, é aplicada automaticamente conforme o cotovelo se dobra.

**Controles principais:**

- New Corrective — configurações de **Shape Key**, **Driver Bone**, eixo de rotação, ângulo de intensidade máxima e entrada gradual
- Lista de corretivas — **Edit** e **Delete**, abaixo da lista, atuam sobre a corretiva selecionada

A malha filha da armature deve ter uma chave de forma de base. Selecione a armature para mostrar New Corrective. A malha filha fornece as chaves de forma.

Para criar uma corretiva:

1. Selecione **Shape Key**.
2. Selecione **Driver Bone**.
3. Selecione o eixo de rotação.
4. Defina o ângulo em que a forma atinge a intensidade máxima.
5. Defina a gradualidade da entrada da forma.
6. Selecione **Create Corrective**.

Para selecionar uma corretiva existente, clique no nome de sua chave de forma na lista.

Edit começa com os valores atuais da corretiva. Depois de clicar em Edit:

1. Em Adjust Last Operation, altere o ângulo.
2. Altere a atenuação.

**Onde encontrar:** aba BoneCraft → Skin → Correctives (a malha precisa de uma chave de forma de base)

Descrição da imagem da fonte em inglês (imagem omitida): Selecione a armature para mostrar New Corrective. A malha filha fornece as chaves de forma.

*Popover do painel nativo, BoneCraft 9.2.18. Selecione a armature para mostrar New Corrective. A malha filha fornece as chaves de forma.*

---

### Ferramentas de curvas {#graph-tools}

**O que faz:** Ferramentas de refinamento de animação para quadros-chave e curvas.

- **Interactive Breakdown** (Breakdowner) — mistura a pose atual entre os quadros-chave mais próximos enquanto você arrasta para a esquerda e para a direita. Seu atalho na viewport 3D é **Ctrl+Shift+B**
- **Apply Delta** (Delta Mover) — desloca os ossos selecionados por uma quantidade exata no espaço da tela ou do mundo. Seu atalho na viewport 3D é **Ctrl+Shift+D**
- **Capture** e **Swap** (Buffer Curves) — mantêm uma cópia das curvas e alternam entre essa cópia e suas edições
- **Smart Bake** — consolida a animação movida por restrições em chaves, descartando chaves redundantes (**Tol** define a tolerância)
- **Euler Filter** — corrige inversões de rotação causadas por bloqueio de gimbal
- Tangent Handles — define os tipos de alça das chaves selecionadas: **Auto**, **Vector**, **Aligned**, **Free** ou **Auto Clamped**

**Onde encontrar:** aba BoneCraft → Review → Graph Tools

Descrição da imagem da fonte em inglês (imagem omitida): Interactive Breakdown inicia um arraste nos ossos de pose selecionados.

*Popover do painel nativo, BoneCraft 9.2.18. Interactive Breakdown inicia um arraste nos ossos de pose selecionados.*

Descrição da imagem da fonte em inglês (imagem omitida): Apply Delta e suas opções de deslocamento.

*Popover do painel nativo, BoneCraft 9.2.18. Apply Delta e suas opções de deslocamento.*

Descrição da imagem da fonte em inglês (imagem omitida): Buffer Curves, Euler Filter e Smart Bake. A seção recolhível Options está fechada.

*Popover do painel nativo, BoneCraft 9.2.18. Buffer Curves, Euler Filter e Smart Bake. A seção recolhível Options está fechada.*

Descrição da imagem da fonte em inglês (imagem omitida): Tangent Handles oferece Auto, Vector, Aligned, Free e Auto Clamped.

*Popover do painel nativo, BoneCraft 9.2.18. Tangent Handles oferece Auto, Vector, Aligned, Free e Auto Clamped.*

---

## Ferramentas de pesos {#weight-tools}

Estas ferramentas controlam como a malha se deforma quando os ossos se movem. Os pesos indicam a cada parte da malha quais ossos acompanhar e em que intensidade.

---

### Recálculo automático de pesos dos ossos {#automatic-bone-weight-recalculation}

**O que faz:** Recalcula os pesos de uma malha a partir do rig existente, sem alterar a malha. Em malhas densas, trabalha por meio de uma malha proxy mais leve para evitar falhas silenciosas.

**Controles principais:** Body calcula os pesos a partir do rig existente. Clothing transfere os pesos de uma malha de origem com pesos corretos. As configurações ficam acima do botão.

1. Em **Mesh to Reweight**, selecione a malha de destino.
2. Em **Existing Armature**, selecione a armature.
3. Selecione o modo Body ou Clothing.

Para o modo Body, selecione o método.

Para o modo Clothing:

1. Em **Weighted Body**, selecione a malha de origem com pesos corretos.
2. Selecione o método.

Para qualquer um dos modos:

1. Defina a mistura.
2. Defina a suavização.
3. Defina o número máximo de influências de ossos por vértice.
4. Defina o peso mínimo.
5. Escolha se deseja manter um backup.
6. Selecione **Automatic Bone Weight Recalculation**.

O atalho do CATS, **Smart Automatic Weights**, abre uma caixa de diálogo para a malha de destino, a armature e o modo. No modo Clothing, a caixa de diálogo também inclui a malha de origem.

**Onde encontrar:** aba BoneCraft → Skin → Weight Tools

Descrição da imagem da fonte em inglês (imagem omitida): Configurações de Automatic Bone Weight Recalculation com a malha e a armature de exemplo selecionadas.

*Popover nativo da versão de teste, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Configurações de Automatic Bone Weight Recalculation com a malha e a armature de exemplo selecionadas.*

---

### Espelhamento de pesos {#weight-mirror}

**O que faz:** Copia pesos de um lado do avatar para o outro. Use em personagens simétricos.

**Controles principais:**

- **Mirror All Weights** — espelha todos os grupos de ossos para o lado oposto
- **Mirror Active Weight** — espelha apenas o grupo de ossos ativo
- **Axis** e **Direction** — escolhem o eixo de reflexão e qual lado fornece os pesos
- **Search Distance** — distância permitida entre a posição refletida de um vértice e sua correspondência espacial
- **Select Unmatched** — seleciona vértices sem par. **Normalize Weights** faz os pesos somarem 1.0 depois

O espelhamento usa posições espaciais, não a topologia da malha.

1. Clique em um botão de espelhamento.
2. Em Adjust Last Operation, selecione **Axis**.
3. Selecione **Direction**.
4. Defina **Search Distance**.

**Mirror Active Weight** também fica em Weights → BoneCraft e na aba Weights da Tool Shelf.

**Onde encontrar:** aba BoneCraft, no modo Weight Paint → Weight Mirror

Descrição da imagem da fonte em inglês (imagem omitida): Ações de Weight Mirror. Depois do clique, defina o eixo em Adjust Last Operation. Defina ali as opções de busca.

*Popover do painel nativo, BoneCraft 9.2.18. Ações de Weight Mirror. Depois do clique, defina o eixo em Adjust Last Operation. Defina ali as opções de busca.*

---

### Transferência de pesos {#weight-transfer}

**O que faz:** Copia pesos de uma malha de origem para a malha ativa. Use ao prender roupas ao corpo ou ao transferir pesos de uma malha de alta resolução para outra de resolução menor.

**Controles principais:** **Normalize**, em Adjust Last Operation, mantém a soma dos pesos em 1.0. **Select Problem Vertices** seleciona vértices com correspondências ruins.

Mantenha a malha de destino ativa no modo Weight Paint.

1. Em **Source Mesh**, selecione a malha de origem.
2. Clique em **Transfer Weights**.
3. Em Adjust Last Operation, selecione o método de transferência.
4. Selecione o filtro de ossos.

O resultado mostra a distância média e a máxima.

**Onde encontrar:** aba BoneCraft, no modo Weight Paint → Weight Transfer (também em Skin → Weight Tools)

Descrição da imagem da fonte em inglês (imagem omitida): Escolha uma Source Mesh antes de Transfer Weights. Os campos de distância permanecem com seus valores iniciais neste exemplo.

*Popover do painel nativo, BoneCraft 9.2.18. Escolha uma Source Mesh antes de Transfer Weights. Os campos de distância permanecem com seus valores iniciais neste exemplo.*

---

### Tabela de pesos {#weight-table}

**O que faz:** Mostra o peso exato do vértice selecionado para cada osso. Você pode definir valores precisos de peso.

**Como usar:**

1. Entre no modo Weight Paint.
2. Ative **vertex-selection masking** (máscara de seleção de vértices).
3. Selecione um vértice.

A tabela lista os ossos e pesos do vértice selecionado.

4. Clique no ícone de mão na linha de um osso.
5. Em Adjust Last Operation, defina **Weight**.

Add Influence usa o osso que você seleciona. Depois de Add Influence, defina também seu novo peso em Adjust Last Operation. Com vários vértices selecionados, **Normalize All Vertices** normaliza todos os vértices selecionados.

**Onde encontrar:** aba BoneCraft, no modo Weight Paint → Weight Table

Descrição da imagem da fonte em inglês (imagem omitida): Weight Table com vários vértices selecionados. Selecione um vértice para editar os pesos em detalhe.

*Popover do painel nativo, BoneCraft 9.2.18. Weight Table com vários vértices selecionados. Selecione um vértice para editar os pesos em detalhe.*

---

### Preenchimento completo {#flood-fill}

**O que faz:** Altera os pesos do grupo de vértices ativo em toda a malha, incluindo vértices não selecionados.

Antes de usar qualquer ação de Flood Fill:

1. Selecione a malha.
2. Entre no modo Weight Paint.
3. Torne ativo o grupo de vértices desejado.

**Ações:**

- **Flood to 0.0** remove os pesos positivos atribuídos do grupo ativo em toda a malha. Os outros grupos de vértices permanecem inalterados.
- **Flood to 1.0** atribui 1.0 ao grupo ativo em todos os vértices. Para cada vértice, remove outros pesos positivos se a soma deles exceder 1e-6.
- **Flood to Custom** atribui um **Value** positivo ao grupo ativo em todos os vértices. Com **Normalize** ativado, também normaliza os pesos em toda a malha. Um **Value** de 0 não faz atribuições nem normalização. Para limpar os pesos, use **Flood to 0.0**.

O menu e a barra Weights chamam os botões de valor fixo de Flood to Zero e Flood to One.

Para um preenchimento personalizado:

1. Selecione **Flood to Custom**.
2. Logo depois, defina **Value** em Adjust Last Operation.
3. Ative ou desative **Normalize**.

**Onde encontrar:** no modo Weight Paint: aba BoneCraft → Skin → Weight Tools; também em Weights → BoneCraft e Tool Shelf → Weights → BoneCraft

Descrição da imagem da fonte em inglês (imagem omitida): Ações de Flood Fill. Depois do clique, defina o valor personalizado em Adjust Last Operation.

*Popover do painel nativo, BoneCraft 9.2.18. Ações de Flood Fill. Depois do clique, defina o valor personalizado em Adjust Last Operation.*

---

### Deformação versus controle {#deform-vs-control}

**O que faz:** Separa os ossos de deformação dos ossos de controle. Os ossos de deformação movem a malha. O animador move os ossos de controle. A ferramenta marca os ossos de deformação e os renomeia conforme uma nomenclatura de deformação. Também exporta um esqueleto apenas com ossos de deformação.

**Onde encontrar:** aba BoneCraft, em Pose Mode → Deform vs Control

Descrição da imagem da fonte em inglês (imagem omitida): Listas Deform e Control no rig de exemplo. Este rig tem 19 ossos de deformação e nenhum osso de controle.

*Popover nativo da versão de teste, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Listas Deform e Control no rig de exemplo. Este rig tem 19 ossos de deformação e nenhum osso de controle.*

---

### Delta Mush {#delta-mush}

**O que faz:** Uma deformação suavizada que reduz pinçamentos nas articulações. A malha mantém sua forma em repouso, mas se deforma de maneira mais limpa em movimento.

**Como usar:** Estas ações exigem Object Mode e uma malha ativa.

1. Clique em **Add Delta Mush**.

A ferramenta adiciona o modificador e o vincula à forma de repouso. Logo após essa operação, ajuste suas opções:

2. Em Adjust Last Operation, defina **Iterations**.
3. Defina **Smooth Strength**.
4. Ative ou desative **Pin Borders**.
5. Ative ou desative **Only Smooth Deform**.

Depois que o modificador existe, o painel mostra **Rebind** e **Remove**. A seção recolhível Settings contém os controles de iterações, intensidade de suavização e fixação das bordas do modificador.

**Onde encontrar:** BoneCraft → Skin → Delta Mush (Object Mode; Mesh)

Descrição da imagem da fonte em inglês (imagem omitida): Add Delta Mush inicia a configuração. Ajuste suas opções logo após o clique.

*Popover do painel nativo, BoneCraft 9.2.18. Add Delta Mush inicia a configuração. Ajuste suas opções logo após o clique.*

---

### Envolvimento por proximidade {#proximity-wrap}

**O que faz:** Faz uma malha acompanhar a superfície de outra, como uma segunda pele. Útil para roupas ajustadas ao corpo.

**Como usar:** Estas ações exigem Object Mode e uma malha de destino ativa. Mantenha a armature da malha condutora na pose de repouso ao vincular.

1. Selecione a malha de destino.
2. Selecione uma **Driver Mesh** diferente.
3. Clique em **Bind Proximity Wrap**.

A seção recolhível Options abaixo do botão lista **Falloff Type** e **Max Distance**. Na versão 9.1.2, a configuração armazena esses valores, mas eles não alteram o vínculo Surface Deform. Depois de vincular, o painel mostra **Rebind** e **Unbind**. Unbind desativa o modificador na viewport e na renderização. Não remove o modificador.

**Onde encontrar:** BoneCraft → Skin → Proximity Wrap (Object Mode; Mesh)

Descrição da imagem da fonte em inglês (imagem omitida): Escolha uma Driver Mesh antes de Bind Proximity Wrap. A seção recolhível Options está fechada.

*Popover do painel nativo, BoneCraft 9.2.18. Escolha uma Driver Mesh antes de Bind Proximity Wrap. A seção recolhível Options está fechada.*

---

## Controles de rig {#rig-controls}

Estas ferramentas aparecem na aba BoneCraft em Pose Mode.

---

### Troca de espaço {#space-switch}

**O que faz:** Muda qual espaço um osso acompanha durante a animação. Uma mão segurando um acessório pode passar de acompanhar o corpo a ficar parada no mundo com um clique.

**Controles principais:**

- **Add Space** e **Remove Space** (ícone X em Manage Spaces) — os espaços que um osso pode acompanhar (World, Origin ou outro osso)
- Um botão por espaço, com o nome desse espaço. O espaço atual tem uma marca ●. Para trocar o espaço do osso, clique no botão de outro espaço

**Onde encontrar:** aba BoneCraft, em Pose Mode → Space Switch

Descrição da imagem da fonte em inglês (imagem omitida): Space Switch antes de qualquer espaço ser definido. Add Space inicia a configuração.

*Popover do painel nativo, BoneCraft 9.2.18. Space Switch antes de qualquer espaço ser definido. Add Space inicia a configuração.*

---

### IK por spline {#spline-ik}

**O que faz:** Faz uma cadeia de ossos acompanhar uma curva. Use para caudas, tentáculos, cordas, cabelos compridos e colunas que precisam de movimentos amplos e suaves.

**Como usar:**

1. Torne ativo o osso inicial.
2. Clique em **Generate Spline IK**.
3. Em Adjust Last Operation, defina **Chain Length**.
4. Defina **Curve Resolution**.
5. Defina **Stretch**.
6. Defina **Volume Preservation**.

**Remove Spline IK** remove a configuração.

**Onde encontrar:** aba BoneCraft, em Pose Mode → Spline IK

Descrição da imagem da fonte em inglês (imagem omitida): Ações de Spline IK. Defina as opções da cadeia em Adjust Last Operation depois da geração.

*Popover do painel nativo, BoneCraft 9.2.18. Ações de Spline IK. Defina as opções da cadeia em Adjust Last Operation depois da geração.*

---

### Dinâmica de cadeias {#chain-dynamics}

**O que faz:** Adiciona movimento secundário semelhante ao da física a uma cadeia de ossos. Os ossos ficam atrasados em relação ao pai em movimento e oscilam de volta quando ele para. Alguns usos são mechas de cabelo, caudas e acessórios.

**Como usar:**

1. Selecione a cadeia de ossos.
2. Clique em **Add Chain Dynamics**.
3. Em Adjust Last Operation, defina **Stiffness**.
4. Defina **Damping**.
5. Defina **Mass**.
6. Defina **Gravity Scale**.

A seção recolhível Settings abaixo da ação também lista esses parâmetros. Depois que a dinâmica existe, o painel mostra **Bake** e **Remove**. A colisão usa uma forma esférica simplificada; por isso, superfícies côncavas podem não colidir corretamente.

**Onde encontrar:** aba BoneCraft, em Pose Mode → Chain Dynamics

Descrição da imagem da fonte em inglês (imagem omitida): Add Chain Dynamics inicia a configuração. Expanda Settings quando precisar de seus parâmetros.

*Popover do painel nativo, BoneCraft 9.2.18. Add Chain Dynamics inicia a configuração. Expanda Settings quando precisar de seus parâmetros.*

---

### Fita {#ribbon}

**O que faz:** Cria uma fita de Bendy Bones, ossos que se curvam e torcem suavemente, para lábios, sobrancelhas, cintos e outras áreas curvas e flexíveis.

**Como usar:**

1. Selecione a cadeia de ossos.
2. Clique em **Generate Ribbon**.
3. Em Adjust Last Operation, defina **Control Bones**.
4. Defina **Ribbon Width**.

**Remove Ribbon** remove a configuração.

**Onde encontrar:** aba BoneCraft, em Pose Mode → Ribbon

Descrição da imagem da fonte em inglês (imagem omitida): Ações de Ribbon e comprimento da cadeia. Ajuste a fita gerada logo após o clique.

*Popover do painel nativo, BoneCraft 9.2.18. Ações de Ribbon e comprimento da cadeia. Ajuste a fita gerada logo após o clique.*

---

### Biblioteca de visemas {#viseme-library}

**O que faz:** Cria e gerencia conjuntos de visemas (formas da boca) vinculados a chaves de forma. Também gera chaves de sincronização labial a partir de texto. Para mapear visemas do VRChat, use VRChat Viseme Mapping. Para gerar novos visemas, use a seção CATS Visemes.

**Controles principais:**

- **New Set** e **Delete** — criam ou removem um conjunto de visemas
- Em cada conjunto, um botão por visema (com ícone de alto-falante) permite visualizá-lo
- Lip Sync — converte texto em chaves de visemas, com quadros por fonema e suavização

**Onde encontrar:** CATS → Avatar Tools → Viseme Library (Armature); Lip Sync (Pose Mode)

Descrição da imagem da fonte em inglês (imagem omitida): Viseme Library começa com New Set. Mude para Pose Mode para usar Lip Sync.

*Popover do painel nativo, BoneCraft 9.2.18. Viseme Library começa com New Set. Mude para Pose Mode para usar Lip Sync.*

Descrição da imagem da fonte em inglês (imagem omitida): Texto de Lip Sync e Generate Lip Sync. Expanda Options para configurar o tempo e a suavização.

*Popover do painel nativo, BoneCraft 9.2.18. Texto de Lip Sync e Generate Lip Sync. Expanda Options para configurar o tempo e a suavização.*

---

### Configurar chave dirigida {#set-driven-key}

**O que faz:** Vincula um valor de transformação de osso a outro sem expressões Python. Por exemplo, mover um osso de controle ao longo de X pode elevar um osso de destino ao longo de Z. Este painel cria alvos de transformação de ossos.

1. Selecione **Driver Bone**.
2. Selecione **Driver Attribute**.
3. Selecione **Target Bone**.
4. Selecione **Target Attribute**.
5. Defina a pose dos ossos.
6. Grave cada ponto.
7. Selecione **Create SDK**.

**Controles principais:**

- **Driver Bone** e **Driver Attribute** — o que conduz
- **Target Bone** e **Target Attribute** — o que é conduzido
- **Set Value** e **Record Point** — gravam um ponto na curva
- **Create SDK** — cria o driver

**Onde encontrar:** aba BoneCraft, em Pose Mode → Set Driven Key

Descrição da imagem da fonte em inglês (imagem omitida): Escolha os ossos condutor e de destino antes de gravar um ponto de chave dirigida. Esses campos não estão atribuídos no exemplo.

*Popover do painel nativo, BoneCraft 9.2.18. Escolha os ossos condutor e de destino antes de gravar um ponto de chave dirigida. Esses campos não estão atribuídos no exemplo.*

---

### Validador de rig {#rig-validator}

**O que faz:** Verifica o rig conforme regras e relata problemas. As verificações abrangem nomenclatura, ossos ausentes, restrições quebradas, hierarquia, pesos, drivers que precisam de Python e regras de Mechanisms. Nomes de ossos com hífens (como `DEF-upper_arm.L`) são aceitos.

**Controles principais:**

- **Run Validation** — executa todas as verificações e lista os resultados
- **Export Report** — salva os resultados em um arquivo

O Task Board (aba BoneCraft → Overview → Task Board) mostra uma tarefa de validação quando uma verificação falha.

**Onde encontrar:** aba BoneCraft → Review → Rig Validator

Descrição da imagem da fonte em inglês (imagem omitida): A validação relata um aviso de coleção. Sem uma malha filha do rig de exemplo, a validação pula a verificação de pesos.

*Popover nativo da versão de teste, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. A validação relata um aviso de coleção. Sem uma malha filha do rig de exemplo, a validação pula a verificação de pesos.*

---

### Notas do rig {#rig-notes}

**O que faz:** Notas escritas vinculadas aos ossos do rig: o que você configurou, lembretes e notas para colaboradores.

**Controles principais:** **Add Note** e **Remove** em cada nota. Rig Readme mostra as notas do rig como uma página somente para leitura.

**Onde encontrar:** aba BoneCraft → Overview → Rig Notes e Review → Rig Readme

Descrição da imagem da fonte em inglês (imagem omitida): Uma nota vinculada a Hips em Pose Mode. Add Note cria uma anotação. Remove exclui essa anotação.

*Popover nativo da versão de teste, candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Uma nota vinculada a Hips em Pose Mode. Add Note cria uma anotação. Remove exclui essa anotação.*

Próximo: [Criador de rigs](06-rig-builder.md)
