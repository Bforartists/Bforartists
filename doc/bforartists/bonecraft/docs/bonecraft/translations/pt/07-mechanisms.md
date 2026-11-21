# Mechanisms {#mechanisms}

[← Sumário](index.md)

## O que Mechanisms faz {#what-mechanisms-does}

Mechanisms constrói rigs mecânicos a partir de peças de superfície rígida. Ele oferece dobradiças, deslizamentos, telescópios, pistões, engrenagens, seguidores e transformações completas controladas por um único controle deslizante. Cria ossos e restrições comuns do Blender. Você pode inspecionar e alterar tudo o que ele constrói. O rig funciona no Blender sem scripts. As engines recebem os ossos `DEF-`. A exportação de movimento de mecanismos consolidado para engines virá depois (consulte Limites desta versão).

O BoneCraft fornece as ferramentas. Você fornece as peças da arma.

Um exemplo prático completo, com etapas escritas e descrições de imagens do original em inglês preservadas, está em [Tutorial: Crescent Rose com Mechanisms](12-crescent-rose.md).

Termos usados nos painéis e nesta página:

| Termo | Significado |
|---|---|
| *Part* | Peça que se move como um bloco sólido: um objeto ou uma parte solta de uma malha. Uma peça pode acompanhar outra. |
| *Joint* | Articulação que define como uma peça pode se mover: Hinge (gira), Slide (desloca), Telescope (estende segmentos encaixados). |
| *Link* | Vínculo que move uma peça por você: Piston, Gear Link, Follow. |
| *Handle* | Osso de controle que você arrasta na viewport. Cada articulação tem um. Seu valor também aparece como um controle deslizante no painel. |
| *Sequence* | Transformação reproduzida por um único controle deslizante, composta de etapas. |
| *Form* | Conjunto salvo de valores dos controles e de Sequence, como “Stowed” ou “Rifle”. |

## Onde fica {#where-it-is}

- **Aba BoneCraft → Mechanisms** na Viewport 3D. A aba BoneCraft fica na Tool Shelf à esquerda (pressione **T**), a menos que você a tenha movido para a barra lateral à direita (**N**) nas preferências. Ela fica entre Skin e Review. Aparece quando uma malha está ativa (para iniciar um rig) ou quando uma armadura com mecanismos está ativa. Caso contrário, explica o que selecionar.
- **Editor de Propriedades → aba Scene → Mechanisms**, logo após Rig Builder. Aparece enquanto Preferences → Tabs → Scene Properties → Show estiver ativado. Sem uma seleção utilizável, mostra uma linha: “Select a mesh to start, or an armature with mechanisms.” (selecione uma malha para começar ou uma armadura com mecanismos). Desativar a aba BoneCraft da viewport não o remove. O controle Scene Properties oculta apenas a cópia de Scene. O controle da ferramenta `mechanisms` (**Preferences → Add-ons → BoneCraft → Tools**) remove a ferramenta de todos os locais. As seções da aba Scene começam recolhidas; clique em **Mechanisms** para expandi-la.
- **Menu Object → Mechanisms** oferece atalhos para adicionar peças, articulações e vínculos e testar movimentos.
- **Barra de ferramentas da viewport → Build Mechanism** inicia uma articulação ou vínculo guiado ao clicar em uma peça, no modo Objeto ou Pose.

Para preparar Build Mechanism:

1. Adicione as peças.
2. Selecione o rig do mecanismo ou uma de suas peças.
3. No cabeçalho da ferramenta, selecione o tipo.

Dentro de Mechanisms há quatro subseções: **1. Parts**, **2. Joints & Links**, **3. Sequences** e **4. Controls**. Elas aparecem quando o rig já tem peças. Antes disso, você vê apenas **Add Parts from Selection**.

Cada botão corresponde a uma etapa de Desfazer. Se uma construção falhar, o BoneCraft restaura tudo o que ela alterou. O painel mostra o motivo.

Descrição da imagem do original em inglês (imagem omitida): Mechanisms na aba BoneCraft.

*Captura histórica da oficina. Mechanisms na aba BoneCraft.*

## Peças {#parts}

