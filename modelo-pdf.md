# Análise da Estrutura dos PDFs de Orçamento PMCELL

## 1. ESTRUTURA DO CABEÇALHO (Padrão em todos os PDFs)

### 1.1 Informações da Empresa (Fixas)
- **Nome**: PMCELL São Paulo
- **Razão Social**: V. Zabin Tecnologia e Comercio Eireili
- **CNPJ**: 29.734.462/0003-86
- **I.E**: 130.745.005.110
- **Endereço**: Rua Comendador Abdo Schahin, 62

### 1.2 Informações do Orçamento
- **Número do Orçamento**: Sempre presente no formato "Orçamento Nº: XXXXX" (5 dígitos)
  - Exemplos: 30567, 30568, 30582, 30590, 30596

### 1.3 Informações do Cliente
- **Código do Cliente**: Formato 6 dígitos (ex: 001007, 000001, 000435, 001014)
- **Nome do Cliente**: Texto livre (pode ser nome completo ou razão social)
  - Exemplos: "ROSANA DE CASSIA SINEZIO", "CLIENTE ATACADO", "INFOCEL CELULARES ASSISTENCIA E SUPRIMENTOS LTDA", "ALI KHALIL FADEL"

### 1.4 Informações do Vendedor
- **Nome do Vendedor**: Sempre "NYCOLAS HENDRIGO MANCINI" nos exemplos analisados
- **Data**: Formato DD/MM/AA (ex: 22/10/25)

### 1.5 Outras Informações do Cabeçalho
- **Condição de Pagamento**: Campo presente mas vazio nos exemplos
- **Forma de Pagamento**: Campo presente mas vazio nos exemplos
- **Validade do Orçamento**: Formato "DD/MM/AA - X dia(s)" (ex: "22/10/25 - 0 dia(s)")

## 2. ESTRUTURA DA TABELA DE PRODUTOS

### 2.1 Colunas da Tabela
1. **Código** - Código interno do produto (5 dígitos com zeros à esquerda)
2. **Produto** - Descrição do produto
3. **Unid.** - Unidade (sempre "UN" nos exemplos)
4. **Quant.** - Quantidade (número inteiro)
5. **Valor** - Valor unitário (formato decimal com 2 casas)
6. **Total** - Valor total (quantidade × valor unitário)

### 2.2 Padrão de Formatação dos Produtos

Cada linha de produto segue o padrão:
```
[CÓDIGO] [DESCRIÇÃO] [UNID] [QUANTIDADE] [VALOR_UNITARIO] [VALOR_TOTAL]
```

**Exemplos de linhas reais:**
- `00010 FO11 --> FONE PMCELL UN 30 3,50 105,00`
- `00032 CB14 --> CABO PMCELL P2XP2 C UN 10 1,40 14,00`
- `00819 PELICULA 3D --> IP 12 PRO MAX UN 05 1,20 6,00`
- `01798 TPU --> SAMSUNG A32 4G UN 200 1,60 320,00`

### 2.3 Padrões Observados no Código do Produto
- **Formato**: 5 dígitos (00000 a 99999)
- **Exemplos**: 00010, 00032, 00255, 01306, 04672

### 2.4 Padrões Observados na Descrição do Produto
A descrição pode conter:
- Siglas de categorias seguidas de números (ex: FO11, CB14, SP42, CJ-42)
- Setas indicativas (-->, --->, -->>)
- Nome descritivo do produto
- Especificações técnicas (ex: "66W TC", "TIPO C", "LIGHTNING")
- Modelos de aparelhos (ex: "IP 12 PRO MAX", "SAM A16", "MOTO G35")

**Categorias identificadas:**
- FO = Fone
- CB = Cabo
- SP = Suporte
- CJ = Carregador/Suporte
- PELICULA 3D = Película 3D
- PRIVACIDADE 3D = Película de privacidade
- 3D = Película 3D (formato curto)
- TPU = Capa TPU
- PACK HIDROGEL = Pacote de películas

