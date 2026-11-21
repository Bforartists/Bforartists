<a id="anim-assist-12112-candidate-user-guide"></a>

# Guia do usuário da versão candidata Anim Assist 12.11.2

Este guia apresenta a versão candidata local e ainda não publicada do Anim Assist 12.11.2. Ela inclui a correção da configuração da faixa de áudio na revisão `7ec664d`. Os downloads publicados continuam na versão 12.11.1. A revisão de 20 de novembro de 2026 abrangeu o código-fonte e a documentação.

Consulte o [registro de alterações atual](../../../../../../scripts/addons_core/B4_anim_assist/CHANGELOG.md) e o [índice da documentação](../README.md) para obter informações sobre as versões.

Cada captura de tela aparece junto das instruções correspondentes. Cada legenda informa a versão capturada ou a data registrada da verificação. As capturas antigas identificam os controles. Elas não registram novos testes de aceitação.

O manual de origem em inglês usa principalmente figuras de painéis da versão 12.11.1, capturadas na compilação fornecida do Bforartists 5.2.3, baseada no Blender 5.4 Alpha, além de uma figura de sincronização labial da versão candidata 12.11.2, capturada no Bforartists oficial 5.2.3, baseado no Blender 5.3 Alpha. Esta edição localizada usa novas capturas nativas da versão candidata local e ainda não publicada 12.11.2; suas legendas informam o contexto de captura e os limites do que foi verificado. Os painéis nativos em janelas flutuantes mostram os controles registrados com clareza. Para usar uma ferramenta, abra o editor correspondente, conforme descrito abaixo.

Use a Tabela de animação para poses e temporização. Use o Editor gráfico para curvas de Ações ou drivers. Use o NLA Editor para clipes e correções. Os controles de ajuda explicam cada ferramenta. Os nomes dos controles neste guia seguem o catálogo em português e os termos nativos verificados. Rótulos sem tradução disponível permanecem em inglês.

<a id="install-and-find-the-tools"></a>

## Instalar e encontrar as ferramentas

<a id="install-the-standalone-add-on"></a>

### Instalar o complemento independente

1. Baixe o [ZIP publicado do complemento 12.11.1](https://raw.githubusercontent.com/Axleonex/B4Artists_Toolkit/main/releases/b4_anim_assist_v12.11.1.zip).

2. No Bforartists, abra **Editar > Preferências > Complementos > Install from Disk**.

3. Selecione o ZIP.

4. Ative o **Anim Assist**.

5. Após a atualização, reinicie o Bforartists.

O pacote independente é `B4_anim_assist`. Durante a instalação, mantenha o ZIP intacto.

A figura a seguir mostra a entrada incluída na compilação fornecida. Para instalar uma cópia independente, siga as etapas de instalação do ZIP acima.

![Preferências do Anim Assist: a entrada está ativada, o idioma Português está selecionado e as opções gerais de ajuda ao passar o ponteiro estão visíveis. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): a764d05d403b.](images/pt/12.11.1-preferences.png)

<a id="use-a-proposed-built-in-integration"></a>

### Usar a integração interna proposta

A compilação personalizada de teste nativo fornecida inclui o Anim Assist. Suas preferências de fábrica ativam o complemento. Essa integração proposta dispensa uma instalação separada por ZIP. Esta descrição não comprova que as versões oficiais do Bforartists incluam o Anim Assist.

1. Inicie a compilação personalizada fornecida.

2. Abra os caminhos dos editores indicados abaixo.

3. Abra **Editar > Preferências > Complementos > Anim Assist** para acessar suas preferências.

Não instale uma segunda cópia independente por cima da integração incluída.

A figura de preferências acima mostra a entrada incluída. As figuras **Área da cena** e **Configuração inicial** abaixo mostram onde ficam os controles de configuração.

<a id="find-the-editor-homes"></a>

### Encontrar as ferramentas nos editores

A verificação anterior em execução usou o Bforartists padrão 5.2.0, baseado no Blender 5.3.0 Alpha, compilação `0a1ca45552db`, com OpenGL. Essas evidências históricas se aplicam àquele aplicativo. O Blender padrão não é compatível. Esses resultados não validam todas as outras compilações do aplicativo.

- **Linha do tempo:** a linha de ferramentas do Anim Assist aparece na parte inferior da área de edição. Veja **Linha do tempo: a linha inferior de ferramentas** abaixo. Os controles de reprodução e de inserção de chaves permanecem no cabeçalho nativo.
- **Tabela de animação, Editor gráfico e NLA Editor:** a barra lateral contém uma aba **Anim Assist**. Sua posição em relação às abas nativas pode variar. O menu **Anim Assist** no cabeçalho também dá acesso às ferramentas.
- **Controladores:** a aba **Anim Assist** da barra lateral e o menu do cabeçalho se adaptam ao trabalho com drivers no modo **Controladores** do Editor gráfico.
- **Scene Properties > Anim Assist:** esta área contém a configuração do personagem, ferramentas gerais de animação, macros, configurações e ajuda. A barra lateral da Janela de Exibição 3D não tem uma aba Anim Assist.

Para abrir as ferramentas da barra lateral:

1. Mova o ponteiro para a Tabela de animação, o Editor gráfico ou o NLA Editor.

2. Pressione N.

3. Selecione a aba **Anim Assist**.

Para trabalhar com drivers, mude o Editor gráfico para o modo **Controladores**.

**Scene Properties > Anim Assist > Configuração (uma vez por rig) > Executar configuração da primeira execução** cria a Prateleira rápida geral. A configuração também oferece uma área de trabalho. O menu radial opcional **Shift Alt D** começa desativado. Para ativá-lo ou alterar seu atalho, use **Configurações**.

![Área de ferramentas da cena em janela flutuante nativa. A Prateleira rápida, os menus radiais e os grupos de ferramentas aparecem juntos. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 5e98b33bf004.](images/pt/12.11.1-scene-home.png)

![Configuração inicial em janela flutuante nativa. O painel inteiro reúne configuração de primeira execução, área de trabalho, associação do rig e acesso à sincronização labial. Os estados desativados e os identificadores técnicos Left/Right e IK/FK são preservados. Nenhum comando de configuração foi executado nesta captura. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 3ea2f1bedbc1.](images/pt/12.11.1-scene-setup.png)

<a id="timeline-the-bottom-tool-row"></a>

## Linha do tempo: a linha inferior de ferramentas

A linha de ferramentas aparece na parte inferior da Linha do tempo, acima da barra de rolagem horizontal nativa. Ela não acrescenta um cabeçalho, uma região nem uma divisão da área de trabalho. Os controles de reprodução e de inserção de chaves permanecem no cabeçalho nativo. Para mostrar ou ocultar a linha, use **Linha do tempo > Visualizar > Mostrar linha de ferramentas do Anim Assist**.

Os botões mantêm a altura completa e áreas de clique correspondentes. O redimensionamento reserva espaço acima da barra de rolagem. Se você soltar o divisor abaixo da altura mínima, a Linha do tempo recupera a altura necessária para a linha. A barra de ferramentas processa os cliques na linha antes dos controles nativos do cursor de reprodução e de seleção de chaves. Deixe altura suficiente acima da linha para inspecionar as chaves.

Da esquerda para a direita, a linha contém:

| Controle | Função |
|---|---|
| **Botão de etapa** (por exemplo, **Todos**, com uma pequena seta) | Mostra a etapa atual e abre a lista de etapas. |
| **Botões de famílias** (Interpolação de poses, Tempo, Curvas, Chaves, Pose, Consolidar, Movimento) | Os nomes coloridos abrem a lista completa de ferramentas de cada família. As ferramentas da linha aparecem depois do nome de cada família. |
| **Ferramentas** | Botões, ícones e controles deslizantes executam ferramentas. O texto ao passar o ponteiro explica cada ferramenta. |
| **+N** | Abre a lista das N ferramentas que não cabem na linha. |
| **Buscar** (lupa) | Pesquisa ou lista todas as 96 ferramentas. Cada resultado tem controles para executar ou fixar a ferramenta. |
| **Configurações** | Abre as Configurações da barra de ferramentas para configurar cada linha. |

1. Clique em um botão de etapa, em um botão de família ou em **+N** para abrir sua lista.

2. Clique em um item para usá-lo.

A lista permanece aberta enquanto o ponteiro se move, inclusive sobre outro editor. Clicar no botão de outra família muda a lista para essa família.

Para fechar a lista, clique novamente no mesmo botão, clique em outro lugar ou pressione **Esc**.

![Linha inferior da Linha do tempo na etapa Todos. A etapa, as famílias, as ferramentas, Buscar e Configurações compartilham a mesma linha. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 84c91c003b74.](images/pt/stage-all.png)

<a id="tool-families"></a>

### Famílias de ferramentas

Cada família agrupa comandos por função. O texto de ajuda de cada ferramenta informa seu escopo e seus requisitos.