1. Selecione os objetos das peças (ou uma malha composta de partes soltas) no modo Objeto.
2. Clique em **Add Parts from Selection**.
    - Vários objetos: uma peça por objeto. Cada objeto é vinculado como filho ao osso da sua peça e permanece onde está.
    - Uma malha com partes soltas: uma peça por parte. Cada parte recebe um grupo de vértices para seu osso e a malha recebe um modificador Armature.
    - Na primeira vez, o BoneCraft cria o rig (uma armadura) para você.
3. Selecione uma peça na lista para editá-la.

Para cada peça:

- **Rides on:** escolha a peça que esta acompanha. Uma peça filha acompanha sua peça pai. “the rig” significa que ela acompanha a raiz do rig.
- **Size** define o comprimento do osso, que determina o tamanho do controle.
- **Edit Pivot** coloca um marcador na peça. **Apply Pivot** move os ossos da peça até o marcador. O objeto permanece no lugar.
- **Apply Transforms** aparece quando uma peça de objeto tem rotação ou escala não aplicadas. Transformações não aplicadas inclinam os eixos. Quando esse botão aparecer, clique em **Apply Transforms**.
- O botão **X** remove a peça. Ele recusa a remoção enquanto uma articulação, vínculo ou outra peça a usar, e informa seus nomes.
- **Merge for VRChat** exige duas ou mais peças de objeto. Mescle apenas peças vinculadas exclusivamente ao rig do mecanismo. Faça isso por último. A ação une as peças de objeto em uma malha com um grupo de vértices por antigo objeto e um modificador Armature. As peças unidas tornam-se partes soltas dessa única malha. A mesclagem remove grupos de vértices com nomes dos ossos dessa armadura, exceto o próprio osso `DEF-` da peça.

Para alterar o pivô de uma peça:

1. Selecione **Edit Pivot**.
2. Arraste o marcador para o ponto a partir do qual a peça deve girar ou deslizar.
3. Clique em **Apply Pivot**.

Você pode renomear o objeto de uma peça: as peças recebem identificadores em seus objetos, permitindo que a peça encontre seu objeto novamente. Uma cópia do objeto (Shift+D) não assume a peça. Se o objeto de uma peça for excluído, ela mostra “Part '&lt;name&gt;' is missing” com **Reassign** e **Delete**. Os outros mecanismos continuam funcionando.

- **Reassign** usa a malha selecionada. Recusa objetos que não sejam malhas e objetos já usados por outra peça de objeto. Partes soltas de uma malha podem compartilhar essa malha.
- **Delete** remove a peça (consulte Edição abaixo para saber quando a remoção é recusada).

Descrição da imagem do original em inglês (imagem omitida): peças adicionadas e controles do pivô da peça selecionada.

Descrição da imagem do original em inglês (imagem omitida): peças adicionadas e controles do pivô da peça selecionada.

*Captura histórica da oficina. Peças adicionadas e controles do pivô da peça selecionada.*

## Articulações e vínculos, um exemplo de cada {#joints-and-links-one-example-each}

**Add Joint** inicia a construção guiada de uma articulação. **Add Link** inicia a construção guiada de um vínculo. Ambos funcionam na aba da viewport e na aba Scene do editor de Propriedades. Na aba Scene, o guia usa a maior Viewport 3D na tela.

Como alternativa, use a barra de ferramentas:

1. Ative Build Mechanism na barra de ferramentas da viewport.
2. No cabeçalho da ferramenta, selecione o tipo de articulação ou vínculo.
3. Clique na primeira peça.

Esse clique inicia o mesmo guia e fornece sua primeira seleção. Continue com as seleções e escolhas de eixos solicitadas na viewport. Os menus Add Joint e Add Link continuam disponíveis.

**Align to Selection** permite dobradiças inclinadas. Ao pressionar **A**, a malha da peça deve estar no modo Edição, com uma aresta ou face selecionada. O guia ignora **Tab**. Antes de usar **Align to Selection**, prepare a malha:

1. Entre no modo Edição na malha da peça.
2. Selecione uma aresta ou face.
3. Permanecendo no modo Edição, inicie **Add Joint → Hinge**.
4. Clique na peça.
5. Pressione **A**.

Se nada utilizável estiver selecionado, o guia mostra uma mensagem. Você pode então pressionar outra tecla.

Regras curtas para todas as construções guiadas:

- Clique nas peças na viewport. As peças clicadas recebem um contorno e um número.
- Quando uma etapa precisar de um eixo, pressione **X**, **Y** ou **Z**.
- Com **Align to Selection** preparado como acima, pressione **A** para alinhar à seleção.
- A última etapa mostra uma prévia do mecanismo movendo-se em ciclo. **Enter** o mantém. **Esc** o remove.
- O cabeçalho e a barra de status mostram uma frase completa para cada etapa. Com Show Helpers desativado, mostram um rótulo curto.

Cada linha da lista Joints & Links tem quatro botões com ícones: **Test** (triângulo de reprodução), **Edit** (lápis, mostra as configurações), **Detach** (corrente quebrada) e **Delete** (X).

Após a construção, o item selecionado na lista mostra somente as configurações usadas por seu tipo.

### Hinge {#hinge}

Blade Hinge, 0°…90°:

1. Use Add Parts from Selection com uma peça Blade.
2. Selecione **Add Joint → Hinge**.
3. Clique em Blade.
4. Pressione **X**.
5. Pressione **Enter**.

A construção cria um controle em semicírculo, `CTRL-Blade`, e um item *Blade Hinge* na lista.

6. Defina **Min** como 0.
7. Defina **Max** como 90 (° para Hinge).
8. Para testar a dobradiça, arraste o controle em semicírculo.

O controle para em 90°. **Set Min** e **Set Max** copiam a pose atual do controle para os limites.

Um limite inferior a uma volta completa deve ficar entre −180°…180°. Limites como 170°…190° são recusados com uma mensagem. Um intervalo de uma volta completa ou mais (por exemplo, −180°…180°) gira livremente, sem limite.

Descrição da imagem do original em inglês (imagem omitida): limites da dobradiça e controles da alça.

*Captura histórica da oficina. Limites da dobradiça e controles da alça.*

### Slide {#slide}

Barrel Slide, 0…0.3:

1. Selecione **Add Joint → Slide**.
2. Clique na peça Barrel.
3. Pressione **Y**.
4. Pressione **Enter**.

A construção cria um controle em forma de seta.

5. Defina **Min** como 0.
6. Defina **Max** como 0.3 (unidades da cena).
7. Para testar o deslizamento, arraste a seta.

O cano desliza e para em 0.3.

Descrição da imagem do original em inglês (imagem omitida): limites de deslocamento de Slide para a peça selecionada.

*Captura histórica da oficina. Limites de deslocamento de Slide para a peça selecionada.*

### Telescope {#telescope}

Mastro com três segmentos:

1. Crie a base e as três peças dos segmentos.
2. Selecione **Add Joint → Telescope**.
3. Clique na base.
4. Clique em cada segmento, na ordem da base para fora.
5. Pressione **Enter**.
6. Pressione a tecla do eixo.
7. Para manter a construção, pressione **Enter**.

A construção cria um controle em forma de seta na base. **Length** é o deslocamento total. **Shares (empty = even)** divide esse deslocamento entre os segmentos.

Para testar divisões personalizadas:

1. Defina **Length** como 1.
2. Digite `0.5, 0.25, 0.25` em **Shares (empty = even)**.
3. Arraste o controle em forma de seta.

Os três segmentos se estendem conforme suas parcelas. A soma das parcelas deve ser igual a Length, para a ponta percorrer o comprimento total. Texto inválido, como `0.5, abc`, produz uma mensagem. Cada segmento exige uma parcela numérica e a soma deve ser igual a Length. **Set Max** define Length a partir da pose do controle.

Descrição da imagem do original em inglês (imagem omitida): comprimento de Telescope e parcelas dos segmentos.

*Captura histórica da oficina. Comprimento de Telescope e parcelas dos segmentos.*

### Piston {#piston}

Elevador: cilindro na estrutura, haste no braço.

1. Adicione Hinge ao braço.
2. Configure o braço para acompanhar a estrutura.
3. Selecione **Add Link → Piston**.
4. Clique na peça do cilindro na estrutura.
5. Clique na peça da haste no braço.

A construção cria um Piston sem controle. Cada peça aponta para o ponto de conexão da outra. A opção **Stretch** estica a haste para molas e cabos.

6. Para testar Piston, mova o controle do braço.

O pistão acompanha. Se nada mover o Piston ainda, a construção funciona, mas não tem prévia. **Test** informa essa condição.

