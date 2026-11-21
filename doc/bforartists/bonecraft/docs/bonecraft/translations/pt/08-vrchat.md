# Ferramentas do VRChat {#vrchat-tools}

[← Sumário](index.md)

## Ferramentas do VRChat {#vrchat-tools-1}

As ferramentas do VRChat ficam na seção **Avatar Tools** da aba **CATS**, na barra lateral à direita. Pressione **N** para mostrar a barra lateral. Avatar Tools abrange ossos humanoides, física do cabelo e Viseme Library / Lip Sync. A exportação para VRChat fica em CATS → Import / Export → Unity / VRChat. A seção separada **VRChat Tools**, abaixo dela, agrupa Check Performance, Attach Clothing, Facial e VRChat Naming Extras. Quando Preferences → Tabs → Scene Properties → Show está ativado, essa seção também aparece na aba **Scene** do editor de **Propriedades**. Esse controle não oculta a aba CATS da viewport.

---

### Set Up Humanoid Bones {#set-up-humanoid-bones}

Mapeia os ossos do esqueleto para as posições humanoides do VRChat e verifica o mapeamento.

Consulte [Guia 5: Mapeie seu avatar para o sistema corporal do VRChat](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system).

Descrição da imagem do original em inglês (imagem omitida): posições humanoides obrigatórias antes de Auto-Map All. Após o mapeamento, revise cada posição. Preencha as lacunas restantes.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Posições humanoides obrigatórias antes de Auto-Map All. Após o mapeamento, revise cada posição. Preencha as lacunas restantes.*

---

### Add Hair Physics {#add-hair-physics}

Configura cadeias PhysBone no cabelo, nas orelhas, nas caudas e nos acessórios, com colisores.