| Família | Trabalho disponível |
|---|---|
| **Interpolação de poses** | Percentuais e arraste de poses intermediárias, criação de intermediárias, distribuição e aproximação ou afastamento das poses vizinhas. |
| **Tempo** | Deslocamento por quadros, predefinições de espaçamento, controles deslizantes de tempo, deslocamento em cascata, inserção/remoção de tempo, distribuição, inversão e arredondamento. |
| **Curvas** | Interpolação spline/em degraus, mesclagem com vizinhos/referência/suavização de entrada e saída, amplificação, suavização, tipos de alças e marcadores de referência. |
| **Chaves** | Seleção de chaves visíveis, intervalos e extremidades, expansão da seleção, tipos de chaves, seleção de poses intermediárias, Copiar e Colar. |
| **Pose** | Espelhamento, seleção oposta, troca, alinhamento, correspondência no espaço global/do pai/do alvo e troca configurada de propriedades do rig. |
| **Consolidar** | Consolidação de objetos e do intervalo de prévia, Consolidar de forma inteligente, redução, temporização em quadros inteiros, criação de proxies, consolidação de sessão e limpeza. |
| **Movimento** | Trajetórias no espaço global, atualização, diagnóstico de arcos, deslocamento da Ação ativa e sua máscara de intervalo. |

![Comandos da família Pose, parte superior do menu vertical. Este detalhe mostra as operações de espelhamento, seleção do oposto, troca de poses e correspondência à origem global. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 3417434d90ad.](images/pt/12.10.0-pose-family-left.png)

![Comandos da família Pose, parte inferior do mesmo menu vertical. O comando de correspondência à origem global aparece nos dois detalhes como referência de sobreposição; abaixo ficam os demais comandos de correspondência, troca do rig, Opções de Pose e Abrir painel do Anim Assist. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): bb3bd3aee1b9.](images/pt/12.10.0-pose-family-right.png)

<a id="choose-a-stage"></a>

### Escolher uma etapa

Uma etapa contém ferramentas para uma fase da animação:

- **Todos:** uma visão geral com ferramentas de todas as famílias.
- **Blocagem:** ferramentas de Interpolação de poses e Chaves para blocar poses.

- **Spline:** ferramentas de Curvas e Movimento para trabalhar com splines e verificar arcos.

- **Refinamento:** ferramentas de Tempo e Pose para espaçamento e simetria.

- **Entrega:** ferramentas da família Consolidar para finalização e exportação.

Para mudar de etapa:

1. Clique no botão de etapa à esquerda da linha.

2. Clique em uma etapa na lista acima dele.

A lista se fecha quando você seleciona uma etapa. Se a Linha do tempo estiver baixa, as cinco opções aparecem em uma única linha dentro da área de edição disponível.

Como alternativa, selecione uma etapa em **Linha do tempo > Visualizar > Etapa do Anim Assist**.

Para percorrer as etapas com a roda do mouse:

1. Mantenha **Ctrl** pressionado sobre o botão de etapa.

2. Gire a roda.

Cada área de trabalho mantém sua própria etapa no arquivo salvo.

![Seletor de etapas acima da barra de ferramentas. O menu mostra Todos, Blocagem, Spline, Refinamento e Entrega; Todos está selecionado. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 9d055659f067.](images/pt/12.10.0-stage-choices.png)

<a id="use-the-tools"></a>

### Usar as ferramentas

Botões e ícones executam uma ferramenta quando você clica neles. Os ícones de tipos de chave usam as cores de chaves da Tabela de animação definidas no seu tema. Os losangos de poses intermediárias são menores. Os losangos de extremos são maiores. Os ícones de alças usam as cores de alças do Editor gráfico.

1. Passe o ponteiro sobre um ícone para ler seu nome.

2. Se uma ferramenta estiver esmaecida, passe o ponteiro sobre ela para ler seu requisito, como chaves selecionadas.

3. Clique em um botão ou ícone disponível para executar sua ferramenta.

Os **controles deslizantes em linha** permanecem na linha. Um clique sem arraste não altera nada.

1. Arraste a faixa do controle para visualizar uma alteração.

2. Solte o botão do mouse para aplicar a alteração.

Durante um arraste, pressione **Esc** ou clique com o botão direito para cancelar. O cancelamento restaura as chaves originais.

- Para um movimento mais preciso, mantenha **Shift** pressionado durante o arraste.
- Para ajustar o movimento ao incremento da ferramenta, mantenha **Ctrl** pressionado durante o arraste.

Para definir um valor exato durante um arraste:

1. Digite o número.

2. Pressione **Enter** para aplicá-lo.

As **marcas** são predefinições na faixa de um controle deslizante. O arraste se ajusta às marcas próximas. Para aplicar o valor exato de uma predefinição, clique em sua marca.

O número à direita de um controle deslizante em linha abre um campo de valor exato. Para aplicar o valor padrão da ferramenta, pressione **R**.

Os **controles deslizantes flutuantes** mostram seu nome na linha. Um arraste e um clique abrem modos flutuantes diferentes.

Para abrir um controle flutuante temporário:

1. Arraste o nome para abrir o controle deslizante.

2. Solte o botão do mouse para aplicar a alteração.

Para manter o controle flutuante aberto:

1. Clique no nome uma vez.

2. Arraste a faixa do controle para visualizar uma alteração.

3. Clique duas vezes ou clique em outro lugar para aplicar a alteração.

Para cancelar uma alteração no controle flutuante, pressione **Esc**.

Para abrir as **Configurações das ferramentas de animação**, clique com o botão direito na ferramenta.

Os dez controles deslizantes numéricos são Pose intermediária, Suavizar, Vizinhos, Para referência, Suavização, Amplificar, Escala de tempo, Deslocamento de tempo, Deslocamento em cascata e Reduzir.

- **Pose intermediária** mescla a pose anterior com a seguinte. Valores abaixo de 0% ou acima de 100% extrapolam essas poses.
- **Escala de tempo** altera o espaçamento das chaves. Abaixo de 100%, as chaves se aproximam e a reprodução fica mais rápida. Acima de 100%, as chaves se afastam e a reprodução fica mais lenta. **Deslocamento de tempo** desloca a Ação do objeto ativo no tempo.
- **Deslocamento em cascata** move as chaves após o cursor de reprodução pelo número de quadros selecionado. O movimento em direção a quadros anteriores para um quadro após o cursor de reprodução.
- **Reduzir** remove chaves se a alteração resultante na curva ficar abaixo da tolerância selecionada. As chaves desaparecem durante a prévia. Pressione **Esc** para restaurá-las.
- **Para referência** mescla em direção ao quadro de referência. **Definir referência** armazena esse quadro. **Amplificar** dimensiona o movimento em torno dessa referência.

Ferramentas que abrangem toda a Ação, como Deslocamento de tempo, afetam mais do que as chaves selecionadas. Antes de alterar uma Ação inteira, verifique o texto de ajuda e as opções da cena.

![Controle flutuante de Escala de tempo, aberto acima do controle correspondente na barra de ferramentas. A instrução permanece em inglês por uma lacuna no catálogo de origem. Seu significado é: arraste para ajustar; clique duas vezes ou fora do controle para aplicar; Esc cancela. A imagem documenta esse fallback real e não comprova uma interface integralmente traduzida. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): a4794a2e07bf.](images/pt/12.10.0-timing-popout.png)

<a id="default-rows"></a>

### Linhas padrão

Cada linha tem um conjunto padrão fixo. As listas a seguir apresentam os controles da esquerda para a direita, na ordem de trabalho.

- **Todos:** a linha começa com o controle deslizante Pose intermediária, com marcas em 25, 50 e 75%. Em seguida aparecem os ícones de deslocamento -1f/+1f e o controle flutuante Escala de tempo. Depois vêm o controle Suavizar e os ícones Copiar, Colar, Espelhar selecionados, Consolidar objeto e Trajetórias, nessa ordem. O olho de Trajetórias mostra ou oculta as trajetórias no espaço global.

![Linha Todos, detalhe à esquerda. Consulte a visão geral da linha completa para localizar Buscar e Configurações. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): bd00c0facf5f.](images/pt/12.10.0-all-row-left.png)

![Linha Todos, detalhe à direita. A sobreposição permite relacioná-lo ao detalhe esquerdo da mesma linha. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): bae266cf5d23.](images/pt/12.10.0-all-row-right.png)

- **Blocagem:** o controle Pose intermediária varia de -25% a 125%. Suas marcas são -25, 25, 50, 75 e 125. As marcas -25 e 125 extrapolam as poses delimitadoras. As marcas 25 e 75 mesclam em direção a elas. Os ícones Pose intermediária e Distribuir aparecem depois do controle. Em seguida vêm Selecionar intervalo, Todas as chaves e Finais, seguidos dos ícones Ampliar à esquerda e Ampliar à direita. Depois aparecem os losangos Marcar chave, Marcar pose intermediária, Marcar extremo e Marcar pausa. Os ícones Copiar e Colar encerram a linha.

![Linha Blocagem, detalhe à esquerda. Leia os controles desta etapa junto de suas descrições. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 3ea3969467d7.](images/pt/12.10.0-block-row-left.png)

![Linha Blocagem, detalhe à direita. A sobreposição permite relacioná-lo ao detalhe esquerdo da mesma linha. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 8ad5cd908ee5.](images/pt/12.10.0-block-row-right.png)

- **Spline:** o ícone de curva Para spline aparece primeiro. Seguem os controles Vizinhos, Suavização e Suavizar. Depois vem o ícone de alvo Definir referência, seguido dos controles Para referência e Amplificar. Em seguida aparecem os ícones de alças Automáticas limitadas, Vetor e Livre. Trajetórias encerra a linha.

![Linha Spline, detalhe à esquerda. Leia os controles desta etapa junto de suas descrições. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 56743718c4d9.](images/pt/12.10.0-spline-row-left.png)

![Linha Spline, detalhe à direita. A sobreposição permite relacioná-lo ao detalhe esquerdo da mesma linha. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 31846fd1f08a.](images/pt/12.10.0-spline-row-right.png)

