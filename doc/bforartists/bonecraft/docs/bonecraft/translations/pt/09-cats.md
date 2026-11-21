# Ferramentas do CATS {#cats-tools}

[← Sumário](index.md)

As ferramentas do CATS ficam na seção **CATS → CATS** da barra lateral à direita. Pressione **N** para mostrar a barra lateral.

As ferramentas também aparecem em **Properties → Scene** quando Preferences → Tabs → Scene Properties → Show está ativado. O controle CATS da viewport e o controle Scene Properties controlam suas cópias de forma independente.

As ferramentas seguem [O pipeline do CATS](04-cats-pipeline.md). No topo da seção, selecione a armadura a processar.

Na versão 9.1, vários painéis contêm configurações opcionais em um grupo recolhido abaixo dos botões de ação. As entradas obrigatórias permanecem acima dos botões. Elas incluem as opções de limpeza de Fix Model, o idioma de origem de Translate Bone Names, as formas da boca e os ossos dos olhos.

As ferramentas de ossos com Adjust Last Operation executam imediatamente. Após a operação, ajuste ali suas opções. Passe o ponteiro sobre um botão ou opção para ler sua dica.

---

## Fix Model {#fix-model}

**Fase do pipeline:** 1 (revisão de limpeza recomendada)

**O que faz:** executa as operações de limpeza ativadas na malha selecionada. Um avatar sem problemas pode não precisar dessas alterações.

**Opções (cada uma pode ser desativada):**

- Aplicar modificadores
- Remover duplicatas — mesclar vértices duplicados na mesma posição
- Recalcular normais — corrigir superfícies invertidas
- Remover geometria solta — faces não ligadas ao corpo
- Remover grupos de vértices vazios
- Remover ossos sem peso — ossos que não movem nenhum vértice
- Remover restrições e corpos rígidos que o VRChat não pode usar

1. Revise as opções de limpeza.

2. Ative apenas as operações de que seu avatar precisa.

3. Salve um ponto de restauração do arquivo.

4. Selecione **Fix Model** para executar as operações ativadas na malha selecionada em uma única passagem.

5. Inspecione o resultado antes de continuar.

Descrição da imagem do original em inglês (imagem omitida): opções e ação de Fix Model. Revise essas escolhas antes da primeira fase do pipeline.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Opções e ação de Fix Model. Revise essas escolhas antes da primeira fase do pipeline.*

---

## Translate Bone Names {#translate-bone-names}

**O que faz:** traduz os nomes dos ossos do esqueleto para nomes em inglês do VRChat. Funciona offline, a partir de um dicionário integrado de nomes de ossos conhecidos.

**Idiomas disponíveis:** japonês (日本語, o mais comum, vindo de MMD e de muitos modelos da comunidade), chinês (中文), coreano (한국어), português (Português), espanhol (Español) e francês (Français).

**Controles principais:**

1. Selecione **Language**, o idioma dos nomes de origem.

2. Selecione **Translate Bone Names**.

Language identifica o idioma dos nomes dos ossos do modelo. Não identifica o idioma da interface. Para um modelo MMD japonês, selecione Japanese independentemente do idioma da interface do Bforartists.

Descrição da imagem do original em inglês (imagem omitida): escolha o idioma dos nomes de origem antes de Translate Bone Names. Nenhum nome correspondente foi detectado neste exemplo.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Escolha o idioma dos nomes de origem antes de Translate Bone Names. Nenhum nome correspondente foi detectado neste exemplo.*

---

## Join Meshes {#join-meshes}

**O que faz:** combina os objetos de malha do avatar em uma única malha. O VRChat tem melhor desempenho com uma malha por avatar. Se as malhas de origem tiverem chaves de forma diferentes, CATS preenche as chaves ausentes com formas neutras. A malha unida tem um conjunto consistente.

**Controles principais:** lista de malhas, seu botão de atualização e **Join Meshes**.

**Quando usar:** após vincular e atribuir pesos às roupas e aos acessórios.

1. Inspecione as malhas de origem.

2. Selecione qualquer limpeza de que as malhas de origem precisem antes de uni-las.

3. Salve um ponto de restauração do arquivo.

