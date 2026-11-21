<a id="ghost-tool-433-user-guide"></a>

# Guia do usuário do Ghost Tool 4.3.3

O Ghost Tool mostra malhas fantasma, trajetórias e marcadores de movimento editáveis no Bforartists. As malhas fantasma, também chamadas de casca de cebola, mostram o alvo em outros momentos da animação. As trajetórias mostram seu movimento. Os marcadores de movimento são pontos editáveis nessas trajetórias. Este guia descreve a versão 4.3.3.

As capturas de tela mostram o Ghost Tool 4.3.3 na compilação fornecida do Bforartists 5.2.3. Os painéis de configurações nativos podem mostrar Tear Off Panel na barra de título.

A versão 4.3.2 adicionou o recolhimento na Linha do tempo e um espaço entre os dois ícones de fantasma. A versão 4.3.3 pode gerar prévias enquanto o ponteiro da Linha do tempo do Anim Assist está ocioso. As operações de edição em andamento ainda pausam a amostragem.

O [ZIP de instalação do Ghost Tool 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/ghost-v4.3.3/b4_ghost_tool_v4.3.3.zip) instala o complemento independente. As [notas da versão 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/RELEASE-NOTES.md) e o [registro do pacote](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/package-receipt.json) contêm as evidências da versão e a soma de verificação.

<a id="install-and-find-ghost-tool"></a>

## Instalar e localizar o Ghost Tool

A compilação de teste personalizada/nativa fornecida inclui o Ghost Tool 4.3.3. Suas preferências de fábrica ativam o complemento. Essa compilação dispensa a instalação separada do ZIP e a ativação manual. Os locais da barra de ferramentas, prateleira de ferramentas, painel lateral e Preferências descritos abaixo também se aplicam a ela.

Para instalar o complemento independente:

1. Baixe `b4_ghost_tool_v4.3.3.zip`.

2. Abra Editar > Preferências > Complementos > Install from Disk.

3. Selecione o ZIP.

4. Ative o Ghost Tool.

5. Após substituir uma versão instalada, reinicie o Bforartists.

6. Confira se Preferências informa a versão 4.3.3.

As mudanças no repositório não atualizam automaticamente um complemento instalado. Um ZIP antigo instala sua versão original.