- **Refinamento:** a linha começa com -1f/+1f. O controle Escala de tempo vem a seguir, com marcas em 80, 90, 110 e 120%. Depois aparecem Deslocamento de tempo e Deslocamento em cascata. Deslocamento em cascata tem marcas em -1 e 1. Em seguida, Ajustar a incrementos ajusta os tempos das chaves para valores inteiros. Os ícones Selecionar oposto, Espelhar selecionados, Espelhar ativo e Trocar encerram a linha.

![Linha Refinamento, detalhe à esquerda. Leia os controles desta etapa junto de suas descrições. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 69cdb38ddde5.](images/pt/12.10.0-polish-row-left.png)

![Linha Refinamento, detalhe à direita. A sobreposição permite relacioná-lo ao detalhe esquerdo da mesma linha. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): cbeedc999934.](images/pt/12.10.0-polish-row-right.png)

- **Entrega:** o ícone Consolidar objeto aparece primeiro, seguido de Consolidar intervalo de prévia e Consolidar de forma inteligente. Depois vem o controle Reduzir, com marcas em 0.001, 0.01 e 0.05. Consolidar chaves em quadros inteiros aparece em seguida e mantém um registro para Redefinir tempo. Segue Proxy e consolidação com um clique. Depois vêm os ícones de proxies de Posição, Rotação, Global e Pai. Consolidar sessão e remover proxies aparece após esses ícones. Remover todas as sessões de proxy encerra a linha.

![Linha Entrega, detalhe à esquerda. Leia os controles desta etapa junto de suas descrições. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 6fb951981ff4.](images/pt/12.10.0-deliver-row-left.png)

![Linha Entrega, detalhe à direita. A sobreposição permite relacioná-lo ao detalhe esquerdo da mesma linha. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 7cea8bca7223.](images/pt/12.10.0-deliver-row-right.png)

**Buscar** inclui ferramentas que não aparecem na linha. Exemplos são **Para degraus** e os botões **Pose intermediária 25/50/75%**.

**Copiar** inclui as alças. O **Colar** do Anim Assist usa os tempos copiados. O Colar nativo pode alinhar ao cursor de reprodução. Antes de usar um atalho nativo no lugar dessas ferramentas, verifique sua dica de ferramenta.

A visão geral da linha completa acima mostra as posições dos controles. Os detalhes de cada linha se sobrepõem para manter os rótulos dos botões legíveis. As figuras das listas de famílias mostram comandos adicionais.

<a id="find-and-more"></a>

### Buscar e Mais

**Buscar** (a lupa) inclui todas as ferramentas.

1. Clique na lupa.

2. Digite parte do nome de uma ferramenta, de uma família ou um termo de pesquisa, como "espaçamento" ou "arco".

3. Clique em uma ferramenta para executá-la.

Para navegar sem pesquisar:

1. Deixe o campo de pesquisa vazio.

2. Selecione uma aba de família.

Para adicionar ou remover uma ferramenta da linha atual, clique em seu alfinete.

Um alfinete aceso indica que a ferramenta está na linha atual.

Fixar uma ferramenta afeta a linha atual, independentemente da família da ferramenta. **Buscar** e **Configurações da barra de ferramentas** compartilham o mesmo leiaute. As alterações em um aparecem no outro.

Se N ferramentas não couberem na largura da Linha do tempo, **Mais** aparece como **+N** antes de Buscar. Se todas as ferramentas couberem, Mais desaparece.

Para executar uma ferramenta em Mais:

1. Clique em **+N**.

2. Clique na ferramenta.

Para obter mais espaço, alargue a Linha do tempo ou encurte os controles deslizantes em linha. Como alternativa, exiba as ferramentas menos usadas como controles flutuantes ou botões.

![Janela completa de Buscar ferramentas, com consulta vazia, sete abas e as dez ferramentas da família Interpolação de poses (Tween), com alfinetes acesos e apagados. A primeira aba aparece abreviada como Interpolação… na interface nativa e é distinta da aba Pose. O campo de busca mantém o texto inglês Search. A captura mostra os controles e seus estados; nenhuma ferramenta ou alfinete foi acionado. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 7ade4711839a.](images/pt/12.10.0-find-tools.png)

![Menu de ferramentas que não couberam na linha, detalhe superior: título e quatro primeiros comandos. Os comandos Espelhar ossos selecionados e Consolidar transformações do objeto aparecem inteiros também no detalhe inferior, formando a referência de sobreposição. O menu completo contém seis comandos em uma única coluna, na janela de 710 px de largura. Suavizar chaves e Colar chaves estão desativados; os outros quatro comandos estão disponíveis. O limite direito do menu coincide com a borda da janela, sem margem externa desse lado. Nenhuma ferramenta foi executada. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 1b63c0e1b377.](images/pt/12.10.0-more-left.png)

![Menu de ferramentas que não couberam na linha, detalhe inferior: comandos de 3 a 6. Espelhar ossos selecionados e Consolidar transformações do objeto se repetem inteiros no detalhe superior; abaixo aparecem as trajetórias de movimento e a colagem de chaves. O menu completo contém seis comandos em uma única coluna, na janela de 710 px de largura. Suavizar chaves e Colar chaves estão desativados; os outros quatro comandos estão disponíveis. O limite direito do menu coincide com a borda da janela, sem margem externa desse lado. Nenhuma ferramenta foi executada. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 82dd1c1b5f53.](images/pt/12.10.0-more-middle.png)

![Menu completo de seis ferramentas que não couberam na linha, com o botão +6 real e os controles vizinhos da barra de ferramentas. A captura preserva as seis linhas do menu e seu acesso +6. O menu completo contém seis comandos em uma única coluna, na janela de 710 px de largura. Suavizar chaves e Colar chaves estão desativados; os outros quatro comandos estão disponíveis. O limite direito do menu coincide com a borda da janela, sem margem externa desse lado. Nenhuma ferramenta foi executada. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 86b4fc86f569.](images/pt/12.10.0-more-right.png)

<a id="undo-from-find-menus-and-the-toolbar"></a>

### Desfazer em Buscar, nos menus e na barra de ferramentas

Na versão 12.11.1, **Buscar** e as ações dos menus nativos usam a entrada nativa de Desfazer da ferramenta. Eles não acrescentam uma segunda entrada para a mesma edição. As ações diretas da barra de ferramentas na área de edição mantêm seu ponto de restauração necessário para Desfazer. A conclusão e o cancelamento de controles deslizantes continuam com tratamentos separados.

1. Conclua a ação ou o gesto no controle deslizante.

2. Use o **Desfazer** nativo para restaurar o resultado anterior.

3. Inspecione as chaves e o movimento antes de continuar.

Alguns controles de seleção, navegação de configurações e outras ações sem edição não criam uma entrada de Desfazer de animação. As entradas do histórico variam entre os controles.

![Parte superior do menu Editar nativo, com Desfazer, Refazer e Histórico do desfazer. Desfazer e Refazer estão desativados no estado de histórico capturado; Histórico do desfazer está disponível. A imagem não mostra o restante do menu nem comprova a execução desses comandos. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): e27dcc39139b.](images/pt/5.2.3-native-undo-menu.png)

<a id="change-what-a-row-shows"></a>

### Alterar o conteúdo de uma linha

1. Clique em **Configurações** à direita da linha.

2. Em **Linha**, selecione **Todos**, **Blocagem**, **Spline**, **Refinamento** ou **Entrega**.

3. Clique no cabeçalho de uma família para abrir suas ferramentas.

4. Para cada ferramenta, selecione seu modo de **Exibição**.

5. Para ferramentas com ícone, em **Rótulo**, selecione **Rótulo** ou **Ícone**.

6. Para um controle deslizante em linha, defina a **Largura** no segundo campo.

7. Para mover uma ferramenta dentro de sua família, clique nas **setas para cima e para baixo**.

8. Para abrir as Configurações das ferramentas de animação, clique em sua **engrenagem**.

9. Clique fora do painel ou pressione **Esc** para fechá-lo.

As ferramentas comuns oferecem os modos de exibição Oculto e Botão. Oculto remove a ferramenta da linha. Os controles deslizantes também oferecem os modos Controle deslizante em painel e Controle deslizante na linha.

**Configurações da barra de ferramentas** abre na linha atual. Seu seletor **Linha** permite visualizar outra linha durante a edição. O cabeçalho de cada família mostra a quantidade de ferramentas visíveis. Uma etapa inicialmente abre suas famílias principais. Para filtrar ferramentas pelo nome, use **Encontrar ferramenta** acima das famílias.

As alterações aparecem imediatamente. Fechar o painel com um clique fora dele ou com Esc mantém essas alterações. O painel não tem botão OK. **Reverter alterações** restaura todas as linhas ao estado que tinham quando o painel foi aberto. Qualquer linha pode conter qualquer ferramenta. Adicionar uma ferramenta de outra família também adiciona o botão dessa família à linha.

A exibição por ícone é compatível com tipos de chaves, tipos de alças, expansão da seleção, -1f/+1f, Pose intermediária, Distribuir, Para spline, Para degraus, Definir referência, Copiar e Colar. Também é compatível com Espelhar selecionados, Espelhar ativo, Selecionar oposto, Trocar, Consolidar objeto, os quatro tipos de proxy e Trajetórias. As outras ferramentas mostram seus nomes.

