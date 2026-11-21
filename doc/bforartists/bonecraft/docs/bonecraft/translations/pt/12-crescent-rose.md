# Tutorial: Crescent Rose com Mechanisms {#tutorial-crescent-rose-with-mechanisms}

[← Sumário](index.md)

<!-- O layout de impressão se limita a este capítulo ilustrado; o renderizador compartilhado permanece inalterado. -->
<style>
@media print {
  h3[id^="12-crescent-rose--"] { break-before: page; break-after: avoid; }
  h2:has(+ h3[id^="12-crescent-rose--"]) { break-before: page; break-after: avoid; }
  h2 + h3[id^="12-crescent-rose--"] { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) { break-after: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) + p { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) table { break-inside: avoid; }
  [id="12-crescent-rose--what-you-built"] { break-before: page; break-after: avoid; }
}
</style>

## O que você vai construir {#what-you-will-build}

Crescent Rose combina uma foice e um rifle. Neste tutorial, você cria o rig do modelo com Mechanisms. Um controle deslizante transforma a foice em rifle. Um segundo controle recolhe o rifle até sua forma compacta.

O tutorial usa todas as articulações e vínculos atuais, exceto Vínculo de engrenagem. Ele inclui oito dobradiças, três deslizamentos, um telescópio, um pistão e um vínculo de acompanhamento. Também cria duas Sequências e três Formas.

As formas são poses didáticas para este modelo feito por fã. Mechanisms não detecta colisões nem produz uma réplica projetada mecanicamente. Ao adaptar o rig, verifique as folgas entre as peças.

O resultado é o arquivo `examples/crescent-rose/CrescentRose_Mechanisms.blend`. Abra-o a qualquer momento para comparar.

## Antes de começar {#before-you-start}

- Arquivos: `examples/crescent-rose/CrescentRose_parts.blend` contém o modelo dividido em 15 objetos de peças. Comece o tutorial por esse arquivo. `CrescentRose_Mechanisms.blend` é o rig concluído.
- Tempo: reserve uma sessão para preparar o FBX e outra para a lição de Mechanisms. São exercícios extensos. Salve pontos de controle entre as etapas.
- Termos: primeiro leia "O que Mechanisms faz" em [Mechanisms](07-mechanisms.md). A seção define peça, articulação, vínculo, controle, Sequência e Forma.
- Idioma: as capturas da fonte em inglês, omitidas aqui, mostram o Bforartists e os painéis do BoneCraft em inglês. Os painéis do BoneCraft seguem a preferência **Language**. O restante do Bforartists segue o idioma da interface. Se o BoneCraft não oferecer suporte ao idioma do seu Bforartists, seus painéis permanecerão em inglês. As instruções escritas desta edição somente de texto continuam válidas.
- Ponto de partida: siga P1-P8 abaixo para o FBX original ou avance para a Etapa 1 com o arquivo preparado. Os dois caminhos usam as mesmas 15 peças.
- Verificações históricas da fonte em inglês: as instruções e as capturas autênticas da interface foram verificadas com BoneCraft `9.1.2` no Bforartists `5.2.0`, usando o mapa de teclas padrão. Nenhuma nova captura nem repetição do tutorial foi realizada para esta edição somente de texto.

**Navegação atual:** na versão 9.2.18, use **BoneCraft → Mechanisms** ou **Properties → Scene → Mechanisms**. Se as seções de Cena estiverem ocultas, ative **Tabs → Scene Properties → Show**. Parts, Joints & Links, Sequences e Controls mantêm seus nomes. As capturas antigas da fonte em inglês, omitidas aqui, podem mostrar uma organização anterior dessas seções.