Estas instruções instalam o complemento independente. A versão integrada proposta depende do PR [7067](https://github.com/Bforartists/Bforartists/pull/7067) do Bforartists. Esse PR continuava sem mesclagem em 2026-11-19. As compilações oficiais já lançadas do Bforartists ainda não incluem essa integração proposta.

Por padrão, o Ghost Tool usa Barra superior na linha nativa de Configurações de ferramentas da Janela de Exibição 3D. Quando os cabeçalhos nativos estão no topo, essa linha fica abaixo do cabeçalho principal da janela. A linha acompanha o alinhamento dos cabeçalhos nativos.

O painel Preferências também oferece Painel lateral direito (N) e Prateleira de ferramentas esquerda (T). O Ghost Tool converte antigas escolhas salvas de Top Header para Barra superior.

![Preferências do Ghost Tool 4.3.3](images/pt/4.3.3-preferences.png)

*Figura 1. A compilação fornecida ativa o Ghost Tool 4.3.3. Local dos controles mostra Barra superior.*

Os controles nativos de ferramentas e modos continuam disponíveis. Janelas estreitas ou divididas mantêm todos os controles da barra Ghost na mesma ordem.

1. Arraste a linha nativa horizontalmente com o botão do meio do mouse para alcançar os controles fora da largura visível.

2. Se os controles Ghost estiverem ocultos, selecione Visualizar > Mostrar barra de fantasmas.

3. Salve as preferências para manter as escolhas de exibição.

<a id="set-the-interface-language"></a>

## Definir o idioma da interface

A versão candidata à localização do Ghost Tool oferece inglês, japonês, coreano, chinês simplificado, português, espanhol e francês. Estas instruções de idioma se aplicam a essa versão candidata.
Os controles de idioma do Bforartists exigem uma compilação com suporte a tradução.

1. Abra Editar > Preferências > Interface.

2. Em Linguagem, selecione o idioma necessário.

3. Para um idioma diferente do inglês, ative Interface, Dicas e Reports em Translate.

4. Abra as preferências do complemento Ghost Tool.

5. Defina Idioma como Idioma da interface.

Idioma da interface faz os textos próprios do Ghost Tool seguirem o idioma da interface do aplicativo.
Desativar Interface devolve os textos próprios com escolha automática de idioma ao inglês.
Escolher explicitamente um idioma do Ghost Tool muda seus textos próprios. Os controles e as dicas nativos ainda usam o idioma do aplicativo.
Use configurações de idioma correspondentes para toda a interface.
Os nomes existentes de objetos e ossos e os identificadores de dados salvos mantêm o texto original.

<a id="quick-start-inspect-an-animated-target"></a>

## Início rápido: inspecionar um alvo animado

1. Selecione um objeto animado ou um osso em pose.

2. Ative o primeiro ícone de fantasma.

3. Clique em Fantasmas para mostrar as prévias de malha.

4. Defina Antes e Depois separadamente.

5. Selecione Aramado ou Sólido para a aparência da malha.

6. Mantenha Fantasmas pressionado para ajustar a amostragem e a aparência.

7. Clique em Trajetórias para mostrar uma trajetória.

8. Clique em Adicionar trajetória selecionada para manter outro alvo selecionado.

9. Ative Exibição dos marcadores para mostrar pontos editáveis em uma trajetória adicionada.

10. Clique em Arrastar.

11. Selecione um marcador na Janela de Exibição 3D.

12. Mova o marcador.

13. Confirme o movimento.

14. Selecione outro marcador para continuar a edição.

15. Para sair do modo de arrastar marcadores, clique novamente em Arrastar ou pressione Escape.

![Cubo animado com prévias de malhas fantasma](images/pt/4.3.3-overview.png)

*Figura 2. As malhas fantasma em cache cercam o cubo animado. O primeiro ícone de fantasma ativa o Ghost Tool.*

Quando não há um alvo de trajetória, Trajetórias pode adicionar o alvo animado selecionado. Seguir seleção mostra a seleção atual. Os alvos adicionados com Adicionar trajetória selecionada permanecem na lista de trajetórias.

<a id="read-the-top-toolbar-from-left-to-right"></a>

## Ler a barra superior da esquerda para a direita

![Barra superior completa do Ghost Tool](images/pt/4.3.3-toolbar-wide.png)

*Figura 3. A barra superior mantém a ordem de controles abaixo, do ícone geral de fantasma até Configurações.*

| Controle | Ação |
| --- | --- |
| Ghost Tool | Ativa ou desativa a ferramenta inteira. Mantenha pressionado para abrir as configurações de atualização. |
| Fantasmas | Mostra ou oculta malhas fantasma. Mantenha pressionado para ajustar a amostragem e a aparência. |
| Antes / Depois ao lado de Fantasmas | Define quantidades independentes de amostras de malha. Cada número tem botões de menos e mais. |
| Aramado / Sólido | Seleciona o estilo de exibição da malha. |
| Trajetórias | Mostra ou oculta trajetórias. Mantenha pressionado para ajustar a amostragem e as linhas. |
| Antes / Depois ao lado de Trajetórias | Define quantidades independentes de amostras de trajetória. Cada número tem botões de menos e mais. |
| Adicionar trajetória selecionada | Mantém o alvo selecionado na lista de trajetórias. |
| Seguir seleção | Mostra uma trajetória da seleção atual. Mantenha pressionado para abrir Destacar trajetória ativa. |
| Arrastar | Ativa o modo de arrastar marcadores para edições repetidas. Mantenha pressionado para abrir as configurações de edição de movimento. |
| Fixar | Seleciona um marcador para fixar ou soltar. Mantenha pressionado para abrir Soltar todos os marcadores. |
| Exibição dos marcadores | Mostra ou oculta marcadores de trajetória editáveis. Mantenha pressionado para ajustar a amostragem e os rótulos. |
| Estilo do arco | Abre as opções Sólido, Cor por velocidade e Esmaecer. |
| Marcas de espaçamento | Mostra ou oculta indicadores de espaçamento. Mantenha pressionado para abrir Indicadores de aceleração. |
| Configurações | Abre os controles avançados. |

O primeiro ícone de fantasma controla a ferramenta inteira. Fantasmas controla separadamente a visibilidade das malhas. Desativar a ferramenta inteira também desativa a edição de marcadores e alças.

As malhas ocultas mantêm o estilo selecionado. Aramado ou Sólido seleciona um estilo. Fantasmas controla se as malhas ficam visíveis.

Exibição dos marcadores é o losango imediatamente à direita de Fixar. Os rótulos aparecem quando o ponteiro está sobre um controle.

Estilo do arco controla o arco de movimento dos fantasmas. Aramado/Sólido controla a exibição das malhas. Estilo da linha em Trajetórias controla a exibição das trajetórias.

O painel Configurações inclui geração de marcadores, alvos, intervalo, edição, Comparar, Física e opções de aparência. Gerar e Limpar não têm ícones adicionais na linha superior.

<a id="set-before-and-ahead-counts"></a>

## Definir as quantidades de Antes e Depois

Cada exibição tem duas quantidades independentes. Antes solicita amostras anteriores ao indicador de tempo. Depois solicita amostras posteriores ao indicador de tempo.

1. Defina a quantidade no campo numérico ou nos botões de menos e mais da barra superior.

2. Defina uma quantidade como zero para desativar as amostras daquele lado.

O painel Opções de casca de cebola usa After para a quantidade Ahead da barra. Em português, ambos aparecem como Depois.

![Opções de casca de cebola para quantidades de malha e amostragem](images/pt/4.3.3-skin-options.png)

*Figura 4. O painel Opções de casca de cebola mostra quantidades de amostras de malha, amostragem, opacidade e Atualizar casca em tempo real.*

As quantidades especificam quantas amostras solicitar. A amostragem especifica suas posições.

Neste exemplo:

1. Defina o indicador de tempo no quadro 20.

2. Defina Antes de Fantasmas como 3.

3. Defina Depois como 2.

4. Defina o passo de quadros como 2.

As amostras anteriores solicitam os quadros 18, 16 e 14. As posteriores solicitam os quadros 22 e 24. A animação disponível e os limites do intervalo podem restringir essas solicitações. A pose atual não é uma amostra de Antes ou Depois.

Por quadro-chave usa chaves de animação em vez de quadros com espaçamento uniforme. Seu intervalo pode pular chaves. Alterar os campos de quantidade de Trajetórias seleciona uma janela ao redor do indicador de tempo com base nessas quantidades. Os modos avançados de intervalo seguem suas próprias regras.

<a id="hold-a-tool-for-its-settings"></a>

## Manter um controle pressionado para abrir suas configurações

Um botão compatível tem duas ações:

1. Para a ação principal, clique no botão.

2. Para o menu de parâmetros, mantenha o botão pressionado.

Estilo do arco e Configurações abrem com um clique comum.

| Controle a manter pressionado | Configurações disponíveis |
| --- | --- |
| Ghost Tool | Atualizar malhas ao percorrer quadros, Atualizar marcadores ao percorrer quadros, Pausar atualizações |
| Fantasmas | Amostragem, A cada (quadros), Intervalo entre quadros-chave, Opacidade, À frente, Esmaecer |
| Trajetórias | Amostragem e intervalo, Estilo da linha, Números dos quadros, Alças Bézier |
| Exibição dos marcadores | Amostragem compartilhada com Trajetórias, Pontos de quadro-chave, Números dos quadros dos marcadores |
| Arrastar | Ao soltar, Forma da curva ou Suavizar vizinhos, Alcance nos quadros próximos, Atenuação |
| Fixar | Instruções de fixação e Soltar todos os marcadores |
| Seguir seleção | Destacar trajetória ativa |
| Marcas de espaçamento | Indicadores de aceleração |

A amostragem por passo de quadros usa A cada (quadros). O valor 1 amostra todos os quadros. A amostragem por quadro-chave usa os controles de intervalo entre quadros-chave. Alguns controles oferecem intervalos personalizados.

Marcadores e Trajetórias compartilham a amostragem. Alterar a amostragem em Exibição dos marcadores também altera a amostragem de Trajetórias.

Configurações > Opções de casca de cebola abre os controles de malha da Figura 4. Configurações > Trajetórias abre os controles de alvos e alças da Figura 7.

<a id="use-the-bottom-timeline-toolbar"></a>

## Usar a barra inferior da Linha do tempo

A faixa compacta fica ao lado dos botões nativos da Linha do tempo, na mesma linha. Ela não adiciona uma linha abaixo da barra da Linha do tempo.

1. Ative o ícone de fantasma à esquerda para revelar os outros controles.

2. Desative esse ícone para recolher a faixa.

Com o Ghost Tool ativo, um espaço visível separa o ícone geral de ativação do ícone Fantasmas das malhas. Esses comportamentos começaram na versão 4.3.2.

![Faixa expandida do Ghost Tool na Linha do tempo](images/pt/4.3.3-timeline-enabled.png)

*Figura 5. A faixa ativa da Linha do tempo mostra quantidades de amostras de malha, estilos de exibição, edição de marcadores e controles de trajetórias.*

![Faixa recolhida do Ghost Tool na Linha do tempo](images/pt/4.3.3-timeline-collapsed.png)

*Figura 6. Com o Ghost Tool desativado, apenas seu ícone geral de fantasma permanece ao lado dos controles nativos da Linha do tempo.*

A faixa ativa tem esta ordem da esquerda para a direita:

1. Ativação geral do Ghost Tool.

2. Exibição de malhas em Fantasmas.

3. Quantidades de amostras de malha Antes e Depois.

4. Estilos de malha Aramado e Sólido.

5. Arrastar marcadores.

6. Losango dos marcadores editáveis.

7. Exibição de Trajetórias.

8. Quantidades de amostras de trajetória Antes e Depois.

Cada par de quantidades segue a mesma ordem temporal de Antes/Depois da barra superior. A Linha do tempo usa campos numéricos nativos compactos.

1. Para configurar a amostragem e a exibição, mantenha Fantasmas ou Trajetórias pressionado na Linha do tempo.

O menu inclui Quadro a quadro, Por quadro-chave e intervalos de amostragem. Mais configurações de fantasmas abre as opções completas.

O losango inferior mostra ou oculta marcadores editáveis. Seu menu separado, aberto por pressionamento prolongado, fica no botão Exibição dos marcadores da barra superior. Comparar contém controles de estados salvos nas configurações avançadas.

O cabeçalho do Editor gráfico também oferece a ativação geral e um segmento de trajetórias quando o Ghost Tool está ativo.

<a id="drag-markers-repeatedly"></a>

## Arrastar marcadores repetidamente

1. Ative o Ghost Tool.

2. Ative os marcadores editáveis de um alvo animado.

3. Clique em Arrastar.

4. Clique em um marcador visível na Janela de Exibição 3D.

5. Mova o marcador.

6. Confirme o movimento.

Se você clicar no espaço vazio, o seletor continua esperando. Após confirmar um movimento, Arrastar permanece ativo para outra edição. Todos os botões de arrastar marcadores compartilham esse modo.

Para parar:

1. Clique novamente em Arrastar ou pressione Escape.

Durante um movimento, Escape cancela esse movimento. O Ghost Tool restaura as curvas e posições originais dos marcadores daquela operação. Os movimentos confirmados antes permanecem como edições separadas.

1. Para reverter movimentos confirmados anteriormente, use Desfazer.

Desativar o Ghost Tool encerra a edição. Perda do alvo, mudança de arquivo, alteração do histórico ou encerramento do complemento também encerram ou cancelam as sessões afetadas.

O arraste de alças de trajetória também permite seleções repetidas.

![Controles de alvos e alças de Trajetórias](images/pt/4.3.3-path-targets.png)

*Figura 7. O painel Trajetórias mantém o cubo animado como alvo. Este exemplo ativa Marcadores e Alças.*

1. Ative Alças Bézier nas configurações de Trajetórias.

2. Inicie a ação de arrastar alças.

3. Selecione uma alça visível.

4. Mova a alça.

5. Confirme o movimento.

6. Selecione outra alça para continuar.

O acesso por Shift+G continua disponível. Durante o arraste de alças, Alt ativa ou desativa o comportamento de alinhamento das alças. Escape cancela um movimento de alça em andamento e sai do modo.

<a id="choose-smooth-or-sharp-motion-edits"></a>

## Escolher edições de movimento suaves ou angulosas

1. Mantenha Arrastar pressionado.

2. Examine Ao soltar.

3. Selecione Remodelar alças ou Inserir quadro-chave.

Remodelar alças altera as alças Bézier existentes para que a curva passe pela amostra movida. Não adiciona quadro-chave.

Forma da curva oferece três opções:

| Opção | Efeito |
| --- | --- |
| Livre | As alças se ajustam sem restrições de ângulo. |
| Bloqueado | Os ângulos das alças permanecem fixos. Os comprimentos das alças podem mudar. |
| Suave | A influência das alças se redistribui pelo segmento. |

Configurações > Editar movimento contém as mesmas opções de Ao soltar e Forma da curva do menu aberto ao manter Arrastar pressionado.

![Configurações de Remodelar alças em Editar movimento](images/pt/4.3.3-reshape-options.png)

*Figura 8. Editar movimento mostra Remodelar alças com tratamento Livre da curva. Alcance controla a influência nos quadros próximos.*

Inserir quadro-chave grava uma chave no quadro do marcador. Após a inserção, Suavizar vizinhos pode suavizar as alças das chaves adjacentes. Alcance nos quadros próximos e Atenuação controlam a influência nos quadros ao redor.

![Controles de quadros-chave e fixação em Editar movimento](images/pt/4.3.3-edit-motion.png)

*Figura 9. Editar movimento mostra Inserir quadro-chave, Suavizar vizinhos, suavização de movimento e controles de fixação. Desenhar chaves precisa de um traço de anotação.*

A distância entre amostras também afeta a linha visível. Amostras muito espaçadas produzem uma linha pouco detalhada mesmo quando a curva de animação é suave.

1. Para inspecionar o resultado, selecione um passo de quadros menor.

Amostras adicionais de exibição não mudam a interpolação da animação nem a forma das alças.

<a id="pin-markers-and-manage-path-targets"></a>

## Fixar marcadores e gerenciar alvos de trajetórias

1. Clique em Fixar.

2. Clique em um marcador visível para alternar seu estado de fixação.

3. Para selecionar outro marcador, clique novamente em Fixar.

Fixar seleciona um marcador por vez. Não permanece ativo como Arrastar. Vários marcadores podem permanecer fixados ao mesmo tempo.

Os marcadores fixados ficam imóveis durante a remodelagem. Uma atualização preserva os registros correspondentes de marcadores fixados.

Para soltar todos os marcadores fixados:

1. Mantenha Fixar pressionado.

2. Selecione Soltar todos os marcadores.

Um alvo de trajetória adicionado mantém um objeto ou osso na lista de trajetórias. Não mantém todas as amostras de animação no estado de um único momento. Seguir seleção muda a prévia da seleção. Os alvos adicionados com Adicionar trajetória selecionada permanecem na lista de trajetórias.

A lista de trajetórias em Configurações contém os controles de alvos. Exibição dos marcadores mostra pontos editáveis nas trajetórias adicionadas. A opção Pontos de quadro-chave oferece uma ajuda de exibição separada.

A Figura 7 mostra a lista de trajetórias. A Figura 9 mostra Fixar e a opção de soltar todos em Editar movimento.

<a id="live-updates-and-native-animation-editing"></a>

## Atualizações em tempo real e edição nativa de animação

Atualizar marcadores em tempo real e Atualizar casca em tempo real começam desativados. As cenas existentes mantêm seus valores salvos. Com essas opções desativadas, a última prévia atualizada permanece enquanto você percorre os quadros.

1. Para abrir Atualizar marcadores ao percorrer quadros e Atualizar malhas ao percorrer quadros, mantenha o ícone geral de fantasma pressionado.

Esses controles usam as mesmas configurações de atualização de marcadores e malhas. Pausar atualizações interrompe temporariamente as atualizações automáticas.

Configurações > Opções de marcadores contém os mesmos controles de atualização de marcadores. A Figura 4 mostra Atualizar casca em tempo real em Opções de casca de cebola.

![Opções de marcadores com controles de atualização em tempo real](images/pt/4.3.3-marker-options.png)

*Figura 10. O painel Opções de marcadores contém Atualizar marcadores em tempo real, Pausar atualizações e o atraso de atualização.*

Durante operações nativas de movimento, rotação, escala e manipuladores, o Ghost Tool mantém a última prévia. Ele não percorre os quadros da animação durante essas operações. Após a confirmação ou o cancelamento, espera a edição se estabilizar. Depois atualiza os fantasmas existentes.

Inserção de chaves automática pode permanecer ativa. Sem inserção automática:

1. Confirme a pose.

2. Insira a chave desejada.

Gerar nos controles avançados de marcadores regenera as prévias quando solicitado.

Na versão 4.3.3, o Ghost Tool pode gerar marcadores e cascas de cebola com o ponteiro do Anim Assist ocioso na Linha do tempo. Essa exceção se aplica apenas a esse tratador passivo de ponteiro.

Controles deslizantes ativos do Anim Assist, transformações, manipuladores, percurso de quadros e operações modais desconhecidas ainda pausam a amostragem.

1. Antes de gerar novamente, termine a operação em andamento.

A correção não muda os padrões de atualização das prévias nem o comportamento da animação de origem.

Os controles avançados ainda contêm Alvos dos marcadores, fontes de casca de cebola, intervalo, subdivisão e configurações de aparência. Os controles de visibilidade dos marcadores e da casca em cache ocultam ou mostram as prévias existentes sem reconstruí-las.

Limpar todos os fantasmas remove marcadores e cascas de cebola.

1. Para ocultar prévias sem removê-las, use os controles de visibilidade.

Você não pode selecionar marcadores ocultos por clique ou seleção por caixa.

<a id="save-compare-and-restore-snapshots"></a>

## Salvar, comparar e restaurar estados

1. Abra Configurações.

2. Abra Comparar.

3. Selecione o Escopo desejado.

4. Confirme o alvo de captura exibido.

5. Ative os marcadores do alvo selecionado.

6. Clique em Salvar estado.

![Comparar com um estado salvo da referência Motion](images/pt/4.3.3-compare.png)

*Figura 11. Comparar contém o estado salvo da referência Motion e seus controles Ocultar, Restaurar, Salvar variante e Excluir.*

Escopo oferece Objeto ativo / Ossos selecionados, Trajetória selecionada, Canais dos marcadores selecionados e Todos os marcadores da cena.

Os estados salvos mantêm as amostras no estado capturado, além dos quadros-chave e alças capturados. Os estados permanecem na cena após salvar e reabrir. Desativar e reativar o complemento também os preserva.

Ocultar ou Mostrar altera a sobreposição do estado salvo sem mudar a animação. Salvar variante cria um estado alternativo independente e registra sua origem. O alternativo permanece se você excluir o estado pai.

A cena pode manter dez estados salvos.

1. Ao atingir o limite, exclua os registros desnecessários antes de salvar outro estado.

Captura, variantes, vínculo, visibilidade, exclusão e restauração permitem usar Desfazer e Refazer nativos.

Antes de gravar, Restaurar valida a identidade da cena, objeto, Ação, Espaço de Ação, osso e canal. Restaura curvas capturadas e registros de marcadores do escopo do estado salvo. Também atualiza a exibição quando as atualizações em tempo real estão desativadas ou pausadas.

Restaurar não muda objetos sem relação nem modificadores arbitrários de Ação. Referências antigas que contêm apenas amostras restauram valores amostrados adequados quando o Ghost Tool consegue remodelar as curvas.

Alvos substituídos exigem um vínculo explícito. O vínculo associa uma referência ao alvo. Espaços de Ação compartilhados impedem o vínculo.

1. Antes de vincular, use Tornar usuário único para tornar os dados de animação independentes.

Vincular ao alvo ativo aceita, por referência, um objeto original e seus canais de ossos identificados por nome. Referências importadas com vários objetos continuam visíveis e sem vínculo. O Ghost Tool não pode vincular esses objetos a um único alvo.

Os vínculos acompanham mudanças de nome dos ossos. Após salvar e reabrir, a identidade do canal identifica a curva. A reversão restaura os valores originais da curva após o cancelamento. Durante uma operação, o Ghost Tool não grava valores de reversão das curvas originais nas curvas substitutas.

<a id="transfer-snapshots-and-use-advanced-tools"></a>

## Transferir estados e usar ferramentas avançadas

1. Para transferir dados de comparação, exporte os estados salvos para JSON.

Importar valida e mescla registros. Se os IDs coincidirem com registros existentes, Importar atribui novos IDs. Ele rejeita versões não compatíveis ou registros que ultrapassem o limite. Uma importação rejeitada não adiciona registros parciais.

As referências importadas e antigas continuam visíveis. A restauração exige um vínculo explícito porque JSON não comprova a identidade do objeto original. Uma importação malsucedida preserva os registros existentes da cena que não podem ser lidos.

![Configurações de exportação e importação JSON do Ghost Tool](images/pt/4.3.3-transfer-settings.png)

*Figura 12. O painel Configurações contém Exportar e Importar para dados JSON do Ghost Tool.*

Editar movimento contém predefinições e controles personalizados de suavização de movimento. Essa suavização controla como a velocidade do movimento muda. Desenhar chaves converte o traço de anotação mais longo em uma trajetória de posição. Traços curtos que o cruzam identificam as chaves. O diálogo Desenhar chaves mantém o alvo selecionado.

Configurações, o painel lateral e a prateleira contêm Sensação física, Aparência, Comparar e outras ferramentas avançadas.

A Figura 9 mostra a suavização de movimento e Desenhar chaves em Editar movimento.

![Controles de prévia física e gravação](images/pt/4.3.3-physics.png)

*Figura 13. Física mostra prévias de trajetórias de lançamento e controles de Sensação física. Gravar nas chaves grava a prévia nas chaves de animação.*

![Controles de Aparência para cores de marcadores e exibição de trajetórias](images/pt/4.3.3-look.png)

*Figura 14. Aparência controla as cores dos marcadores, Linhas de arco, Marcas de espaçamento e rótulos de quadros.*

<a id="troubleshooting-and-version-evidence"></a>

## Solução de problemas e evidências de versão

| Problema | Verificação ou ação |
| --- | --- |
| Nenhuma prévia aparece | Ative o Ghost Tool. Confira a animação do alvo, a visibilidade e as quantidades diferentes de zero. |
| Faltam pontos editáveis | Adicione o alvo a Trajetórias. Ative Exibição dos marcadores. |
| As amostras parecem muito espaçadas | Reduza o passo de quadros ou altere o intervalo entre quadros-chave. |
| A Linha do tempo mostra apenas um ícone de fantasma | Ative esse ícone para expandir a faixa. |
| A barra está oculta | Selecione Barra superior nas preferências. Selecione Visualizar > Mostrar barra de fantasmas. |
| Os controles ultrapassam uma janela dividida | Arraste a linha nativa horizontalmente com o botão do meio do mouse. |
| A amostragem espera durante a edição | Confirme ou cancele a operação de edição em andamento. |
| A geração continua bloqueada com o Anim Assist ocioso | Instale o Ghost Tool 4.3.3. Reinicie o Bforartists. |

A Figura 1 mostra as preferências do Ghost Tool. As Figuras 5 e 6 mostram a faixa da Linha do tempo expandida e recolhida.

A amostragem dos marcadores segue a amostragem de Trajetórias. As preferências de largura da prateleira esquerda continuam disponíveis. A verificação completa de largura e escala estava incompleta na versão 4.2.11. Este guia não afirma uma nova correção de largura da prateleira.

A implementação anterior da barra direta passou por 188 verificações direcionadas em segundo plano. Esses resultados se aplicam àquela implementação. Eles não vêm de novos testes para este manual.

As [notas da versão 4.3.3](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/RELEASE-NOTES.md) registram verificações direcionadas de regressão e interface gráfica no Bforartists 5.2.3 oficial. A verificação gráfica usou o Anim Assist 12.11.0 e recursos de usuário isolados. Ela verificou nove marcadores e três prévias de malha. As chaves de origem e o indicador de tempo permaneceram inalterados.

Essas evidências não certificam todos os operadores, rigs de produção ou futuros aplicativos hospedeiros. O [registro do pacote](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/package-receipt.json) registra a integridade do ZIP, a versão e a correspondência com o código-fonte.

1. Informe o alvo, a operação e a etapa que falhou no [rastreador de problemas](https://github.com/Axleonex/B4Artists_Toolkit/issues).