A engrenagem ou um clique com o botão direito em uma ferramenta da linha abre **Configurações das ferramentas de animação**. Esse painel configura exibição, intervalo, valor padrão, largura, precisão, sensibilidade ao arraste, ajuste a incrementos, predefinições e **Predefinições como marcas**. **Intervalo personalizado / ultrapassagem** permite um intervalo personalizado dentro dos limites da ferramenta.

Cada etapa armazena sua própria exibição, rótulo, predefinições e marcas. Todas as linhas compartilham os demais valores. As configurações da cena armazenam máscaras, alvos e âncoras de poses intermediárias. **Opções de ferramentas da cena** abre essas configurações.

| Configuração | Limite |
|---|---|
| Largura do controle deslizante | 80–240 pixels lógicos. Linhas estreitas podem encurtar a faixa desenhada. |
| Precisão | 0–4 casas decimais. |
| Sensibilidade | 10–2,000 pixels ao longo do intervalo de um controle flutuante. |
| Predefinições | No máximo 12 valores finitos dentro do intervalo permitido. |
| Intervalo personalizado de Pose intermediária | -100% a 200%. |
| Intervalo personalizado de Escala de tempo | Mínimo de 1%. |
| Intervalo personalizado de Deslocamento em cascata | -500 a 500 quadros. |
| Intervalo personalizado de Reduzir | 0 a 1 unidade de tolerância. |

O intervalo padrão exibido pode ser menor que o intervalo personalizado permitido. Esses limites de configuração da barra de ferramentas não recomendam tolerâncias para rigs de produção.

![Configurações da barra de ferramentas para a linha Blocagem. Este recorte mostra apenas a seção superior Interpolação de poses, com controles de exibição, largura, ordem e configuração das ferramentas. As reticências e abreviações são as da interface nativa; o campo de busca mantém o texto inglês Search. A seção inferior de chaves não aparece. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 01c9f2b27311.](images/pt/12.10.0-toolbar-settings.png)

![Configurações das ferramentas de animação para Arrastar pose intermediária. A janela inteira, do título aos botões OK e Cancelar, mostra exibição, largura, intervalo, sensibilidade, precisão, ajuste a incrementos e predefinições como marcas. Algumas instruções e campos apresentam reticências ou abreviações nativas, preservadas nesta captura. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 5a6a9cdb31a7.](images/pt/12.11.1-tool-settings.png)

<a id="save-load-and-reset-layouts"></a>

### Salvar, carregar e redefinir leiautes

Um leiaute contém todas as linhas: Todos e as quatro etapas.

| Controle | Resultado |
|---|---|
| **Salvar como** | Nomeia e salva o leiaute atual. |
| **Carregar** | Restaura um leiaute salvo. |
| **Atualizar salvo** | Substitui o leiaute salvo pelas linhas atuais. |
| **Renomear** e **Excluir** | Renomeiam ou excluem leiautes salvos. |
| **Recomendado** | Identifica o leiaute interno fixo. |
| **Restaurar Blocagem aos padrões** | Restaura o conjunto padrão dessa etapa. O nome do controle muda conforme a linha em edição. |
| **Restaurar layout recomendado** | Restaura Todos e cada etapa. Os leiautes salvos continuam disponíveis. |

As preferências do complemento armazenam os leiautes. Os leiautes se aplicam a todas as Linhas do tempo.

Se as Preferências não forem salvas automaticamente, clique em **Salvar preferências** nas Configurações da barra de ferramentas. Isso mantém as alterações após uma reinicialização.

Os nomes de leiautes salvos contêm de 1–64 caracteres. A biblioteca permite no máximo 100 leiautes salvos. Carregar um leiaute substitui a organização de trabalho. Antes de substituir uma organização modificada, leia o controle de alterações não salvas.

As etapas começam com padrões fixos. Adicionar uma ferramenta a Todos não a adiciona a uma etapa. Adicione a ferramenta separadamente a cada etapa necessária. As Preferências do complemento não têm controle de etapa. Cada área de trabalho usa o botão de etapa da linha.

A figura **Configurações da barra de ferramentas** acima mostra os controles de leiautes salvos. Use o mesmo painel para configurar linhas e gerenciar leiautes.

<a id="hover-explanations-and-shortcuts"></a>

### Explicações ao passar o ponteiro e atalhos

Para ver a explicação de um controle, mantenha o ponteiro sobre ele por cerca de meio segundo. **Explicações ao passar o mouse** controla a quantidade de texto de ajuda. A opção fica em Editar > Preferências > Complementos > Anim Assist > Geral.

A ajuda ao passar o ponteiro, as opções de etapas e os controles deslizantes flutuantes permanecem acima dos botões da barra de ferramentas. A Linha do tempo mostra uma dica do Anim Assist sob o ponteiro. A ajuda da barra de ferramentas tem prioridade sobre o Scene Strip Gizmo abaixo da linha.

- **Completo:** o texto explica a função, o escopo, os requisitos e o uso da ferramenta.
- **Curto:** o texto fornece o nome e uma linha de explicação. Para uma ferramenta esmaecida, também informa o motivo.
- **Desativado:** a linha não mostra texto de ajuda do Anim Assist ao passar o ponteiro. Os botões nativos do Bforartists nos painéis e menus do Anim Assist continuam mostrando o nome da ferramenta. O Bforartists sempre exibe uma linha de descrição nesses locais. Os campos de configuração mantêm sua própria dica de uma linha.

Para desativar todas as dicas de ferramentas, use **Editar > Preferências > Interface > Dicas**.

O texto de ajuda lista atalhos somente quando existe uma associação:

- **Atalho:** esta tecla está associada àquela ferramenta exata do Anim Assist. As ferramentas da linha não têm atalhos padrão. Para mostrar um atalho aqui, associe um em **Editar > Preferências > Mapa de teclas**.
- **Tecla do Bforartists:** esta tecla executa um comando nativo para a mesma função. Os padrões da Tabela de animação incluem **Ctrl C** para Copiar e **Ctrl V** para Colar. **A** seleciona todas as chaves. **Ctrl Numpad +** expande a seleção dos dois lados. **R** dimensiona a temporização das chaves. **W** move as chaves no tempo. Os comandos nativos podem se comportar de forma diferente das ferramentas do Anim Assist. O Colar nativo usa o cursor de reprodução em vez dos tempos copiados.

![Explicação completa de Suavizar chaves (arrastar), com o controle Suavizar destacado. A ferramenta aproxima as chaves selecionadas da média de suas vizinhas imediatas e informa o escopo editável. Arraste para pré-visualizar; solte para aplicar; Esc cancela. Clique com o botão direito para configurar a ferramenta. Esta captura não mostra uma linha de atalho. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 6a7d26c0753e.](images/pt/12.10.0-hover-explanation.png)

A figura **Preferências do Anim Assist incluído**, perto da instalação, mostra **Completo**, **Curto** e **Desativado**. A figura **Configurações**, mais adiante neste guia, mostra as opções de atalhos e menus.

<a id="dope-sheet-poses-and-key-timing"></a>

## Tabela de animação: poses e temporização das chaves

O resumo conta os proprietários visíveis, as curvas editáveis e as chaves selecionadas. Ele inclui controles de seleção Todos/Nenhum. **Blocagem e interpolação** começa aberto. Os demais grupos são **Tempo, Chaves e canais, Pose e correspondência, Consolidar e concluir e Prateleira rápida**.

1. Selecione um objeto animado ou ossos de pose.

2. Mostre os canais da Ação.

3. Selecione as chaves para editar.

4. Use **Blocagem e interpolação** para percentuais de poses intermediárias, criação de intermediárias e ferramentas de arraste.

5. Expanda as opções de **Blocagem e interpolação** para acessar máscaras, predefinições e opções de amostragem.

6. Use **Tempo** para espaçamento, deslocamentos e cascata.

7. Use **Chaves e canais** para seleção, gerenciamento de chaves e metadados.

8. Use **Pose e correspondência** para correspondência e espelhamento.

9. Use **Consolidar e concluir** para ferramentas de consolidação e diagnóstico.

Para selecionar lados de alças, use o Editor gráfico. A Tabela de animação mantém os tipos avançados de alças. Scene Properties contém a criação de macros e a configuração.

![Ferramentas de Blocagem e interpolação na Tabela de animação. A cena de exemplo mostra os proprietários HumanArmature e Toolkit_Offer_Animated_Cube, com chaves nos quadros 1 e 24; o estado registrado contém 15 chaves selecionadas e seis curvas editáveis. O campo de busca mantém o texto inglês Search, e nomes longos de ações permanecem abreviados pela largura nativa dos canais. A captura mostra o escopo e os controles, sem comprovar a execução de uma operação. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): bc8203d5d9a2.](images/pt/12.8.0-dopesheet-tools.png)

<a id="breakdown-anchors"></a>

### Âncoras de poses intermediárias

Em um quadro vazio, as chaves ao redor ancoram a mesclagem. Por exemplo, os valores 0 e 10 produzem 5 a 50%.

Se o cursor de reprodução já estiver sobre uma chave, essa chave se torna a âncora anterior. Um valor atual de 5 e um próximo valor de 10 produzem 7.5 a 50%. Repetir a operação pode alterar novamente a chave existente.

Antes de aplicar uma pose intermediária, verifique o cursor de reprodução, as chaves e as máscaras.

A figura da Tabela de animação acima mostra as ações de poses intermediárias e suas opções. Cada exemplo numérico descreve uma disposição diferente de cursor de reprodução e chaves.

