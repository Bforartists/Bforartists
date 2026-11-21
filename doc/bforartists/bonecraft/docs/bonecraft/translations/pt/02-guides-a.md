# Guias 1–7 {#guides-17}

[← Sumário](index.md)

## Guia 1: Leve seu primeiro avatar para o VRChat {#guide-1-get-your-first-avatar-into-vrchat}

Para obter uma malha de prática, siga a [oficina escrita do manequim](06-rig-builder.md#illustrated-mannequin-workshop). Suas etapas são Simple Human, um manequim sem rig, Auto-Rig e IK/FK.

> **Tempo:** cerca de 45–60 minutos para uma primeira execução completa
> **Resultado:** avatar com rig, pronto para VRChat e exportado para o SDK do VRChat

**Antes de começar — verifique:**

- [ ] Seu modelo 3D está importado no Bforartists (File > Import, escolha seu formato)
- [ ] O modelo está em pose T (braços abertos para os lados, corpo ereto) — ou perto disso
- [ ] O modelo não tem geometria obviamente danificada (nenhum triângulo aleatório flutuando)
- [ ] Você consegue ver o modelo na Viewport 3D como uma forma cinza sólida

---

### Etapa 1 — Abra o Rig Builder {#step-1--open-the-rig-builder}

1. Na Viewport 3D, pressione **T** para mostrar a Tool Shelf à esquerda.

2. Abra **Rig Builder**.

Rig Builder também aparece em **Properties → Scene** quando Preferences → Tabs → Scene Properties → Show está ativado. Suas três partes são **Auto-Rig Wizard**, Quick Rig (armaduras prontas) e **Mannequin**.

3. Expanda **Auto-Rig Wizard**.

4. Selecione **Start Auto-Rig**.

Você também pode iniciar o assistente pelo menu Add → Armature → Auto-Rig Wizard da Viewport 3D e continuar em Rig Builder.

Descrição da imagem do original em inglês (imagem omitida): Auto-Rig Wizard na aba Rig Builder.

*Captura histórica da oficina. Auto-Rig Wizard na aba Rig Builder.*

---

### Etapa 2 — Selecione sua malha {#step-2--select-your-mesh}

O assistente lista as malhas da cena.

1. Selecione a malha do avatar na lista.

2. Selecione **Next**.

**O que você deve ver:** uma linha “Selected:” com o nome da malha, seguida pela etapa do tipo de rig.

Descrição da imagem do original em inglês (imagem omitida): escolha a malha de entrada do Auto-Rig Wizard.

*Captura histórica da oficina. Escolha a malha de entrada do Auto-Rig Wizard.*

---

### Etapa 3 — Escolha o tipo de rig {#step-3--choose-the-rig-type}

1. Para piscadas, expressões e sincronização labial, selecione **Body + Face**.

2. Para um corpo sem controles faciais, selecione **Body Only**.

3. Em Generation Options, defina **Kinematics** como IK/FK, IK only ou FK only.

4. Selecione **Next**.

Descrição da imagem do original em inglês (imagem omitida): escolha o tipo de rig do corpo e os métodos IK/FK.

*Captura histórica da oficina. Escolha o tipo de rig do corpo e os métodos IK/FK.*

---

### Etapa 4 — Posicione os marcadores do corpo {#step-4--place-body-markers}

Os marcadores identificam pelve, coluna, pescoço, cabeça, ombros, braços, mãos, pernas e pés. O BoneCraft usa essas posições para construir os ossos. Verifique cada marcador com cuidado.

**Smart Detection:**

1. Selecione **Detect Markers**.

2. Selecione **Accept High** para manter os marcadores de alta confiança.

3. Selecione **Reset Low** para limpar os marcadores de baixa confiança e posicioná-los manualmente.

O BoneCraft percorre os membros da malha e atribui uma confiança a cada marcador. **Guess Markers from Mesh** estima as posições a partir das proporções da malha.

**Com a ferramenta da viewport:**

1. Em Object Mode, ative Place Rig Markers na barra de ferramentas da viewport.

2. Clique na malha para posicionar e confirmar o marcador indicado no cabeçalho da ferramenta.

3. Repita para o próximo marcador não confirmado.

4. Quando a etapa dos marcadores estiver concluída, selecione **Next** no assistente.

O cabeçalho da ferramenta também contém bloqueios de eixos e um controle de espelhamento.

**Um marcador por vez:** cada marcador tem uma linha de botões com ícones. Passe o ponteiro sobre um botão para ler sua dica.

1. Selecione **Place Marker**, o ícone de seta na linha do marcador.

2. Clique na posição necessária no avatar.

3. Quando a posição estiver correta, selecione **Confirm Marker**, a marca de verificação.

**Reset Marker**, a seta circular, limpa um marcador posicionado para posicioná-lo novamente.

**Simetria:** **Toggle Symmetry** posiciona o marcador oposto sempre que você posiciona um marcador. É o primeiro ícone em cada linha de marcador esquerdo ou direito. **Mirror L to R** e **Mirror R to L** copiam todos os marcadores confirmados para o lado oposto.

1. Quando todos os marcadores estiverem posicionados, selecione **Confirm All Placed**.

2. Selecione **Next**.

Descrição da imagem do original em inglês (imagem omitida): revise os marcadores do corpo detectados antes de ajustá-los.

*Captura histórica da oficina. Revise os marcadores do corpo detectados antes de ajustá-los.*

---

### Etapa 5 — Posicione os marcadores dos dedos {#step-5--place-finger-markers}

1. Em Finger Detail, selecione a quantidade de dedos, de “0 — No Fingers” a “5 — Full Human Hand”.

2. Selecione **Guess Finger Markers**.

3. Ajuste as posições incorretas dos marcadores.

4. Selecione **Next**.

O BoneCraft percorre cada dedo da articulação à ponta usando a forma da mão. Uma mão padrão usa “5 — Full Human Hand”.

---

### Etapa 6 — Posicione os marcadores faciais (somente Body + Face) {#step-6--place-face-markers-body--face-only}

1. Selecione **Guess Face Markers**.

2. Ajuste olhos, pálpebras, sobrancelhas, cantos da boca e mandíbula conforme necessário.

3. Selecione **Next**.

Os marcadores dos olhos mantêm as posições atribuídas manualmente.

---

### Etapa 7 — Revise e gere {#step-7--review-and-generate}

A etapa de revisão lista os avisos e as opções de geração. Clique em **Generate Rig**.

**O que você deve ver:** ossos laranja dentro do avatar, incluindo membros IK/FK e ossos dos dedos. Um rig Body + Face também contém um rig facial. A pele vinculada se deforma quando os ossos se movem.

A etapa final oferece **Build Control Rig** e **Close Wizard**. Build Control Rig aplica as opções de revisão que Generate Rig não aplica. [Construtor de Rig](06-rig-builder.md) descreve ambos os controles.

> **Pesos de deformação** definem quais ossos movem cada parte da malha. O BoneCraft define os pesos automaticamente. Para refiná-los, use Weight Tools em [Ferramentas de rig](05-rig-tools.md).

Descrição da imagem do original em inglês (imagem omitida): revise as configurações do rig antes da geração.

*Captura histórica da oficina. Revise as configurações do rig antes da geração.*

---

### Etapa 8 — Mapeie os ossos humanoides do VRChat {#step-8--map-to-vrchats-humanoid-bones}

1. Pressione **N** para mostrar a barra lateral à direita.

2. Abra **CATS → Avatar Tools → Set Up Humanoid Bones**.

3. Selecione **Auto-Map All**.

4. Selecione **Normalize Names**.

5. Selecione **Validate**.

Auto-Map All conecta os ossos às posições corporais do VRChat. Normalize Names atribui aos ossos mapeados os nomes esperados pelo VRChat.

**O que você deve ver:** cada posição obrigatória (Hips, Spine, Head, LeftUpperArm e assim por diante) mostra um osso. O Guia 5 explica as posições.

Consulte os [controles de mapeamento humanoide](08-vrchat.md#set-up-humanoid-bones).

---

### Etapa 9 — Exporte para o VRChat {#step-9--export-for-vrchat}

Consulte as [configurações de exportação Unity / VRChat](08-vrchat.md#export-to-vrchat).

1. Selecione a armadura do avatar.
2. Abra **CATS → Import / Export → Game Engine Export → Unity / VRChat**.
3. Defina **Folder**.
4. Defina **Avatar** com o nome da exportação.
5. Escolha **Bone Names**.
6. Revise a prévia de nomes ao usar uma predefinição.
7. Clique em **Export to VRChat (Unity)**.

**Keep Original Names** é o padrão. **Unity-Preset** e **Unreal-Preset** renomeiam ossos reconhecidos nas cópias de exportação. O rig de trabalho mantém seus nomes.

Os botões principais de exportação Unity e Unreal aceitam os modos Objeto, Pose e Edição. Restauram o modo e a seleção anteriores.

Consulte [Nomes de exportação e limites](08-vrchat.md#export-bone-naming) para conflitos, mapeamento e restrições de animação.

**O que você deve ver:** o avatar exportado na pasta escolhida, pronto para o VRChat Creator Companion e o SDK do VRChat no Unity.

---

**O que isso permite:** um avatar do VRChat com rig. As próximas opções incluem física do cabelo (Guia 6), roupas (Guia 7), sincronização labial (Guia 8) e verificações de desempenho (Guia 9). Para limpeza com CATS e configuração para o VRChat, consulte [Guia 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats).

---

## Guia 2: Leve um avatar VRoid para o VRChat {#guide-2-bring-a-vroid-avatar-into-vrchat}

> **Tempo:** cerca de 15–25 minutos
> **Resultado:** avatar VRoid pronto para exportação para o VRChat

**Antes de começar — verifique:**

- [ ] Você exportou o avatar do VRoid Studio como arquivo `.vrm` ou o baixou do VRoid Hub como `.zip`
- [ ] O BoneCraft está instalado e ativado

---

### Etapa 1 — Instale o complemento VRM {#step-1--install-the-vrm-add-on}

O BoneCraft precisa do complemento VRM para ler arquivos `.vrm`.

1. Abra **CATS → Import / Export → VRM / VRoid**.

2. Instale a dependência antes de importar.

3. Ative a dependência.

A ponte inativa oferece **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** e **Show Manual Instructions**.

Para um pacote offline:

1. Abra as preferências nativas.

2. Para um ZIP de complemento legado, instale por **Add-ons → Install from Disk…**.

3. Para um pacote de extensão moderno, use o menu nativo de instalação de Extensions.

4. Volte à ponte.

5. Confirme que a ponte informa **Active**.

Consulte os [controles de instalação de pontes de formatos](08-vrchat.md#vrm-bridge).

---

### Etapa 2 — Importe seu avatar {#step-2--import-your-avatar}

1. Em **VRM / VRoid**, selecione **Import VRM…**.

2. Selecione seu arquivo `.vrm`.

Para um download do VRoid:

1. Selecione **Import VRoid (.vroid / .zip)…**.

2. Selecione o arquivo `.zip` baixado.

Se selecionar um arquivo de projeto do VRoid Studio (`.vroid`), o BoneCraft mostra um cartão “VRoid Studio Project”. Um projeto ainda não é um avatar.

Para esse arquivo de projeto:

1. Exporte o projeto para VRM no VRoid Studio.

2. Importe esse arquivo VRM.

**O que você deve ver:** seu personagem VRoid na viewport, com o esqueleto no lugar.

---

### Etapa 3 — Mapeie os ossos humanoides do VRChat {#step-3--map-to-vrchats-humanoid-bones}

1. Abra **CATS → Avatar Tools → Set Up Humanoid Bones**.

2. Selecione **Auto-Map All**.

Os esqueletos VRoid seguem um leiaute padrão, por isso normalmente todas as posições são preenchidas. Se uma posição estiver errada, selecione **Fix Humanoid Map** em Lint, em **VRM / VRoid**. Isso corrige erros comuns de mapeamento de nomes do VRoid.

---

### Etapa 4 — Corrija os nomes dos ossos {#step-4--fix-bone-names}

Em **Set Up Humanoid Bones**, selecione **Normalize Names**. Isso substitui os nomes VRoid dos ossos mapeados pelos nomes esperados pelo VRChat.

---

### Etapa 5 — Configure os visemas (sincronização labial) {#step-5--set-up-visemes-lip-sync}

Avatares VRoid já têm as formas da boca para sincronização labial. Na seção **VRM / VRoid**, clique em **Map VRoid Visemes**. O BoneCraft faz as chaves de forma do VRoid corresponderem às formas de sincronização labial do VRChat.

---

### Etapa 6 — Física do cabelo (opcional) {#step-6--hair-physics-optional}

O cabelo do VRoid usa SpringBones. **Convert SpringBones → PhysBones** na seção **VRM / VRoid** os converte em PhysBones do VRChat. O Guia 6 explica a física do cabelo com mais detalhes.

---

### Etapa 7 — Exporte {#step-7--export}

Exporte como no Guia 1, etapa 9.

**O que isso permite:** seu avatar VRoid está pronto para o VRChat Creator Companion. Você também pode verificar o desempenho (Guia 9) antes de enviar.

---

## Guia 3: Leve um avatar MMD para o VRChat {#guide-3-bring-an-mmd-avatar-into-vrchat}

> **Tempo:** cerca de 20–30 minutos
> **Resultado:** modelo MMD `.pmx` pronto para o VRChat

**Antes de começar — verifique:**

- [ ] Você tem um arquivo de modelo MMD `.pmx` ou `.pmd`
- [ ] O BoneCraft está instalado

---

### Etapa 1 — Instale mmd_tools {#step-1--install-mmd_tools}

O BoneCraft exige **mmd_tools** para ler arquivos MMD. Reconhece tanto complementos legados quanto Blender Extensions modernas.

1. Abra **CATS → Import / Export → MMD / PMX**.
2. Clique em **Auto-Install Latest from GitHub** quando a ponte informar uma dependência ausente.
3. Use **Open Add-on Preferences** para ativar uma cópia instalada e desativada.
4. Confirme que a ponte informa **Active** antes de importar.

Para instalação manual:

1. No cartão da ponte inativa, selecione **Website** ou **Show Manual Instructions**.

2. Instale a extensão MMD oficial por **Preferences → Get Extensions**.

Para um ZIP offline:

1. Para um pacote de extensão moderno, use o menu de instalação de extensões.

2. Para um pacote de complemento legado, use **Add-ons → Install from Disk…**.

O conteúdo da ponte independente também oferece **Install from .zip on Disk...** quando exibido.

Se a instalação informar que não há repositório local de extensões:

1. Abra **Preferences → Get Extensions → Repositories**.

2. Adicione ou ative um repositório local.

3. Tente instalar novamente.

Use o pacote de lançamento do projeto original. Um erro de instalação ou uma importação cancelada não contam como importação bem-sucedida.

Consulte os [controles de instalação de pontes de formatos](08-vrchat.md#vrm-bridge).

---

### Etapa 2 — Importe o arquivo PMX {#step-2--import-your-pmx-file}

1. Em **MMD / PMX**, selecione **Import PMX / PMD...**.

2. Selecione seu modelo.

**O que você deve ver:** seu personagem MMD na viewport, com nomes de ossos em japonês.

---

### Etapa 3 — Corrija os nomes dos ossos {#step-3--fix-bone-names}

Mapeie os ossos MMD para as posições humanoides do Unity antes de exportar para o VRChat.

1. Em **MMD / PMX**, selecione **Convert Bone Names -> Unity**.

Para nomes em outro idioma:

1. Abra **CATS → CATS → Translate Bone Names**.

2. Selecione o **Language** de origem.

3. Selecione **Translate Bone Names**.

---

### Etapa 4 — Limpe o modelo {#step-4--clean-up-the-model}

Modelos MMD frequentemente contêm geometria extra e partes separadas.

1. Abra **CATS → CATS**.

2. Revise as opções de **Fix Model**.

3. Selecione as operações de limpeza de que seu avatar precisa.

4. Execute **Fix Model**.

5. Selecione **Join Meshes** para combinar as partes do corpo em uma única malha, como recomendado para o VRChat.

[Guia 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats) explica o pipeline completo do CATS.

---

### Etapa 5 — Mapeie os ossos humanoides do VRChat {#step-5--map-to-vrchats-humanoid-bones}

1. Abra **CATS → Avatar Tools → Set Up Humanoid Bones**.

2. Selecione **Auto-Map All**.

3. Para uma posição vazia, selecione seu botão.

4. Selecione o osso correspondente.

Os esqueletos MMD se parecem com os esqueletos VRChat, por isso a maioria das posições é preenchida automaticamente.

---

### Etapa 6 — Física e exportação {#step-6--physics-and-export}

**Convert Physics -> PhysBones** na seção **MMD / PMX** converte a física de corpos rígidos do cabelo e da saia do MMD em PhysBones do VRChat. Depois exporte como no Guia 1, etapa 9.

**O que isso permite:** seu avatar MMD está pronto para o VRChat. Você pode adicionar física ao cabelo (Guia 6) e configurar a sincronização labial (Guia 8) antes de enviar.

---

## Guia 4: Corrija os nomes dos ossos do avatar {#guide-4-fix-your-avatars-bone-names}

> **Tempo:** cerca de 5–15 minutos
> **Resultado:** os ossos necessários ao VRChat recebem nomes compatíveis com o VRChat

**Antes de começar — verifique:**

- [ ] Seu avatar está aberto com o esqueleto (armadura) visível

---

### Etapa 1 — Detecte o estilo atual dos nomes {#step-1--detect-the-current-naming-style}

Consulte os [controles de Naming](08-vrchat.md#vrchat-naming-extras).

1. Abra **CATS → VRChat Tools**.

2. Em Naming, selecione **Detect**.

3. Após alterações de nomes, selecione **Force Rescan** para verificar novamente.

O BoneCraft informa o estilo de nomes detectado, como Mixamo, VRoid ou Unity, e uma pontuação.

Para nomes de ossos em japonês, chinês, coreano, português, espanhol ou francês:

1. Abra **CATS → CATS → Translate Bone Names**.

2. Selecione o **Language** de origem.

3. Selecione **Translate Bone Names**.

Isso converte os nomes reconhecidos para inglês.

---

### Etapa 2 — Renomeie com os nomes do VRChat {#step-2--rename-to-vrchat-names}

Para nomear somente na exportação, mantenha os nomes de trabalho e escolha **Unity-Preset** na seção de exportação. Consulte [Nomes de ossos na exportação](08-vrchat.md#export-bone-naming).

1. Mapeie os ossos como descrito no Guia 5, etapa 2.

2. Em **Set Up Humanoid Bones**, selecione **Normalize Names**.

Cada osso mapeado recebe o nome esperado pelo VRChat.

**O que você deve ver:** nomes de ossos como `Hips`, `Spine`, `Chest` e `LeftUpperArm`.

---

### Etapa 3 — Correções manuais (se necessário) {#step-3--manual-fixes-if-needed}

O grupo Naming em **VRChat Tools** também tem ferramentas em lote para os ossos restantes:

- **Find and Replace** — substitui um trecho de texto por outro em cada nome de osso
- **Add Prefix** e **Add Suffix** — adicionam texto ao início ou ao fim de cada nome de osso
- **Remove Prefix** e **Remove Suffix** — removem esse texto novamente
- **Regex Replace** — faz o mesmo com uma expressão regular

**O que isso permite:** nomes de ossos corretos permitem que o mapeamento humanoide (Guia 5) funcione automaticamente. Sem eles, o VRChat não sabe como o personagem deve se mover.

---

## Guia 5: Mapeie seu avatar para o sistema corporal do VRChat {#guide-5-map-your-avatar-to-vrchats-body-system}

> **Tempo:** cerca de 10–15 minutos
> **Resultado:** esqueleto do avatar conectado ao sistema humanoide de movimento do VRChat

**Antes de começar — verifique:**

- [ ] Os ossos do avatar têm nomes adequados (consulte o Guia 4 caso contrário)
- [ ] O esqueleto está selecionado
- [ ] Você está em **Object Mode** (verifique o menu no canto superior esquerdo da viewport)

---

### Etapa 1 — Abra Set Up Humanoid Bones {#step-1--open-set-up-humanoid-bones}

Na aba **CATS**, expanda **Avatar Tools** → **Set Up Humanoid Bones**.

---

### Etapa 2 — Mapeie automaticamente {#step-2--auto-map}

Clique em **Auto-Map All**. O BoneCraft examina o esqueleto e preenche as posições corporais.

> Uma posição humanoide identifica uma parte do corpo, como Hips, Head ou Left Hand. O BoneCraft atribui ossos a essas posições. Os mapeamentos humanoides salvos são carregados corretamente quando você reabre um arquivo.

**O que você deve ver:** atribuições de ossos e a proporção de posições obrigatórias preenchidas. Há 15 posições obrigatórias: Hips, Spine, Head e, dos dois lados, braços, antebraços, mãos, coxas, pernas e pés. As posições opcionais incluem Chest, UpperChest e Neck.

---

### Etapa 3 — Verifique o mapeamento {#step-3--check-the-mapping}

Clique em **Validate**. O BoneCraft verifica se cada posição obrigatória tem um osso e se a hierarquia faz sentido.

---

### Etapa 4 — Preencha manualmente as posições vazias {#step-4--fill-empty-slots-by-hand}

Uma posição vazia mostra “(click to map)”.

1. Selecione a posição vazia.

2. Selecione o osso correto.

3. Selecione **Validate** novamente.

4. Selecione **Normalize Names** para atribuir os nomes do VRChat aos ossos mapeados.

---

### Etapa 5 — Configure o rastreamento dos olhos (opcional) {#step-5--set-up-eye-tracking-optional}

Se o avatar tiver ossos dos olhos:

1. Abra **CATS → CATS → Eye Tracking**.

2. Selecione **Auto-Detect** para pesquisar os nomes dos ossos dos olhos.

3. Verifique as atribuições **Left Eye** e **Right Eye**.

4. Se necessário, selecione os ossos corretos manualmente.

5. Defina os limites de rotação.

6. Selecione **Create Eye Tracking**.

[Guia 13, fase 3](03-guides-b.md#phase-3--eye-tracking) explica as configurações.

**O que isso permite:** o mapeamento humanoide permite que o avatar acompanhe seus movimentos no VRChat. IK (cinemática inversa) faz as mãos no jogo acompanharem seus controles.

---

## Guia 6: Adicione física ao cabelo {#guide-6-add-hair-physics}

> **Tempo:** cerca de 15–25 minutos
> **Resultado:** cabelo do avatar (e outras partes macias) balançando naturalmente no VRChat

**Antes de começar — verifique:**

- [ ] Seu avatar está aberto com o esqueleto selecionado
- [ ] Set Up Humanoid Bones foi concluído (Guia 5)

> PhysBone = componente do VRChat que faz ossos saltarem e balançarem como se tivessem peso. O BoneCraft os configura em cadeias de ossos: cabelo, orelhas, caudas, saias e acessórios.

---

### Etapa 1 — Abra Add Hair Physics {#step-1--open-add-hair-physics}

Na aba **CATS**, expanda **Avatar Tools** → **Add Hair Physics**. Há quatro partes: Hair Chain Detection, Hair Chain Generation, PhysBone Configuration e Hair Physics Colliders.

---

### Etapa 2 — Encontre as cadeias do cabelo {#step-2--find-the-hair-chains}

Se o cabelo já tiver ossos, selecione **Detect Hair Physics Chains**. O BoneCraft pesquisa cadeias de ossos semelhantes a cabelo, ligadas de ponta a ponta a partir de uma raiz. A lista mostra o osso raiz e o comprimento de cada cadeia.

Se o cabelo não tiver ossos:

1. Selecione as malhas do cabelo.

2. Em Hair Chain Generation, selecione **Generate**.

3. Defina imediatamente **Chain Density** como Low, Medium ou High em **Adjust Last Operation**.

**Replace** pede confirmação e atualmente cria novas cadeias sem remover as anteriores.

Antes de gerar novamente:

1. Revise a lista de ossos.

2. Se houver cadeias indesejadas, remova-as.

---

### Etapa 3 — Escolha uma predefinição PhysBone {#step-3--choose-a-physbone-preset}

1. Selecione um osso da cadeia.

2. Em PhysBone Configuration, selecione **Hair**, **Skirt** ou **Tail**.

Skirt é adequado para saias e capas. Tail é adequado para caudas e cordas.

**O que você deve ver:** os parâmetros da cadeia: Pull, Spring, Stiffness, Gravity e Max Angle.

---

### Etapa 4 — Ajuste fino (opcional) {#step-4--fine-tune-optional}

O painel mostra os valores da cadeia, mas não pode editá-los. Maior Stiffness reduz a flexão. Maior Gravity puxa a cadeia para baixo. Menor Max Angle restringe o balanço. Para alterar os valores, selecione outra predefinição. Como alternativa, após importar o avatar, edite seu componente PhysBone no Unity.

---

### Etapa 5 — Adicione colisores (recomendado) {#step-5--add-colliders-recommended}

Colisores são formas invisíveis que impedem o cabelo de atravessar a cabeça e o corpo. Em Hair Physics Colliders, selecione **Place Default Colliders**. Isso adiciona colisores à cabeça, aos ombros e ao peito. **Add Collider** e **Remove Collider** adicionam ou removem um colisor por vez.

**O que isso permite:** o cabelo do avatar agora se move naturalmente no VRChat quando você vira a cabeça, pula ou dança. As mesmas etapas funcionam para caudas, orelhas, saias e acessórios pendentes.

---

## Guia 7: Adicione roupas que acompanham seu corpo {#guide-7-attach-clothing-that-moves-with-your-body}

> **Tempo:** cerca de 20–30 minutos
> **Resultado:** peça de roupa vinculada ao esqueleto do avatar, movendo-se com seu corpo

**Antes de começar — verifique:**

- [ ] O avatar base tem um esqueleto concluído e seu corpo tem pesos pintados
- [ ] A peça de roupa está no mesmo arquivo (com sua própria armadura, se veio com uma)
- [ ] A roupa se ajusta aproximadamente ao redor do corpo do avatar

---

### Etapa 1 — Abra Attach Clothing {#step-1--open-attach-clothing}

Consulte os [controles de Clothing e a ordem de seleção](08-vrchat.md#attach-clothing).

Na aba **CATS**, expanda **VRChat Tools** e encontre o grupo Clothing. Há três partes: Bone Matching, Collision Detection e Clothing Merge.

---

### Etapa 2 — Faça os ossos corresponderem {#step-2--match-bones}

Se a roupa tiver uma armadura:

1. Mude para Object Mode.

2. Selecione a armadura da roupa e a armadura do avatar.

3. Selecione **Match Bones** para comparar seus nomes de ossos.

**O que você deve ver:** contagens informadas de correspondências HIGH, MEDIUM, LOW e UNMATCHED. O painel não mostra uma lista de pares de ossos. Para roupas sem armadura, pule esta etapa.

Antes de mesclar duas armaduras:

1. Selecione **Detect Collisions** para verificar conflitos de nomes de ossos.

2. Revise as renomeações propostas.

3. Torne a armadura da roupa ativa.

4. Selecione **Resolve Collisions** para aplicar as renomeações a essa armadura.

Detect Collisions verifica apenas nomes. Não verifica interseções entre malhas.

---

### Etapa 3 — Mescle a roupa {#step-3--merge-the-clothing}

1. Se a roupa tiver armadura, selecione essa armadura e suas malhas.

2. Se a roupa não tiver armadura, selecione apenas suas malhas.

3. Com Shift pressionado, clique por último na armadura do avatar para torná-la ativa.

4. Selecione **Merge Clothing**.

Com uma armadura de roupa, o BoneCraft move a roupa para o esqueleto do avatar e mescla os ossos. Sem armadura de roupa, transfere os pesos do corpo para as malhas da roupa.

> Pesos (pintura de pesos) = números que informam quanto cada osso move cada ponto de uma malha. Se a manga esquerda tiver peso no osso do braço esquerdo, mover esse osso puxa a manga junto.

**O que você deve ver:** a roupa sob o esqueleto do avatar. Mover um osso move tanto o corpo quanto a roupa.

---

### Etapa 4 — Verifique interseções {#step-4--check-for-clipping}

1. Posicione o avatar em pose.

2. Inspecione os locais em que a roupa atravessa o corpo.

3. Se houver interseções, ajuste o encaixe ou os pesos da roupa nesses locais.

Consulte Weight Tools em [Ferramentas de rig](05-rig-tools.md). **Detect Collisions** não verifica interseções físicas.

**O que isso permite:** roupas que acompanham naturalmente seu corpo. Repita para cada peça do traje.

Próximo: [Guias 8–13](03-guides-b.md)
