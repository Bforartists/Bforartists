# O pipeline do CATS {#the-cats-pipeline}

[← Sumário](index.md)

**Leia isto antes de usar qualquer ferramenta do CATS pela primeira vez.**

As ferramentas do CATS oferecem um fluxo de preparação recomendado. Revise as fases nesta ordem. Pule as fases de que seu avatar não precisa. Antes de alterar dados da malha ou do rig, salve um ponto de restauração do arquivo. Inspecione cada resultado. As ferramentas continuam disponíveis quando uma fase anterior está incompleta.

---

## As seis fases, em ordem {#the-six-phases-in-order}

Pipeline Status, na aba CATS, lista as fases e marca cada uma quando ela é concluída:

1. **Fix Model** — Revise as opções de limpeza, como remover duplicatas e corrigir normais. Inspecione a malha após a operação.

2. **Material Atlas** — Combine os materiais do avatar em uma única folha de textura (opcional, para melhorar o desempenho).

    1. Mantenha **Preserve Backup Duplicate** ativado até revisar o resultado.

    2. Selecione **Analyze Materials**.

    3. Selecione as fontes.

    4. Selecione **Bake Checked Sources**.

    5. Revise o resultado.

    6. Use Accept ou Revert antes de outra consolidação.

    Consulte [Combinador de atlas de materiais](09-cats.md#material-atlas-combiner).

3. **Visemes** — Gere as 15 formas de boca para sincronização labial do VRChat a partir das três formas básicas (A, O, CH).

4. **Eye Tracking** — Configure o movimento dos olhos no VRChat com os ossos dos olhos do avatar.

5. **Pose to Shape Key** — Capture a combinação atual de chaves de forma da malha como uma nova chave. Esse botão não consolida a deformação dos ossos da armadura. Consulte o [fluxo nativo de pose de ossos](09-cats.md#save-a-bone-deformed-pose) para essa tarefa.

6. **Apply All Transforms** — Aplique posição, rotação e escala à malha e à armadura. Compare o resultado antes de exportar.

---

## Pipeline Status e Operation Ledger {#pipeline-status-and-the-operation-ledger}

Pipeline Status mostra uma linha por fase. Quando uma fase termina, sua linha mostra uma marca de verificação. A cena armazena esse estado no arquivo.

Operation Ledger lista cada operação do CATS, com as mais recentes ao final, incluindo horário e resultado. Changed significa que a operação alterou o modelo. Clean significa que nenhuma alteração foi necessária. Failed significa que a operação falhou. **Copy** copia o registro para a área de transferência para solicitações de suporte. **Clear** esvazia o registro.

A ordem é uma recomendação. Se uma fase anterior estiver incompleta, as ferramentas ainda executam, com um aviso como “Run Fix Model first for best results” (execute Fix Model primeiro para obter melhores resultados). Revise o aviso antes de continuar.

Descrição da imagem do original em inglês (imagem omitida): Pipeline Status lista as seis fases na ordem recomendada.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Pipeline Status lista as seis fases na ordem recomendada.*

Descrição da imagem do original em inglês (imagem omitida): Operation Ledger antes de existir qualquer entrada. Copy e Clear atuam sobre as entradas registradas.

*Painel nativo em janela flutuante, BoneCraft 9.2.18. Operation Ledger antes de existir qualquer entrada. Copy e Clear atuam sobre as entradas registradas.*

---

## Por que esta ordem {#why-this-order}

Esta ordem facilita revisar um tipo de alteração por vez:

- **Revise primeiro a limpeza.** Fix Model pode alterar a geometria ou remover dados, dependendo das opções. Verifique a malha e suas chaves de forma existentes antes de gerar mais dados.

- **Revise as formas da boca e depois os olhos.** Teste os visemas gerados ou mapeados. Eye Auto-Detect pesquisa os nomes dos ossos. Verifique as atribuições Left Eye e Right Eye separadamente da orientação dos ossos e das restrições.

- **Revise depois a captura de expressões.** Pose to Shape Key captura uma combinação de chaves de forma, não a deformação dos ossos.

    1. Redefina os valores das chaves originais para 0.

    2. Teste a nova chave com valor 1.

    Para salvar uma pose deformada por ossos, use o fluxo nativo vinculado acima.

- **Revise as transformações antes de exportar.** Aplicar transformações altera os dados dos objetos e redefine seus canais de transformação. As ferramentas anteriores continuam disponíveis. Compare o resultado e as configurações de exportação. Para restaurar o estado anterior, use Desfazer ou um ponto de restauração salvo.

---

## Antes de pular uma fase {#before-skipping-a-phase}

**Pular Fix Model:**
Inspecione a geometria importada, as normais, os pesos, os modificadores e as chaves de forma existentes. Selecione as operações de limpeza de que seu avatar precisa. Verifique separadamente os problemas das formas da boca e do movimento dos olhos. Uma fase desmarcada no pipeline, por si só, não identifica a causa desses problemas.

**Pular Visemes:**
Sem visemas gerados ou mapeados, seu avatar não tem sincronização labial. Se já existirem chaves de forma de visemas, mapeie-as em VRChat Viseme Mapping (Guia 8). Não gere substitutas desnecessariamente. Pipeline Status deixa então Visemes desmarcado. Esse comportamento é esperado.

**Pular Eye Tracking:**
Seu avatar não move os olhos no VRChat e olha fixamente para a frente. Isso é aceitável quando ele não tem ossos dos olhos.

**Pular Pose to Shape:**
Opcional: pule esta fase se não precisar de uma captura da combinação atual de chaves de forma. As expressões existentes podem ser revisadas e usadas sem criar outra chave.

Próximo: [Ferramentas de rig](05-rig-tools.md)