<a id="graph-editor-curve-shaping"></a>

## Editor gráfico: modelar curvas

**Modelar curvas** começa aberto com ações diretas de modelagem, interpolação e alças. Os grupos são **Selecionar e canais, Modelar curvas, Ajustar tempo, Limpar, Pose e consolidação e Prateleira rápida**. **Selecionar e canais** inclui a seleção de alças. **Limpar** contém gerenciamento de chaves e diagnósticos. **Pose e consolidação** inclui correspondência, espelhamento, poses intermediárias e consolidação. Suas **Opções de pose intermediária**, recolhidas, configuram a amostragem das poses intermediárias. Elas não configuram a interpolação geral das curvas.

1. Selecione chaves de Ação visíveis e editáveis.

2. Aplique a ação de modelagem ou interpolação.

3. Inspecione a curva resultante e a janela de visualização.

A interpolação de chaves selecionadas afeta somente chaves selecionadas, editáveis e visíveis. Os comandos de temporização do Gerenciador de chaves respeitam a visibilidade do editor e os bloqueios de canais. **Mover chaves** e **Inserir quadros** são executados imediatamente. Para ajustar seus valores, use o **Ajustar Última Operação** nativo.

Os auxiliares de seleção de Ações são compatíveis com **Ações de objetos**. Se o escopo estiver vazio, eles não selecionam a Ação ativa inteira. Eles excluem Ações fixadas sem vínculo e fontes que não sejam objetos. A barra lateral explica essas exclusões. Antes de usar ferramentas que abrangem toda a Ação, verifique suas descrições.

![Visão geral do Editor gráfico com a seção Modelar curvas expandida. O estado registrado de HumanArmature contém seis chaves selecionadas e três curvas editáveis, em sua maioria planas. Os controles de modelagem estão visíveis; a imagem não demonstra um resultado de modelagem. Os textos nativos Search e Quick permanecem em inglês. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): d47760581581.](images/pt/12.8.0-graph-tools.png)

<a id="drivers-inspect-and-shape-driver-responses"></a>

## Controladores: inspecionar e modelar respostas

Para acessar as ferramentas de drivers, mude o Editor gráfico para o modo **Controladores**. A barra lateral **Anim Assist** e o menu do cabeçalho mostram quatro seções específicas para drivers. Voltar às curvas de Ações restaura os grupos de Ações descritos acima. O modo Controladores usa canais de drivers em vez de ferramentas de chaves de Ações.

<a id="driver-target"></a>

### Driver e alvo

Esta seção conta os drivers visíveis selecionados. Para um driver ativo, ela também mostra **Proprietário**, **Propriedade** e **Valor atual**. Quando aplicável, mostra um **Índice da matriz**. Uma propriedade não resolvida gera um aviso.

1. Selecione um canal de driver visível na lista de canais.

2. Inspecione seu proprietário e a propriedade controlada em **Driver e alvo**.

3. Clique em **Enquadrar selecionados** para enquadrar as curvas selecionadas.

4. Para ver toda a visualização de drivers, clique em **Enquadrar tudo**.

**Todos os canais** e **Nenhum** alteram a seleção de canais. **Selecionar proprietário** torna ativo o objeto que contém o driver. Os outros objetos selecionados continuam selecionados. O proprietário deve pertencer à camada de visualização atual e permitir a seleção visível de objetos. Controladores em outros blocos de dados não podem usar essa ação de seleção de objetos.

Se o proprietário for editável, **Silenciado** e **Bloqueado** alteram as configurações nativas de canal do driver ativo. Um único driver visível selecionado continua disponível para inspeção após o bloqueio. Para desbloqueá-lo, desative **Bloqueado**. Se vários canais selecionados tornarem o driver ativo ambíguo, selecione explicitamente o canal desejado.

Com a seleção vazia, as quatro seções continuam visíveis e mostram orientações. Elas não criam um driver.

Antes de usar essas seções:

1. Crie drivers com o fluxo nativo de drivers do Bforartists.

2. Conecte esses drivers.

![Barra lateral completa do Anim Assist para um driver selecionado e desbloqueado de Empty, propriedade scale, índice 0, valor atual 1 e expressão var + 1.0. Os pontos da curva de resposta não estão selecionados, por isso Interpolação e Alças aparecem desativados. O comando para enquadrar os elementos selecionados aparece abreviado como Enquadrar selecio… na interface nativa. Nenhuma edição da resposta ou execução do diagnóstico é demonstrada nesta figura. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-21 às 00:04:54.454336 (UTC). SHA-256 da imagem (prefixo): 745a451d2ef7.](images/pt/12.11.0-selected-driver.png)

<a id="variables-expression"></a>

### Variáveis e expressão

Esta seção conta as variáveis. Controladores por script mostram **Expressão**. Os outros tipos de driver mostram **Tipo**. A aba nativa **Controladores** contém todas as configurações editáveis de variáveis e expressões.

1. Desbloqueie o canal do driver desejado.

2. Clique nesse canal para torná-lo o driver editável ativo nativo.

3. Abra **Variáveis e expressão**.

4. Clique em **Abrir configurações do driver**.

5. Edite as variáveis, os alvos, o tipo de driver ou a expressão na aba nativa **Controladores**.

6. Volte a **Anim Assist** para acessar ações de resposta e diagnósticos.

O botão abre a categoria nativa da barra lateral. Ele não abre uma cópia separada da janela de configurações. Um driver bloqueado pode continuar disponível para inspeção sem tornar as configurações nativas editáveis. As abas nativas da barra lateral podem aparecer em ordens diferentes. Identifique **Controladores**, **Modificadores** e **Anim Assist** pelo nome.

![Configurações nativas do driver de Escala X de Empty, índice 0. A expressão var + 1.0 usa uma variável que lê a Localização em X de Empty no espaço do ambiente: entrada 0 e saída 1. O seletor de tipo mantém a abreviação nativa; Driver Property significa propriedade do driver, Expression significa expressão e Add Input Variable significa adicionar variável de entrada. Esses textos permanecem em inglês na imagem. A categoria nativa já estava selecionada no estado compartilhado; a captura não demonstra um clique no botão português nem uma alteração da variável ou expressão. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-21 às 00:05:30.226447 (UTC). SHA-256 da imagem (prefixo): f5e4bdfe30d3.](images/pt/12.11.0-native-driver-settings.png)

<a id="response-curve"></a>

### Curva de resposta

O eixo horizontal representa a entrada do driver. O eixo vertical representa a saída controlada. Os pontos de resposta mapeiam a entrada para a saída. Eles diferem das chaves de Ações, que usam o tempo da animação.

1. Selecione os canais de drivers visíveis que deseja editar.

2. Desbloqueie esses canais.

3. Verifique se seus proprietários são editáveis.

4. Para alterações em pontos, selecione pontos de resposta ou lados de alças.

5. Selecione **Interpolação** ou **Alças** em **Curva de resposta**.

6. Inspecione a resposta resultante e a propriedade controlada.

| Controle | Escopo e resultado |
|---|---|
| **Interpolação** | Altera pontos de resposta selecionados em canais de drivers selecionados, visíveis e editáveis. As opções são Constante, Linear e Bezier. |
| **Alças** | Altera os lados de alças selecionados nesses canais. Se um ponto de controle estiver selecionado, a ação altera as duas alças. |
| **Extrapolação** | Altera canais de drivers selecionados, visíveis e editáveis fora do intervalo entre suas extremidades. Constante mantém a saída. Linear continua a inclinação da extremidade. |
| **Adicionar modificador (ativo)** | Adiciona o modificador de resposta escolhido somente ao driver editável ativo. Não afeta todos os canais selecionados. |
| **Abrir configurações de modificadores** | Abre a aba nativa **Modificadores** do driver ativo. |

As ações de pontos exigem pontos ou alças selecionados. A extrapolação exige canais editáveis selecionados. As ações de modificadores exigem um driver ativo desbloqueado com proprietário editável. Abrir as configurações nativas também exige um driver editável que esteja ativo nativamente. Se um controle estiver desativado, passe o ponteiro sobre ele para ler seu requisito.

Interpolação, alças, extrapolação e criação de modificadores oferecem suporte nativo a **Desfazer** e **Ajustar Última Operação**. Essas ações afetam somente os drivers especificados. Elas excluem chaves de Ações e drivers não relacionados. A verificação em execução não abrange cada tipo nativo de modificador separadamente.

A figura do driver selecionado acima mostra **Interpolação**, **Alças**, **Extrapolação** e **Adicionar modificador (ativo)**. O destino nativo dos modificadores aparece abaixo.

![Editor de Controladores em uma janela de 710 px, com a curva Escala X de Empty selecionada e desbloqueada. A categoria nativa Modificadores está aberta e mostra Adicionar modificador, mas a pilha de modificadores está vazia. Nenhum modificador foi adicionado; a captura registra a categoria já selecionada e não demonstra um clique no botão português. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-21 às 00:07:50.220892 (UTC). SHA-256 da imagem (prefixo): 09d87fecfbad.](images/pt/12.11.0-native-modifier-settings.png)

<a id="diagnostics"></a>

### Diagnóstico

1. Selecione os canais de drivers visíveis que deseja inspecionar.

2. Abra **Diagnóstico**.

3. Clique em **Verificar drivers selecionados**.

4. Leia a janela de resultados.

5. Corrija os alvos, caminhos, ossos ou expressões indicados nas configurações nativas apropriadas.

