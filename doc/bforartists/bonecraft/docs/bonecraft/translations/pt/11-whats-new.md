# Novidades {#whats-new}

[← Sumário](index.md)

Da mais recente para a mais antiga.

## 9.2.19 — Controles de painéis (versão candidata local) {#9219--panel-controls-local-candidate}

Esta versão candidata local ainda não foi publicada. A versão independente continua sendo a 9.2.18.

- Collections e Visibility Bookmarks inicializam suas configurações fora do desenho dos painéis.
- Os painéis agrupados usam seus próprios controles e verificam a seleção e o modo atuais.
- Hair Physics lê os ossos de pose selecionados nos aplicativos hospedeiros atuais.
- Bone Inspector mostra o roll dos ossos em repouso e copia nomes pelo botão no cabeçalho.
- Eye Tracking mostra valores em graus, preservando as configurações salvas.

O manual em inglês acrescenta imagens correspondentes às ferramentas e configurações. As imagens anteriores mantêm seus rótulos de versão originais.

## 9.2.18 — Formas de mecanismos salvas {#9218--saved-mechanism-forms}

As formas salvas anteriormente continuam legíveis e utilizáveis nas compilações atuais do Bforartists. Abrir ou aplicar uma forma não a salva novamente. **Save Form** captura os valores atuais usando o formato atual. As alças, os controles deslizantes e os locais dos painéis existentes permanecem iguais.

