# Soluções rápidas e glossário {#quick-fixes-and-glossary}

[← Sumário](index.md)

## Índice de soluções rápidas {#quick-fix-index}

Use este índice para encontrar orientações sobre um problema.

| Problema | Onde procurar |
|---|---|
| O envio falha — ossos não reconhecidos | [Guia 4](02-guides-a.md#guide-4-fix-your-avatars-bone-names) + [VRChat Naming Extras](08-vrchat.md#vrchat-naming-extras) |
| Avatar em pose T / não acompanha o movimento | [Guia 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system) + [Set Up Humanoid Bones](08-vrchat.md#set-up-humanoid-bones) |
| A malha deforma de modo estranho / a pele estica | [Weight Transfer](05-rig-tools.md#weight-transfer) + [Weight Mirror](05-rig-tools.md#weight-mirror), ou recalcule com [Recálculo automático de pesos dos ossos](05-rig-tools.md#automatic-bone-weight-recalculation) |
| Um lado do corpo tem pesos diferentes | [Weight Mirror](05-rig-tools.md#weight-mirror) |
| O cabelo atravessa a cabeça | [Guia 6, etapa 5](02-guides-a.md#step-5--add-colliders-recommended) — adicione colisores |
| A física do cabelo não se move | [Guia 6](02-guides-a.md#guide-6-add-hair-physics) — verifique a detecção de cadeias e a predefinição PhysBone |
| A roupa atravessa o corpo | [Guia 7](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body): <ol><li>Inspecione a malha em pose.</li><li>Se houver interseções, ajuste o encaixe ou os pesos.</li></ol> **Detect Collisions** verifica somente nomes de ossos. |
| A sincronização labial não funciona | [Guia 8](03-guides-b.md#guide-8-set-up-lip-sync) + [VRChat Viseme Mapping](08-vrchat.md#vrchat-viseme-mapping) |
| O desempenho do avatar é Very Poor | [Guia 9](03-guides-b.md#guide-9-improve-your-avatars-performance) + [Check Performance](08-vrchat.md#check-performance) |
| A importação VRM falha | [Guia 2, etapa 1](02-guides-a.md#step-1--install-the-vrm-add-on) — instale o complemento VRM |
| A importação MMD falha | [Guia 3, etapa 1](02-guides-a.md#step-1--install-mmd_tools) — instale mmd_tools |
| O MMD está instalado, mas sua ponte está inativa | Ative mmd_tools por **Open Add-on Preferences**. Revise a mensagem de instalação no [Guia 3](02-guides-a.md#step-1--install-mmd_tools). |
| A seleção do atlas muda após atualizar | **Refresh Analysis** reconstrói as escolhas. <ol><li>Revise as fontes.</li><li>Selecione Bake Checked Sources.</li></ol> Consulte [Combinador de atlas de materiais](09-cats.md#material-atlas-combiner). |
| Select All deixa uma textura desmarcada | Texturas ausentes permanecem excluídas. A seleção em massa altera somente sua lista no grupo ativo — [seleção de fontes](09-cats.md#analyze-and-choose-sources) |
| O atlas informa uma fonte alterada | <ol><li>Atualize a análise.</li><li>Revise novamente as fontes.</li></ol> A verificação prévia rejeita fontes analisadas desatualizadas antes de criar o backup. |
| O atlas não tem a opção Revert | **Preserve Backup Duplicate** estava desativado ou Accept excluiu o backup. Use o ponto de restauração do arquivo salvo. |
| A consolidação Metallic ou ORM do atlas está bloqueada | Deixe **Metallic** e **Pack ORM Channels** desativados. Essas passagens continuam bloqueadas na versão 9.2.18. |
| A textura do atlas parece embaralhada na engine | Verifique UV0. **Keep Source UV Maps** pode deixar `atlas_uv` em UV1 — [configurações UV](09-cats.md#advanced-options) |
| A exportação falha no modo Pose ou Edição | Use o botão principal atual de Unity ou Unreal. Ele restaura o modo e a seleção. Use o modo Objeto para **Export (Profile)**. |
| A nomeação de exportação informa um conflito | Corrija o nome de destino ou o mapeamento humanoide — [Nomes de ossos na exportação](08-vrchat.md#export-bone-naming) |
| All Actions é bloqueado com uma predefinição de nomes | Selecione **Active Action**, **No Animation** ou **Keep Original Names** — [Exportação por perfil validada](08-vrchat.md#validated-profile-export). |
| Formas de mecanismos antigas precisam de uma versão atual | A versão 9.2.18 lê e aplica formas anteriores sem salvá-las novamente — [Formas](07-mechanisms.md#forms) |
| O validador do rig mostra erros | [Rig Validator](05-rig-tools.md#rig-validator): <ol><li>Execute a validação.</li><li>Siga as mensagens.</li></ol> |
| Os ossos sumiram / não consigo ver nenhum osso | [Bone Collections](05-rig-tools.md#bone-collections) → **Show All Collections** |
| Não encontro os painéis do BoneCraft | BoneCraft e Rig Builder usam a Tool Shelf à esquerda (**T**). CATS usa a barra lateral à direita (**N**). Consulte [Onde fica cada coisa](01-start.md#where-things-are). |
| Quero um exemplo completo de Mechanisms | [Tutorial: Crescent Rose](12-crescent-rose.md) — 8 etapas de preparação e 30 etapas de Mechanisms com instruções escritas e descrições de imagens do original em inglês preservadas, além do arquivo concluído em `examples/crescent-rose/` |
| Uma aba está no lado errado | Preferences → Add-ons → BoneCraft → Tabs → Left ou Right |
| As seções do BoneCraft não aparecem em Properties → Scene | Preferences → Add-ons → BoneCraft → Tabs → Scene Properties → Show. Azul significa ativado. Verifique também os pacotes de ferramentas em Tools. |
| Quero ocultar o BoneCraft em Properties → Scene | Desative Scene Properties → Show em Preferences → Tabs. As abas da viewport e a aba de dados da Armadura permanecem iguais. |
| Uma ferramenta executa antes de eu escolher suas opções | Na versão 9.1, ajuste as opções imediatamente depois, no painel Adjust Last Operation da viewport, antes de executar outra operação |
| Place Rig Markers não posiciona um marcador | <ol><li>Inicie Auto-Rig Wizard.</li><li>Avance até uma etapa de marcadores.</li><li>Mude para o modo Objeto.</li><li>Clique na malha selecionada pelo assistente.</li></ol> Consulte [Construtor de Rig](06-rig-builder.md#auto-rig-wizard). |
| Build Mechanism não sabe quais peças usar | <ol><li>Use primeiro Add Parts from Selection.</li><li>Selecione o rig do mecanismo ou uma de suas peças.</li><li>Selecione o tipo no cabeçalho da ferramenta.</li><li>Clique na primeira peça.</li></ol> Consulte [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each). |
| Exportação bloqueada: ossos humanoides são informados como ausentes, embora existam | Se um osso obrigatório não existir, o rig precisa dele primeiro. Se os ossos obrigatórios existirem: <ol><li>Execute Auto-Map All.</li><li>Execute Fix Humanoid Map na seção de verificação de VRM / VRoid.</li></ol> Consulte [Guia 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system). |
| O FBX exportado mostra formas auxiliares ou tubos gigantes | Se não precisar de malhas de controles ou formas personalizadas, mantenha **Helper Meshes** desativado. |
| Unity ou Unreal importa materiais cinza | <ol><li>Exporte com Embed Textures ativado.</li><li>Use as opções de importação/extração de materiais do Unity ou a importação de materiais FBX do Unreal.</li></ol> |
| Os pesos estão todos nos ossos errados | Execute novamente Generate Rig do assistente, use [Weight Transfer](05-rig-tools.md#weight-transfer) ou **Smart Automatic Weights** na aba CATS |
| Dois rigs precisam virar um | [Guia 11: Mescle dois rigs](03-guides-b.md#guide-11-merge-two-rigs-together) |
| A forma corretiva não é ativada | Verifique o eixo e o ângulo do osso em [Chaves de forma corretivas](05-rig-tools.md#corrective-shape-keys) |
| A animação parece errada em outro rig | [Retarget](05-rig-tools.md#retarget) — verifique o mapeamento dos ossos |
| Uma ferramenta CATS avisa “Run Fix Model first” | <ol><li>Revise as opções de limpeza.</li><li>Decida se o avatar precisa delas.</li></ol> O aviso não bloqueia as ferramentas. Consulte [O pipeline do CATS](04-cats-pipeline.md). |
| A boca se rasga ou se separa ao falar | Inspecione as chaves de origem da boca, a topologia da malha e os modificadores — [CATS: Visemas](09-cats.md#visemes) |
| Os olhos do avatar ficam presos olhando para baixo no VRChat | <ol><li>Verifique as atribuições esquerda/direita dos ossos, sua orientação e as restrições.</li><li>Inspecione o avatar exportado.</li></ol> Consulte [CATS: Rastreamento dos olhos](09-cats.md#eye-tracking). |
| A chave de forma faz a malha explodir ao ser acionada | <ol><li>Teste a chave isoladamente.</li><li>Inspecione a topologia, os valores das chaves de origem e os modificadores.</li></ol> O BoneCraft captura uma combinação de chaves, não a deformação dos ossos. Consulte [CATS: Pose e chaves de forma](09-cats.md#pose--shape-keys). |
| O avatar aparece com tamanho errado no VRChat | Verifique as transformações da malha e da armadura e as configurações de escala de exportação/importação. Se precisar restaurar, use Desfazer ou um ponto de restauração salvo. Consulte [Apply All Transforms](09-cats.md#apply-all-transforms). |
| Os nomes dos ossos estão em japonês / chinês / coreano | [CATS: Traduzir nomes de ossos](09-cats.md#translate-bone-names) |
| O avatar não tem sincronização labial nem chaves de forma da boca | [CATS: Visemas](09-cats.md#visemes): crie primeiro as formas básicas da boca. CATS gera 15 visemas a partir de três atribuições de origem: A, O e CH. |
| Um mecanismo mostra “changed by hand” | [Mechanisms](07-mechanisms.md) — use **Keep mine** ou **Restore** |

## Glossário {#glossary}

**Adjust Last Operation:** painel da viewport para alterar as opções da última operação. Muitas ferramentas do BoneCraft 9.1 executam primeiro e mostram suas opções aqui. Ajuste essas opções antes de outra operação.

**Armadura (Armature):** termo do Bforartists para um esqueleto: um conjunto de ossos que pode receber poses e animação.

**Blend shape:** consulte Chave de forma.

**Osso (Bone):** um segmento de um esqueleto. Os ossos formam uma hierarquia (pai → filho), na qual os ossos filhos acompanham seus pais.

**Coleção de ossos (Bone collection):** grupo nomeado de ossos. Você pode mostrar ou ocultar uma coleção inteira de uma vez.

**Bone Names:** escolha de nomes na exportação. Keep Original Names mantém os nomes. Unity-Preset e Unreal-Preset renomeiam ossos reconhecidos nas cópias de exportação.

**Bake Checked Sources:** ação do atlas que consolida as escolhas revisadas de grupos e fontes, sem reconstruir automaticamente a análise.

**CATS:** ferramentas CATS: preparação de modelos para VRChat com um pipeline guiado (limpeza, visemas, rastreamento dos olhos, transformações). Ficam na aba CATS.

**Pipeline do CATS:** ordem de seis fases das ferramentas CATS: Fix Model → Material Atlas → Visemes → Eye Tracking → Pose to Shape → Apply Transforms. As ferramentas avisam quando uma fase anterior da qual dependem não foi concluída.

**Chave de forma corretiva (Corrective shape key):** chave de forma ativada quando um osso atinge um ângulo, para corrigir a malha em poses extremas.

**Osso de deformação (Deform bone):** osso que move a malha. Alguns ossos são apenas controles e não deformam a malha.

**Rastreamento dos olhos (Eye tracking):** ferramenta do CATS que configura os ossos dos olhos (`LeftEye`, `RightEye`) e as restrições de rotação usadas pelo VRChat para movê-los.

**FBT (Full Body Tracking):** recurso do VRChat que rastreia o corpo inteiro, incluindo quadril e pés, com hardware adicional, como Vive Trackers. Fix FBT ajusta o osso raiz para esse recurso.

**FBX:** formato de arquivo que transporta modelos 3D, esqueletos e animações entre programas. É o formato padrão do VRChat.

**Fix Model:** operações de limpeza selecionáveis do CATS para vértices duplicados, geometria solta, normais e outros dados.

1. Revise as opções.

2. Execute apenas as operações de que seu avatar precisa.

**FK (Forward Kinematics):** criação de poses girando cada osso de uma cadeia por vez: ombro, depois cotovelo e depois pulso. É natural para poses amplas do corpo.

**IK (Inverse Kinematics):** criação de poses posicionando a extremidade de uma cadeia, como uma mão ou um pé. Os ossos intermediários acompanham. Esse método é adequado para posicionamento preciso de mãos e pés.

**Humanoide (Humanoid):** sistema de avatares do VRChat que mapeia ossos para posições corporais padrão, para todos os avatares usarem os mesmos controles de movimento.

**Mecanismo (Mechanism):** rig de objeto ou máquina construído com ossos e restrições comuns. Pode ser uma articulação (Hinge, Slide, Telescope) ou um vínculo (Piston, Gear Link, Follow). Consulte [Mechanisms](07-mechanisms.md).

**Malha (Mesh):** superfície 3D que constitui o corpo visível do avatar.

**MMD (MikuMikuDance):** software gratuito de animação 3D popular no Japão e na comunidade de anime. Usa arquivos de modelo `.pmx` e arquivos de animação `.vmd`.

**Morph target:** consulte Chave de forma.

**Operation Ledger:** lista do CATS com todas as operações executadas, incluindo horário e resultado.

**PhysBone:** componente do VRChat que faz os ossos balançarem, saltarem e colidirem. Usado para cabelo, caudas e acessórios pendentes.

**Pipeline Status:** lista do CATS com as seis fases, com uma marca de verificação para cada fase concluída.

**PMX:** principal formato de modelo 3D do MikuMikuDance.

**Modo Pose (Pose Mode):** modo para criar poses e animar ossos.

1. Selecione a armadura.

2. Pressione Ctrl+Tab.

Como alternativa, selecione Pose Mode no menu de modos do canto superior esquerdo da viewport.

**Rig / rigging:** criação de um esqueleto dentro de um modelo 3D e conexão da malha a ele, para permitir poses e animação.

**Chave de forma (Shape key):** versão salva de uma malha em uma posição deformada. Chaves de forma se mesclam em intensidades diferentes. Elas controlam expressões faciais, sincronização labial e alterações da forma do corpo.

**SDK (Software Development Kit):** no VRChat, o VRChat Creator Companion e suas ferramentas do Unity para enviar avatares.

**Spline IK:** cadeia de ossos que acompanha uma curva. Usada para caudas, tentáculos, cabelos longos e colunas vertebrais.

**Pose T (T-pose):** pose de referência: em pé, com os braços abertos para os lados.

**Tool Shelf:** painel esquerdo da Viewport 3D (**T**). BoneCraft e Rig Builder usam esse painel por padrão.

**Vértice (Vertex):** ponto único no espaço 3D. Malhas são formadas por muitos vértices unidos por arestas e faces.

**Grupo de vértices (Vertex group):** conjunto nomeado de vértices que define quais vértices um osso move.

**Visema (Viseme):** forma da boca para um som da fala. O VRChat usa 15 visemas para sincronização labial.

**Peso / pintura de pesos (Weight / weight painting):** valores de 0.0 a 1.0 que indicam a intensidade com que cada osso move cada vértice. A pintura de pesos é a maneira visual de ajustá-los.

**Assistente (Wizard):** Auto-Rig Wizard do Rig Builder: posiciona marcadores na malha e constrói o rig a partir deles.

**Osso sem peso (Zero-weight bone):** osso que não move nenhum vértice. Ele reduz o desempenho sem alterar a aparência do avatar. Fix Model e o otimizador de desempenho removem esses ossos.

Próximo: [Novidades](11-whats-new.md)