6. Após corrigir uma dependência, clique em **Atualizar dependências**.

**Verificar drivers selecionados** verifica a validade da avaliação, alvos ausentes, caminhos de propriedades não resolvidos e ossos ausentes. Também informa proprietários vinculados/somente leitura, canais bloqueados e drivers silenciados. Se um alvo de propriedade tiver um valor de reserva ativado, a verificação não relata uma falha de caminho não resolvido para esse alvo.

As verificações inspecionam somente drivers visíveis selecionados. Elas não examinam o arquivo inteiro. Elas não comprovam que cada expressão produz o movimento desejado. **Atualizar dependências** atualiza os proprietários dos drivers selecionados e reavalia a camada de visualização. Não corrige expressões, reconecta alvos, altera pontos de resposta nem exclui drivers.

![Resultado completo do diagnóstico do driver selecionado: Nenhum problema encontrado. O resultado se limita ao exemplo desbloqueado de Escala X de Empty, índice 0, com expressão var + 1.0, entrada 0 e saída 1. Ele não certifica outros drivers ou todo o fluxo de trabalho; não houve reparo automático nem exclusão. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-21 às 00:10:11.127400 (UTC). SHA-256 da imagem (prefixo): 26439ff95d54.](images/pt/12.11.0-driver-diagnostics.png)

<a id="nla-arrange-clips-and-blend-corrections"></a>

## NLA: organizar clipes e mesclar correções

**Organizar e ajustar tempo** e **Mesclagem e correções** começam abertos. **Ações e trilhas, Consolidar e concluir e Prateleira rápida** começam fechados. O resumo mostra o proprietário, o clipe ativo, a Ação de origem, a quantidade de clipes selecionados, o intervalo da cena e o intervalo da origem. Os quadros da cena indicam a posição do clipe. Os quadros de origem indicam o intervalo da Ação dentro do clipe.

<a id="arrange-clips"></a>

### Organizar clipes

1. Selecione os clipes de Ações que deseja alterar.

2. Clique no corpo do clipe de referência para torná-lo ativo.

3. Verifique se o clipe de referência continua selecionado.

4. Clique em **-1f/+1f** para deslocar por quadro, ou em **Mover clipes selecionados** para um movimento nativo.

5. Para alinhar clipes ao clipe ativo selecionado, use **Align Starts to Active Clip / Align Ends to Active Clip**.

6. Para colocar os clipes em sequência a partir do início do clipe de referência, use **Sequenciar clipes**.

7. Altere o incremento ou o intervalo da sequência em **Ajustar Última Operação**.

8. Expanda **Opções de tempo** para acessar escala, repetição, inversão e início/fim na cena do clipe ativo.

A temporização usa quadros da cena. As ferramentas rejeitam lotes bloqueados ou sobrepostos sem fazer alterações parciais. A organização fica suspensa durante a edição da origem. Essas ferramentas não podem editar faixas de transição, meta ou áudio.

![Janela de mesclagem da correção selecionada, com o modo Combinar e Influência animada marcada. No quadro 12, a influência é 0,500, em um campo amarelo com chave. A origem é preservada. O título inglês Blend Options permanece como texto de origem sem tradução e significa opções de mesclagem; a imagem não mostra uma visão geral de todo o editor NLA. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): ca284b582103.](images/pt/12.8.0-nla-arrange.png)

Antes de usar ações para o clipe ativo, verifique se o resumo mostra o proprietário, o clipe e a Ação correspondentes.

<a id="edit-sources-and-manage-sharing"></a>

### Editar origens e gerenciar o compartilhamento

**Editar ação** entra no Tweak Mode NLA nativo. **Abrir Dope Sheet/Abrir Graph Editor** reutiliza um editor adequado não fixado ou muda a área atual. O Tweak Mode nativo mapeia o tempo de origem para clipes movidos, dimensionados, repetidos e invertidos.

Para voltar à organização após a edição:

1. No seletor de editor, escolha **Animação não linear** para voltar ao NLA.

2. Clique em **Concluir edição**.

Editar uma Ação compartilhada pode afetar outros clipes. O resumo avisa sobre o compartilhamento e informa as origens excluídas. Silenciar e Solo afetam a avaliação.

| Controle | Resultado |
|---|---|
| **Tornar únicos os clipes selecionados** | Separa as Ações de origem dos clipes selecionados. |
| **Duplicar independente** | Copia a Ação. |
| **Duplicar vinculado** | Compartilha a Ação. |
| **Mover trilhas selecionadas para cima/baixo** | Reordena trilhas. Não move clipes entre trilhas. |

**Push Down Active Action / Stash Active Action** operam na Ação atribuída ao proprietário ativo. Enviar para baixo exige a avaliação NLA ativada. Se nenhum clipe estiver selecionado, o resumo oferece **Adicionar clipe de ação existente** para um objeto ativo editável.

![Janela completa de ações e trilhas, com o clipe de origem na trilha Manual Source e intervalo de 1 a 24. Os comandos ingleses Push Down Active Action e Stash Active Action permanecem desativados: significam transferir a ação ativa para um clipe NLA e armazenar a ação ativa em uma trilha silenciada. O proprietário está sem ação atribuída; nenhum desses comandos foi executado. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 45b79d2d0638.](images/pt/12.11.1-nla-actions.png)

<a id="add-a-transform-correction"></a>

### Adicionar uma correção de transformação

1. Selecione um clipe de Ação de origem compatível.

2. Clique em **Nova correção de transformação**.

3. Selecione o novo clipe de correção.

4. Clique em **Editar correção**.

5. Edite suas chaves de transformação no Tweak Mode nativo.

6. Após a edição, clique em **Concluir edição**.

7. Mantenha neutros os canais não modificados: localização zero, rotação zero/identidade, escala um.

8. No cursor de reprodução, clique em **0%, 50% ou 100%** para inserir uma chave de influência do clipe ativo.

A mesclagem nativa **Combinar** aplica a correção sobre o movimento de origem. Para usar outro valor de influência, insira-o em **Ajustar Última Operação**. Com influência zero, a correção não contribui com movimento.

A criação adiciona uma Ação de correção independente e uma trilha acima da origem. As correções são compatíveis com transformações de objetos e ossos de pose. A criação bloqueia rigs com restrições ou drivers, ossos não resolvidos e canais de origem que não sejam de transformação. Ela explica o motivo. Essas correções são separadas das ferramentas gerais de Camadas de animação em Scene Properties.

Mesclagem e Influência animada são configurações nativas da faixa. Se Influência animada estiver desativada, a barra lateral identifica o envelope de mesclagem automática. **Blend Options** mostra Mesclagem automática, entrada/saída da mesclagem e extrapolação. Os botões de influência criam chaves nativas de influência. Eles não criam chaves de pose na Ação de origem.

A figura **Controles de organização e correção NLA** acima mostra a trilha de correção, **Editar correção**, a mesclagem **Combinar** e os botões de influência.

<a id="bake-while-retaining-the-source-stack"></a>

### Consolidar mantendo a pilha de origem

1. Selecione um clipe do proprietário para consolidar.

2. Abra **Consolidar e concluir**.

3. Verifique o proprietário e o intervalo da cena exibidos.

4. Clique em **Consolidar em nova ação**.

5. Se necessário, ajuste o intervalo e o incremento em **Ajustar Última Operação**.

6. Verifique o nome e o intervalo da saída.

7. Antes de ativar a consolidação, silencie ou remova restrições ativas que seriam aplicadas novamente.

8. Selecione **Usar última consolidação (NLA desativado)**.

A consolidação grava as transformações avaliadas de objetos/poses em uma nova Ação e a mantém. A nova Ação inicialmente fica **sem atribuição**. As Ações, os clipes, os pais e as restrições originais permanecem. Ativar a consolidação é uma operação separada. **Usar última consolidação (NLA desativado)** atribui o resultado e desativa a avaliação da pilha de origem.

Salve a cena de origem para comparação. Renomear não altera a quem pertence a saída. Outro objeto que receba o nome antigo não pode receber essa saída. **Remover trilhas vazias** remove as trilhas vazias separadamente.

Os atalhos da Prateleira rápida NLA tornam as origens independentes, editam a origem ativa e fazem a consolidação do proprietário. Eles não executam macros gerais de edição de chaves em faixas.

![Consolidação NLA preservando os originais. A execução registrada concluiu o intervalo de 1 a 24, com incremento 1, e criou Toolkit_Offer_Animated_Cube NLA Bake. No momento desta captura, a saída ainda não estava atribuída ao proprietário e Usar última consolidação não havia sido executado. A origem e a correção foram mantidas. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 6e18b146fad0.](images/pt/12.11.1-nla-retained-bake.png)

<a id="scene-properties-and-broader-tools"></a>

## Scene Properties e ferramentas gerais

**Scene Properties > Anim Assist** contém **Prateleira rápida, Esta pose, Animação inteira, Rig, Rosto, Configuração (uma vez por rig), Configurações, Ajuda e diagnóstico**.

| Grupo | Trabalho |
|---|---|
| **Esta pose** | Deslocamentos de transformação, correspondência, troca de espaço e espelhamento de pose. |
| **Animação inteira** | Deslocamentos da Ação ativa, trajetórias de movimento e Camadas de animação. |
| **Rig** | Localizadores, proxies, configurações de consolidação e limpeza de sessão. |
| **Rosto** | Configuração de sincronização labial, conexão de alvos, prévia e controles de consolidação. |
| **Configuração (uma vez por rig)** | Configuração inicial e procedimentos de área de trabalho/sistema. |
| **Configurações** | Configurações compartilhadas, atalho radial opcional e criação de macros. |
| **Ajuda e diagnóstico** | Ajuda das ferramentas, relatórios de diagnóstico e orientações de recuperação. |

