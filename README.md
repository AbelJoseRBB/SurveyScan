# SurveyScan

O **SurveyScan** é uma ferramenta desenvolvida em Python para automatizar a leitura e organização de dados coletados por meio de formulários físicos digitalizados.

O projeto foi desenvolvido para auxiliar no processamento de questionários de uma pesquisa acadêmica, reduzindo a necessidade de transcrição manual das respostas.

A partir dos questionários digitalizados em PDF, o sistema realiza o alinhamento das páginas, identifica respostas objetivas, reconhece campos numéricos e textuais manuscritos e organiza os resultados em uma planilha Excel.

Como o reconhecimento automático pode apresentar erros, o SurveyScan também possui um fluxo de revisão manual que permite identificar, corrigir e armazenar resultados considerados duvidosos.

## Principais funcionalidades

- Processamento em lote de questionários em PDF;
- Alinhamento automático das páginas com um formulário de referência;
- Reconhecimento de questões objetivas;
- Detecção de respostas ambíguas;
- Reconhecimento de campos numéricos manuscritos;
- Reconhecimento de campos textuais manuscritos;
- Comparação de palavras reconhecidas com vocabulários conhecidos;
- Identificação automática de campos que precisam de revisão;
- Geração de recortes dos campos problemáticos;
- Exportação dos resultados para Excel;
- Correção manual de respostas;
- Persistência das correções entre diferentes execuções;
- Processamento independente dos questionários, evitando que um arquivo inválido interrompa todo o lote.

## Pipeline de processamento

O processamento de cada questionário segue, de forma simplificada, o seguinte fluxo:

```text
Questionário em PDF
        ↓
Conversão das páginas em imagens
        ↓
Alinhamento com o formulário de referência
        ↓
┌─────────────────────────────────────┐
│       Reconhecimento de dados       │
├─────────────────────────────────────┤
│ Questões objetivas                  │
│ Campos numéricos manuscritos        │
│ Campos textuais manuscritos         │
└─────────────────────────────────────┘
        ↓
Validação dos resultados
        ↓
Campos duvidosos → Revisão manual
        ↓
Exportação para Excel
```

## Processamento das imagens

Os questionários são inicialmente convertidos de PDF para imagens utilizando **PyMuPDF**.

Como pequenas diferenças de posição, rotação ou digitalização poderiam deslocar as regiões analisadas, cada página é alinhada com um formulário vazio utilizado como referência.

O alinhamento é realizado utilizando recursos do **OpenCV**, permitindo que as regiões configuradas para leitura permaneçam consistentes entre diferentes questionários digitalizados.

## Reconhecimento das respostas

O SurveyScan utiliza estratégias diferentes de acordo com o tipo de informação presente no formulário.

### Questões objetivas

As alternativas das questões objetivas são analisadas em regiões previamente definidas.

O sistema pode identificar:

- uma alternativa marcada;
- ausência de marcação;
- múltiplas alternativas marcadas.

Quando mais de uma alternativa é detectada, a resposta é classificada como `AMBÍGUA` e pode ser destacada para revisão.

### Campos numéricos

Campos como:

- número do questionário;
- idade;
- renda;
- quantidade de filhos;
- data da coleta;

são processados utilizando modelos de classificação de dígitos.

Atualmente são utilizados dois modelos:

- **SVM (Support Vector Machine)**
- **KNN (K-Nearest Neighbors)**

Os dígitos são segmentados e classificados pelos modelos, permitindo reconstruir os valores presentes nos campos numéricos.

A combinação dos resultados também auxilia na identificação de casos em que o reconhecimento deve ser revisado manualmente.

### Campos textuais manuscritos

Para campos de texto manuscrito, o SurveyScan utiliza uma combinação de diferentes ferramentas:

- **TrOCR Large Handwritten** como principal modelo de reconhecimento;
- **EasyOCR** como reconhecimento auxiliar;
- **RapidFuzz** para comparação com vocabulários conhecidos.

O TrOCR é responsável pela principal tentativa de transcrição do texto manuscrito.

O EasyOCR fornece uma segunda leitura que pode auxiliar na análise de casos duvidosos.

Para campos cujo conjunto de respostas pode ser parcialmente conhecido, como ocupações e religiões, o RapidFuzz compara o texto reconhecido com palavras presentes em vocabulários previamente definidos.