### 2.5 Padrão dos Valores Numéricos (CRÍTICO PARA PARSING)

**DESCOBERTA PRINCIPAL**: Os últimos 3 conjuntos de números em cada linha SEMPRE seguem a ordem:
1. **QUANTIDADE** (inteiro)
2. **VALOR UNITÁRIO** (decimal com vírgula, 2 casas)
3. **VALOR TOTAL** (decimal com vírgula, 2 casas)

**Regra Matemática para Validação:**
```
QUANTIDADE × VALOR_UNITARIO = VALOR_TOTAL
```

**Exemplos de validação matemática:**
- `30 × 3,50 = 105,00` ✓
- `10 × 1,40 = 14,00` ✓
- `05 × 1,20 = 6,00` ✓
- `200 × 0,85 = 170,00` ✓
- `571 × 1,60 = 913,60` ✓

### 2.6 Estratégia de Extração Recomendada

**Para cada linha de produto:**

1. **Extrair Código** (REGEX):
   - Primeiros 5 dígitos da linha
   - Padrão: `^\d{5}`

2. **Extrair os 3 últimos números** (REGEX):
   - Usar regex para capturar os 3 últimos grupos numéricos
   - Padrão sugerido: `(\d+)\s+(\d+,\d{2})\s+(\d+,\d{2})$`

3. **Validação Matemática**:
   - Converter valores para float
   - Verificar se: `quantidade * valor_unitario == valor_total` (com tolerância de ±0.01 para arredondamento)
   - Se validação falhar, tentar outros grupos numéricos ou sinalizar erro

4. **Extrair Nome do Produto** (REGEX):
   - Tudo entre o código e o campo "UN" (unidade)
   - Remover espaços extras no início e fim

## 3. RODAPÉ DO ORÇAMENTO

### 3.1 Totalizadores (Sempre presentes)
```
VALOR TOTAL    R$ [valor]
DESCONTO       R$ [valor]
VALOR A PAGAR  R$ [valor]
```

**Observação**: Nos exemplos analisados, o DESCONTO sempre foi R$ 0,00

### 3.2 Fórmula de Cálculo
```
VALOR_A_PAGAR = VALOR_TOTAL - DESCONTO
```

## 4. VARIAÇÕES OBSERVADAS

### 4.1 Quantidade de Produtos por Orçamento
- **Mínimo**: 1 produto (Orçamento 30567)
- **Máximo**: 40 produtos (Orçamento 30582)
- **Média**: ~15 produtos

### 4.2 Formato dos Valores
- **Valores unitários**: Variam de R$ 0,85 a R$ 600,00
- **Quantidades**: Variam de 1 a 600 unidades
- **Valores totais de orçamento**: Variam de R$ 105,00 a R$ 1.994,80

### 4.3 Casas Decimais
- Valores unitários e totais SEMPRE têm 2 casas decimais
- Separador decimal: vírgula (,)
- Separador de milhares: ponto (.) quando aplicável

## 5. CAMPOS PARA EXTRAÇÃO (Resumo)

### 5.1 Dados do Cabeçalho (Obrigatórios)
- ✓ Número do Orçamento
- ✓ Código do Cliente
- ✓ Nome do Cliente
- ✓ Nome do Vendedor
- ✓ Data do Orçamento

### 5.2 Dados dos Produtos (Para cada item)
- ✓ Código do Produto (5 dígitos)
- ✓ Descrição do Produto (texto livre)
- ✓ Quantidade (inteiro, extraído por validação matemática)
- ✓ Valor Unitário (decimal, extraído por validação matemática)
- ✓ Valor Total (decimal, extraído por validação matemática)

### 5.3 Dados do Rodapé
- ✓ Valor Total do Orçamento
- ✓ Desconto Aplicado
- ✓ Valor a Pagar

## 6. ALGORITMO DE PARSING RECOMENDADO