A versão corrige os diagnósticos de compatibilidade em aplicativos hospedeiros mais recentes. O diagnóstico, por si só, não provava que os aplicativos anteriores não podiam usar formas salvas. Consulte [Formas](07-mechanisms.md#forms) e as [notas da versão](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md).

Esta é a versão independente do Toolkit. Ela não estabelece aceitação no Bforartists oficial. Os limites históricos das capturas e dos testes dos tutoriais permanecem em seus capítulos.

## 9.2.17 — Nomes de exportação e restauração do modo {#9217--export-naming-and-mode-restoration}

**Unity / VRChat** e **Unreal Engine 5** agora oferecem **Bone Names**: **Keep Original Names**, **Unity-Preset** e **Unreal-Preset**. A prévia mostra os ossos reconhecidos e os nomes propostos. A nomeação afeta as cópias de exportação, incluindo grupos de vértices, canais de animação e referências dos arquivos auxiliares do Unity. O rig de trabalho mantém seus nomes.

Os dois botões principais de exportação para engines agora aceitam os modos Objeto, Pose e Edição. Eles restauram o modo e a seleção originais após a exportação ou limpeza. A consolidação FBX da ação ativa não exige mais um clipe NLA separado.

Ossos humanoides opcionais reconhecidos, dedos das mãos e dos pés participam da nomeação. Nomes em conflito ou mapeamentos ambíguos bloqueiam a renomeação. Esses perfis mantêm a hierarquia, a orientação e a pose de repouso. Eles não constroem um esqueleto Manny/Quinn.

A saída renomeada de **Export (Profile)** oferece suporte a **Active Action** e **No Animation**. **All Actions** exige **Keep Original Names**. Consulte [Exportação para engines de jogos](08-vrchat.md#game-engine-export) e as [notas da versão 9.2.17](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.17/RELEASE-NOTES.md).

## 9.2.15 — Fluxo revisado de atlas de materiais {#9215--reviewed-material-atlas-workflow}

O painel agora apresenta três etapas: seleção de alvos, seleção de materiais e texturas e, por fim, consolidação e revisão. **Smart Combine Materials** é o atalho automático inicial. Após a análise, **Refresh Analysis** reconstrói as listas. **Bake Checked Sources** consolida as escolhas revisadas.

As duas listas de fontes têm **Select All** e **Deselect All**. Esses controles alteram as caixas Include apenas no grupo e na lista de fontes ativos. As texturas ausentes permanecem desmarcadas. A seleção em massa não ativa um grupo desativado. **Object → Atlas Source Selection** oferece as mesmas ações.

**Source Details** começa recolhido. **Copy Debug Report** fica em **Advanced Options**. Backup, Accept e Revert continuam visíveis. Essas alterações da interface mantêm o fluxo de consolidação e as restrições de preservação existentes.

## 9.2.14 — Malhas somente com cor {#9214--color-only-meshes}

Malhas somente com cor, sem UVs criadas pelo autor, recebem a camada UV do atlas consolidado durante a montagem final.

## 9.2.13 — Contagem de materiais {#9213--material-counts}

As estimativas e os resultados de materiais contam os slots de atlas em cada malha de saída. Revert redefine esses resultados.

## 9.2.12 — UV0 de exportação {#9212--export-uv0}

A malha de atlas reconstruída exporta `atlas_uv` como UV0 enquanto **Keep Source UV Maps** estiver desativado. Manter os mapas de origem pode deixar o atlas em UV1.

## 9.2.11 — Verificações de fontes alteradas {#9211--changed-source-checks}

A verificação prévia rejeita fontes de materiais analisadas que estejam ausentes ou tenham sido alteradas, antes de criar um backup do atlas.

1. Atualize a análise.

2. Revise novamente as escolhas de fontes.

## 9.2.10 — Materiais excluídos {#9210--excluded-materials}

A montagem do atlas preserva os materiais excluídos e as referências compartilhadas de materiais.

## 9.2.9 — Fontes ocultas na renderização {#929--render-hidden-sources}

O combinador consolida fontes ocultas na renderização usando cópias temporárias. Revert restaura a visibilidade original.

## 9.2.8 — Entradas conectadas dos shaders {#928--connected-shader-inputs}

O combinador preserva as redes conectadas de tonalidade, mapeamento e alfa do Principled durante a consolidação. MToon mantém seu caminho alternativo. **Metallic** e **Pack ORM Channels** continuam bloqueados pela verificação prévia.

## 9.2.7 — Classificação de transparência {#927--transparency-classification}

A classificação de materiais trata a opacidade DITHERED moderna e o alfa vinculado ou constante. A configuração de renderização, por si só, não força mais um material opaco a entrar em um grupo transparente.

## 9.2.6 — Instalação de MMD e PMX {#926--mmd-and-pmx-installation}

O instalador reconhece as extensões MMD modernas e os complementos legados. A instalação de extensões preserva suas dependências e informa repositórios locais indisponíveis. Uma extensão ativada é reconhecida mesmo sem metadados de complemento legado. Importações PMX canceladas continuam canceladas, em vez de informar sucesso.

O [registro datado das correções](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md) abrange as versões 9.2.6–9.2.15 e suas verificações com cenas de teste geradas. A [revisão da interface 9.2.15](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md) registra verificações dos operadores e limites dos testes visuais. Esses registros históricos não afirmam que todo o manual tenha sido repetido recentemente na versão 9.2.18.

## 9.2.5 — Aba de catálogo Starter Rigs {#925--starter-rigs-catalog-tab}

Starter Rigs agora usa uma aba de catálogo na prateleira nativa inferior de assets. Ela substitui os controles do canto superior esquerdo da viewport. Para mostrar a aba ao lado de outros catálogos, ative **Starter Rigs** uma vez no menu de catálogos da prateleira. A importação nativa de assets e **Add → Armature → Starter Rig Catalog** continuam disponíveis.

## 9.2.4 — Quadro de tarefas e ferramentas nativas {#924--task-board-and-native-tools}

**Open Health Check** agora executa a validação do rig e abre os resultados. Antes de usar, selecione uma armadura ou sua malha vinculada. **Quick Wins** mostra até três recomendações. **Remaining Tasks** exclui esses cartões. **Refresh Task Board** verifica novamente.

Place Rig Markers e Build Mechanism continuam disponíveis como ferramentas da viewport. Seu registro não prejudica mais Grab/Move nativo nem a alternância de ferramentas nos modos Objeto e Pose.

## 9.2.3 — Local de exportação para VRChat {#923--vrchat-export-location}

Remove o painel Export to VRChat duplicado de Avatar Tools. A exportação permanece em CATS → Import / Export → Unity / VRChat.

## 9.2.2 — Interface atual {#922--current-interface}

Cada aba contém um grupo de trabalho. Setup Rigging, Skin, Review, Avatar Tools e Facial são seções expansíveis dentro das abas. Os caminhos abaixo usam os rótulos da interface em inglês. Os rótulos traduzidos dependem da preferência Language.

- Bone Merge → BoneCraft → Setup Rigging
- Delta Mush / Proximity Wrap → BoneCraft → Skin
- Viseme Library / Lip Sync → CATS → Avatar Tools
- VRChat Viseme Mapping / Face Tracking → CATS → VRChat Tools → Facial

## 9.2.0 (outubro de 2026) {#920-october-2026}

- **Catálogo inicial completo:** os nove esqueletos/metarigs incluídos têm miniaturas desde o início. São Basic Humanoid, Simple Human, Full Human, Basic Quadruped, Cat, Horse, Wolf, Bird e Shark. O seletor do catálogo agrupa Humans, Quadrupeds e Other Animals.
- **Rigify quando necessário:** Basic Humanoid funciona de forma independente. Os rigs iniciais do Rigify continuam visíveis enquanto ele está desativado. Selecionar um deles oferece **Enable Rigify & Add Rig** ou Cancel. Cancelamento, falha na ativação ou predefinição indisponível não adicionam um rig.
- **Prateleira opcional, local histórico na versão 9.2.0:** o controle **Starter Rigs** do cabeçalho da viewport voltou à prateleira comum de assets. A escolha persistia nas preferências. A versão 9.2.5 substitui esse controle por uma aba nativa de catálogo. **Add → Armature → Starter Rig Catalog** ainda abre o seletor em uma janela flutuante.
- **Clicar ou arrastar:** clicar em um rig inicial o adiciona, assim como soltá-lo dentro da viewport. O ajuste à malha começa ativado. A atribuição de pesos e a geração de controles começam desativadas. Adjust Last Operation controla essas opções. As verificações de clique, soltura, cancelamento e Desfazer/Refazer nativos usaram o Bforartists 5.2.0.

## 9.1.2 (outubro de 2026) {#912-october-2026}

- **Controle Scene Properties:** Preferences > Tabs tem uma nova linha Scene Properties. Seu botão Show controla todas as seções do BoneCraft na aba Properties > Scene. São Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools e Import / Export. O controle começa ativado e fica azul enquanto ativo. Ele não desativa o complemento nem altera as abas da viewport ou a aba Armature. Consulte [Onde fica cada coisa](01-start.md#where-things-are).

## 9.1.1 (outubro de 2026) {#911-october-2026}

- **Ícones mais claros:** cada ícone agora tem um único significado em toda a interface. Cerca de 60 botões receberam ícones do Bforartists que representam melhor suas funções. Exemplos incluem Apply All Transforms, Decimate, Normalize Names, Translate, Merge, Separate, Blend Pose e Lip Sync. Cada botão usa o mesmo ícone em todos os painéis.
- **Painéis mais tranquilos:** títulos e textos fixos não têm mais ícones de assunto. Dicas que informam um estado mostram o ícone de informação, aviso ou verificação.
- **Grade de ícones legível:** cada botão nas abas Pose e Weights da Tool Shelf tem seu próprio ícone, mantendo a leitura em uma prateleira estreita.

## 9.1.0 (outubro de 2026) {#910-october-2026}

- **Ferramentas onde o Bforartists coloca as suas:** o BoneCraft adiciona entradas a Add → Armature e aos menus Pose, Weights e Object. Também adiciona painéis de botões às abas Pose e Weights da Tool Shelf do Bforartists.
- **Execute primeiro, ajuste depois:** Quick Rig, Fit Dropped Rig e as ferramentas de pesos executam imediatamente com os últimos valores usados. Ribbon, Spline IK, Delta Mush e as ferramentas de ossos do CATS também executam imediatamente com seus últimos valores. Adjust Last Operation controla as opções depois. As ferramentas usam menos janelas de confirmação.
- **Ações primeiro, opções recolhidas:** vários painéis mostram botões acima de um grupo recolhido de configurações opcionais. Entradas obrigatórias e opções de limpeza de Fix Model permanecem acima da ação. As configurações usam caixas de seleção, não botões. Os cabeçalhos dos painéis não têm ícones.
- **Ferramentas de gestos:** Place Rig Markers e Build Mechanism ficam na barra de ferramentas da viewport. Place Rig Markers posiciona o próximo marcador do Auto-Rig Wizard quando você clica na malha. Build Mechanism inicia uma articulação ou vínculo quando você clica em uma peça.
- **Seções de avatar, local histórico na versão 9.1.0:** Avatar Tools reunia mapeamento humanoide, cabelo, visemas e exportação. A seção separada VRChat Tools agrupa utilitários de desempenho, roupas e nomes. A exportação agora fica em **Import / Export → Game Engine Export → Unity / VRChat**.
- **Dicas:** cada operador e cada opção se explica.
- **Mostrar, em vez de ocultar:** quando não há rig disponível, as seções continuam visíveis e explicam o que selecionar. Auto-Rig Wizard aparece primeiro em Rig Builder. As prateleiras começam com largura suficiente para leitura.
- **Correções:** Generate Spline IK volta a funcionar. Add Influence usa o osso escolhido. As prévias de visemas usam seu conjunto.

## 9.0.0 (outubro de 2026) {#900-october-2026}

- **Mechanisms:** uma nova seção na aba BoneCraft e na aba Properties Scene cria rigs de objetos e máquinas. Seus tipos são Hinge, Slide, Telescope, Piston, Gear Link, Follow e Sequence. Etapas guiadas os constroem. Test verifica seus movimentos. O BoneCraft nunca sobrescreve automaticamente uma edição manual. **Keep mine** mantém a edição. **Restore** reconstrói o mecanismo. Consulte [Mechanisms](07-mechanisms.md).
- **Arquivo de exemplo:** `examples/crescent-rose/` contém Crescent Rose com rig criado em Mechanisms (formas de foice, fuzil e compacta), e o [capítulo 12](12-crescent-rose.md) do manual o constrói passo a passo.
- **Lados das abas:** cada aba da viewport pode ficar na Tool Shelf à esquerda ou na barra lateral à direita (Preferences → Tabs → Left / Right). BoneCraft e Rig Builder começam à esquerda; CATS, à direita.
- **Rig Builder:** sempre aparece na aba Properties Scene e também tem sua própria aba na viewport. Um leiaute compacto cabe em uma Tool Shelf estreita. A biblioteca de assets BoneCraft Rigs inclui Basic Humanoid. Fit Dropped Rig ajusta um rig solto da prateleira de assets.
- **Aba CATS:** Import / Export foi movido para a aba CATS. CATS, VRChat e Import / Export também ficam sempre na aba Scene.
- **Show Helpers:** uma preferência mostra ou oculta os textos de orientação do BoneCraft. Compact Mode controla a mesma preferência.
- **Rig Validator:** nomes de ossos com hífens passam. Drivers geram aviso apenas para expressões que precisam de Python. As verificações também abrangem rigs de Mechanisms. A tarefa de validação do Task Board volta a emitir resultados.
- **Nome:** o complemento se chama BoneCraft.

## 8.9.x (setembro–outubro de 2026) {#89x-septemberoctober-2026}

- **8.9.6:** toda a peça do vestido acompanha os ossos da saia sem atravessar o quadril. As correções dos cantos da boca ao abrir a mandíbula oferecem suporte a lábios aderentes.
- **8.9.5:** a troca IK/FK do cotovelo preserva a pose sem salto. A detecção dos ombros é simétrica. Os marcadores dos olhos não saltam mais de posição. Control Picker mostra a seleção. Outras alterações incluem cantos da boca mais arredondados, correção do vestido sobre a coxa, clavículas mais relaxadas no redirecionamento e exportação em pose T.
- **8.9.4:** correções substituem Preserve Volume para joelhos mais arredondados. Esta versão também adiciona chaves de contato para flexões profundas e uma mesclagem na junção do ombro.
- **8.9.3:** ossos de saia com dois segmentos acompanham as pernas. As pernas também empurram esses ossos.
- **8.9.2:** chaves de forma criam piscadas sem dobras nas pálpebras. A abertura da boca é oval.
- **8.9.1:** a atribuição de pesos a malhas densas fica mais rápida (678,000 vértices: de 232 s para 57 s). Bone heat usa uma malha proxy mais leve em vez de falhar silenciosamente.
- **8.9.0:** esta versão adiciona chaves de forma corretivas das articulações e controles faciais para direção do olhar, piscadas e acompanhamento dos lábios. As roupas se dobram com as articulações.
- A versão 8.9 também adiciona recálculo automático dos pesos dos ossos e seleção mais clara no atlas.

## 8.7–8.8 (setembro de 2026) {#8788-september-2026}

- **8.8.0:** o painel de redirecionamento funciona em aplicativos hospedeiros Blender 5. A colocação dos marcadores dos dedos usa a forma da mão. Outras alterações incluem alongamento IK até a pele, uma opção Preserve Volume e uma correção da vinculação de Delta Mush.
- **8.7.0:** esta versão adiciona um rig de controle integrado, detecção de articulações pelo traçado dos membros, redirecionamento com direções correspondentes e ossos de torção.

## 8.5–8.6 (julho de 2026) {#8586-july-2026}

- **8.6.1–8.6.3:** Material Atlas adiciona diagnósticos dos blocos após a consolidação e melhor separação de materiais mistos. Ele verifica a transparência MToon em relação ao alfa real da textura e preserva essa transparência ao criar o atlas.
- **8.5.5–8.5.10:** os materiais VRM / MToon respeitam o modo alfa. O alfa funciona em aplicativos hospedeiros Blender 5. Outras alterações evitam emissão excessiva e adicionam diagnósticos em magenta e nomes seguros para atlas.
- **8.5.4:** os mapeamentos humanoides são carregados corretamente. Esta versão também adiciona orientações de Naming Prep.
- **8.5.2–8.5.3:** essas versões adicionam importação de downloads do VRoid (.zip) e um cartão de transferência de projeto VRoid.
- **8.5.1:** a exportação FBX preserva blend shapes.

## Versões anteriores {#earlier-versions}

**8.5.0:** após a consolidação, Smart Combine torna `atlas_uv` o UV0 de exportação por padrão. A menos que **Keep Source UV Maps** esteja ativado nas configurações avançadas, ele remove o mapa UV de origem anterior ao atlas da malha de atlas gerada. A compilação aberta do Blender agora compartilha os controles CATS / Material Combiner / derivados do UVToolkit. Os sistemas de rigging para produção, controles, redirecionamento/exportação e versões exclusivas do B4Artists continuam exclusivos do B4Artists.

A versão 8.5.0 também atualiza a exportação e a validação. As exportações VRChat, VRM, MMD e Unreal agora têm controles de pasta e nome de arquivo nos painéis do BoneCraft. As configurações de exportação não dependem mais apenas dos padrões do navegador de arquivos do Blender. As exportações FBX para VRChat/Unity e Unreal ativam **Embed Textures** por padrão para simplificar a importação de materiais. A menos que **Helper Meshes** esteja ativado, a exportação VRChat exclui do FBX as malhas auxiliares e de formas de controles. O painel VRM adiciona **Lint Now** e **Fix Humanoid Map**. Fix Humanoid Map corrige mapeamentos de aliases humanoides desatualizados antes da exportação, sem renomear ossos.

**8.4.5:** durante a consolidação, Smart Combine faz as texturas de origem amostrarem o UV preservado anterior ao atlas. Ele valida a malha de atlas gerada antes de ocultar os originais. Redefine todas as faces do atlas para o slot final do material do atlas. Isso evita seções de túnicas/roupas cinzas ou embaralhadas.

**8.4.4:** Material Atlas Combiner adiciona controles de inspeção antes da consolidação para equivalência de qualidade. Eles incluem diagnósticos de shaders/materiais, rótulos da função das texturas, marcadores de fontes duplicadas/compartilhadas, substituições de tamanho por material e predefinições de empacotamento. As consolidações opcionais de saída abrangem Normal/Emission/Roughness. A verificação prévia bloqueia o empacotamento de canais Metallic/ORM até que esse caminho seja verificado.

**8.4.3:** Material Atlas Combiner adiciona métodos selecionáveis de empacotamento UV ao fluxo existente. As opções incluem Smart Pack, Grid Pack, Seeded Variation, Oriented Pack, Fit 0-1 Bounds, Advanced Variation e Rotation Step. O relatório de depuração e o registro de consolidação registram os detalhes do método UV.

**8.4.2:** durante a consolidação, Material Atlas Combiner usa o UV do atlas gerado como alvo. Os nós de textura de origem copiados leem explicitamente o UV anterior ao atlas. Isso corrige erros no atlas de túnicas/roupas causados pela amostragem de mapas UV diferentes nas texturas de origem e no atlas consolidado. As linhas selecionáveis de materiais e texturas da versão 8.4.1 continuam disponíveis.

**7.1.3 (limpeza dos rótulos de preferências):** dois controles das preferências do complemento têm novos rótulos correspondentes às abas da barra lateral. “VRChat Avatar Tools” passa a ser **CATS**, correspondendo à aba CATS da barra lateral. “Task Board & Sidebar” passa a ser **Rig Builder**, correspondendo à aba Rig Builder da barra lateral. Somente os rótulos dos controles em Edit > Preferences > Add-ons > BoneCraft mudaram. Nenhuma ferramenta foi removida.

**7.1.1:** o BoneCraft adiciona o conjunto completo do CATS para limpeza, otimização e configuração de avatares do VRChat. CATS tem sua própria aba na barra lateral. Seu pipeline orienta a ordem das operações.

Próximo: [Tutorial: Crescent Rose com Mechanisms](12-crescent-rose.md)