4. Se a lista de malhas precisar de atualização, use o botão ao lado dela.

5. Selecione **Join Meshes**.

6. Inspecione a malha unida, as chaves de forma e os pesos.

Descrição da imagem do original em inglês (imagem omitida): após Refresh Mesh List, a lista contém uma malha marcada com seis polígonos. Revise-a antes de escolher Join Meshes.

*Janela flutuante nativa da compilação de teste, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Após Refresh Mesh List, a lista contém uma malha marcada com seis polígonos. Revise-a antes de escolher Join Meshes.*

---

## Combinador de atlas de materiais {#material-atlas-combiner}

**Fase do pipeline:** 2 (opcional)

**O que faz:** consolida vários materiais em uma única folha de textura (um atlas). Menos materiais melhoram a classificação de desempenho no VRChat.

**Local:** **CATS → CATS → Material Atlas**. O painel divide o trabalho em **1. Choose Target**, **2. Choose Materials and Textures** e **3. Bake and Review**.

### Analisar e escolher fontes {#analyze-and-choose-sources}

Descrição da imagem do original em inglês (imagem omitida): Material Atlas antes da análise. Escolha o alvo, mantenha um backup e use Analyze Materials.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Material Atlas antes da análise. Escolha o alvo, mantenha um backup e use Analyze Materials.*

**Target** oferece **Active Avatar**, **Selected Meshes** e **Visible Scene**. Active Avatar usa as malhas filhas da armadura ativa. Se não houver armadura ativa, usa a malha ativa. Visible Scene usa malhas visíveis. Para um conjunto específico, selecione Selected Meshes.

1. Salve uma cópia do arquivo.

2. Selecione o escopo necessário em **Target**.

3. Mantenha **Preserve Backup Duplicate** ativado.

4. Selecione **Analyze Materials**.

5. Selecione um grupo de atlas.

6. Para consolidar esse grupo, ative sua caixa de seleção.

7. Em **Materials to combine**, ative os materiais a incluir.

8. Em **Texture images**, ative as imagens a incluir.

9. Repita a revisão das fontes para cada grupo ativado.

**Analyze Materials** cria as listas de fontes. Seu rótulo passa a ser **Refresh Analysis** depois que os grupos existem. Atualizar reconstrói as listas e suas escolhas. Revise-as novamente após atualizar.

Cada lista tem **Select All** e **Deselect All**. Esses botões alteram as caixas **Include** dessa lista no grupo ativo. Não alteram a linha destacada. As listas de materiais e texturas permanecem independentes. Os outros grupos mantêm suas escolhas. Texturas ausentes permanecem desmarcadas. A seleção em massa não ativa um grupo desativado.

As mesmas ações em massa estão disponíveis em **Object → Atlas Source Selection**. Use Accept ou Revert em uma prévia de atlas pendente antes de alterar sua seleção de fontes.

Um grupo ativado precisa de pelo menos dois materiais marcados. A consolidação ignora grupos desativados e grupos com um único material. Slots de materiais excluídos e referências de materiais compartilhadas permanecem separados. Excluir uma imagem a omite da consolidação. Isso não exclui todo o seu material.

Materiais transparentes e emissivos começam em grupos separados. Os grupos Alpha Blend começam desativados para preservar a ordem de desenho. Se aceitar possíveis alterações nessa ordem, ative esses grupos.

**Source Details** começa desativado. Ative-o para inspecionar diagnósticos da malha, avisos de chaves de forma e UVs, dimensionamento de materiais, funções de texturas e grupos de fontes duplicadas. **Override Size** de um material mostra sua escolha de tamanho. O tamanho personalizado usa **Width** e **Height**. Materiais somente com cor usam o tamanho **Fallback**.

A lista de grupos oferece **Resolution** e controles de adição/remoção. **Add Group** e **Remove Group** gerenciam os grupos. Não consolidam por si só.

Descrição da imagem do original em inglês (imagem omitida): fontes analisadas de duas malhas de exemplo. Revise as caixas de seleção de grupos, materiais e imagens, incluindo o aviso de UV.