Descrição da imagem do original em inglês (imagem omitida): configurações de Piston para as peças conectadas.

*Captura histórica da oficina. Configurações de Piston para as peças conectadas.*

### Gear Link {#gear-link}

Engrenagem 20:40:

As duas peças precisam primeiro de uma articulação. A peça motriz precisa de Hinge. Para Gear e Belt, a peça movida precisa de Hinge. Para Rack, precisa de Slide.

1. Selecione **Add Link → Gear Link**.
2. Clique na peça motriz.
3. Clique na peça movida.

Para o método por número de dentes:

1. Nas configurações do vínculo, defina **Source Teeth** como 20.
2. Defina **Target Teeth** como 40.

Como alternativa, digite um **Ratio**. **Kind** pode ser Gear, Belt ou Rack. **Reverse** inverte a direção. Para testar o vínculo, gire a origem.

Com **Kind** em Gear, o alvo gira −0.5× a distância angular da origem (+0.5× com Belt). Gear inverte a direção. Belt mantém a direção. Rack converte rotação em deslizamento. Sua distância por radiano é igual a **Ratio** × **Pinion Radius**.

Como o BoneCraft constrói isso depende do intervalo de Hinge da origem:

- Menos de uma volta completa: uma restrição Transform. Ela acompanha tudo o que move a origem, incluindo Sequences.
- Uma volta completa ou mais: um driver que não precisa de Python. O alvo gira indefinidamente com a origem. Ele acompanha somente controles e engrenagens. Rig Validator avisa quando uma Sequence ou Follow seria perdida.

Descrição da imagem do original em inglês (imagem omitida): controles de Gear Link antes de inserir o exemplo 20:40. A proporção mostrada é 1.00 e as duas contagens de dentes são 0.

*Janela flutuante nativa da compilação de teste, versão candidata BoneCraft 9.2.19. Bforartists 5.2.3, Blender 5.4 Alpha. Controles de Gear Link antes de inserir o exemplo 20:40. A proporção mostrada é 1.00 e as duas contagens de dentes são 0.*

### Follow {#follow}

Blade 0–90° levanta Cover 0–40°:

As duas peças precisam de Hinge ou Slide. Hinge da origem precisa de limites inferiores a uma volta completa. O BoneCraft recusa uma origem de rotação livre.

1. Selecione **Add Link → Follow**.
2. Clique na peça condutora (Blade).
3. Clique na peça seguidora (Cover).

Inicialmente, cada intervalo de mapeamento abrange o intervalo completo de sua articulação.

4. Defina **Source Range** como 0…90.
5. Defina **Target Range** como 0…40.
6. Para testar Follow, mova o controle Blade.

Cover acompanha. Além de qualquer extremidade do intervalo, o alvo mantém o valor. Para alterar a forma do mapeamento no Editor gráfico, ative **Curve**. O BoneCraft nunca sobrescreve sua curva (consulte Edição abaixo).

Descrição da imagem do original em inglês (imagem omitida): intervalos de origem e alvo de Follow.

*Captura histórica da oficina. Intervalos de origem e alvo de Follow.*

### Sequence {#sequence}

Grave etapas para dobrar uma arma:

1. Em **3. Sequences**, clique em **Add Sequence**.

Isso cria um controle deslizante chamado `CTRL-SEQ-<name>`.

2. Clique em **Move Slider to End**.

O controle salta para seu final (1). O botão passa a ser Record Step seguido do número da próxima etapa.

3. Posicione os controles das articulações na pose da primeira etapa.
4. Clique em Record Step 1.

Cada controle movido vira uma etapa com seu valor-alvo. Os controles retornam a zero.

Para cada gravação adicional:

1. Clique em **Move Slider to End**.
2. Posicione os controles das articulações na pose da próxima etapa.
3. Clique no botão numerado atual Record Step.

Por padrão, cada nova etapa ocupa o próximo quarto do controle deslizante. Para cada etapa gravada:

1. Defina **Target**.
2. Selecione a suavização: Linear, Ease In, Ease Out, Ease In Out ou Snap.
3. Defina **Start**.
4. Defina **End**.

Fora de sua faixa, uma etapa mantém seu valor final. Várias Sequences podem se somar. Para testar a Sequence, clique em **Test**. O controle reproduz 0 → 1 → 0.