Consulte [Guia 6: Adicione física ao cabelo](02-guides-a.md#guide-6-add-hair-physics).

Descrição da imagem do original em inglês (imagem omitida): cadeias de Hair Physics, ações de geração, predefinições e controles de colisores. Revise as cadeias detectadas antes de aplicar a física.

*Janela flutuante nativa da compilação de teste, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Cadeias de Hair Physics, ações de geração, predefinições e controles de colisores. Revise as cadeias detectadas antes de aplicar a física.*

---

### Attach Clothing {#attach-clothing}

**Onde encontrar:** aba CATS → VRChat Tools → Clothing

Mescla a roupa ao esqueleto do avatar e transfere seus pesos.

Consulte [Guia 7: Adicione roupas que acompanham seu corpo](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body).

Descrição da imagem do original em inglês (imagem omitida): controles de Clothing e ordem de seleção de Pre-Merge. Antes de mesclar a roupa, faça os ossos corresponderem. Verifique conflitos de nomes de ossos.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Controles de Clothing e ordem de seleção de Pre-Merge. Antes de mesclar a roupa, faça os ossos corresponderem. Verifique conflitos de nomes de ossos.*

---

### VRChat Naming Extras {#vrchat-naming-extras}

**Onde encontrar:** aba CATS → VRChat Tools → Naming

**O que faz:** detecta o estilo de nomes do esqueleto e renomeia ossos em lote.

Consulte [Guia 4: Corrija os nomes dos ossos do avatar](02-guides-a.md#guide-4-fix-your-avatars-bone-names).

**Ferramentas em lote:** **Find and Replace**, **Add Prefix**, **Remove Prefix**, **Add Suffix**, **Remove Suffix** e **Regex Replace**

Descrição da imagem do original em inglês (imagem omitida): Naming detecta Unity Humanoid com confiança de 16/24 neste exemplo. Revise os nomes antes de usar as ações em lote.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Naming detecta Unity Humanoid com confiança de 16/24 neste exemplo. Revise os nomes antes de usar as ações em lote.*

---

### VRChat Viseme Mapping {#vrchat-viseme-mapping}

**Onde encontrar:** CATS → VRChat Tools → Facial. Face Tracking fica na mesma seção.

**O que faz:** mapeia as chaves de forma da malha para os 15 visemas de sincronização labial do VRChat.

Consulte [Guia 8: Configure a sincronização labial](03-guides-b.md#guide-8-set-up-lip-sync). Para criar visemas que o avatar ainda não tem, consulte [Ferramentas do CATS: Visemas](09-cats.md#visemes).

**As 15 posições de visemas do VRChat:** `sil`, `PP`, `FF`, `TH`, `DD`, `kk`, `CH`, `SS`, `nn`, `RR`, `aa`, `E`, `I`, `O`, `U`

Descrição da imagem do original em inglês (imagem omitida): posições de visemas e Face Tracking antes do mapeamento. Este exemplo tem visemas não mapeados e 0 de 55 expressões mapeadas.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Posições de visemas e Face Tracking antes do mapeamento. Este exemplo tem visemas não mapeados e 0 de 55 expressões mapeadas.*

---

### Check Performance {#check-performance}

**Onde encontrar:** aba CATS → VRChat Tools → Performance

**O que faz:** mede a classificação de desempenho do avatar no VRChat e oferece correções.

Consulte [Guia 9: Melhore o desempenho do avatar](03-guides-b.md#guide-9-improve-your-avatars-performance).

**Níveis de desempenho (do melhor para o pior):** Excellent → Good → Medium → Poor → Very Poor

**Ferramentas:**

- **Calculate Performance Rank** — classificação atual, detalhada por polígonos, malhas deformáveis, slots de materiais, ossos, PhysBones e contatos
- O otimizador oferece **Remove Zero-Weight Bones**, **Merge Same-Material Meshes**, **Remove Unused Shape Keys** e **Remove Unused Vertex Groups**. **What-If Mode** mostra o que essas correções alterariam
- VRChat Decimation — reduz a contagem de polígonos por uma proporção, protegendo as chaves de forma

Para VRChat Decimation:

1. Selecione a malha do avatar.
2. Selecione **Preview**.
3. Selecione **Apply**.

Descrição da imagem do original em inglês (imagem omitida): métricas de desempenho e controles What-If. Selecione uma malha de avatar para usar as ações de limpeza de malhas.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Métricas de desempenho e controles What-If. Selecione uma malha de avatar para usar as ações de limpeza de malhas.*

Descrição da imagem do original em inglês (imagem omitida): configurações de Decimation antes de Preview ou Apply. O exemplo usa Ratio 0.50 e Shape Key Safety. What-If Mode está ativado para as ações de limpeza abaixo.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Configurações de Decimation antes de Preview ou Apply. O exemplo usa Ratio 0.50 e Shape Key Safety. What-If Mode está ativado para as ações de limpeza abaixo.*

---

### Export to VRChat {#export-to-vrchat}

**O que faz:** exporta o avatar concluído como FBX para o SDK do VRChat no Unity. A menos que **Remove Shape Keys** esteja ativado, a exportação mantém as chaves de forma (blend shapes).

**Configurações:**

- **Folder** — destino da exportação
- **Avatar** — nome do arquivo exportado
- **Sidecar** — também grava um arquivo de configurações `.bfvrc` para o importador do Unity do BoneCraft
- **Merge Meshes** — une as malhas da cópia de exportação em uma só
- **Separate Clothing** — mantém as roupas como malhas separadas
- **Remove Shape Keys** — aplica as chaves de forma à base da cópia de exportação
- **Embed Textures** — incorpora as texturas ao FBX, para o Unity encontrá-las
- **Helper Meshes** — inclui malhas ocultas ou auxiliares. Para avatares comuns, deixe desativado
- **Bone Names** — **Keep Original Names**, **Unity-Preset** ou **Unreal-Preset**, aplicados às cópias de exportação

**Local:** CATS → Import / Export → Game Engine Export → Unity / VRChat.

Antes de exportar:

1. Se faltarem posições obrigatórias, execute **Auto-Map Humanoid** aqui.
2. Revise as posições.

Para verificar o desempenho antes de exportar, selecione **Check Performance Rank**. Antes de usar uma predefinição de **Bone Names**, corrija conflitos de mapeamento ou nomes. A seção **Nomes de ossos na exportação** abaixo explica esses conflitos. Antes de exportar, torne os objetos vinculados locais. Para gravar o FBX, selecione **Export to VRChat (Unity)**.

**Normalize Names** renomeia o rig de trabalho. As predefinições de **Bone Names** renomeiam as cópias de exportação.

O exportador Unity/VRChat grava a pose de repouso sem animação. Os botões principais de exportação Unity e Unreal aceitam os modos Objeto, Pose e Edição. Eles usam temporariamente o modo Objeto e depois restauram o modo e a seleção anteriores.

Descrição da imagem do original em inglês (imagem omitida): configurações de Unity / VRChat antes de configurar a pasta e o mapeamento humanoide. Este exemplo mostra 0 de 15 posições obrigatórias mapeadas.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Configurações de Unity / VRChat antes de configurar a pasta e o mapeamento humanoide. Este exemplo mostra 0 de 15 posições obrigatórias mapeadas.*

---

### Limpeza {#cleanup}

A limpeza da malha antes de exportar fica nas ferramentas do CATS: **Fix Model**, **Join Meshes** e **Apply All Transforms**. Consulte [Ferramentas do CATS](09-cats.md).

---

## Ponte VRM {#vrm-bridge}

As ferramentas VRM ficam em **CATS** → **Import / Export** → **VRM / VRoid**. Elas precisam do complemento VRM. Uma ponte inativa oferece **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** e **Show Manual Instructions**.

Para um pacote offline, use as preferências nativas. Um ZIP de complemento legado usa **Add-ons → Install from Disk…**. Um pacote de extensão moderno usa o menu nativo de instalação de Extensions.

1. Instale o pacote pelo menu nativo apropriado.
2. Ative a dependência.
3. Confirme que a ponte informa **Active**.

O cartão inativo do hub não tem botão de instalação por ZIP.

Descrição da imagem do original em inglês (imagem omitida): o exemplo não tem nenhuma das pontes de formato ativada. Instale a ponte necessária antes de seus controles de importação e exportação aparecerem.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. O exemplo não tem nenhuma das pontes de formato ativada. Instale a ponte necessária antes de seus controles de importação e exportação aparecerem.*

---

### Importação VRM e VRoid {#vrm-and-vroid-import}

**O que faz:** importa avatares `.vrm` (VRoid Studio, Virtual Cast e outros avatares VRM) com seus materiais, esqueleto e chaves de forma.

- **Import VRM…** — um arquivo `.vrm`
- **Import VRoid (.vroid / .zip)…** — um download do VRoid Hub (`.zip`). Um projeto do VRoid Studio (`.vroid`) mostra um cartão que explica como exportá-lo primeiro para VRM.

---

### Exportação VRM {#vrm-export}

**O que faz:** exporta o personagem com rig para VRM ou para o formato de um aplicativo de destino.

**Configurações:**

- **Folder** e **File** — destino e nome do arquivo. A extensão acompanha o destino
- **Target** — VRM 1.0, VRM 0.x, VRChat FBX, VSeeFace, Warudo ou Resonite
- **Scope** — a armadura ativa ou todas as armaduras com dados VRM
- Skip lint — exporta sem a verificação do destino. Use esta opção somente se compreender o risco informado

Clique em **Export…**.

---

### Verificação VRM {#vrm-lint}

**O que faz:** verifica a armadura em relação ao destino selecionado antes de exportar. As verificações abrangem mapeamento humanoide, metadados VRM, visemas do destino e requisitos do aplicativo de destino.

**Lint Now** executa a verificação sem alterar nada. A menos que você pule a verificação, os erros bloqueiam a exportação. Os avisos identificam conteúdo que o aplicativo de destino pode importar com desempenho reduzido.

Se a verificação informar ossos humanoides ausentes que existem, clique em **Fix Humanoid Map**. O BoneCraft detecta novamente as posições humanoides e salva o mapeamento. Ele não renomeia ossos.

**Também aqui:** **Convert SpringBones → PhysBones** (física de cabelo do VRoid para VRChat) e **Map VRoid Visemes**.

---

## Ponte MMD {#mmd-bridge}

As ferramentas MMD ficam em **CATS → Import / Export → MMD / PMX**. Precisam de **mmd_tools** instalado e ativado. O BoneCraft reconhece pacotes legados e Blender Extensions modernas.

Uma ponte inativa oferece **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** e **Show Manual Instructions**. O conteúdo da ponte independente também oferece **Install from .zip on Disk...** quando exibido. Consulte [Guia 3](02-guides-a.md#step-1--install-mmd_tools) para a instalação e as verificações de repositórios locais de extensões.

---

### Importação MMD {#mmd-import}

- **Import PMX / PMD...** — modelos MMD
- **Import VMD Motion...** — animações MMD
- **Import VPD Pose...** — poses MMD

Confirme que a importação termina com sucesso. Uma importação PMX cancelada ou um erro de instalação deixa a tarefa incompleta. Os modelos importados podem precisar de verificações de materiais e mapeamento de ossos antes da conversão.

---

### Exportação MMD {#mmd-export}

**Configurações:** **Folder** define o destino. Cada formato tem configurações de nome de arquivo e escopo:

- **PMX File** e **PMX Scope**.
- **VMD File** e **VMD Scope**.
- **VPD File** e **VPD Scope**.

Cada escopo seleciona o modelo ativo ou todos os modelos MMD da cena.

**Botões:** **Export PMX...**, **Export VMD Motion...** e **Export VPD Pose...**

**Também aqui:** **Convert Bone Names -> Unity** e **Convert Physics -> PhysBones**.

---

## Exportação para engines de jogos {#game-engine-export}

**Game Engine Export** é a área incorporada em **CATS → Import / Export**. Ela contém **Unity / VRChat** e **Unreal Engine 5**. O painel filho separado **Game Export** oferece exportação por perfil validada.

### Unreal Engine 5 {#unreal-engine-5}

Com **Bake Anim** ativado, o exportador consolida a ação ativa. Não é necessário um clipe NLA separado. Ele não exporta todas as ações não relacionadas.

Antes de usar uma predefinição de **Bone Names**, corrija conflitos de mapeamento ou nomes. A seção **Nomes de ossos na exportação** abaixo explica esses conflitos. Antes de exportar, torne os objetos vinculados locais.

1. Selecione a armadura e suas malhas.
2. Abra **CATS → Import / Export → Game Engine Export → Unreal Engine 5**.
3. Defina **Folder**.
4. Defina **File** com o nome do FBX.
5. Revise **Bone Names** e sua prévia.
6. Se a exportação precisar da animação ativa, ative **Bake Anim**.
7. Clique em **Export to Unreal (FBX)**.

**Selected Only** começa ativado. Inclua a armadura com suas malhas. **Unit Scale** começa ativado, **Leaf Bones** começa desativado e **Embed Textures** começa ativado. O painel abrevia **Bake Animation** para **Bake Anim**.

**Import from Unreal (FBX)** abre o navegador de arquivos de importação.

Descrição da imagem do original em inglês (imagem omitida): configurações de Unreal Engine 5 antes de escolher uma pasta de saída. Revise Bone Names, Selected Only e Bake Anim antes de exportar.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Configurações de Unreal Engine 5 antes de escolher uma pasta de saída. Revise Bone Names, Selected Only e Bake Anim antes de exportar.*

### Nomes de ossos na exportação {#export-bone-naming}

As duas seções de engines oferecem as mesmas opções de **Bone Names**:

| Opção | Resultado da exportação |
| --- | --- |
| Keep Original Names | Mantém os nomes de ossos existentes. É o padrão. |
| Unity-Preset | Usa nomes reconhecidos de Unity Humanoid, incluindo `Hips`, `LeftUpperArm` e `LeftIndexProximal`. |
| Unreal-Preset | Usa nomes humanoides reconhecidos de Unreal, incluindo `pelvis`, `spine_01`, `upperarm_l`, `index_01_l` e `ball_l`. |

Selecione uma armadura para ver a prévia. Ela mostra as contagens **Recognized / renamed** e até três alterações propostas. Ossos não reconhecidos mantêm seus nomes.

Os mapeamentos humanoides salvos têm prioridade sobre a detecção por nomes. Ossos opcionais reconhecidos de peito, pescoço, ombros, olhos, mandíbula, dedos das mãos e dos pés também participam. Um `Root` separado reconhecido vira `root` com **Unreal-Preset**.

Nomes de destino em conflito, ossos ambíguos e posições humanoides reutilizadas bloqueiam a renomeação. Corrija o conflito de mapeamento ou nomes antes de exportar. O BoneCraft não adiciona sufixos `.001` para resolver esses conflitos.

Antes de exportar, torne os objetos vinculados locais. As predefinições renomeiam cópias temporárias de exportação. O rig de trabalho mantém seus nomes de ossos. Os grupos de vértices exportados, os canais de animação e as referências de ossos do arquivo auxiliar do Unity seguem os nomes selecionados. A limpeza remove os dados temporários tanto no sucesso quanto na falha.

Essas predefinições alteram apenas os nomes. Mantêm a hierarquia, a orientação dos ossos e a pose de repouso. Não adicionam articulações ausentes nem constroem um esqueleto Manny/Quinn completo. O mapeamento de Unity Avatar ou o redirecionamento no Unreal ainda podem ser necessários.

### Exportação por perfil validada {#validated-profile-export}

**O que faz:** exporta com um perfil validado: Unreal humanoide ou universal, Unity humanoide, Godot humanoide, FBX genérico ou GLB. A lista de resultados mostra as correções disponíveis. As correções exigem sua ação explícita.

Use o modo Objeto para esse fluxo de perfil. A garantia de restauração Objeto/Pose/Edição aplica-se aos dois botões principais de exportação para engines.

Antes de usar uma predefinição de **Bone Names**, corrija conflitos de mapeamento ou nomes. A seção **Nomes de ossos na exportação** acima explica esses conflitos. Antes de exportar, torne os objetos vinculados locais.

**Configurações do navegador de arquivos:** **Profile**, **Animation**, **Bone Names**, **Root Motion**, **Interpolation** e **T-Pose**. **Bone Names** segue inicialmente a seleção da seção Unreal. O perfil de formato de exportação continua sendo uma escolha separada.

Para uma predefinição de nomes, selecione **Active Action** ou **No Animation**. **All Actions** exige **Keep Original Names**, pois pode incluir ações de outros rigs.

O padrão de **T-Pose** segue o perfil. Os perfis Unity humanoide e VRChat usam uma pose T. A exportação em pose T inclui a pose de repouso sem animação. Se precisar da pose de repouso modelada, selecione **Export as modelled**.

1. Selecione a armadura e suas malhas.
2. Abra **CATS → Import / Export → Game Export**.
3. Clique em **Check for Export**.
4. Revise os resultados e quaisquer correções explícitas.
5. Clique em **Export (Profile)**.
6. Selecione as configurações no navegador de arquivos.
7. Selecione o arquivo de saída.
8. Confirme a exportação.

Descrição da imagem do original em inglês (imagem omitida): opções de exportação por perfil antes da confirmação. Este exemplo usa Generic FBX, Active Action e Keep Original Names.

*Prévia local, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Opções de exportação por perfil antes da confirmação. Este exemplo usa Generic FBX, Active Action e Keep Original Names.*

**Botões:**

- **Check for Export** — verifica o rig em relação ao perfil e lista os resultados
- **Apply Transforms (Fix)** — uma das correções explícitas que a verificação pode oferecer
- **Export (Profile)** — exporta com o perfil

**Onde encontrar:** aba **CATS** → **Import / Export** → **Game Export**

Consulte o [guia independente de nomes de exportação](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/export-bone-naming.md) para mais detalhes de nomeação e verificações históricas do aplicativo hospedeiro.

Descrição da imagem do original em inglês (imagem omitida): Check for Export, correções explícitas e Export (Profile). O exemplo ainda não tem resultados de verificação de perfil.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Check for Export, correções explícitas e Export (Profile). O exemplo ainda não tem resultados de verificação de perfil.*

---

## Task Board {#task-board}

**O que faz:** resume o rig atual com uma pontuação de integridade, melhorias rápidas e tarefas agrupadas por categoria. As tarefas incluem ossos humanoides ausentes, nomes não resolvidos, visemas ausentes e avisos do validador do rig. **Quick Wins** mostra até três tarefas recomendadas. **Remaining Tasks** contém apenas as outras tarefas. **Open Health Check** executa a validação e abre seus resultados. **Refresh Task Board** verifica novamente.

**Onde encontrar:** aba **BoneCraft** → **Overview** → **Task Board**

Descrição da imagem do original em inglês (imagem omitida): Task Board lista os resultados de integridade e as ações rápidas para o rig de exemplo ativo.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Task Board lista os resultados de integridade e as ações rápidas para o rig de exemplo ativo.*

---

### Bone Inspector {#bone-inspector}

**O que faz:** mostra as dimensões em repouso do osso de pose ativo, seu pai, restrições, dados personalizados, drivers e pesos de deformação da malha.

As informações são somente de leitura. Com um osso ativo no modo Pose, abra este painel. Para copiar o nome do osso, selecione **Copy Name** no cabeçalho.

**Onde encontrar:** aba **BoneCraft** → **Review** → **Bone Inspector**

Descrição da imagem do original em inglês (imagem omitida): Bone Inspector mostra detalhes do osso em repouso, restrições, dados personalizados, drivers e pesos de deformação da malha. O cabeçalho inclui Copy Name.

*Janela flutuante nativa da compilação de teste, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Bone Inspector mostra detalhes do osso em repouso, restrições, dados personalizados, drivers e pesos de deformação da malha. O cabeçalho inclui Copy Name.*

Próximo: [Ferramentas do CATS](09-cats.md)