*Versão candidata BoneCraft 9.2.19. Compilação nativa de teste do Bforartists 5.2.3, Blender 5.4 Alpha. Fontes analisadas de duas malhas de exemplo. Revise as caixas de seleção de grupos, materiais e imagens, incluindo o aviso de UV.*

### Consolidar e revisar {#bake-and-review}

1. Após revisar as listas de fontes, selecione **Bake Checked Sources**.

2. Leia o resumo da verificação prévia.

3. Corrija qualquer erro informado de fonte ou configuração.

4. Quando as alterações planejadas estiverem corretas, confirme a consolidação.

5. Inspecione o atlas, a transparência, as chaves de forma e o canal UV exportado.

6. Se o resultado estiver correto, selecione **Accept — Delete Backup**.

Se precisar do resultado original, selecione **Revert — Restore Originals**. Accept exclui o backup. Revert restaura objetos, materiais e visibilidade originais. Revert também redefine os resultados da contagem de materiais.

Descrição da imagem do original em inglês (imagem omitida): um grupo Opaque de 2048 pixels consolidado a partir de duas malhas de exemplo. O painel ainda informa de 2 para 2 materiais e classificação Excellent. Inspecione o aviso de UV antes de Accept ou Revert.

*Versão candidata BoneCraft 9.2.19. Bforartists oficial 5.2.3, Blender 5.3 Alpha. Um grupo Opaque de 2048 pixels consolidado a partir de duas malhas de exemplo. O painel ainda informa de 2 para 2 materiais e classificação Excellent. Inspecione o aviso de UV antes de Accept ou Revert.*

**Preserve Backup Duplicate** começa ativado. Mantém uma duplicata visível anterior ao atlas para revisão e Revert. Desativá-lo remove os originais após a criação do atlas e não deixa backup para Revert. Antes de desativar essa opção, salve um arquivo separado.

Use Accept ou Revert na prévia atual antes de outra análise ou consolidação. Se um objeto analisado, slot de material ou classificação de renderização mudar, a verificação prévia pode cancelar antes de criar um backup.

Antes de consolidar novamente:

1. Selecione **Refresh Analysis**.

2. Revise as escolhas reconstruídas.

**Smart Combine Materials** é o atalho automático inicial antes de existir uma análise. Com **Auto Analyze** ativado, reconstrói a análise antes da consolidação. Use **Bake Checked Sources** para consolidar suas escolhas revisadas sem reanálise automática. Instruções anteriores chamam esse operador de **Bake Atlas**.

**Se a consolidação não puder começar:** a consolidação de atlas exige Cycles. Se o Bforartists informar que Cycles está indisponível, use uma compilação completa que o inclua.

### Opções avançadas {#advanced-options}

**Advanced Options** substitui o rótulo anterior Override Inherited Settings. Reúne controles opcionais de fluxo de trabalho, consolidação, UV e saída.

| Configuração | Uso |
| --- | --- |
| Auto Analyze | Reconstrói grupos para o atalho automático Smart Combine. |
| Debug Report / Copy Debug Report | Ativa diagnósticos e copia o relatório mais recente para investigar problemas. |
| Albedo (Color) | Passagem obrigatória de consolidação da cor de base. Mantenha ativada. |
| Normal Map / Emission / Roughness | Passagens opcionais separadas de saída. Inspecione os dados de origem aceitos e os resultados da consolidação. |
| Metallic / Pack ORM Channels | A verificação prévia bloqueia essas opções nesta compilação. Deixe desativadas. |
| Packing Preset / Bake Padding / UV Margin | Define preenchimento e espaçamento entre ilhas do atlas. |
| Pixel Art No-Bleed / Preserve Island Orientation | Controla o comportamento do preenchimento e o tratamento disponível da orientação das ilhas. |
| UV Method / UV Seed / Rotation Step | Escolhe o empacotamento e a variação. Os controles de semente e rotação aparecem somente para métodos que os usam. |
| Keep Source UV Maps | Mantém as camadas UV de origem na malha de saída. Começa desativado. |
| Fallback Size | Define o tamanho reservado no atlas para materiais somente com cor, sem imagens. |
| Format Output | Escolhe PNG, TGA ou EXR. EXR preserva emissão acima de 1.0. PNG e TGA a limitam. |
| Material Output Type / Surface Output | Escolhe o tipo de renderização e o shader de superfície do material gerado. |
| Path Output | Define a pasta de saída das texturas. |