Quando uma correspondência suficientemente próxima é encontrada, o sistema pode utilizar a sugestão automaticamente. Caso contrário, o campo é encaminhado para revisão.

## Sistema de revisão

Um dos objetivos do SurveyScan é evitar que resultados incertos sejam aceitos silenciosamente como corretos.

Quando o sistema identifica um campo que necessita de verificação, o resultado é encaminhado para a aba `Revisao` da planilha.

Cada pendência apresenta:

| Campo | Descrição |
|---|---|
| ID | Identificador interno do questionário |
| Campo | Campo que apresentou problema |
| Valor lido | Resultado obtido automaticamente |
| Imagem | Recorte da região original do formulário |
| Correção | Espaço para correção manual |

A imagem da região problemática é inserida diretamente na planilha para facilitar a comparação entre o valor reconhecido e a escrita original.

### Correção manual

Após a revisão, o valor correto pode ser informado na coluna `Correção`.

Na próxima execução do SurveyScan, essa correção é recuperada e aplicada automaticamente aos dados finais.

O campo corrigido também deixa de aparecer como uma pendência de revisão.

### Persistência das correções

As correções realizadas são armazenadas na aba `Correcoes`.

Isso permite que uma correção manual continue válida mesmo após novas execuções do sistema.

Dessa forma:

- campos já corrigidos não retornam para a fila de revisão;
- as correções continuam sendo aplicadas aos resultados;
- campos corrigidos deixam de ser destacados como pendentes;
- novas pendências podem ser adicionadas sem perder correções anteriores.

## Identificação dos questionários

Cada questionário processado recebe um identificador baseado no conteúdo do próprio arquivo.

Esse identificador permite associar de forma consistente:

- dados reconhecidos;
- imagens de revisão;
- correções manuais;
- execuções posteriores do sistema.

Assim, as correções não dependem apenas do nome do arquivo ou da ordem em que os questionários são processados.

## Planilha gerada

O resultado do processamento é organizado em um arquivo Excel contendo três abas principais.

### `Questionarios`

Contém os dados consolidados dos questionários.

Entre os campos exportados estão:

- ID;
- número do questionário;
- data da coleta;
- idade;
- sexo;
- cor;
- estado civil;
- religião;
- ocupação;
- renda mensal;
- número de filhos;
- período acadêmico;
- respostas das questões Q10 a Q13.

Campos que ainda necessitam de revisão são destacados visualmente.

### `Revisao`

Funciona como uma fila de pendências.

Somente resultados que ainda precisam de intervenção manual permanecem nessa aba.

Quando necessário, o recorte correspondente do formulário é exibido junto à pendência.

### `Correcoes`

Mantém o histórico das correções manuais utilizadas pelo sistema.

Essas informações são carregadas nas próximas execuções para evitar que uma pendência já resolvida precise ser analisada novamente.

## Estrutura do projeto