**Buscar** encontra ferramentas existentes. **Recentes** lista ferramentas concluídas, da mais nova para a mais antiga. **Repetir último** usa a entrada mais recente. Comandos cancelados ou não concluídos não entram em Recentes. Arquivos antigos ordenam Recentes pelo registro de data e hora. **Alternar modo da prateleira** percorre os modos da prateleira.

Para configurar macros, abra **Scene Properties > Anim Assist > Configurações**.

As figuras **Área da cena** e **Configuração inicial**, perto da instalação, mostram os pontos de acesso compartilhados. As figuras a seguir mostram cada painel registrado em uma janela flutuante nativa.

![Janela completa de Configurações, com controles de exibição, menus do cabeçalho e preferências. O menu radial está desativado; o texto Shift Alt D aparece desativado e não demonstra um atalho ativo. Os nomes Graph Editor e Dope Sheet permanecem como aliases ingleses exibidos nesta interface. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): ede7e985a2f4.](images/pt/12.11.1-settings.png)

![Janela completa de configurações de macros. As macros integradas estão listadas, não há macros personalizadas e o modo em lote está definido para objetos selecionados. Nenhuma macro foi executada. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): a561a20f2b21.](images/pt/12.11.1-macros.png)

<a id="offset-match-and-mirror"></a>

### Deslocar, corresponder e espelhar

1. Selecione o proprietário animado e as chaves ou os ossos de pose desejados.

2. Abra **Tabela de animação > Anim Assist > Blocagem e interpolação > Deslocamento de transformação** para deslocar chaves.

3. Selecione a máscara de canais.

4. Selecione o escopo do deslocamento.

5. Defina os valores de deslocamento.

6. Selecione o espaço de transformação.

7. Use **Ajustar quadro atual**, **Deslocar chaves selecionadas** ou **Arraste interativo** para o escopo desejado.

8. Antes de usar **Reaplicar último** ou **Inverter último**, inspecione o resultado.

![Controles de Deslocamento de transformação no contexto da Tabela de animação, com a ação consolidada preenchida e atribuída após a execução real de Usar última consolidação. Este estado é posterior à saída ainda não atribuída da figura 35. Os canais de translação, o quadro atual, o espaço local e a ausência de atenuação estão configurados; nenhuma operação de deslocamento foi executada. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): e134a46db945.](images/pt/12.11.1-transform-offset.png)

**Scene Properties > Anim Assist > Esta pose > Deslocamento de pose** desloca os ossos de pose selecionados por incrementos ou por arraste interativo. Deslocamento de pose exige o **Modo de pose**.

Quadro atual, Chaves selecionadas e Intervalo de quadros são escopos de deslocamento separados. A atenuação do intervalo de quadros distribui o deslocamento ao longo do tempo. A atenuação de entrada/saída suavizada não altera as tangentes das curvas. Essas ferramentas usam o pivô **Origens individuais**. Elas não fazem os elementos orbitarem em torno da mediana ou do cursor.

A correspondência oferece ações nos espaços Global, Pai e Alvo, específicas por canal, visuais/avaliadas e por matriz local. A correspondência com alvo geralmente exige dois objetos selecionados.

Para corresponder a um alvo:

1. Selecione o alvo primeiro.

2. Selecione o objeto que deseja alterar.

**Alinhar objetos selecionados ao ativo** usa o objeto ativo como referência. Esses controles não interpretam automaticamente todos os rigs.

Antes de usar fluxos de troca de espaço com compensação ou IK/FK:

1. Configure os mapeamentos das propriedades de troca.

2. Configure as cadeias.

As ferramentas de espelhamento exigem uma armação no **Modo de pose**. **Selecionar oposto** altera a seleção. As ações de espelhamento de quadro/intervalo também podem inserir chaves.

Antes de usar **Espelhar pose**, **Selecionado** ou **Trocar**:

1. Verifique a detecção de pares e as exceções de nomes.

2. Verifique o espaço e o eixo de espelhamento.

3. Verifique os filtros de canais.

4. Leia a descrição da ferramenta.

![Correspondência de transformação com Configurações expandidas na Vista 3D. Todos os canais TRS e os eixos XYZ estão selecionados; Manter deslocamento está desmarcado e o respeito aos canais bloqueados está marcado. Alguns comandos estão desativados neste estado; Global, Alvo, Pos, Rot e Escala permanecem disponíveis. A imagem documenta as configurações, sem demonstrar uma correspondência executada. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 95b884b8a941.](images/pt/12.11.1-transform-match.png)

Abra **Tabela de animação > Anim Assist > Pose e correspondência** para acessar todas as configurações de correspondência e espelhamento.

![Janela completa de Deslocamento de pose com HumanArmature em modo Pose e ossos selecionados. O espaço é local e não há contato configurado. A captura mostra os controles sem demonstrar uma alteração ou deslocamento da pose. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 56a63bcdaf3e.](images/pt/12.11.1-pose-offset.png)

![Janela completa dos controles de espelhamento com HumanArmature em modo Pose e ossos selecionados. Os comandos de espelhamento, seleção e troca são mostrados, sem que uma dessas operações tenha sido executada para a captura. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 11f55eab5d58.](images/pt/12.11.1-pose-mirror.png)

<a id="action-offsets-and-motion-trails"></a>

### Deslocamentos de Ação e trajetórias de movimento

**Animação inteira** inclui deslocamentos da Ação ativa e uma máscara opcional de intervalo. Esses deslocamentos podem afetar mais do que as chaves selecionadas.

Antes de ativar uma edição que abrange toda a Ação:

1. Configure a máscara.

2. Configure o intervalo.

Para usar trajetórias de movimento:

1. Selecione os objetos ou ossos de pose que serão alvos das configurações de trajetória.

2. Abra **Animação inteira > Sobreposição de trajetórias**.

3. Selecione o modo de exibição.

4. Selecione o escopo da amostragem.

5. Defina o incremento da amostragem.

6. Clique em **Ativar sobreposição**, ou use o olho de **Trajetórias** na Linha do tempo.

7. Após alterações, atualize as trajetórias quando necessário.

8. Execute os diagnósticos de arcos para identificar movimentos que precisam de inspeção.

9. Inspecione o movimento indicado.

As opções de trajetórias incluem marcas de quadros/chaves, números dos quadros e exibições de velocidade, tangente, fantasmas e cores. Os intervalos ao redor do quadro atual e personalizados limitam a amostragem. **Máximo de amostras** limita a quantidade de amostras. Os diagnósticos de arcos identificam movimentos que precisam de inspeção. Eles não certificam a qualidade da animação nem resolvem automaticamente um rig.

![Máscara de deslocamento de Ação com Usar máscara marcado. O intervalo da máscara é de 1 a 250, com entrada e saída da mesclagem em 5; ele difere do intervalo da cena, de 1 a 24. A captura mostra essa configuração, sem execução do comando Ativar. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 9860d4d49c40.](images/pt/12.11.1-action-offset.png)

![Configurações de Sobreposição de trajetórias com a sobreposição desativada. O escopo usa o quadro atual, com 25 quadros antes e depois, incremento 1, máximo 160 e largura de trajetória 2. Nenhuma trajetória foi ativada ou calculada para esta captura. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): b3f20e84cc4c.](images/pt/12.11.1-motion-trails.png)

<a id="locators-proxies-and-bake-sessions"></a>

### Localizadores, proxies e sessões de consolidação

1. Abra **Rig > Proxy e consolidação**.

2. Selecione o objeto desejado.

3. Selecione um localizador ou um proxy de Translação, Orientação, Espaço global ou Espaço do pai.

4. Defina o intervalo de consolidação para o comando de consolidação selecionado.

5. Defina o incremento da consolidação.

6. Selecione os canais de consolidação.

7. Execute o comando de consolidação.

8. Inspecione o movimento resultante da consolidação.

9. Use a limpeza de sessão somente após verificar o resultado da consolidação.

Os controles de localizadores criam localizadores em alvos, na média da seleção ou no cursor. Também criam relações de parentesco, aplicam restrições, fazem correspondências e consolidações entre localizadores e alvos. Antes de usar controles em pares, leia a direção de suas setas.

**Consolidar de forma inteligente** combina consolidação de transformações com redução de chaves. **Reduzir chaves** simplifica chaves existentes conforme sua tolerância. Os intervalos disponíveis são cena, Ação, personalizado, chaves selecionadas e prévia. Esses comandos gerais de consolidação diferem do fluxo **Consolidar em nova ação** do NLA, que preserva a origem.

**Proxy e consolidação com um clique** registra o movimento global em sua própria sessão de proxy antes da consolidação. **Consolidar sessão e remover proxies** limpa essa sessão. **Remover todas as sessões de proxy** afeta um escopo maior. A verificação existente não certifica todos os casos com parentesco, restrições ou rigs de produção. Antes de remover auxiliares, compare o resultado.

![Janela completa de proxy e consolidação sem sessão de proxy ativa. Os controles de localizador, criação de proxy, consolidação e limpeza aparecem com seus estados desativados preservados. A captura não demonstra criação de proxy, correspondência, consolidação nem limpeza. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): c12941c1392a.](images/pt/12.11.1-proxy-bake.png)