Com **Keep Source UV Maps** desativado, a malha final do atlas usa `atlas_uv` como UV0 para FBX, Unity e VRChat. Ativá-lo pode deixar `atlas_uv` em UV1. Verifique o canal UV da engine ao manter mapas de origem. Malhas somente com cor, sem UVs criadas pelo autor, também recebem a camada UV do atlas gerado.

### Preservação e limites {#preservation-and-limits}

O combinador preserva a tonalidade conectada do Principled, o mapeamento de texturas e o alfa durante a consolidação. Trata malhas de origem ocultas na renderização por meio de cópias temporárias de consolidação. Referências de materiais excluídas continuam compartilhadas com outros objetos. As posições da geometria, as chaves de forma e os vínculos de parentesco permanecem protegidos durante a montagem.

Materiais VRM / MToon mantêm seu caminho alternativo dedicado. A classificação de transparência considera a rede real de alfa e o alfa da textura. A configuração de renderização DITHERED, por si só, não classifica um material como transparente. Blocos problemáticos podem aparecer em magenta após a consolidação. Inspecione esses blocos antes de aceitar.

As correções documentadas têm verificações no aplicativo hospedeiro com cenas de teste geradas. Elas não certificam todos os avatares de produção ou redes de shaders. O comportamento visível do navegador de arquivos, o leiaute em janelas reais e Desfazer/Refazer interativos mantêm seus limites de teste registrados. Consulte o [registro histórico de correções](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md) e a [revisão da interface 9.2.15](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md).

**Créditos de origem:** esse fluxo continua a linhagem de integração do CATS e credita o Cats Blender Plugin original. A linhagem de Material Combiner credita Grim-es/material-combiner-addon. A inspiração do fluxo UV vem do UV Toolkit de Alexander Belyakov e do repositório de arquivo oRazeD/UVToolkit. O BoneCraft implementa seus próprios auxiliares UV de atlas. Ele não inclui código-fonte do UVToolkit.

---

## Visemas {#visemes}

**Fase do pipeline:** 3

**O que faz:** cria os 15 visemas do VRChat a partir de três formas básicas da boca.

**Antes da geração:** cada campo **A Shape**, **O Shape** e **CH Shape** precisa de uma atribuição de origem. Cada campo de origem deve nomear uma chave de forma existente da boca.

**Seleção manual das fontes:**

1. Selecione a chave de origem em **A Shape**.

2. Selecione a chave de origem em **O Shape**.

3. Selecione a chave de origem em **CH Shape**.

**Alternativa automática:** selecione **Auto-Detect**.

**Após qualquer uma das formas de seleção de fontes:**

1. Verifique se os três campos de origem nomeiam chaves existentes.

2. Se necessário, expanda Options abaixo dos botões.

3. Se necessário, altere a opção de sobrescrever visemas existentes.

4. Selecione **Generate Visemes**.

