# Guias 8–13 {#guides-813}

[← Sumário](index.md)

## Guia 8: Configure a sincronização labial {#guide-8-set-up-lip-sync}

> **Tempo:** Cerca de 10–20 minutos
> **Resultado:** A boca do avatar se movendo corretamente quando você fala no VRChat

**Antes de começar — verifique:**

- [ ] A malha da cabeça do avatar tem chaves de forma para a boca (também chamadas de blend shapes ou morph targets — as diferentes posições da boca durante a fala)
- [ ] Você sabe aproximadamente os nomes dessas chaves (veja a lista Shape Keys nas propriedades Object Data da malha)

> Visema = uma forma da boca para um som. `aa` representa o som "ahh", `O` representa "ohh" e assim por diante. O VRChat usa 15 visemas para controlar a sincronização labial do avatar.
>
> Chave de forma (blend shape) = uma versão salva da malha em outra posição. A chave de boca aberta é a sua malha com a boca aberta.

---

### Etapa 1 — Abra VRChat Viseme Mapping {#step-1--open-vrchat-viseme-mapping}

Consulte os [controles de Viseme Mapping e Face Tracking](08-vrchat.md#vrchat-viseme-mapping).

Abra **CATS → VRChat Tools → Facial → VRChat Viseme Mapping**.

---

### Etapa 2 — Mapeie os visemas automaticamente {#step-2--auto-map-visemes}

Clique em **Auto-Map All Visemes**. O BoneCraft lê as chaves de forma da malha e as associa, pelo nome, aos 15 campos de visemas do VRChat.

**O que você deve ver:** A lista de visemas, com uma chave de forma atribuída à maioria dos campos.

---

### Etapa 3 — Preencha os campos ausentes {#step-3--fill-in-missing-slots}

Um campo vazio mostra "(unmapped)".

1. Selecione o botão do campo para abrir a lista de pesquisa de chaves de forma da malha.

2. Digite para filtrar a lista.

3. Selecione a chave de forma mais próxima.

Para limpar um campo, selecione "(unmapped)". Correspondências comuns:

| Visema do VRChat | Como soa | Chave de forma a procurar |
|---|---|---|
| `aa` | "ahh" | mouth_open, A, aa |
| `O` | "ohh" | mouth_o, OH, oh |
| `CH` | "ch" / "sh" | mouth_ch, CH |
| `PP` | lábios unidos (P, B, M) | mouth_m, MM, lips_together |
| `SS` | "sss" / "zzz" | mouth_s, SS |

**Chaves de forma de visemas ausentes:** CATS → **Visemes** cria as 15 chaves a partir de três formas básicas: A, O e CH. Se a malha não tiver formas da boca, crie essas três primeiro. Consulte o [Guia 13, Fase 2](#phase-2--viseme-generation).

---

### Etapa 4 — Verifique uma forma da boca {#step-4--check-a-mouth-shape}

1. Em **Properties → Object Data → Shape Keys**, defina o valor da chave mapeada como 1.0.

2. Observe a forma da boca.

3. Retorne o valor a 0.

---

### Etapa 5 — Rastreamento facial (opcional) {#step-5--face-tracking-optional}

Abaixo da lista de visemas, **Face Tracking (SteamVR)** prepara formas de expressão para equipamentos de rastreamento facial. É opcional: a maioria dos usuários não precisa dele.

**O que isso permite:** A boca do avatar se move quando você fala no VRChat. As expressões usam as chaves de forma que você acabou de mapear.

---

## Guia 9: Melhore o desempenho do avatar {#guide-9-improve-your-avatars-performance}

> **Tempo:** Cerca de 15–25 minutos
> **Resultado:** Uma classificação de desempenho melhor no VRChat e carregamento mais rápido para outros jogadores

**Antes de começar — verifique:**

- [ ] O avatar está concluído (com rig, roupas e sincronização labial configurados)
- [ ] Você conhece a classificação desejada (Good ou Excellent para a maioria dos usuários)

> Classificação de desempenho = a avaliação do VRChat sobre o quanto o avatar exige de recursos. Avatares Very Poor podem ser ocultados por outros jogadores. Avatares Good e Excellent carregam rapidamente e são sempre exibidos.

---

### Etapa 1 — Verifique a classificação atual {#step-1--check-the-current-rank}

1. Abra **CATS → VRChat Tools**.

2. Em Performance, selecione **Calculate Performance Rank**.

O BoneCraft informa a classificação geral e a distância de cada métrica até a próxima faixa. As métricas incluem polígonos, malhas deformadas por esqueleto, campos de materiais, ossos, PhysBones e contatos.

Consulte os [controles de Performance](08-vrchat.md#check-performance).

---

### Etapa 2 — Faça a limpeza {#step-2--clean-up}

O VRChat Optimizer, na mesma seção, lista as ferramentas de limpeza. **What-If Mode** começa ativado. Cada correção informa as mudanças propostas sem aplicá-las.

1. Execute a correção necessária em What-If Mode.

2. Examine o relatório.

3. Para aplicar essas mudanças, desative What-If Mode.

4. Execute a correção novamente.

Correções disponíveis:

1. **Remove Zero-Weight Bones** — exclui ossos que não movem nenhuma parte da malha
2. **Merge Same-Material Meshes** — une malhas que compartilham um material
3. **Remove Unused Shape Keys** — remove chaves de forma vazias cuja deformação é igual à Basis. Não verifica referências de outras ferramentas.
4. **Remove Unused Vertex Groups** — remove grupos de pesos vazios

---

### Etapa 3 — Reduza a quantidade de polígonos (se necessário) {#step-3--reduce-the-polygon-count-if-needed}

Consulte os [controles de Performance e Decimation](08-vrchat.md#check-performance).

Se a quantidade de polígonos for alta demais:

1. Selecione a malha.

2. Em VRChat Decimation, defina a proporção desejada.

3. Selecione **Preview**.

4. Observe o resultado.

5. Para manter o resultado, selecione **Apply**.

Uma proporção de 0.5 reduz a quantidade de polígonos pela metade. Uma proporção de 0.8 remove 20%. A dizimação protege as chaves de forma.

> Comece em 0.8. Reduza a proporção aos poucos enquanto verifica a aparência do avatar. Pequenas reduções podem melhorar o desempenho com pouca mudança visível.

---

### Etapa 4 — Combine materiais (opcional) {#step-4--merge-materials-optional}

Se o avatar usa muitos materiais, combine-os em uma única folha de texturas (um atlas). Na aba **CATS** → **CATS** → **Material Atlas**:

1. Salve uma cópia do arquivo.
2. Defina **Target** com as malhas que deseja processar.
3. Mantenha **Preserve Backup Duplicate** ativado.
4. Clique em **Analyze Materials**.
5. Selecione um grupo do atlas.
6. Marque pelo menos dois materiais nesse grupo ativado.
7. Marque as imagens de textura a incluir.
8. Use **Select All** ou **Deselect All** acima de cada lista quando necessário.
9. Clique em **Bake Checked Sources**.
10. Examine o resumo de verificação prévia antes de confirmar o bake.
11. Observe os materiais gerados, a transparência e os UVs.
12. Clique em **Accept — Delete Backup** para manter o resultado.

Use **Revert — Restore Originals** quando o resultado precisar de mudanças. Accept exclui a cópia de segurança. Desativar **Preserve Backup Duplicate** remove a opção Revert.

A seleção em massa afeta apenas sua própria lista de fontes no grupo ativo. Texturas ausentes permanecem desmarcadas. A outra lista e os demais grupos não mudam.

**Refresh Analysis** reconstrói as listas de fontes e suas escolhas. Use **Bake Checked Sources** depois de revisar as escolhas. **Smart Combine Materials** é o atalho automático inicial.

[Ferramentas CATS: Material Atlas Combiner](09-cats.md#material-atlas-combiner) explica cada configuração.

---

### Etapa 5 — Verifique a classificação novamente {#step-5--check-the-rank-again}

Clique em **Calculate Performance Rank** novamente para ver a melhora.

**O que isso permite:** Uma classificação melhor significa que mais jogadores veem seu avatar. Um avatar Good ou Excellent carrega rapidamente, usa menos GPU e é exibido para outros jogadores por padrão.

---

## Guia 10: Salve e reutilize poses {#guide-10-save-and-reuse-poses}

> **Tempo:** Cerca de 5–10 minutos
> **Resultado:** Uma biblioteca salva de poses que você pode aplicar com um clique

**Antes de começar — verifique:**

- [ ] O avatar tem um esqueleto concluído
- [ ] Você está no **Pose Mode**

Para entrar no Pose Mode:

1. Selecione a armature.

2. Pressione Ctrl+Tab.

Como alternativa, selecione **Pose Mode** no menu de modo no canto superior esquerdo da viewport.

---

### Etapa 1 — Abra a biblioteca de poses {#step-1--open-the-pose-library}

Na aba **BoneCraft** da Barra de ferramentas à esquerda, expanda **Review** → **Pose Library**.

Consulte os [controles de Pose Library](05-rig-tools.md#pose-library).

---

### Etapa 2 — Defina a pose do avatar {#step-2--pose-your-avatar}

Mova os ossos para a pose que deseja salvar. Uma pose pode combinar rotações dos braços, inclinação da cabeça e outras posições de ossos.

---

### Etapa 3 — Salve a pose {#step-3--save-the-pose}

1. Selecione **Save**.

2. Digite um nome para a pose, como "Peace Sign" ou "Thinking".

**Category** agrupa poses sob nomes como "Greetings". **Filter** mostra uma categoria por vez. A pose salva inclui uma miniatura da viewport.

---

### Etapa 4 — Aplique uma pose salva {#step-4--apply-a-saved-pose}

1. Selecione uma pose.

2. Selecione **Apply**.

- **Blend** — aplica a pose com intensidade parcial, para misturar duas poses
- **Mirror** — aplica a pose espelhada da esquerda para a direita

**Rename** e **Delete** gerenciam a lista.

---

### Etapa 5 — Exporte e importe poses {#step-5--export-and-import-poses}

**Export** salva a biblioteca de poses em um arquivo `.bfpose`, que você pode guardar com o projeto ou compartilhar. **Import** carrega poses de um arquivo `.bfpose`.

**O que isso permite:** Uma biblioteca pessoal de poses que você pode reutilizar entre projetos, misturar para criar chaves de animação ou compartilhar com outros usuários do BoneCraft.

---

## Guia 11: Una dois rigs {#guide-11-merge-two-rigs-together}

> **Tempo:** Cerca de 25–40 minutos, dependendo da complexidade
> **Resultado:** Dois esqueletos combinados em um, preservando todos os pesos

**Antes de começar — verifique:**

- [ ] O avatar base e o segundo rig (de roupa ou acessório) estão no mesmo arquivo
- [ ] Ambos têm rig e pesos atribuídos

> União de rigs = absorver um esqueleto em outro para obter um único esqueleto combinado. É útil quando o rig do corpo e um rig de cabelo ou roupa precisam se tornar um só.

---

### Etapa 1 — Abra Bone Merge {#step-1--open-bone-merge}

Abra **BoneCraft → Setup Rigging → Bone Merge**. Suas três etapas abrem em ordem à medida que você as conclui.

Consulte os [controles de Bone Merge por etapas](06-rig-builder.md#bone-merge).

---

### Etapa 2 — Estágio 1: Escopo {#step-2--stage-1-scope}

1. Selecione a armature **Base**, o esqueleto do corpo que permanecerá.

2. Selecione a armature de roupa ou cabelo que será incorporada.

3. Selecione **Analyze**.

Durante a união final, a armature recebida se une à base e depois fica oculta.

Analyze compara os dois esqueletos e lista:

- ✓ Matched — ossos que existem em ambos e estão alinhados
- \+ Source only — ossos do rig recebido sem correspondência na base
- − Target only — ossos da base que não existem no rig recebido

Depois de ler a lista, clique em **Acknowledge Scope — Proceed to Rename**.

---

### Etapa 3 — Estágio 2: Renomeação {#step-3--stage-2-rename}

Para cada osso presente apenas na origem, escolha o caminho aplicável.

Se o osso tiver um equivalente na base:

1. Digite o nome desse osso da base.

2. Selecione **Apply Rename**.

Se o osso não tiver equivalente, selecione **Mark as Unique**. Ele se junta à base sem mudar de nome.

**Normalize Both Armatures** renomeia ossos padrão reconhecidos, como coluna, braços e pernas, nos dois rigs. **Auto-Propose Renames** sugere nomes para os outros ossos com base em suas posições. **Apply Batch Pattern** renomeia vários ossos com um único padrão.

Quando todos os ossos exclusivos da origem estiverem resolvidos, clique em **Verify Rename — Proceed to Merge**.

---

### Etapa 4 — Estágio 3: União {#step-4--stage-3-merge}

Clique primeiro em **Run Merge Preview**: ele informa o que a união fará sem alterar nada.

Quando o relatório estiver correto, clique em **Merge Armatures**. O BoneCraft faz uma cópia de segurança das duas armatures e depois as combina.

**O que você deve ver:** Uma armature com todos os ossos dos dois esqueletos e todas as malhas com pesos atribuídos a ela.

**O que isso permite:** Um único rig mais fácil de exportar e editar. É necessário para qualquer avatar com rigs separados de roupas ou acessórios.

---

## Guia 12: Resolva problemas de upload {#guide-12-fix-upload-problems}

> **Tempo:** Cerca de 5–15 minutos, dependendo do problema

**Antes de começar:** Encontre seu problema na lista abaixo e vá até a seção correspondente.

---

### "O upload falhou — ossos não reconhecidos" {#upload-failed--bones-not-recognized}

Os nomes dos ossos não são reconhecidos pelo VRChat. → [Guia 4: Corrija os nomes dos ossos do avatar](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

---

### "O avatar está em T-pose / não acompanha meus movimentos no VRChat" {#avatar-is-in-t-pose--not-moving-with-me-in-vrchat}

O mapeamento humanoide está ausente ou incorreto. → [Guia 5: Mapeie o avatar para o sistema corporal do VRChat](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)

---

### "A malha se deforma de modo estranho / a pele estica errado" {#mesh-is-deforming-weirdly--skin-stretching-wrong}

Os pesos dos ossos precisam de ajustes. → Consulte Weight Transfer e Weight Mirror em [Ferramentas de rig](05-rig-tools.md) ou execute **Smart Automatic Weights** na aba CATS.

---

### "O cabelo atravessa a cabeça" {#hair-is-clipping-through-the-head}

Os colisores do cabelo estão ausentes ou são pequenos demais. → [Guia 6: Adicione física ao cabelo](02-guides-a.md#guide-6-add-hair-physics), Etapa 5.

---

### "O avatar tem desempenho Very Poor e outros jogadores o bloqueiam" {#avatar-is-very-poor-performance-and-being-blocked-by-other-players}

→ [Guia 9: Melhore o desempenho do avatar](#guide-9-improve-your-avatars-performance)

---

### "A sincronização labial não funciona" {#lip-sync-not-working}

Os visemas não estão mapeados corretamente. → [Guia 8: Configure a sincronização labial](#guide-8-set-up-lip-sync)

---

### "O validador do rig mostra erros" {#rig-validator-shows-errors}

1. Abra **BoneCraft → Review → Rig Validator**.

2. Selecione **Run Validation**.

3. Siga a sugestão do resultado ou consulte o [Índice de correções rápidas](10-reference.md#quick-fix-index).

Cada resultado identifica o problema e o osso. **Export Report** salva os resultados em um arquivo.

---

### "A importação de VRM não funciona" {#vrm-import-not-working}

O complemento VRM pode não estar instalado. → [Guia 2](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat), Etapa 1.

---

### "A importação de MMD não funciona" {#mmd-import-not-working}

Verifique se **mmd_tools** está instalado e ativado. A ponte oferece suporte a Extensions modernas e pacotes legados. Examine a mensagem de instalação antes de tentar novamente. Consulte o [Guia 3](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat), Etapa 1.

---

## Guia 13: Prepare o avatar para o VRChat com CATS {#guide-13-get-your-avatar-vrchat-ready-with-cats}

> **Tempo:** Cerca de 20–35 minutos para uma execução completa do fluxo
> **Resultado:** Um avatar limpo e otimizado, com sincronização labial, rastreamento ocular e transformações corretas — pronto para o upload no VRChat

**Antes de começar — leia primeiro:**

As ferramentas CATS têm um fluxo recomendado. Pipeline Status marca as fases concluídas: Fix Model, Material Atlas, Visemes, Eye Tracking, Pose To Shape e Apply Transforms. O Operation Ledger registra cada operação CATS.

As ferramentas ainda funcionam quando uma fase anterior está incompleta. Elas mostram um aviso como "Run Fix Model first for best results".

Comece examinando as opções de limpeza de Fix Model. Salve um ponto de controle do arquivo antes de alterar o avatar.

Antes de continuar, leia [O fluxo de trabalho CATS](04-cats-pipeline.md).

**Antes de começar — verifique:**

- [ ] O avatar foi importado e está visível na viewport 3D
- [ ] A aba CATS está aberta na barra lateral direita (pressione N se a barra estiver oculta)
- [ ] O avatar está selecionado (clique nele na viewport ou no Outliner)

---

### Fase 1 — Fix Model {#phase-1--fix-model}

Fix Model é a fase de limpeza recomendada. Examine suas opções para o avatar importado e depois verifique o resultado antes de continuar.

**O que Fix Model faz** (cada parte pode ser desativada nas opções):

- Aplica modificadores
- Remove vértices duplicados e geometria solta (triângulos flutuando separados do corpo)
- Recalcula as normais (as direções que determinam qual lado da malha fica voltado para fora)
- Remove grupos de vértices vazios e ossos sem peso
- Remove restrições e corpos rígidos que o VRChat não pode usar

**Etapas:**

1. Abra **CATS → CATS → Fix Model**.

2. Selecione a malha do avatar.

3. Selecione **Fix Model**.

4. Aguarde a operação terminar.

5. Verifique se Pipeline Status marca Fix Model com ✓.

Malhas grandes podem levar alguns segundos.

**O que você deve ver:** O avatar parece igual ou um pouco mais limpo. Pipeline Status marca Fix Model e o Operation Ledger lista a execução.

**Se o modelo desaparecer ou parecer virado do avesso após Fix Model:**

O sintoma por si só não identifica a causa.

1. Examine as opções de limpeza ativadas, a visibilidade dos objetos, a geometria e as normais.

2. Se for necessário restaurar, use Undo ou um ponto de controle salvo para recuperar o estado anterior.

3. Antes de tentar novamente, corrija o problema identificado.

Consulte os [controles de Fix Model](09-cats.md#fix-model).

---

### Fase 2 — Geração de visemas {#phase-2--viseme-generation}

Execute depois de: Fix Model ✓

A seção Visemes cria as 15 formas de boca para sincronização labial do VRChat a partir de três formas básicas que você já possui. Se o avatar já tiver um conjunto completo de chaves de visemas, você pode pular esta fase — mas verifique-as em VRChat Viseme Mapping (Guia 8).

O VRChat precisa de 15 formas de boca (visemas) para mover os lábios do avatar enquanto você fala. A maioria dos avatares tem apenas algumas formas básicas de boca. O CATS combina essas formas para criar as restantes.

As três formas básicas:

- **A Shape** — boca bem aberta (a forma de "ahh")
- **O Shape** — boca arredondada (a forma de "ohh")
- **CH Shape** — boca pouco aberta, mostrando os dentes (a forma de "ch" / "sh")

**Se o avatar não tiver chaves de forma da boca:** primeiro esculpa ou edite A, O e CH como chaves de forma. O CATS usa essas chaves para gerar as formas restantes. Consulte a entrada Shape Key no Glossário.

**Etapas:**

1. Abra **CATS → CATS → Visemes**.

2. Escolha a seleção automática ou manual das fontes abaixo.

   Para a seleção automática, selecione **Auto-Detect** para preencher as três formas de origem.

   Para a seleção manual, selecione a correspondência mais próxima para cada uma das três formas de origem.

   Exemplos de nomes de chaves incluem `mouth_open`, `vrc.v_O` e `mouth_wide`.

3. Selecione **Generate Visemes**.

4. Verifique se Pipeline Status mostra Visemes ✓.

O CATS cria 15 chaves de forma com nomes do VRChat, incluindo `vrc.v_aa`, `vrc.v_O` e `vrc.v_CH`.

**O que você deve ver:** 15 novas chaves na lista Shape Keys da malha (Properties → Object Data → Shape Keys).

Consulte os [controles de Visemes do CATS](09-cats.md#visemes).

---

### Fase 3 — Eye Tracking {#phase-3--eye-tracking}

Execute depois de: Fix Model ✓

Eye Tracking configura os ossos dos olhos para o rastreamento ocular integrado do VRChat. Os olhos podem então se mover e olhar para outros jogadores.

**O que faz:**

- Encontra os ossos dos olhos esquerdo e direito
- Dá a eles os nomes exigidos pelo VRChat (`LeftEye` e `RightEye`)
- Adiciona as restrições de rotação necessárias para o VRChat mover os olhos
- Limita a rotação dos olhos a um intervalo natural (para cima, para baixo e para os lados)

Auto-Detect procura nomes comuns de ossos dos olhos. Não examina a geometria da malha nem as posições dos ossos.

Se você renomear os ossos:

1. Execute a detecção novamente.

2. Verifique as duas atribuições de ossos dos olhos.

Se o movimento dos olhos estiver errado, examine a orientação dos ossos, as restrições e o avatar exportado.

**Etapas:**

1. Abra **CATS → CATS → Eye Tracking**.

2. Selecione **Auto-Detect** para procurar nomes comuns de ossos dos olhos esquerdo e direito.

3. Verifique os campos **Left Eye** e **Right Eye**.

4. Se uma atribuição estiver errada, selecione manualmente o osso correto.

5. Se necessário, defina **Up Limit**, **Down Limit** e **Side Limit**.

6. Selecione **Create Eye Tracking**.

7. Verifique se Pipeline Status mostra Eye Tracking ✓.

**O que você deve ver:** Os dois ossos dos olhos renomeados, com restrições de rotação no painel Bone Constraints.

> **Se o CATS não encontrar os ossos dos olhos:** o esqueleto pode não tê-los. Alguns formatos (especialmente modelos MMD antigos) piscam com chaves de forma em vez de ossos. Pule esta fase: o VRChat usa a animação ocular por chaves de forma quando não há ossos dos olhos.

---

### Fase 4 — Pose to Shape Key {#phase-4--pose-to-shape-key}

Execute depois de: Fix Model ✓

O botão atual **Pose to Shape Key** captura a mistura atual de chaves de forma da malha selecionada. Não faz bake da deformação dos ossos da armature. Para uma pose deformada por ossos, use o [procedimento nativo verificado de Save as Shape Key](09-cats.md#save-a-bone-deformed-pose).

**Etapas:**

1. Mude para o Object Mode.

2. Selecione a malha de destino.

3. Defina os valores das chaves de forma existentes com a mistura que deseja capturar.

4. Mantenha a malha ativa.

5. Abra **CATS → CATS → Pose & Shape Keys**.

6. Selecione **Pose to Shape Key**.

7. Digite o nome da nova chave de forma.

8. Confirme a operação.

9. Retorne os valores das chaves originais a 0.

10. Observe a nova chave isoladamente.

11. Verifique se Pipeline Status mostra Pose To Shape ✓.

A ferramenta já define a nova chave como 1.

**O que você deve ver:** Uma nova chave de forma que reproduz a mistura capturada. Manter as chaves originais ativas soma sua deformação novamente.

> **Shape Key to Basis:** torna a chave ativa que não é Basis a nova Basis. Ajusta as demais chaves em relação a essa Basis. Antes desta operação, salve um ponto de controle. Depois, examine as chaves restantes.

Consulte os [controles de Pose to Shape Key](09-cats.md#pose-to-shape-key).

---

### Fase 5 — Apply Transforms {#phase-5--apply-transforms}

Execute depois de: todas as fases anteriores de que você precisa

Apply Transforms é a fase final de preparação recomendada. Aplica posição, rotação e escala à malha e ao esqueleto. Os canais retornam a 0, 0 e 1, respectivamente.

Salve um ponto de controle antes desta operação. Compare o avatar antes e depois da operação. As ferramentas anteriores continuam disponíveis.

Se o avatar exportado tiver o tamanho errado, examine as transformações da malha e da armature e as configurações de escala de exportação e importação. Use Undo ou um ponto de controle salvo quando precisar restaurar um estado anterior.

**As ferramentas de Transforms & FBT:**

- **Apply All Transforms** — aplica posição, rotação e escala à malha e à armature juntas
- **Fix FBT** — uma correção de transformação para configurações de rastreamento de corpo inteiro (move o osso raiz para o nível do chão)
- **Remove FBT** — remove essa correção novamente

Material Atlas e Pose To Shape são opcionais. Se você mapeou visemas existentes, Visemes permanece desmarcado.

**Etapas:**

1. Em Pipeline Status, confirme que as fases necessárias para o avatar estão marcadas.

2. Abra **CATS → CATS → Transforms & FBT**.

3. Selecione **Apply All Transforms**.

4. Verifique se Pipeline Status mostra Apply Transforms ✓.

5. Exporte por **CATS → Import / Export → Game Engine Export → Unity / VRChat** (Guia 1, Etapa 9).

**O que você deve ver:** Apply Transforms marcado, depois das fases de que você precisou. Examine o avatar exportado no VRChat Creator Companion.

Consulte os [controles de transformação e FBT](09-cats.md#apply-all-transforms).

---

**O que isso permite:** Um avatar preparado para as verificações de exportação, com a limpeza, as formas da boca, o rastreamento ocular e as expressões que você escolheu. Valide-o no aplicativo de destino antes do upload.

Próximo: [O fluxo de trabalho CATS](04-cats-pipeline.md)