```text
SurveyScan/
├── formularios/
│   ├── FormsVazio.pdf
│   └── ...
│
├── models/
│   ├── digit_knn.pkl
│   └── digit_svm.pkl
│
├── output/
│   ├── revisao/
│   └── resultado.xlsx
│
├── src/
│   ├── readers/
│   │   ├── answer_reader.py
│   │   ├── easyocr_reader.py
│   │   ├── fuzz_matcher.py
│   │   ├── handwriting_comparison.py
│   │   ├── handwriting_reader.py
│   │   ├── text_reader.py
│   │   └── __init__.py
│   │
│   ├── config.py
│   ├── excel_exporter.py
│   ├── image_processor.py
│   └── main.py
│
├── tools/
│   ├── coordinate_picker.py
│   ├── test_handwriting_models.py
│   ├── test_numeric_models.py
│   ├── train_digit_model.py
│   └── train_digit_svm.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

## Organização do código

### `src/main.py`

Responsável por coordenar o processamento em lote dos questionários.

O fluxo principal carrega os modelos necessários, prepara o formulário de referência, processa cada PDF individualmente e encaminha os resultados para exportação.

### `src/image_processor.py`

Contém as operações relacionadas ao processamento das páginas, incluindo:

- conversão de PDF para imagem;
- conversão para escala de cinza;
- preparação do formulário de referência;
- alinhamento das páginas utilizando características visuais.

### `src/readers/`

Agrupa os diferentes mecanismos de reconhecimento utilizados pelo sistema.

Os leitores são separados de acordo com suas responsabilidades, incluindo questões objetivas, números e textos manuscritos.

### `src/excel_exporter.py`

Responsável pela organização dos resultados e geração da planilha final.

Também implementa o fluxo de revisão, persistência das correções, formatação das planilhas, destaque de pendências e inserção das imagens de revisão.

### `src/config.py`

Centraliza configurações utilizadas durante o processamento, incluindo diretórios e regiões do formulário analisadas pelo sistema.

### `models/`

Armazena os modelos treinados utilizados para classificação dos dígitos manuscritos.

### `tools/`

Contém ferramentas e scripts auxiliares utilizados durante o desenvolvimento, treinamento e avaliação das estratégias de reconhecimento.

## Ferramentas de desenvolvimento

### Coordinate Picker

```text
tools/coordinate_picker.py
```

Ferramenta utilizada durante o desenvolvimento para identificar as coordenadas das regiões de interesse do formulário.

### Benchmark de manuscritos

```text
tools/test_handwriting_models.py
```

Utilizado para avaliar estratégias de reconhecimento dos campos textuais manuscritos.

### Benchmark de campos numéricos

```text
tools/test_numeric_models.py
```

Utilizado para comparar estratégias de reconhecimento dos campos numéricos.

### Treinamento dos modelos

```text
tools/train_digit_model.py
tools/train_digit_svm.py
```

Scripts utilizados durante o treinamento dos modelos KNN e SVM responsáveis pela classificação dos dígitos.

## Tecnologias utilizadas

O projeto utiliza principalmente:

- **Python**
- **OpenCV** — processamento e alinhamento das imagens;
- **PyMuPDF** — conversão dos documentos PDF;
- **NumPy** — manipulação dos dados de imagem;
- **Pandas** — organização dos resultados;
- **OpenPyXL** — geração, formatação e manipulação do Excel;
- **Scikit-learn** — modelos SVM e KNN;
- **PyTorch** — execução dos modelos de deep learning;
- **Hugging Face Transformers** — utilização do TrOCR;
- **TrOCR** — reconhecimento de escrita manuscrita;
- **EasyOCR** — OCR auxiliar;
- **RapidFuzz** — comparação aproximada de textos.

## Execução

O SurveyScan foi desenvolvido especificamente para o modelo de questionário utilizado nesta pesquisa. As regiões de leitura, campos e regras de reconhecimento estão configuradas de acordo com sua estrutura.

Com o ambiente configurado e as dependências instaladas, o processamento é iniciado através de:

```powershell
python src/main.py
```

Os questionários utilizados pelo projeto são armazenados em:

```text
formularios/
```

e os resultados são gerados em:

```text
output/
```

> Na primeira execução, alguns modelos utilizados pelo reconhecimento podem precisar ser baixados automaticamente.

## Dependências

As dependências necessárias estão disponíveis em:

```text
requirements.txt
```

Para instalar:

```powershell
pip install -r requirements.txt
```

Entre as principais dependências estão OpenCV, PyMuPDF, Pandas, OpenPyXL, Scikit-learn, PyTorch, Transformers, EasyOCR e RapidFuzz.

## Limitações atuais

O reconhecimento automático pode ser afetado por fatores como:

- qualidade da digitalização;
- desalinhamento significativo das páginas;
- legibilidade da escrita;
- rasuras;
- marcações muito fracas;
- preenchimento fora das regiões esperadas;
- diferenças significativas em relação ao layout utilizado no desenvolvimento.

Por esse motivo, o SurveyScan não considera que todo resultado produzido pelos modelos esteja necessariamente correto. O sistema utiliza o fluxo de revisão manual para permitir a verificação dos casos considerados duvidosos.

Os critérios atuais foram desenvolvidos e testados utilizando formulários preenchidos para desenvolvimento. O comportamento com o conjunto completo de questionários reais ainda deverá ser avaliado.

## Status do projeto

O pipeline principal do SurveyScan encontra-se funcional, incluindo:

- processamento em lote;
- alinhamento dos formulários;
- reconhecimento das questões objetivas;
- reconhecimento dos campos numéricos;
- reconhecimento de texto manuscrito;
- identificação de resultados duvidosos;
- geração da planilha Excel;
- revisão manual;
- persistência das correções.

A próxima etapa do projeto é avaliar o sistema com o conjunto de questionários reais da pesquisa e, a partir dos resultados obtidos, realizar ajustes nos critérios de reconhecimento quando necessário.