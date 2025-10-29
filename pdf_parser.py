"""
Parser de Orçamentos PDF com Validação Matemática Determinística

Extrai informações de orçamentos PDF usando regex e validação matemática
para garantir 100% de acurácia na identificação de produtos e valores.

Autor: Nycolas Mancini
Data: 2025-10-29
"""

import re
import PyPDF2
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Produto:
    """Representa um produto extraído do orçamento"""
    codigo: str
    descricao: str
    unidade: str
    quantidade: Decimal
    valor_unitario: Decimal
    valor_total: Decimal
    linha_original: str
    validacao_matematica: bool


@dataclass
class Orcamento:
    """Representa um orçamento completo"""
    numero: str
    codigo_cliente: str
    nome_cliente: str
    vendedor: str
    data: str
    valor_total: Decimal
    produtos: List[Produto]
    condicao_pagamento: Optional[str] = None
    forma_pagamento: Optional[str] = None


class PDFParser:
    """Parser principal de orçamentos PDF"""

    # Regex para captura de código de produto (5 dígitos)
    REGEX_CODIGO = r'(\d{5})'

    # Regex para linha completa de produto
    # Captura: código + tudo até encontrar "UN" + sequência numérica
    REGEX_PRODUTO = r'(\d{5})\s+(.+?)\s+(UN)\s+([\d\s,\.]+)'

    # Tolerância para validação matemática (0.01 = 1 centavo)
    TOLERANCIA_MATEMATICA = Decimal('0.01')

    def __init__(self, pdf_path: str):
        """
        Inicializa o parser com o caminho do PDF

        Args:
            pdf_path: Caminho completo para o arquivo PDF
        """
        self.pdf_path = pdf_path
        self.texto_completo = ""
        self.orcamento: Optional[Orcamento] = None

    def extrair_texto(self) -> str:
        """
        Extrai todo o texto do PDF

        Returns:
            Texto completo do PDF
        """
        texto = []

        with open(self.pdf_path, 'rb') as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)

            for pagina in leitor.pages:
                texto.append(pagina.extract_text())

        self.texto_completo = '\n'.join(texto)
        return self.texto_completo

    @staticmethod
    def converter_valor_brasileiro(valor_str: str) -> Decimal:
        """
        Converte string de valor brasileiro para Decimal

        Args:
            valor_str: String com valor (ex: "1.405,00" ou "270,00")

        Returns:
            Valor como Decimal
        """
        # Remove espaços
        valor_str = valor_str.strip()

        # Remove pontos de milhar e substitui vírgula por ponto
        valor_str = valor_str.replace('.', '').replace(',', '.')

        return Decimal(valor_str)

    @staticmethod
    def validar_matematica(quant: Decimal, unit: Decimal, total: Decimal,
                          tolerancia: Decimal) -> bool:
        """
        Valida se a equação matemática está correta: quant × unit = total

        Args:
            quant: Quantidade
            unit: Valor unitário
            total: Valor total
            tolerancia: Tolerância aceita (ex: 0.01)

        Returns:
            True se a equação está correta dentro da tolerância
        """
        resultado_esperado = quant * unit
        diferenca = abs(resultado_esperado - total)

        return diferenca <= tolerancia

    def extrair_numeros_linha(self, texto: str) -> List[Decimal]:
        """
        Extrai todos os números de uma linha de texto

        Args:
            texto: Texto da linha

        Returns:
            Lista de números como Decimal
        """
        # Regex para capturar números com vírgula decimal
        # Aceita: 300, 0,90, 270,00, 1405,00
        regex_numero = r'\d+(?:,\d+)?'

        numeros_str = re.findall(regex_numero, texto)
        numeros = [self.converter_valor_brasileiro(n) for n in numeros_str]

        return numeros

    def encontrar_valores_deterministicos(self, texto_linha: str) -> Optional[Tuple[Decimal, Decimal, Decimal, int]]:
        """
        Encontra quantidade, valor unitário e valor total usando validação matemática

        NOVA ESTRATÉGIA: Busca de trás para frente (reversed)
        Os valores corretos do produto são sempre os 3 ÚLTIMOS números que satisfazem a equação.
        Números no meio da descrição (como "27 MODELOS") podem gerar falsos positivos.

        Args:
            texto_linha: Linha completa do produto

        Returns:
            Tupla (quantidade, valor_unit, valor_total, índice_início) ou None
        """
        numeros = self.extrair_numeros_linha(texto_linha)

        # Precisa de pelo menos 3 números
        if len(numeros) < 3:
            return None

        # Testa todas as janelas de 3 números consecutivos DE TRÁS PARA FRENTE
        # Isso garante que pegamos os valores reais do produto, não números da descrição
        for i in range(len(numeros) - 3, -1, -1):  # De trás para frente
            quant = numeros[i]
            unit = numeros[i + 1]
            total = numeros[i + 2]

            # Valida a equação matemática
            if self.validar_matematica(quant, unit, total, self.TOLERANCIA_MATEMATICA):
                return (quant, unit, total, i)

        return None

    def extrair_descricao_produto(self, texto_completo: str, codigo: str,
                                   numeros_linha: List[Decimal], idx_inicio_validacao: int) -> str:
        """
        Extrai a descrição do produto

        Descrição = tudo entre o código e o início dos 3 ÚLTIMOS números validados

        Nova estratégia: Remove os 3 últimos números (quant, unit, total) do final
        para preservar números que fazem parte da descrição

        Args:
            texto_completo: Linha completa do produto
            codigo: Código do produto (5 dígitos)
            numeros_linha: Lista de todos os números extraídos da linha
            idx_inicio_validacao: Índice onde começa a sequência validada (quant, unit, total)

        Returns:
            Descrição limpa do produto
        """
        # Remove o código do início
        texto_sem_codigo = texto_completo.replace(codigo, '', 1).strip()

        # Pega os 3 valores validados (quant, unit, total)
        valores_validados = numeros_linha[idx_inicio_validacao:idx_inicio_validacao + 3]

        # Remove os 3 valores do final (em ordem reversa: total, unit, quant)
        for valor in reversed(valores_validados):
            # Formata o número para buscar no texto (com vírgula brasileira)
            valor_str = str(valor).replace('.', ',')

            # Remove a ÚLTIMA ocorrência desse valor (rfind)
            idx = texto_sem_codigo.rfind(valor_str)
            if idx != -1:
                texto_sem_codigo = texto_sem_codigo[:idx].strip()

        return texto_sem_codigo

    def processar_linha_produto(self, linha: str) -> Optional[Produto]:
        """
        Processa uma linha do PDF e extrai o produto

        Nova estratégia: Usa " UN" isolado (com espaço) como marcador final
        Estrutura: [Código] [Descrição (pode conter "50UN")] [quant] [valor_unit] [valor_total] UN

        O "UN" final é isolado (com espaço antes) e marca o fim da linha de produto.
        "UN" dentro da descrição (como "50UN CADA") não deve ser considerado marcador.

        Args:
            linha: Linha de texto do PDF

        Returns:
            Objeto Produto ou None se não for uma linha válida
        """
        # Busca código de 5 dígitos
        match_codigo = re.search(self.REGEX_CODIGO, linha)

        if not match_codigo:
            return None

        codigo = match_codigo.group(1)

        # Verifica se tem " UN" isolado no final (com espaço antes)
        # Usa rfind para pegar a ÚLTIMA ocorrência de " UN"
        idx_un_final = linha.rfind(' UN')

        if idx_un_final == -1:
            return None

        # Remove a parte após " UN" (inclusive " UN")
        # Estrutura: [Código] [Descrição] [valores] → tudo até o " UN" final
        linha_sem_marcador = linha[:idx_un_final].strip()

        # Encontra valores usando validação matemática em toda a linha (sem o marcador)
        resultado = self.encontrar_valores_deterministicos(linha_sem_marcador)

        if not resultado:
            return None

        quant, unit, total, idx_inicio = resultado

        # Extrai descrição: remove código e os 3 valores validados
        numeros_linha = self.extrair_numeros_linha(linha_sem_marcador)

        descricao = self.extrair_descricao_produto(linha_sem_marcador, codigo, numeros_linha, idx_inicio)

        return Produto(
            codigo=codigo,
            descricao=descricao,
            unidade='UN',
            quantidade=quant,
            valor_unitario=unit,
            valor_total=total,
            linha_original=linha,
            validacao_matematica=True
        )

    def extrair_header(self) -> Dict[str, str]:
        """
        Extrai informações do header do orçamento

        Returns:
            Dicionário com dados do header
        """
        header = {}

        linhas = self.texto_completo.split('\n')

        # Código do cliente (linha: "Cliente:002633")
        for linha in linhas:
            if 'Cliente:' in linha:
                match = re.search(r'Cliente:(\d+)', linha)
                if match:
                    header['codigo_cliente'] = match.group(1)
                break

        # Nome do cliente (próxima linha após Cliente:)
        # Formato 1: "20.517.107 NOME COMPLETO" (com número CNPJ/CPF)
        # Formato 2: "NOME COMPLETO" (sem número)
        for i, linha in enumerate(linhas):
            if 'Cliente:' in linha and i + 1 < len(linhas):
                proxima_linha = linhas[i + 1]
                # Torna o número CNPJ/CPF opcional com (?: ... )?
                match = re.search(r'(?:[\d\.]+ )?(.+)', proxima_linha)
                if match:
                    header['nome_cliente'] = match.group(1).strip()
                break

        # Vendedor e Data (linha: "NYCOLAS HENDRIGO MANCINI27/10/25Orçamento Nº:")
        for linha in linhas:
            # Procura por linha que contém nome em maiúsculas seguido de data
            match = re.search(r'([A-Z][A-Z\s]+?)(\d{2}/\d{2}/\d{2,4})', linha)
            if match and len(match.group(1).strip()) > 5:  # Nome deve ter mais de 5 caracteres
                # Verifica se não é uma linha de cabeçalho
                if 'Vendedor:' not in linha or 'Data:' in linha:
                    header['vendedor'] = match.group(1).strip()
                    header['data'] = match.group(2)
                    break

        # Número do orçamento (linha isolada com 5 dígitos, geralmente após empresa)
        for i, linha in enumerate(linhas):
            linha_stripped = linha.strip()
            # Procura por linha que seja apenas 5 dígitos (número do orçamento)
            if re.fullmatch(r'\d{5}', linha_stripped):
                # Verifica se não é um código de produto (não deve ter "UN" na próxima linha)
                if i + 1 < len(linhas) and 'Código Produto' not in linhas[i]:
                    header['numero'] = linha_stripped
                    break

        # Valor total (formato: "VALOR TOTAL R$ 1.405,00" ou "VALOR A PAGAR R$ 1.405,00")
        # Procura na lista de linhas para evitar capturar números de produtos
        for linha in linhas:
            if 'VALOR TOTAL' in linha.upper() or 'VALOR A PAGAR' in linha.upper():
                # Captura valor após R$
                match = re.search(r'R\$\s*([\d\.,]+)', linha)
                if match:
                    header['valor_total'] = match.group(1)
                    break

        # Condição de pagamento
        match = re.search(r'Condição\s+de\s+Pagto:\s*([^\n]+)', self.texto_completo)
        if match:
            header['condicao_pagamento'] = match.group(1).strip()

        # Forma de pagamento
        match = re.search(r'Forma\s+de\s+Pagto:\s*([^\n]+)', self.texto_completo)
        if match:
            header['forma_pagamento'] = match.group(1).strip()

        return header

    def parse(self) -> Orcamento:
        """
        Executa o parsing completo do PDF

        Returns:
            Objeto Orcamento com todos os dados extraídos
        """
        # Extrai texto do PDF
        self.extrair_texto()

        # Extrai header
        header = self.extrair_header()

        # Extrai produtos linha por linha
        produtos = []
        linhas = self.texto_completo.split('\n')

        for linha in linhas:
            produto = self.processar_linha_produto(linha)
            if produto:
                produtos.append(produto)

        # Cria objeto Orcamento
        self.orcamento = Orcamento(
            numero=header.get('numero', ''),
            codigo_cliente=header.get('codigo_cliente', ''),
            nome_cliente=header.get('nome_cliente', ''),
            vendedor=header.get('vendedor', ''),
            data=header.get('data', ''),
            valor_total=self.converter_valor_brasileiro(header.get('valor_total', '0')),
            produtos=produtos,
            condicao_pagamento=header.get('condicao_pagamento'),
            forma_pagamento=header.get('forma_pagamento')
        )

        return self.orcamento

    def validar_integridade(self) -> bool:
        """
        Valida a integridade do orçamento extraído

        Verifica se:
        - Soma dos produtos = valor total do orçamento
        - Todos os produtos passaram na validação matemática

        Returns:
            True se o orçamento está íntegro
        """
        if not self.orcamento:
            return False

        # Verifica se todos os produtos passaram na validação
        for produto in self.orcamento.produtos:
            if not produto.validacao_matematica:
                return False

        # Soma total dos produtos
        soma_produtos = sum(p.valor_total for p in self.orcamento.produtos)

        # Compara com valor total do orçamento
        diferenca = abs(soma_produtos - self.orcamento.valor_total)

        return diferenca <= self.TOLERANCIA_MATEMATICA

    def gerar_relatorio(self) -> str:
        """
        Gera relatório textual do parsing

        Returns:
            String com relatório formatado
        """
        if not self.orcamento:
            return "Nenhum orçamento processado"

        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append(f"ORÇAMENTO Nº {self.orcamento.numero}")
        relatorio.append("=" * 80)
        relatorio.append(f"Cliente: {self.orcamento.codigo_cliente} - {self.orcamento.nome_cliente}")
        relatorio.append(f"Vendedor: {self.orcamento.vendedor}")
        relatorio.append(f"Data: {self.orcamento.data}")
        relatorio.append(f"Valor Total: R$ {self.orcamento.valor_total}")
        relatorio.append("")
        relatorio.append(f"Total de produtos: {len(self.orcamento.produtos)}")
        relatorio.append("")
        relatorio.append("-" * 80)
        relatorio.append("PRODUTOS EXTRAÍDOS:")
        relatorio.append("-" * 80)

        for i, produto in enumerate(self.orcamento.produtos, 1):
            relatorio.append(f"\n{i}. Código: {produto.codigo}")
            relatorio.append(f"   Descrição: {produto.descricao}")
            relatorio.append(f"   Quantidade: {produto.quantidade}")
            relatorio.append(f"   Valor Unit.: R$ {produto.valor_unitario}")
            relatorio.append(f"   Valor Total: R$ {produto.valor_total}")
            relatorio.append(f"   Validação: {'✓ OK' if produto.validacao_matematica else '✗ FALHOU'}")

        relatorio.append("")
        relatorio.append("-" * 80)
        relatorio.append(f"VALIDAÇÃO DE INTEGRIDADE: {'✓ PASSOU' if self.validar_integridade() else '✗ FALHOU'}")
        relatorio.append("-" * 80)

        return '\n'.join(relatorio)


if __name__ == '__main__':
    # Teste com o primeiro orçamento
    pdf_path = '/Users/nycolasmancini/Documents/Orcamento - 30703 - Marcio - R$ 1405,00.pdf'

    print("Iniciando parsing do orçamento...")
    print(f"Arquivo: {pdf_path}")
    print()

    parser = PDFParser(pdf_path)
    orcamento = parser.parse()

    print(parser.gerar_relatorio())