Ao lado do botão de gravação de etapas e de **Test**, a Sequence selecionada tem **Detach** (corrente quebrada) e **Delete** (X). Uma Sequence retida por edição manual (por exemplo, uma etapa cuja curva você remodelou) mostra sua mensagem e um botão **Restore**. Restore regenera as etapas a partir do registro. Keep mine não é oferecido para Sequence.

Descrição da imagem do original em inglês (imagem omitida): criação de Sequence, etapas gravadas e temporização.

Descrição da imagem do original em inglês (imagem omitida): criação de Sequence, etapas gravadas e temporização.

*Captura histórica da oficina. Criação de Sequence, etapas gravadas e temporização.*

## Test {#test}

**Test** (botão de reprodução na lista e em 3. Sequences) percorre todo o intervalo de um mecanismo e retorna. Não grava chaves e restaura a pose ao terminar. Para interromper o teste antes do final, pressione **Esc**. Isso também restaura a pose. Para Gear Link ou Follow, Test percorre o intervalo da origem. Para Piston, Test percorre a articulação que o move. O BoneCraft não detecta colisões. Observe se as peças se chocam.

Descrição da imagem do original em inglês (imagem omitida): testar o mecanismo selecionado em seu intervalo de movimento.

*Captura histórica da oficina. Testar o mecanismo selecionado em seu intervalo de movimento.*

## Formas {#forms}

Em **4. Controls**:

- Cada articulação e Sequence tem um controle deslizante. É o próprio canal do controle da viewport; portanto, arrastar esse controle e usar o controle deslizante são a mesma coisa.
- **Save Form** registra cada valor dos controles e dos controles deslizantes de Sequence sob um nome. Renomeie a forma na lista.
- **Go to Form** define todos os controles com os valores salvos.
- **Go and Key** faz o mesmo e também insere chaves no quadro atual.
- O **X** ao lado da lista remove uma forma.

**Arquivos salvos anteriores:** o BoneCraft 9.2.18 lê e aplica formas capturadas por versões anteriores. Abrir ou aplicar uma forma não a salva novamente. **Save Form** captura os valores atuais dos controles usando o formato atual. Salvar com o nome de uma forma existente substitui os valores capturados dessa forma.

Os controles permanecem em **Mechanisms → 4. Controls**. A correção de compatibilidade não altera os controles do rig, os controles deslizantes de Sequence nem os locais dos painéis.

Descrição da imagem do original em inglês (imagem omitida): os controles de Formas mostram controles deslizantes, Save Form, Go to Form e Go and Key.

*Captura histórica da oficina. Os controles de Formas mostram controles deslizantes, Save Form, Go to Form e Go and Key.*

## O que o BoneCraft constrói {#what-bonecraft-builds}

Para cada peça:

| Osso | Função | Visível |
|---|---|---|
| `CTRL-<part>` | O controle. Seu valor é o controle deslizante do painel. Somente Hinge, Slide e Telescope criam um. | Sim |
| `MCH-<part>` | Soma o controle e cada vínculo e depois aplica os limites. | Oculto |
| `DEF-<part>` | Copia `MCH-<part>`. A malha está vinculada a ele. As engines recebem esse osso. | Oculto |

Os ossos ficam nas coleções `Mechanism Controls`, `Mechanism MCH` e `Mechanism DEF`. Uma peça sem articulação tem somente ossos `MCH-` e `DEF-`. O controle de Telescope é `CTRL-<telescope name>`. O de Sequence é `CTRL-SEQ-<name>`. Piston adiciona ossos `MCH-<part>-aim` e `MCH-<part>-target` para cada uma de suas duas peças.

As restrições em `MCH-<part>` vêm sempre na mesma ordem: Copy Transforms do controle, depois a contribuição de cada vínculo e por fim Limit Rotation ou Limit Location da articulação. `DEF-<part>` tem uma restrição Copy Transforms de `MCH-<part>`.

Tudo o que o BoneCraft constrói recebe identificadores de seu registro: nomes de restrições começam com `BC·<id>·<role>`, e os ossos têm as propriedades `bc_mech_id` e `bc_mech_role`. O BoneCraft encontra seus ossos pelo identificador, não pelo nome; portanto, você pode renomear qualquer osso. Uma reconstrução o encontra novamente e não cria duplicatas.