Esta edição somente de texto preserva os limites originais das capturas e da execução do tutorial da fonte em inglês na versão 9.1.2; as imagens foram omitidas. A revisão da fonte 9.2.18 não as substitui por uma nova execução do tutorial. Formas salvas anteriormente continuam legíveis e utilizáveis. Abri-las ou aplicá-las não salva novamente seus valores. Consulte [Formas](07-mechanisms.md#forms).

As imagens da fonte em inglês usam marcações numeradas em vermelho para indicar onde clicar, digitar ou verificar. Esta edição somente de texto omite essas imagens e preserva suas descrições escritas e legendas com as ações numeradas. Siga as etapas escritas e as notas de ações na ordem (1, depois 2, depois 3). Esses números se referem às anotações da fonte em inglês e recomeçam a cada imagem da fonte. Nessa evidência original, um retângulo indica um resultado a verificar e um círculo indica uma peça ou botão a usar.

## Prepare o FBX original (P1-P8) {#prepare-the-original-fbx-p1-p8}

Se você usar `CrescentRose_parts.blend`, pule esta seção.

1. Trabalhe em um arquivo novo.

2. Mantenha o FBX original e sua pasta `CrescentRoseTextures` juntos.

Estas etapas foram repetidas no Bforartists 5.2.0 com o mapa de teclas padrão. Use o menu de modo visível. Nesse mapa, Tab pode alternar as sobreposições em vez de entrar no Edit Mode.

### P1 - Importe o FBX {#p1---import-the-fbx}

Use o importador Legacy para este procedimento.

1. Comece com uma cena vazia.

2. Selecione **File > Import > FBX (.fbx) (Legacy)**.

3. Selecione `CrescentRose.fbx`.

4. Mantenha a Scale de importação em `1.00`.

5. Selecione Import FBX.

6. Pressione Numpad 3 para a vista Direita.

7. Pressione Home para enquadrar os objetos importados.

O Outliner contém um objeto raiz e três malhas de materiais: `Black01`, `Blades01` e `Red01`.

Descrição da imagem da fonte em inglês (imagem omitida): P1: opções de importação FBX Legacy com Scale 1.00

*1: Selecione CrescentRose.fbx. 2: Mantenha Scale em 1.00. 3: Clique em Import FBX; use o importador Legacy.*

### P2 - Preserve a posição e defina o tamanho {#p2---preserve-placement-and-set-the-size}

A arma importada tem aproximadamente `0.32 m` de altura. O arquivo preparado já está na escala correta. Faça este redimensionamento apenas uma vez nas malhas importadas.

1. Mude para o Object Mode.

2. Selecione as três malhas.

3. Selecione **Object > Parent > Clear and Keep Transformation**.

4. Remova da cena de trabalho o objeto raiz que deixou de ser usado.

5. Com as três malhas selecionadas, selecione **Object > Apply > Rotation & Scale**.

6. Pressione Ctrl+R para iniciar Escala neste mapa de teclas do Bforartists.

7. Digite `6.25` para escalar as três malhas juntas.

8. Confirme a escala.

9. Selecione **Object > Apply > Rotation & Scale** novamente.

A arma completa agora tem aproximadamente `1.997 m` de altura.

Descrição da imagem da fonte em inglês (imagem omitida): P2: remover o parentesco preservando a posição

*1: Pressione F3 e procure Clear Parent Keep Transform. 2: Escolha Clear and Keep Transformation. Repita para as três malhas antes de remover o objeto raiz.*

Descrição da imagem da fonte em inglês (imagem omitida): P2: rotação e escala aplicadas à arma importada

*1: Depois de escalar as três malhas juntas por 6.25, aplique Rotation & Scale; Rotation deve indicar 0. 2: Scale deve indicar 1 em todos os eixos.*

O campo Dimensions de um objeto individual mede apenas a malha daquele material. Ao medir a arma, verifique a extensão total da base até o topo. Os três objetos devem indicar rotação zero e escala 1 antes da separação.

### P3 - Conecte os materiais {#p3---connect-the-materials}

1. Mude para o espaço de trabalho Shading.

2. Selecione Material Preview.

Cada um dos três materiais usa quatro imagens de `CrescentRoseTextures`:

| Imagem | Espaço de cor |
|---|---|
| `BaseColor` | **sRGB** |
| `Metallic` | `Non-Color` |
| `Roughness` | `Non-Color` |
| `Normal` | `Non-Color` |

Para cada material, processe uma imagem de cada vez:

1. Carregue a imagem correspondente de `CrescentRoseTextures`.

2. Defina o espaço de cor dessa imagem conforme a tabela.

3. Para uma imagem BaseColor, Metallic ou Roughness, conecte a saída Color de Image Texture à entrada correspondente do Principled BSDF.

Para cada imagem Normal, use esta ramificação de conexão separada:

1. Insira um nó **Normal Map**.

2. Mantenha o nó Normal Map em `Tangent Space`.

3. Conecte a saída Color da imagem Normal à entrada Color de Normal Map.

4. Conecte a saída Normal de Normal Map à entrada Normal do Principled BSDF.

Mantenha os UVs existentes.

Descrição da imagem da fonte em inglês (imagem omitida): P3: quatro mapas de textura e Normal Map em espaço tangente conectados para o material preto

*1: Conecte Color de BaseColor à entrada Base Color do BSDF. 2: Mantenha BaseColor em sRGB. 3: Defina todos os mapas de dados como Non-Color. 4: Conecte imagem Normal > Normal Map > Normal do BSDF, usando espaço tangente.*

Descrição da imagem da fonte em inglês (imagem omitida): P3: os três materiais em Material Preview

*1: Verifique o material da lâmina. 2: Verifique os materiais vermelho/preto do corpo em Material Preview; não deve haver o rosa de texturas ausentes.*

O procedimento se aplica aos materiais preto, da lâmina e vermelho. Depois de selecionar cada imagem, verifique seu espaço de cor. A configuração de espaço de cor pertence à imagem. A arma deve ficar vermelha, preta e metálica, sem o rosa de texturas ausentes.

### P4 - Separe as peças soltas {#p4---separate-loose-pieces}

1. Selecione as três malhas de materiais.

2. Selecione **Edit Mode** no menu de modo da viewport.

3. Selecione toda a geometria.

4. Selecione **Mesh > Separate > By Loose Parts**.

5. Volte ao Object Mode.

Agora há **37** objetos de malha. Os sufixos numéricos gerados podem variar. Identifique os objetos pela posição e pelo formato.

Descrição da imagem da fonte em inglês (imagem omitida): P4: entrar no Edit Mode e escolher By Loose Parts

*1: Mude para o Edit Mode e selecione toda a geometria. 2: Pressione F3, procure Separate Loose e escolha By Loose Parts.*

Descrição da imagem da fonte em inglês (imagem omitida): P4: as 37 peças soltas depois da separação

*1: Verifique se o total de objetos é 37 após a separação. 2: Use o Outliner para selecionar peças pelo formato e pela posição; os sufixos podem variar.*

### P5 - Una os 15 grupos móveis {#p5---join-the-15-moving-groups}

A tabela lista todas as ilhas da malha original. Os nomes dos materiais descrevem a aparência, não os nomes finais dos objetos.

| Objeto final | Peças a combinar | Vértices da malha após a união |
|---|---|---:|
| `BladeTip` | Botão preto da articulação da ponta e espigão metálico da ponta | 252 |
| `Blade2` | Duas placas metálicas do segundo segmento e duas coberturas vermelhas | 1000 |
| `Blade1` | Duas placas metálicas do primeiro segmento, mais próximas da cabeça | 512 |
| `HeadMount` | Bloco traseiro preto, tampa superior e núcleo; duas placas internas vermelhas e duas coberturas superiores finas | 1395 |
| `PlateL` | Uma placa externa vermelha da cabeça no lado negativo de X | 676 |
| `PlateR` | Uma placa externa vermelha da cabeça no lado positivo de X | 676 |
| `RearSpike` | Duas lâminas metálicas do espigão, duas tampas vermelhas do pivô e duas placas vermelhas de suporte | 1194 |
| `Receiver` | Corpo preto e botão pequeno, anel metálico acima do ferrolho, carcaça vermelha comprida | 2609 |
| `Grip` | Bloco vermelho da empunhadura abaixo do corpo do rifle | 194 |
| `Magazine` | Tubo preto sob o corpo | 96 |
| `Bolt` | Cilindro vermelho do ferrolho e suas duas peças de botão | 362 |
| `Pole` | Haste metálica inferior e colar vermelho | 148 |
| `ButtSpike` | Espigão metálico inferior | 110 |
| `StrutBase` | Vareta vermelha fina entre o corpo do rifle e a cabeça | 34 |
| `StrutRod` | Luva preta com entalhes ao redor dessa vareta | 108 |

Não una as placas externas a Blade1. Não una as duas peças da escora. A escora já tem duas peças separadas. Não é necessário bissectar.

Trabalhe da ponta da lâmina para dentro, depois passe pelo corpo do rifle e pela haste. Para cada grupo móvel:

1. Selecione as peças que devem se mover juntas.

2. Para peças emparelhadas em lados opostos, orbite a vista para selecionar ambas.

3. Verifique a seleção antes de unir.

4. Selecione **Object > Join** (Ctrl+J).

5. Renomeie o objeto unido no Outliner.

O total deve ser de **15 malhas e 9,366 vértices**. A Etapa 2 repete os nomes finais das peças e o parentesco que será usado depois.

Descrição da imagem da fonte em inglês (imagem omitida): P5: os 15 grupos móveis nomeados no Outliner

*1: Renomeie cada grupo unido no Outliner para corresponder aos 15 nomes da tabela.*

Descrição da imagem da fonte em inglês (imagem omitida): P5: as duas placas originais de Blade1 selecionadas antes da união

*1: Selecione as duas placas metálicas de Blade1 em lados opostos. 2: Verifique se ambos os objetos estão selecionados; use Join e renomeie o resultado para Blade1.*

Descrição da imagem da fonte em inglês (imagem omitida): P5: comando Join no menu Object

*1: Abra Object depois de selecionar apenas as peças de um grupo. 2: Escolha Join (Ctrl+J). Este recorte do menu identifica o comando; use a seleção de duas peças descrita acima.*

### P6 - Centralize as origens {#p6---centre-the-origins}

1. Mude para o Object Mode.

2. Selecione as 15 malhas.

3. Selecione **Object > Set Origin > Origin to Geometry**.

4. Defina a opção Center da operação como `Bounds Center`.

5. Verifique se a rotação é zero e a escala é 1.

Os objetos ainda não têm pais. Não há armature. Estas origens servem para a preparação. A Etapa 6 move os pivôs dos mecanismos para as articulações reais.

Descrição da imagem da fonte em inglês (imagem omitida): P6: Object > Set Origin > Origin to Geometry

*1: Abra Object. 2: Passe o ponteiro sobre Set Origin. 3: Escolha Origin to Geometry; defina Bounds Center nas opções da operação.*

Descrição da imagem da fonte em inglês (imagem omitida): P6: a origem centralizada de Blade1 com transformações aplicadas

*1: A origem laranja agora está centralizada na malha. 2: Confirme Rotation 0. 3: Confirme Scale 1. Os pivôs dos mecanismos serão movidos depois.*

### P7 - Redimensione e empacote as texturas {#p7---resize-and-pack-the-textures}

Há **12 mapas usados**, quatro por material. Não sobrescreva os JPEGs originais. Para cada mapa usado:

1. Selecione o mapa no Editor de imagens.

2. Selecione **Image > Resize**.

3. Defina a largura como **1024**.

4. Defina a altura como **1024**.

5. Confirme o redimensionamento.

6. Selecione **Image > Pack**.

O empacotamento preserva os pixels redimensionados dentro do arquivo blend. Depois de processar todos os mapas, verifique a Material Preview.

Descrição da imagem da fonte em inglês (imagem omitida): P7: menu Imagem empacotando uma textura redimensionada para 1024 por 1024

*1: Escolha Image > Resize e digite 1024 para largura e altura. 2: Verifique as dimensões resultantes de 1024 x 1024. 3: Escolha Pack. Repita para os 12 mapas usados.*

### P8 - Salve e reabra o arquivo preparado {#p8---save-and-reopen-the-prepared-file}

1. Salve a cópia de trabalho como `CrescentRose_parts.blend`.

2. Reabra esse arquivo.

3. Verifique as 15 malhas nomeadas, suas transformações e os materiais vermelho/preto.

4. Selecione a vista Direita novamente.

5. Pressione Home.

6. Continue na Etapa 1.

Os 12 mapas devem continuar disponíveis sem o diretório original de texturas.

Descrição da imagem da fonte em inglês (imagem omitida): P8: o arquivo preparado reaberto com a arma texturizada intacta

*1: Abra File para usar Save As e depois Open para recarregar sua cópia de trabalho. 2: Confirme que as 15 malhas nomeadas foram preservadas. 3: Verifique os materiais; a barra de título identifica o arquivo reaberto.*

## A. Abra o arquivo {#a-open-the-file}

### Etapa 1 — Abra o arquivo de peças {#step-1--open-the-parts-file}

1. Abra `examples/crescent-rose/CrescentRose_parts.blend`.

2. Selecione o sombreamento Material Preview na viewport.

3. Pressione Numpad 3 para a vista Direita.

4. Pressione Home para enquadrar a arma.

A lâmina aponta para a esquerda e o espigão inferior aponta para baixo.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 1: o arquivo de peças na vista Direita

*1: Clique em Material Preview. 2: Pressione Numpad 3 até a vista indicar Right Orthographic; pressione Home para enquadrar a arma.*

**O que você deve ver:** A foice em vermelho e preto, com cerca de 2 m de altura, sem nada selecionado.

### Etapa 2 — Conheça as peças {#step-2--meet-the-parts}

O Outliner lista os 15 objetos. Cada um é uma peça que se move como um único bloco:

| Objeto | O que é | Apoiado em |
|---|---|---|
| `Receiver` | O corpo do rifle com a luneta, o gatilho e a mira | o rig |
| `Grip` | A empunhadura sob o corpo do rifle | `Receiver` |
| `Magazine` | O carregador cilíndrico | `Receiver` |
| `Bolt` | O ferrolho | `Receiver` |
| `Pole` | A haste inferior e seu colar | `Receiver` |
| `ButtSpike` | O espigão inferior | `Pole` |
| `HeadMount` | O bloco da cabeça ao qual a lâmina se prende | `Receiver` |
| `Blade1` | O primeiro segmento da lâmina, mais próximo da cabeça | `HeadMount` |
| `Blade2` | O segundo segmento | `Blade1` |
| `BladeTip` | A ponta | `Blade2` |
| `RearSpike` | O espigão na parte de trás da cabeça | `HeadMount` |
| `PlateL`, `PlateR` | As placas laterais externas da cabeça | `HeadMount` |
| `StrutBase` | A vareta fina entre o corpo do rifle e a cabeça | `Receiver` |
| `StrutRod` | A luva com entalhes ao redor dessa vareta | `HeadMount` |

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 2: os 15 objetos de peças no Outliner

*1: Identifique os três segmentos da lâmina. 2: Compare os nomes do corpo, da cabeça e da haste com a tabela. 3: Mantenha StrutBase e StrutRod como objetos separados.*

Para o FBX original, siga P1-P8 acima. Essas ações de interface produziram o arquivo preparado fornecido. O script de preparação do repositório oferece uma tabela de referência dos agrupamentos.

### Etapa 3 — Encontre Mechanisms {#step-3--find-mechanisms}

Se a Barra de ferramentas à esquerda estiver oculta:

1. Com o ponteiro sobre a viewport, pressione T.

2. Selecione Tools no menu Region Toggle.

Depois:

1. Abra a aba BoneCraft na Barra de ferramentas à esquerda.

2. Expanda **Mechanisms**.

3. Arraste a borda direita da barra para tornar o texto do painel legível.

A mesma seção aparece em **Properties > Scene** quando Scene Properties está definido como Show nas preferências do BoneCraft. As capturas omitidas da fonte em inglês usam a Barra de ferramentas.

Com uma malha ativa e sem rig, **Add Parts from Selection** aparece no topo. Antes de usá-lo, selecione todas as peças conforme a Etapa 4. As subseções numeradas ficam disponíveis depois de adicionar peças.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 3: a seção Mechanisms da aba BoneCraft

*1: Clique na aba BoneCraft. 2: Expanda Mechanisms. 3: Localize Add Parts from Selection; selecione as malhas antes de usá-lo.*

## B. Peças {#b-parts}

### Etapa 4 — Add Parts from Selection {#step-4--add-parts-from-selection}

1. Com o ponteiro sobre a viewport, pressione A para selecionar os 15 objetos.

2. Selecione **Add Parts from Selection**.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 4: todas as peças selecionadas, Add Parts from Selection

*1: Passe o ponteiro sobre a viewport e pressione A para selecionar as 15 malhas. 2: Clique em Add Parts from Selection.*

**O que você deve ver:** Uma nova armature, "Mechanism Rig", aparece no Outliner com as peças abaixo dela. Os objetos de malha continuam selecionados. **1. Parts** lista as 15 peças. A aba BoneCraft agora começa pela seção Overview recolhível do rig.

### Etapa 5 — Apoiado em {#step-5--rides-on}

Uma peça fica apoiada na peça à qual está ligada.

1. Selecione `Blade1` em **1. Parts**.

2. Abra o menu "Rides on" abaixo da lista.

3. Selecione `HeadMount`.

4. Repita para cada peça usando a tabela da Etapa 2.

`Receiver` mantém "the rig".

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 5: Blade1 fica apoiada em HeadMount

*1: Selecione Blade1 na lista Parts. 2: Abra Rides on e escolha HeadMount. Repita usando a tabela de parentesco.*

### Etapa 6 — Pivôs {#step-6--pivots}

Uma dobradiça gira em torno do pivô da sua peça. Os segmentos da lâmina, a cabeça e a empunhadura devem girar nas articulações, em vez de girar em seus centros. Trabalhe na vista lateral ortográfica para preservar a posição lateral do pivô.

1. Selecione `Blade1` na lista.

2. Selecione **Edit Pivot**.

3. Selecione o marcador.

4. Pressione Ctrl+W para Move no Bforartists.

5. Clique onde o segmento encontra a cabeça.

6. Selecione **Apply Pivot**.

7. Repita o procedimento do pivô para as peças abaixo.

| Peça | Posição do pivô |
|---|---|
| `Blade2` | Onde encontra `Blade1` |
| `BladeTip` | Onde encontra `Blade2` |
| `HeadMount` | Seu ponto mais baixo, onde a escora a encontra |
| `Grip` | Sua borda superior |
| `RearSpike` | Onde encontra a cabeça |
| `PlateL` e `PlateR` | O centro do parafuso redondo, onde Blade1 encontra a cabeça |
| `StrutBase` | Sua base |
| `StrutRod` | Seu topo |

A posição do marcador na captura omitida da fonte em inglês serve como referência. Alguns milímetros não fazem diferença visível.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 6: selecionar a peça e clicar em Edit Pivot

*1: Selecione Blade1 em Parts. 2: Clique em Edit Pivot; depois mova e aplique o marcador conforme descrito a seguir.*

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 6: marcador do pivô de Blade1 na articulação, Apply Pivot

*1: Mova o marcador do pivô até a articulação da lâmina com Ctrl+W. 2: Clique em Apply Pivot para manter essa posição.*

## C. A cabeça {#c-the-head}

### Etapa 7 — Add Joint → Hinge {#step-7--add-joint--hinge}

Se alguma obstrução precisar ser ocultada, oculte-a antes de iniciar o assistente.

Abra **Add Joint → Hinge**. O cabeçalho e a barra de status da criação guiada explicam cada etapa.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 7: menu Add Joint, Hinge

*1: Abra Add Joint. 2: Clique em Hinge. A criação guiada agora aguarda uma peça.*

### Etapa 8 — Clique na cabeça {#step-8--click-the-head}

O cabeçalho diz "click the part that turns". Na vista Direita, a placa externa encobre a cabeça. Clique no bloco traseiro da cabeça atrás das placas, na posição indicada pelo círculo da fonte.

Se o cabeçalho indicar `PlateR`:

1. Pressione Esc.

2. Reinicie **Add Joint > Hinge**.

3. Clique mais para trás na cabeça.

Enquanto está ativo, o assistente intercepta os atalhos de teclado comuns.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 8: clicar no bloco traseiro da cabeça

*1: Clique no bloco preto traseiro de HeadMount, atrás da placa externa vermelha. Verifique se o assistente indica HeadMount.*

### Etapa 9 — Pressione X e depois Enter {#step-9--press-x-then-enter}

O cabeçalho solicita o eixo.

1. Pressione X.

2. Observe a prévia em repetição.

3. Pressione Enter para manter a dobradiça.

A cabeça gira em torno do eixo lateral.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 9: a etapa do eixo

*1: Siga a solicitação do eixo: pressione X e depois Enter. 2: Observe a cabeça girar em torno do pivô antes de confirmar.*

**O que você deve ver:** `HeadMount Hinge` em **2. Joints & Links**, com seu controle deslizante em **4. Controls**. Use esses controles no Object Mode.

Para usar os controles de ossos na viewport:

1. Selecione a armature.

2. Mude para o Pose Mode.

### Etapa 10 — Limites {#step-10--limits}

1. Selecione `HeadMount Hinge` na lista.

2. Defina **Min** como 0.

3. Defina **Max** como 120.

Valores positivos giram a cabeça para baixo e para trás. Mantenha o limite de movimento de 120 graus. A sequência Rifle usa um alvo de 90 graus junto com as dobradiças da lâmina.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 10: Min 0, Max 120

*1: Selecione HeadMount Hinge. 2: Defina Min como 0. 3: Defina Max como 120; clique duas vezes no número, digite e pressione Enter.*

### Etapa 11 — Teste {#step-11--test}

Clique no botão de reprodução da linha. A cabeça percorre o movimento até 120° e volta; a pose é restaurada.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 11: Test na linha da dobradiça

*1: Clique no pequeno triângulo de reprodução na linha HeadMount Hinge. Observe o movimento de ida e volta.*

## D. A cadeia da lâmina {#d-the-blade-chain}

### Etapa 12 — Mais três dobradiças {#step-12--three-more-hinges}

Para cada uma de `Blade1`, `Blade2` e `BladeTip`, repita as Etapas 7 a 10:

1. Abra **Add Joint → Hinge**.

2. Clique no segmento.

3. Pressione X.

4. Pressione Enter.

5. Defina **Max** como 120.

Cada segmento fica apoiado no anterior. As três dobradiças formam uma cadeia.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 12: as três dobradiças dos segmentos da lâmina e a dobradiça separada da cabeça na lista

*1: Crie e selecione cada dobradiça da lâmina: Blade1, Blade2, BladeTip. 2: Defina Max como 120 para cada uma; use X como eixo.*

### Etapa 13 — Experimente a cadeia {#step-13--try-the-chain}

1. Recolha **2. Joints & Links** para abrir espaço.

2. Expanda **4. Controls**.

3. No Object Mode, defina `Blade1 Hinge`, `Blade2 Hinge` e `BladeTip Hinge` como 60 graus cada.

Para inserir cada valor:

1. Clique duas vezes no campo numérico.

2. Pressione Ctrl+A.

3. Digite o valor.

4. Pressione Enter.

Os segmentos posteriores acompanham os anteriores, curvando a cadeia. Antes de continuar, retorne os três valores a 0.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 13: as três dobradiças da lâmina a 60 graus em Controls

*1: Insira 60 em cada um dos três controles deslizantes da lâmina. 2: Verifique se a cadeia se curva em conjunto. Retorne os três controles a 0.*

## E. Placas e escora {#e-plates-and-strut}

### Etapa 14 — Dobradiças nas placas {#step-14--hinges-on-the-plates}

`PlateL` fica oculta atrás da cabeça na vista Direita.

1. Adicione uma Dobradiça a `PlateR` usando o mesmo procedimento.

2. Defina seu **Max** como 30.

3. Pressione Ctrl+Numpad 3 para a vista Esquerda.

4. Adicione uma Dobradiça a `PlateL`.

5. Defina seu **Max** como 30.

6. Pressione Numpad 3 para voltar à vista Direita.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 14: PlateL Hinge e PlateR Hinge

*1: Crie as dobradiças de PlateR e PlateL; use a vista do lado oposto para alcançar PlateL. 2: Defina Max como 30 em cada uma.*

### Etapa 15 — Add Link → Follow {#step-15--add-link--follow}

Um único controle deve mover as duas placas. Ajuste a vista antes de iniciar o assistente:

1. Pressione Numpad 1 para a vista Frontal.

2. Selecione `Blade2`.

3. Use F3 > Frame Selected para aproximar a cabeça.

As duas placas externas aparecem nas bordas esquerda e direita.

1. Abra **Add Link > Follow**.

2. Clique em `PlateL`, na borda esquerda, como peça condutora.

3. Clique em `PlateR`, na borda direita, como peça seguidora.

4. Pressione Enter.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 15: a vista Frontal expõe as duas placas externas para a seleção do vínculo de acompanhamento

*1: Clique primeiro em PlateL, a peça condutora. 2: Clique depois em PlateR, a peça seguidora. Pressione Enter.*

### Etapa 16 — Intervalos {#step-16--ranges}

1. Selecione o novo vínculo de acompanhamento.

2. Verifique os valores preenchidos automaticamente: **Source Range** 0…30 e **Target Range** 0…30.

3. Em **Name**, renomeie o vínculo para `PlateR Follow`.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 16: Source Range e Target Range

*1: Nomeie o vínculo como PlateR Follow. 2: Verifique se Source Range vai de 0 a 30. 3: Verifique se Target Range vai de 0 a 30.*

### Etapa 17 — Add Link → Piston {#step-17--add-link--piston}

A escora deve apontar entre o corpo do rifle e a cabeça enquanto a cabeça se dobra. O assistente intercepta os atalhos de navegação enquanto está ativo. Antes de iniciá-lo:

1. Pressione Numpad 3 para a vista Direita.

2. Selecione `StrutRod` no Outliner.

3. Use F3 > Frame Selected para uma vista próxima.

4. Abra **Add Link > Piston**.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 17: menu Add Link, Piston

*1: Abra Add Link depois de enquadrar StrutRod. 2: Escolha Piston; o assistente solicita primeiro o cilindro.*

### Etapa 18 — O cilindro e a haste {#step-18--the-cylinder-and-the-rod}

Os papéis de cilindro/haste no assistente descrevem as extremidades do vínculo. Os nomes dos objetos do modelo descrevem suas peças originais. `StrutBase` é a vareta vermelha fina exposta nos entalhes da luva. `StrutRod` é a luva preta.

1. Na vista próxima, clique primeiro em `StrutBase` como peça do cilindro.

2. Clique depois em `StrutRod` como peça da haste.

3. Pressione Enter para aceitar.

4. Renomeie o vínculo para `Head Strut`.

5. Mantenha **Stretch** desativado.

1. Altere `HeadMount Hinge` em Controls.

2. Observe a escora.

3. Retorne o valor a zero.

**O que você deve ver:** A escora acompanha a cabeça. Cada peça aponta para a outra.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 18: assistente de pistão, primeiro o cilindro vermelho exposto e depois a luva preta

*1: Clique primeiro na StrutBase vermelha exposta. 2: Clique depois na luva preta StrutRod. Pressione Enter.*

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 18: configurações de Head Strut com Stretch desativado

*1: Renomeie o vínculo para Head Strut. 2: Deixe Stretch desmarcado; depois teste HeadMount Hinge e restaure 0.*

## F. O rifle {#f-the-rifle}

### Etapa 19 — Dobradiças da empunhadura e do espigão traseiro {#step-19--grip-and-rear-spike-hinges}

Para cada uma de `Grip` e `RearSpike`:

1. Abra **Add Joint → Hinge**.

2. Clique na peça.

3. Pressione X.

4. Pressione Enter.

5. Defina **Min** como 0.

6. Defina **Max** como 90.

Depois:

1. Selecione `RearSpike Hinge` na lista.

2. Defina seu Axis X como -1.

3. Mantenha Y e Z em 0.

4. Mantenha Grip no sentido positivo de X.

5. Confirme que `Grip Hinge` e `RearSpike Hinge` aparecem na lista de articulações.

Inverter o eixo X de RearSpike faz a peça se dobrar em direção à cabeça recolhida na forma Compact. Estes controles recolhem a empunhadura e o espigão traseiro para a forma compacta da Etapa 25.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 19: Grip Hinge, Max 90

*1: Selecione Grip Hinge. 2: Mantenha Axis X em 1 e Y e Z em 0. 3: Defina Max como 90; mantenha Min em 0.*

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 19: RearSpike Hinge com Axis X -1 e Max 90

*1: Selecione RearSpike Hinge. 2: Defina Axis X como -1. 3: Defina Max como 90; mantenha Min em 0.*

### Etapa 20 — Deslizamentos de Magazine e Bolt {#step-20--magazine-and-bolt-slides}

Para `Magazine` e depois `Bolt`:

1. Abra **Add Joint → Slide**.

2. Clique na peça.

3. Pressione Z.

4. Pressione Enter.

5. Defina **Max** como 0.04 para Magazine ou 0.06 para Bolt.

Deslizamentos usam unidades da cena. Um valor de 0.06 corresponde a 6 cm.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 20: Magazine Slide, eixo Z e Max 0.04

*1: Selecione Magazine Slide depois de Add Joint > Slide. 2: Use o eixo Z (Z = 1, X = Y = 0). 3: Defina Max como 0.04; mantenha Min em 0.*

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 20: Bolt Slide, eixo Z e Max 0.06

*1: Selecione Bolt Slide depois de Add Joint > Slide. 2: Use o eixo Z (Z = 1, X = Y = 0). 3: Defina Max como 0.06; mantenha Min em 0.*

### Etapa 21 — Deslizamento de Pole {#step-21--pole-slide}

1. Abra **Add Joint → Slide**.

2. Clique em `Pole`.

3. Pressione Z.

4. Pressione Enter.

5. Defina **Max** como 0.6.

6. Em **4. Controls**, defina `Pole Slide` como 0.6.

7. Observe a haste retraída.

8. Retorne o controle a zero.

Valores positivos movem a haste para cima, para dentro do corpo do rifle.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 21: configurações de Pole Slide, eixo Z e Max 0.6

*1: Selecione Pole Slide depois de Add Joint > Slide. 2: Use o eixo Z (Z = 1, X = Y = 0). 3: Defina Max como 0.6; mantenha Min em 0.*

### Etapa 22 — Telescópio de Pole {#step-22--pole-telescope}

1. Abra **Add Joint → Telescope**.

2. Clique em `Pole` como base.

3. Clique em `ButtSpike` como segmento.

4. Pressione Enter.

5. Pressione Z.

6. Pressione Enter.

7. Defina **Length** como 0.2.

8. Teste o controle separado.

9. Retorne o controle a zero.

O controle move o espigão até 20 cm ao longo do sentido positivo de Z, para dentro da haste deste modelo.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 22: seleção guiada do Telescópio, Pole como base e ButtSpike como segmento

*1: Clique em Pole como base. 2: Clique em ButtSpike como segmento. Pressione Enter, depois Z e depois Enter.*

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 22: configurações de Pole Telescope, eixo Z e Length 0.2

*1: Selecione Pole Telescope. 2: Verifique se Z é seu eixo. 3: Insira Length 0.2; teste o controle e retorne a zero.*

## G. Sequências {#g-sequences}

### Etapa 23 — Add Sequence {#step-23--add-sequence}

1. Em **3. Sequences**, selecione **Add Sequence**.

2. Clique duas vezes no nome da sequência na lista.

3. Digite `Scythe to Rifle`.

4. Pressione Enter.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 23: Add Sequence

*1: Clique em Add Sequence. 2: Clique duas vezes no novo nome e digite Scythe to Rifle. Pressione Enter.*

### Etapa 24 — Grave um grupo de movimento {#step-24--record-a-motion-group}

1. Selecione **Move Slider to End**.

O controle deslizante da sequência vai para `100%`. O botão passa a ser Record Step 1.

1. Em **4. Controls**, defina `BladeTip Hinge` como 70.

2. Defina `Blade2 Hinge` como 120.

3. Selecione Record Step 1.

Isso armazena duas entradas de alvo, uma por controle movido. Os dois controles deslizantes das articulações retornam a zero.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 24: Move Slider to End antes de definir a pose do primeiro grupo

*1: Clique uma vez em Move Slider to End. O botão muda para Record Step 1.*

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 24: Record Step 1 com Blade2 a 120 e BladeTip a 70 graus

*1: Insira Blade2 = 120 e BladeTip = 70. 2: Clique em Record Step 1; os dois alvos são armazenados e os controles das articulações retornam a zero.*

*Grupos de movimento restantes.* A gravação continua armada após cada captura. Não a arme novamente. Para cada grupo restante abaixo:

1. Defina a pose dos controles do grupo com os valores indicados.

2. Selecione o botão Record Step exibido.

| Grupo de movimento | Defina a pose destes controles | Botão de gravação após os grupos anteriores |
|---|---|---|
| 2 | `Blade1 Hinge` 10 e `PlateL Hinge` 30 | Record Step 3 |
| 3 | `HeadMount Hinge` 90 | Record Step 5 |
| 4 | `Pole Slide` 0.6 | Record Step 6 |

O número do botão é igual à quantidade de entradas de alvo armazenadas mais um. Gravar dois controles avança o número em dois. Ele não conta os cliques de gravação. Os quatro grupos de movimento produzem seis entradas de alvo. Se você mudar quais controles se movem, use o número exibido no botão.

### Etapa 25 — As etapas {#step-25--the-steps}

Cada alvo gravado tem uma entrada sob a sequência. A entrada mostra **Target**, suavização, **Start** e **End**. Os campos Start/End usam 0-1. Os controles deslizantes em Controls mostram 0-100%.

| Movimento | Start | End |
|---|---:|---:|
| A lâmina se dobra primeiro | 0 | 0.25 |
| As placas e o primeiro segmento acompanham | 0.25 | 0.5 |
| A cabeça se dobra em terceiro | 0.5 | 0.8 |
| A haste se move por último | 0.8 | 1 |

As entradas do mesmo grupo de movimento usam os mesmos valores de Start e End. Para cada entrada de `Scythe to Rifle`:

1. Defina **Start** com o valor de Start do seu grupo de movimento na tabela.

2. Defina **End** com o valor de End do seu grupo de movimento na tabela.

3. Mantenha a entrada em `Ease In Out`.

Antes do intervalo de uma etapa, ela mantém seu valor inicial. Depois do intervalo, mantém seu valor final.

Quando cada sequência estiver concluída, selecione **Cancel** na faixa de captura. Cancel encerra a gravação, mantém as entradas armazenadas e retorna o controle da sequência a zero. Enquanto a gravação está armada, um aviso de sobreposição descreve o próximo intervalo de gravação proposto. Não adicione um grupo vazio extra.

Para a segunda sequência, use o procedimento de gravação da Etapa 24:

1. Adicione `Rifle to Compact`.

2. Selecione **Move Slider to End** uma vez para armar a gravação.

3. Defina `Grip Hinge` como 90 para o primeiro grupo.

4. Defina `RearSpike Hinge` como 90.

5. Selecione Record Step 1.

6. Para cada entrada do primeiro grupo:

    1. Defina **Start** como 0.

    2. Defina **End** como 0.5.

7. Defina `Magazine Slide` como 0.04 para o segundo grupo.

8. Defina `Bolt Slide` como 0.06.

9. Selecione Record Step 3.

10. Para cada entrada do segundo grupo:

    1. Defina **Start** como 0.5.

    2. Defina **End** como 1.

11. Mantenha cada entrada em `Ease In Out`.

12. Selecione **Cancel** na faixa de captura para encerrar a gravação.

Cada grupo cria duas entradas. No segundo grupo, o botão de gravação muda de Record Step 1 para Record Step 3.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 25: os seis alvos e intervalos de tempo em Scythe to Rifle

*1: Target é o valor da articulação gravado. 2: Escolha Ease In Out. 3: Insira Start. 4: Insira End. Repita esses campos para as seis entradas usando os valores indicados.*

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 25: os quatro alvos e intervalos de tempo em Rifle to Compact

*1: Grip e RearSpike usam Target 90, Start 0, End 0.5. 2: Magazine e Bolt usam 0.04 / 0.06, Start 0.5, End 1. Mantenha Ease In Out.*

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 25: encerrar a gravação com Cancel na faixa de captura

*1: Depois de concluir uma sequência, clique em Cancel nesta faixa de captura para encerrar a gravação. Isso mantém as entradas e retorna a sequência a zero.*

### Etapa 26 — Teste a sequência {#step-26--test-the-sequence}

**Test**, ao lado do botão de gravação de etapas, percorre o controle de 0% a 100% e de volta a 0%. Depois restaura o valor que o controle tinha antes do teste.

1. Partindo de Scythe, selecione **Test** para `Scythe to Rifle`.

2. Com a primeira sequência em 100%, selecione **Test** para `Rifle to Compact`.

3. Depois de testar, retorne as duas sequências a 0%.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 26: o botão Test da sequência durante o recolhimento

*1: Clique em Test ao lado do botão de gravação. 2: Observe o recolhimento e o retorno. Teste Compact com Scythe to Rifle em 100%.*

**O que você deve ver:** A lâmina se curva, as placas se fecham, a cabeça se dobra para baixo ao longo do corpo do rifle e a haste desliza para cima. Depois, tudo volta.

## H. Formas {#h-forms}

### Etapa 27 — Salvar forma {#step-27--save-form}

Mantenha todos os controles individuais das articulações em zero. As Sequências fornecem o movimento. Levar a sequência selecionada ao fim pode armar a gravação novamente. Salvar uma Forma não grava outra etapa. A menos que você pretenda adicionar outro alvo, não selecione Record Step.

Em **4. Controls**:

1. Com todos os controles deslizantes em 0, selecione **Save Form**.

2. Clique duas vezes na nova entrada da lista.

3. Nomeie-a como `Scythe`.

4. Defina `Scythe to Rifle` como `100%`.

5. Selecione **Save Form**.

6. Nomeie a nova entrada como `Rifle` usando o mesmo procedimento.

7. Defina também `Rifle to Compact` como `100%`.

8. Selecione **Save Form**.

9. Nomeie a nova entrada como `Compact`.

Para desarmar a gravação:

1. Selecione `Scythe` na lista de formas.

2. Selecione **Go to Form**.

As duas sequências retornam a zero. Ir para Rifle ou Compact pode armar a gravação novamente, pois a sequência selecionada fica em 100%.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 27: Save Form com todos os controles deslizantes em 0

*1: Comece com as duas sequências e todas as articulações em 0. 2: Clique em Save Form. 3: Clique duas vezes na nova entrada da lista e nomeie-a como Scythe; repita para Rifle e Compact.*

### Etapa 28 — Ir para forma {#step-28--go-to-form}

1. Selecione uma forma na lista.

2. Selecione **Go to Form**.

**Go and Key** também insere chaves para todos os controles no quadro atual. Essas chaves animam a transformação.

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 28: Rifle selecionada, Go to Form

*1: Selecione a forma salva. 2: Clique em Go to Form. Go and Key também insere chaves de animação.*

### Etapa 29 — O rifle {#step-29--the-rifle}

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 29: a forma Rifle

*1: Selecione Rifle. 2: Clique em Go to Form. 3: Compare as porcentagens das sequências com a pose mostrada na imagem da fonte.*

### Etapa 30 — Compacta {#step-30--compact}

Descrição da imagem da fonte em inglês (imagem omitida): Etapa 30: a forma Compact

*1: Selecione Compact. 2: Clique em Go to Form. 3: Compare as porcentagens das sequências com a pose mostrada na imagem da fonte.*

1. Volte a `Scythe`.

2. Salve o arquivo.

## O que você construiu {#what-you-built}

| Registro | Ossos | O que faz |
|---|---|---|
| 15 peças | `MCH-<part>` e `DEF-<part>` | A malha de cada peça é filha do seu osso `DEF-` |
| 8 dobradiças, 3 deslizamentos, 1 telescópio | `CTRL-<part>` | Os controles; seus valores são os controles deslizantes em **4. Controls** |
| 1 pistão | `MCH-<part>-aim` e `MCH-<part>-target` | Mantém as duas peças da escora apontadas uma para a outra |
| 1 vínculo de acompanhamento | nenhum | `PlateR` gira com `PlateL` |
| 2 Sequências | `CTRL-SEQ-<name>` | Um controle deslizante para cada uma |
| 3 Formas | nenhum | Valores salvos dos controles deslizantes |

O exemplo atualizado passou no Rig Validator sem problemas relatados. Também passou nas verificações de recarregamento com Auto Run Python Scripts desativado, incluindo cada controle individual e as três Formas.

## Experimente a seguir {#try-next}

Para editar o mapeamento do vínculo de acompanhamento:

1. Ative **Curve** em `PlateR Follow`.

2. Remodele o mapeamento no Editor de gráficos.

Para outra pose, salve uma quarta forma, `Carry`, com a lâmina dobrada e a cabeça erguida.

Para animar e exportar:

1. Insira chaves para as formas ao longo dos quadros com **Go and Key**.

2. Exporte os ossos `DEF-` (consulte [Ferramentas VRChat](08-vrchat.md)).

## Vínculo de engrenagem {#gear-link}

Crescent Rose não tem um par de engrenagens; por isso, este rig não tem Vínculo de engrenagem. Um Vínculo de engrenagem gira uma Dobradiça quando outra gira, de acordo com uma razão de dentes. Exemplos incluem uma manivela e uma roda ou uma cremalheira que converte rotação em deslizamento. Consulte [Vínculo de engrenagem](07-mechanisms.md#gear-link).

## Créditos {#credits}

Modelo Crescent Rose de amandangm, https://sketchfab.com/3d-models/crescent-rose-dcb6bfbb3b824c01a182fa131fe35824, CC BY 4.0. Este tutorial usa uma versão dividida, escalada e com rig. Crescent Rose é um projeto da Rooster Teeth Productions. Este é um recurso de tutorial feito por fã.

[← Sumário](index.md)