Consulte [Guia 13, fase 2](03-guides-b.md#phase-2--viseme-generation).

Descrição da imagem do original em inglês (imagem omitida): CATS Visemes: selecione as formas de origem A, O e CH, ou use Auto-Detect, antes de Generate Visemes.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. CATS Visemes: selecione as formas de origem A, O e CH, ou use Auto-Detect, antes de Generate Visemes.*

---

## Rastreamento dos olhos {#eye-tracking}

**Fase do pipeline:** 4 (execute após Fix Model)

Auto-Detect pesquisa nomes comuns de ossos dos olhos. Não usa a geometria da malha nem as posições dos ossos.

1. Verifique **Left Eye** e **Right Eye**.

2. Se faltar uma atribuição, selecione esse osso manualmente.

Se você renomear os ossos:

1. Execute a detecção novamente.

2. Verifique novamente as duas atribuições.

Se o movimento dos olhos estiver errado, inspecione a orientação dos ossos, as restrições e o avatar exportado.

**O que faz:** encontra os ossos dos olhos e os nomeia `LeftEye` e `RightEye`, como o VRChat exige. Cria as restrições de rotação para o movimento dos olhos no VRChat.

**Controles principais:**

- **Auto-Detect** — pesquisa nomes comuns dos ossos dos olhos esquerdo e direito
- **Left Eye** e **Right Eye** — ossos dos olhos, se você os selecionar manualmente
- **Up Limit**, **Down Limit** e **Side Limit** — até onde os olhos podem girar, em graus
- **Create Eye Tracking** — renomeia os ossos e cria as restrições

Descrição da imagem do original em inglês (imagem omitida): Eye Tracking antes da detecção de ossos. Os limites do exemplo são 30 graus para cima, 20 para baixo e 30 para os lados.

*Janela flutuante nativa da compilação de teste, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Eye Tracking antes da detecção de ossos. Os limites do exemplo são 30 graus para cima, 20 para baixo e 30 para os lados.*

---

## Pose e chaves de forma {#pose--shape-keys}

**Fase do pipeline:** 5 (opcional)

### Pose to Shape Key {#pose-to-shape-key}

O botão atual captura a **combinação atual de chaves de forma** da malha selecionada. Ele não consolida a deformação dos ossos da armadura.

1. Mude para o modo Objeto.

2. Selecione a malha-alvo.

3. Defina os valores de suas chaves de forma existentes com a combinação a capturar.

4. Selecione **Pose to Shape Key**.

5. Digite um nome.

6. Confirme a operação.

7. Redefina os valores das chaves de forma originais para 0.

8. Inspecione a nova chave isoladamente.

A ferramenta define a nova chave como 1 e deixa as chaves originais ativas. Deixar os valores originais ativos soma novamente sua deformação.

### Salvar uma pose deformada por ossos {#save-a-bone-deformed-pose}

Use este fluxo nativo quando precisar armazenar a deformação dos ossos da armadura. O modificador deve preservar a topologia da malha.

**Save as Shape Key** mantém o modificador Armature. **Apply as Shape Key** o remove.

1. Posicione a armadura na pose.

2. Salve um ponto de restauração do arquivo.

3. Volte ao modo Objeto.

4. Selecione a malha deformada.

5. Abra **Properties → Modifiers**.

6. Abra o menu suspenso do modificador Armature.

7. Selecione **Save as Shape Key**.

8. Redefina a pose dos ossos.

9. Redefina quaisquer valores das chaves de forma originais.

10. Defina o valor da nova chave como 1.

11. Revise a nova chave isoladamente.

Se a pose dos ossos ou a combinação de origem permanecer ativa, ela soma a deformação novamente. Essa operação nativa não atualiza a marca de verificação Pose To Shape do pipeline do BoneCraft.

Descrição da imagem do original em inglês (imagem omitida): o menu nativo do modificador Armature oferece Save as Shape Key separadamente de Apply as Shape Key.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Menu nativo do modificador Armature antes da execução. Save as Shape Key mantém o modificador; esta imagem não mostra o resultado de uma pose capturada.*

### Shape Key to Basis {#shape-key-to-basis}

Torna a chave de forma ativa que não seja Basis a nova Basis. Ajusta as outras chaves em relação a essa Basis.

1. Antes dessa operação, salve um ponto de restauração do arquivo.

2. Após a operação, revise as chaves restantes.

Descrição da imagem do original em inglês (imagem omitida): Pose to Shape Key captura a combinação atual de chaves. Shape Key to Basis torna a chave ativa a nova Basis.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Pose to Shape Key captura a combinação atual de chaves. Shape Key to Basis torna a chave ativa a nova Basis.*

---

## Transformações e FBT {#transforms--fbt}

**Fase do pipeline:** 6 (última)

### Apply All Transforms {#apply-all-transforms}

Aplica posição, rotação e escala à malha e à armadura, redefinindo seus canais de transformação. As ferramentas anteriores continuam disponíveis.

1. Antes dessa operação, salve um ponto de restauração do arquivo.

2. Compare o avatar antes e depois da operação.

Se o tamanho diferir após a exportação, inspecione as transformações da malha e da armadura e as configurações de escala de exportação e importação.

### Fix FBT {#fix-fbt}

Correção de transformação para configurações Full Body Tracking: move o osso raiz até o nível do chão.

### Remove FBT {#remove-fbt}

Remove novamente a correção de Fix FBT.

Descrição da imagem do original em inglês (imagem omitida): Apply All Transforms, Fix FBT e Remove FBT são as ações finais do pipeline.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Apply All Transforms, Fix FBT e Remove FBT são as ações finais do pipeline.*

---

## Ferramentas de ossos {#bone-tools}

- **Create Root Bone** — adiciona um osso raiz (nomeado por **Root Name**) na base da hierarquia
- **Merge Bones** — mescla ossos mais curtos que **Merge Threshold** a seus pais
- **Duplicate Bones** — duplica os ossos selecionados

Descrição da imagem do original em inglês (imagem omitida): Create Root Bone, Merge Bones e Duplicate Bones. Ajuste nomes de raiz e limites após a ação.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Create Root Bone, Merge Bones e Duplicate Bones. Ajuste nomes de raiz e limites após a ação.*

---

## Ferramentas de armadura {#armature-tools}

**O que faz:** mescla uma armadura a outra, por exemplo, a armadura de uma roupa à do corpo.

**Controles principais:**

- **Base / Root** — armadura que permanece (o resultado mantém seu nome)
- **Incoming** — armadura que é mesclada à base. Ossos com o mesmo nome são mesclados aos da base.
- Naming Prep — faz os nomes dos ossos dos dois rigs corresponderem antes da mesclagem. Funciona em qualquer rig, incluindo rigs de outras fontes além de Mixamo.
- Opções para vincular os ossos como filhos automaticamente e unir as malhas depois
- **Merge Incoming Into Base** — executa a mesclagem

Para Naming Prep:

1. Selecione Mixamo Prefixed.

2. Selecione **Normalize Merge Names**.

3. Selecione Mixamo Stripped.

4. Selecione **Normalize Merge Names** novamente.

Os dois rigs terminam com os mesmos nomes.

Para uma mesclagem por etapas com prévias, use Bone Merge (consulte [Construtor de Rig](06-rig-builder.md#bone-merge)).

Descrição da imagem do original em inglês (imagem omitida): escolha as armaduras Base e Incoming, revise Naming Prep e use Merge Incoming Into Base.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Escolha as armaduras Base e Incoming, revise Naming Prep e use Merge Incoming Into Base.*

---

## Ferramentas de malha {#mesh-tools}

- **Separate by Materials** — uma malha por material
- **Separate by Loose Parts** — uma malha por parte conectada
- **Separate by Shape Keys** — separa as partes movidas pelas chaves de forma

Descrição da imagem do original em inglês (imagem omitida): separar malhas por materiais, partes soltas ou chaves de forma.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Separar malhas por materiais, partes soltas ou chaves de forma.*

---

## Smart Automatic Weights {#smart-automatic-weights}

**Smart Automatic Weights** abre uma janela com padrões inteligentes e um backup oculto.

1. Verifique a malha e a armadura de destino.

2. Para recalcular pesos a partir do rig existente, selecione Body.

3. Para transferir pesos de uma malha de origem com pesos, selecione Clothing.

**Advanced Recalculation** expande uma indicação de local para **BoneCraft → Skin → Weight Tools**. Não abre os controles completos aqui. Consulte [Ferramentas de rig](05-rig-tools.md#automatic-bone-weight-recalculation).

Descrição da imagem do original em inglês (imagem omitida): Smart Automatic Weights abre sua janela de configuração. Advanced Recalculation indica os controles completos de pesos.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Smart Automatic Weights abre sua janela de configuração. Advanced Recalculation indica os controles completos de pesos.*

---

## Pipeline Status e Operation Ledger {#pipeline-status-and-operation-ledger}

Pipeline Status mostra quais das seis fases foram concluídas. Operation Ledger lista cada operação do CATS com horário e resultado: Changed, Clean ou Failed. **Copy** copia o registro para a área de transferência. **Clear** esvazia o registro. Consulte [O pipeline do CATS](04-cats-pipeline.md).

Próximo: [Soluções rápidas e glossário](10-reference.md)