Com Show Helpers ativado, cada articulação e vínculo tem uma nota **How this works**. Ela lista as restrições por nome, explica o que cada uma faz e tem um botão **Select** (ícone de seta) para inspecionar o osso.

Suas próprias restrições, drivers e ossos nunca são alterados. Uma restrição adicionada por você a um osso MCH permanece abaixo das restrições do BoneCraft após uma reconstrução.

## Edição e alterações manuais {#editing-and-hand-edits}

- **Edições de valores** (limites, proporção, intervalos, temporização, suavização, aparência do controle) atualizam as restrições existentes no lugar. Não há reconstrução.
- **Edições estruturais** (**Kind** de Gear Link, **Curve** de Follow, **Stretch** de Piston) substituem as restrições desse mecanismo e reconstroem somente esse mecanismo.
- **Changed by hand.** Após editar uma restrição do BoneCraft, como um limite, a mensagem do mecanismo termina com “(changed by hand)”. O BoneCraft nunca sobrescreve a edição silenciosamente. Selecione uma opção:
    - **Keep mine** copia seus valores para o registro. Recusa aquilo que não consegue ler de volta. Sua mensagem orienta usar Restore ou Detach.
    - **Restore** descarta sua edição e reconstrói a partir do registro.
- Um mecanismo retido por edição manual também retém todos os mecanismos que usam seus ossos, até você resolver a situação.
- A mesma proteção se aplica a uma curva remodelada. Com **Curve** ativado, você pode remodelar a curva de Follow no Editor gráfico. Uma alteração posterior, como Target Range, substituiria a curva. Essa alteração faz a mensagem de Follow terminar com “(changed by hand)”. **Keep mine** mantém sua curva. **Restore** a regenera.
- Uma Sequence retida mostra sua mensagem e **Restore** em **3. Sequences**, com **Detach** e **Delete** ao lado. Keep mine não é oferecido para Sequences.
- **Detach** (botão de corrente quebrada) exclui o registro e os identificadores, mas mantém os ossos e as restrições como seu próprio rig feito à mão. Detach e Delete recusam um registro usado por outro registro e informam seus usuários.
- **Delete** (botão X) remove o registro e tudo o que o BoneCraft construiu para ele.
- Um ciclo de vínculos é recusado antes que qualquer coisa seja construída, e o ciclo é informado, por exemplo: “Blade Hinge → Cover Follow → Blade Hinge would loop.”

Rig Validator e Task Board informam:

- Ciclos de vínculos.
- Peças ausentes.
- Ossos DEF movidos de fora do seu mecanismo.
- Drivers que precisam de Python.
- Gear Links que perdem uma Sequence ou Follow.

A verificação de nomes do validador aceita hífens (`CTRL-`, `MCH-`, `DEF-`). Sua verificação de drivers avisa somente sobre expressões que precisam de Python. Um rig de Mechanisms sem problemas não mostra erros de validação. Mostra apenas o aviso do osso `root`, descrito em Limites desta versão.

## Show Helpers {#show-helpers}

**Show Helpers** é uma preferência para todo o BoneCraft: **Preferences → Add-ons → BoneCraft → Helpers**. Desativá-la oculta os textos de orientação em todos os locais: linhas de o que faz / quando usar, notas **How this works** e frases completas das etapas guiadas (que viram rótulos curtos). As próprias etapas, as listas, Test, os avisos e as dicas do Blender ao passar o ponteiro sempre permanecem.

O botão **Compact Mode** do VRChat é seu atalho: Compact Mode ativado significa Show Helpers desativado.

## Limites desta versão {#limits-of-this-version}

- Os mecanismos Click Turn, Track e Linkage virão depois.
- A exportação de movimento de mecanismos consolidado para engines virá depois da verificação manual no desktop. Até lá, os ossos `DEF-` são os ossos a exportar.
- O BoneCraft não detecta colisões. Para verificar colisões:
    1. Use Test.
    2. Observe as peças.
- Gear Link de rotação livre acompanha somente controles e engrenagens.
- O osso `root` do rig não pertence a nenhuma coleção de ossos; por isso, a verificação de coleções do Rig Validator avisa sobre ele e Task Board mostra “Rig validation warnings (1)”.

Próximo: [Ferramentas do VRChat](08-vrchat.md)