```python
# Pseudocódigo do algoritmo

1. Extrair texto do PDF
2. Identificar seção do cabeçalho (até linha com "Código Produto Unid...")
3. Extrair dados do cabeçalho usando regex específicos
4. Identificar seção de produtos (entre tabela e "VALOR TOTAL")
5. Para cada linha de produto:
   a. Extrair código (primeiros 5 dígitos)
   b. Extrair os 3 últimos números da linha
   c. Validar matematicamente: num1 * num2 == num3
   d. Se válido: num1=quantidade, num2=valor_unitário, num3=valor_total
   e. Se inválido: tentar outros padrões ou marcar para revisão manual
   f. Extrair descrição (texto entre código e "UN")
6. Extrair totalizadores do rodapé
7. Validar soma de todos os valores totais == VALOR TOTAL
```

## 7. CASOS ESPECIAIS IDENTIFICADOS

### 7.1 Produtos com Descrições Longas
- Exemplo: `INFOCEL CELULARES ASSISTENCIA E SUPRIMENTOS LTDA`
- Descrições podem ter mais de 50 caracteres

### 7.2 Produtos com Caracteres Especiais
- Setas: `-->`, `--->`, `-->>`
- Parênteses: `(1 - 2)`, `(50. UN)`
- Aspas: `11"`
- Barra: `/` (ex: "TYPE C / TYPE C")

### 7.3 Valores com Zeros à Esquerda
- Quantidades podem ter zeros à esquerda: `05`, `01`, `03`
- Devem ser tratados como inteiros normais

## 8. PRECISÃO DA VALIDAÇÃO MATEMÁTICA

**Taxa de Sucesso Esperada**: 100%

Todos os 78 produtos analisados nos 5 PDFs passaram na validação matemática:
- Quantidade × Valor Unitário = Valor Total (com precisão de 2 casas decimais)

**Tolerância recomendada**: ±0.01 (para lidar com arredondamentos)

## 9. LAYOUT VISUAL

```
┌─────────────────────────────────────────────────────────┐
│                    LOGO PMCELL                          │
│              Dados da Empresa (fixos)                   │
│                                                         │
│  Orçamento Nº: XXXXX                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Código: XXXXXX    Data: DD/MM/AA                 │  │
│  │ Cliente: NOME DO CLIENTE                         │  │
│  │ Vendedor: NOME DO VENDEDOR                       │  │
│  │ Condição/Forma/Validade                          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Código | Produto | Unid | Quant | Valor | Total │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ XXXXX  | DESC... | UN   | XX    | X,XX  | XX,XX │  │
│  │ ...                                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│                            VALOR TOTAL    R$ XXX,XX    │
│                            DESCONTO       R$ X,XX      │
│                            VALOR A PAGAR  R$ XXX,XX    │
│                                                         │
│                         Página 1                        │
└─────────────────────────────────────────────────────────┘
```

## 10. CONCLUSÕES E RECOMENDAÇÕES

### 10.1 Pontos Fortes do Formato
- ✓ Estrutura consistente entre todos os PDFs
- ✓ Validação matemática possível (quantidade × valor = total)
- ✓ Campos obrigatórios sempre presentes
- ✓ Formato numérico padronizado

### 10.2 Desafios de Parsing
- ⚠ Descrições de produtos são muito variadas (texto livre)
- ⚠ Uso de caracteres especiais nas descrições
- ⚠ Necessidade de OCR ou extração de texto precisa

### 10.3 Estratégia Recomendada
1. **Usar biblioteca de extração de texto de PDF** (ex: PyPDF2, pdfplumber, PyMuPDF)
2. **Aplicar regex para campos estruturados** (código, números)
3. **Usar validação matemática como garantia de precisão**
4. **Implementar fallback para casos especiais**
5. **Criar log de erros para revisão manual quando necessário**

---

**Arquivo gerado em**: 2025-10-24
**Análise baseada em**: 5 PDFs de orçamento (30567, 30568, 30582, 30590, 30596)
**Total de produtos analisados**: 78 itens