A figura mostra os controles de configuração antes da criação da sessão. Uma sessão ativa disponibiliza a limpeza.

<a id="animation-layers"></a>

### Camadas de animação

1. Abra **Animação inteira > Camadas de animação**.

2. Ative o sistema de camadas.

3. Clique em **Criar camada base** para a animação atual.

4. Adicione uma camada de trabalho.

5. Selecione a camada de trabalho.

6. Selecione seu modo de mesclagem.

7. Defina seu peso.

8. Configure suas atribuições de ossos.

9. Antes de inserir chaves, selecione a camada de trabalho desejada.

10. Visualize com os controles Solo, Silenciar e Bloquear da camada.

Uma lista de atribuições vazia inclui todos os ossos. No Modo de pose, o painel visível oferece **Atribuir**, **Remover** e **Selecionar** para atribuições de ossos. Cada linha de camada contém peso, Solo, Silenciar, Bloquear e Inserção automática de chaves.

Este painel registrado não mostra **Editar somente a camada ativa**, **Atribuir automaticamente ao inserir chave** nem todos os controles avançados de camadas. A pesquisa nativa de operadores oferece ações registradas como **Atribuir por padrão**, **Mesclar para baixo** e **Unir todas as camadas**. Antes de mesclar ou unificar, inspecione a pilha. Essas camadas são separadas dos clipes de correção de transformação NLA.

![Camadas de animação após a inicialização em HumanArmature, em modo Pose com 19 ossos. Os nomes de dados Polish e Base Layer são preservados; ambas as linhas mostram peso 1,00, e a camada Polish usa o modo Aditivo. Nenhuma consolidação de camadas foi executada. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 2a84ef06358c.](images/pt/12.11.1-animation-layers.png)

<a id="lipsync"></a>

### Sincronização labial

1. Abra **Rosto > Sincronização labial**.

2. Ative a sincronização labial.

3. Adicione uma camada de sincronização labial com **+**.

4. Selecione a camada.

5. Em **Áudio**, associe um arquivo **WAV**.

6. Selecione **Chaves de forma**, **Ossos** ou **Ambos** como alvo.

7. Selecione a malha ou armação de destino.

8. Configure **Conexões de chaves de forma** ou **Conexões do rig de ossos** para a biblioteca de visemas selecionada.

9. Verifique os nomes dos alvos nas entradas de conexão.

10. Verifique a antecipação, o deslocamento de quadros e o mecanismo de análise.

11. Clique em **Consolidar**.

12. Inspecione o movimento da boca.

Antes de **Consolidar novamente**, use **Bloquear chaves selecionadas** para preservar o trabalho manual selecionado.

**Prévia em tempo real/Consolidado** mostra o estado da camada. A saída por chaves de forma exige uma malha com chaves de forma conectadas. A saída por ossos exige uma camada de animação, uma armação e conexões válidas. **Preencher automaticamente** fornece entradas de conexão. **Capturas de visemas > Capturar** armazena uma pose personalizada.

Use o controle de estado para o fluxo de prévia ou de consolidação desejado.

A análise de amplitude não exige um executável externo de fonemas. A análise opcional pelo Rhubarb exige um **Caminho do Rhubarb** configurado. Antes de confiar na saída, leia os relatórios de uso do mecanismo de reserva e de camadas ausentes. Se existir uma faixa de alto-falante, a sobreposição de alto-falante mostra o áudio na Tabela de animação/Linha do tempo.

**Limpar**, na barra lateral, remove a saída automática e mantém o trabalho manual marcado. **Consolidar novamente** também mantém as substituições manuais. **Destacar chaves manuais** mostra as edições protegidas. Alterar o áudio marca a camada como desatualizada. Antes de consolidar novamente, resolva os problemas relatados de WAV, alvo e camada.

![Sincronização labial após a configuração inicial, com o painel inteiro até Caminho do Rhubarb. A configuração criou uma faixa SOUND AA_P12_face_lipsync_1 no canal 1 com manual-example.wav, no modo de chaves de forma e abertura básica da boca. A tabela contém zero indicações; a malha e as conexões permanecem sem atribuição. Não houve análise de áudio nem consolidação de movimentos da boca. As reticências nativas do caminho longo são preservadas. Candidata local Anim Assist 12.11.2 no Bforartists, distribuição oficial 5.2.3; versão informada pela API: 5.3.0 Alpha. Captura de 2026-11-20 (UTC). SHA-256 da imagem (prefixo): 9ac26bb40e3e.](images/pt/12.11.2-lipsync-setup.png)

<a id="troubleshooting-and-verification-limits"></a>

## Solução de problemas e limites da verificação

Se uma operação de chaves não fizer nada:

1. Verifique o editor ativo.

2. Verifique as chaves editáveis selecionadas e os canais visíveis.

3. Verifique os bloqueios, o proprietário e a Ação.

4. Inspecione os dados da Ação e os filtros do editor.

A visibilidade da barra de ferramentas, por si só, não comprova que a operação inseriu chaves. Inserir quadro-chave nativo continua sendo o fluxo normal de inserção de chaves em malhas/objetos.

Ao relatar um problema, inclua a versão do complemento, a compilação do Bforartists, o comando exato e uma pequena cena que reproduza o problema.

Se uma ação NLA estiver indisponível:

1. Verifique os bloqueios de trilhas e as exclusões por Silenciar/Solo.

2. Verifique se há uma Ação ausente, avaliação NLA desativada ou Tweak Mode ativo.

3. Antes de organizar clipes, clique em **Concluir edição**.

4. Para criar correções, leia a explicação sobre rigs/canais incompatíveis.

Após alterar a temporização ou consolidar:

1. Inspecione o movimento.

2. Se necessário, use Desfazer nativo.

3. Salve a cena.

4. Reabra-a antes de confiar no resultado.

Se as configurações de drivers estiverem indisponíveis, selecione um canal de driver desbloqueado para torná-lo ativo nativamente. Um driver bloqueado pode continuar visível para inspeção e desbloqueio. Se vários drivers selecionados não tiverem um alvo ativo claro, as ferramentas não escolhem um. As ações de edição de pontos exigem pontos de resposta selecionados.

As [notas da versão 12.11.1](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.11.1/RELEASE-NOTES.md) descrevem a correção do encaminhamento de Desfazer na Linha do tempo. A [verificação da versão 12.11.0](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.11.0/qualification.md) registra testes específicos de Controladores e observações com o ponteiro nativo no Bforartists 5.2.0. Eles abrangem escopo de canais, navegação nas configurações nativas e Desfazer/Refazer de modificadores. Os registros também abrangem o registro de leiautes e 11 cenários de regressão em editores de animação. Esses resultados vêm de testes anteriores. A atualização do manual não repetiu esses testes.

A [verificação da versão 12.10.0](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.10.0/qualification.md) abrange os conjuntos de ferramentas das etapas. A [verificação da versão 12.9.1](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.9.1/qualification.md) abrange as correções das abas de etapas. A [verificação da versão 12.8.0](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.8.0/qualification.md) registra 16 grupos de interação nativa, Desfazer/Refazer e recarregamento da área de trabalho. Também registra 98 registros de painéis e cinco regressões de leiaute da Linha do tempo. Suas evidências incluem inserção de chaves em malhas e capturas da barra lateral com 220, 280 e 360 px.

Esses testes não certificam todos os operadores, modificadores, rigs de produção ou compilações do aplicativo. As evidências antigas de controles deslizantes e sincronização labial continuam sendo históricas. A revisão da documentação de 20 de novembro verifica o código-fonte atual, os links e a apresentação do PDF. Ela não fornece certificação formal pelo dicionário STE.

**Configurar sincronização labial** da versão candidata 12.11.2 foi concluído no Bforartists oficial 5.2.3, baseado no Blender 5.3 Alpha. A operação criou uma faixa de áudio. A nova figura mostra a camada resultante antes da conexão de alvos e da consolidação. Ela não demonstra movimento de boca com consolidação.

Se a configuração informar **compilado sem suporte ao Audaspace**, use uma compilação do Bforartists com suporte a áudio. A configuração pode ser concluída sem criar sua faixa de áudio. A compilação personalizada fornecida, baseada no Blender 5.4 Alpha, produziu esse resultado.

Use as figuras **Tabela de animação**, **Editor gráfico** e **Driver selecionado** para localizar os resumos de escopo e seleção.

<a id="screenshot-sources-and-limits"></a>

## Fontes e limites das capturas de tela

O manual de origem em inglês mantém capturas históricas da Linha do tempo e das configurações da barra de ferramentas, capturas de driver selecionado da verificação da versão 12.11.0, visões gerais dos editores da verificação da versão 12.8.0 e capturas de faixas separadas da versão 12.5.0. Esta edição localizada substitui essas figuras por novas capturas nativas da versão candidata local e ainda não publicada 12.11.2. A legenda de cada figura informa o que a captura demonstra e os limites do que foi verificado; uma nova captura não repete nem amplia os testes das versões anteriores.

As capturas nativas da versão 12.11.1 fornecidas pelo usuário mostram escopos vazios. Elas documentam o leiaute visível. Elas não demonstram uma edição concluída:

- [Barra lateral de Controladores sem driver selecionado](../images/12.11.1-native-drivers-empty.png).
- [Barra lateral do Gráfico de Ações sem curvas editáveis no escopo](../images/12.11.1-native-action-graph.png).
