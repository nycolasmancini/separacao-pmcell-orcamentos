# -*- coding: utf-8 -*-
"""
Parser de PDFs de orçamento PMCELL.

Este módulo contém a classe PDFParser responsável por extrair
texto bruto de arquivos PDF de orçamentos usando a biblioteca pdfplumber.

Example:
    >>> from core.infrastructure.pdf import PDFParser
    >>> parser = PDFParser()
    >>> texto = parser.extrair_texto("/caminho/para/orcamento.pdf")
    >>> print(texto[:100])
    'Orçamento Nº: 30567...'
"""

import os
import re
import logging
import pdfplumber
from typing import List, Optional
from decimal import Decimal

from .exceptions import InvalidPDFError, PDFExtractionError
from core.application.dtos.orcamento_dtos import OrcamentoHeaderDTO, ProdutoDTO


# Configurar logger
logger = logging.getLogger(__name__)


# Constantes
EXTENSAO_PDF = '.pdf'
MENSAGEM_ARQUIVO_NAO_ENCONTRADO = "Arquivo não encontrado: {}"
MENSAGEM_ARQUIVO_NAO_PDF = "Arquivo não é um PDF válido: {}"
MENSAGEM_PDF_CORROMPIDO = "Arquivo PDF está corrompido ou inválido: {}"
MENSAGEM_ERRO_EXTRACAO = "Erro ao extrair texto do PDF: {}"


class PDFParser:
    """
    Parser para extração de texto de PDFs de orçamento PMCELL.

    Esta classe utiliza pdfplumber para extrair texto bruto de arquivos PDF,
    preservando a formatação original (quebras de linha, espaços, caracteres especiais).

    O parser realiza as seguintes validações:
    - Verifica se o arquivo existe
    - Verifica se o arquivo possui extensão .pdf
    - Trata PDFs corrompidos ou inválidos
    - Loga todas as operações (info, warning, error)

    Attributes:
        Nenhum atributo de instância.

    Examples:
        >>> parser = PDFParser()
        >>> texto = parser.extrair_texto("orcamento_30567.pdf")
        >>> "Orçamento Nº" in texto
        True

        >>> parser.extrair_texto("arquivo.txt")
        InvalidPDFError: Arquivo não é um PDF válido: arquivo.txt
    """

    def extrair_texto(self, pdf_path: str) -> str:
        """
        Extrai texto bruto de um arquivo PDF.

        Este método abre o PDF usando pdfplumber, extrai o texto de todas
        as páginas e retorna o texto completo como uma string, preservando
        a formatação original (quebras de linha, espaços múltiplos, etc).

        Args:
            pdf_path (str): Caminho completo do arquivo PDF.

        Returns:
            str: Texto extraído do PDF. String vazia se o PDF não contiver
                texto ou se todas as páginas estiverem vazias.

        Raises:
            FileNotFoundError: Se o arquivo não existir no caminho especificado.
            InvalidPDFError: Se o arquivo não for um PDF válido (extensão incorreta
                ou PDF corrompido).
            PDFExtractionError: Se ocorrer erro durante a extração (ex: permissões,
                PDF protegido por senha, etc).

        Examples:
            >>> parser = PDFParser()
            >>> texto = parser.extrair_texto("orcamento.pdf")
            >>> len(texto) > 0
            True

            >>> parser.extrair_texto("/caminho/inexistente.pdf")
            FileNotFoundError: Arquivo não encontrado: /caminho/inexistente.pdf

        Note:
            - O método preserva a formatação original do PDF
            - Quebras de linha são mantidas
            - Espaços múltiplos NÃO são normalizados
            - Caracteres especiais são preservados
        """
        logger.info(f"Iniciando extração de texto do PDF: {pdf_path}")

        # Verificar se arquivo existe
        if not os.path.exists(pdf_path):
            logger.error(MENSAGEM_ARQUIVO_NAO_ENCONTRADO.format(pdf_path))
            raise FileNotFoundError(MENSAGEM_ARQUIVO_NAO_ENCONTRADO.format(pdf_path))

        # Verificar se é arquivo PDF (extensão)
        if not pdf_path.lower().endswith(EXTENSAO_PDF):
            logger.error(MENSAGEM_ARQUIVO_NAO_PDF.format(pdf_path))
            raise InvalidPDFError(MENSAGEM_ARQUIVO_NAO_PDF.format(pdf_path))

        logger.info(f"Arquivo validado. Extensão: {EXTENSAO_PDF}")

        # Extrair texto usando pdfplumber
        try:
            texto_completo: List[str] = []

            with pdfplumber.open(pdf_path) as pdf:
                total_paginas = len(pdf.pages)
                logger.info(f"PDF aberto com sucesso. Total de páginas: {total_paginas}")

                # Verificar se é PDF válido (tem páginas)
                if total_paginas == 0:
                    logger.warning("PDF sem páginas. Retornando string vazia.")
                    return ""

                # Extrair texto de cada página
                for i, pagina in enumerate(pdf.pages, 1):
                    texto_pagina = pagina.extract_text()

                    # Se a página tem texto, adicionar
                    if texto_pagina:
                        texto_completo.append(texto_pagina)
                        logger.debug(f"Página {i}/{total_paginas}: {len(texto_pagina)} caracteres extraídos")
                    else:
                        logger.warning(f"Página {i}/{total_paginas}: sem texto")

            # Juntar texto de todas as páginas preservando quebras de linha
            texto_final = '\n'.join(texto_completo)
            logger.info(f"Extração concluída com sucesso. Total de caracteres: {len(texto_final)}")

            return texto_final

        except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e:
            mensagem_erro = MENSAGEM_PDF_CORROMPIDO.format(str(e))
            logger.error(mensagem_erro)
            raise InvalidPDFError(mensagem_erro)

        except Exception as e:
            # Qualquer outro erro durante extração
            mensagem_erro = MENSAGEM_ERRO_EXTRACAO.format(str(e))
            logger.error(mensagem_erro)
            raise PDFExtractionError(mensagem_erro)


class PDFHeaderExtractor:
    """
    Extrator de dados do cabeçalho de orçamentos PMCELL.

    Esta classe extrai informações estruturadas do cabeçalho de orçamentos
    a partir do texto bruto extraído de PDFs. Utiliza expressões regulares
    para identificar e capturar os campos obrigatórios.

    Campos extraídos:
    - Número do orçamento (5 dígitos)
    - Código do cliente (6 dígitos)
    - Nome do cliente
    - Nome do vendedor
    - Data do orçamento (formato DD/MM/AA)

    A classe implementa fail-safe: se um campo não for encontrado,
    adiciona o nome do campo à lista de erros mas continua a extração.

    Examples:
        >>> extractor = PDFHeaderExtractor()
        >>> texto = "Orçamento Nº: 30567\\nCódigo: 001007\\n..."
        >>> header = extractor.extrair_header(texto)
        >>> header.numero_orcamento
        '30567'
        >>> header.is_valid
        True
    """

    # Padrões regex para extração de campos
    PATTERN_NUMERO_ORCAMENTO = r'Orçamento\s+Nº:\s*(\d{5})'
    PATTERN_CODIGO_CLIENTE = r'Código:\s*(\d{6})'
    PATTERN_VENDEDOR = r'Vendedor:\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]+?)(?=\s+(?:Validade do Orçamento:|\n))'
    PATTERN_DATA = r'Data:\s*(\d{2}/\d{2}/\d{2})'

    def __init__(self):
        """Inicializa o extrator de cabeçalho."""
        logger.info("PDFHeaderExtractor inicializado")

    def extrair_header(self, texto: str) -> OrcamentoHeaderDTO:
        """
        Extrai dados do cabeçalho de um orçamento.

        Este método analisa o texto bruto extraído de um PDF e utiliza
        expressões regulares para identificar e extrair os campos obrigatórios
        do cabeçalho do orçamento.

        Se algum campo não for encontrado, o método adiciona o nome do campo
        à lista de erros do DTO, mas NÃO lança exceção (fail-safe).

        Args:
            texto (str): Texto bruto extraído do PDF.

        Returns:
            OrcamentoHeaderDTO: DTO contendo os dados extraídos.
                Se algum campo não foi encontrado, estará como None
                e o nome do campo estará em DTO.errors.

        Examples:
            >>> extractor = PDFHeaderExtractor()
            >>> texto = "Orçamento Nº: 30567\\nCódigo: 001007\\n..."
            >>> header = extractor.extrair_header(texto)
            >>> header.numero_orcamento
            '30567'
            >>> header.is_valid
            True

            >>> texto_incompleto = "Texto sem dados de orçamento"
            >>> header = extractor.extrair_header(texto_incompleto)
            >>> header.is_valid
            False
            >>> 'numero_orcamento' in header.errors
            True

        Note:
            - Não lança exceções (fail-safe)
            - Campos faltantes são adicionados a DTO.errors
            - Logging completo de todas as operações
        """
        logger.info("Iniciando extração de dados do cabeçalho")
        logger.debug(f"Tamanho do texto a analisar: {len(texto)} caracteres")

        # Extrair número do orçamento
        numero_orcamento = self._extrair_campo(
            texto,
            self.PATTERN_NUMERO_ORCAMENTO,
            'numero_orcamento'
        )

        # Extrair código do cliente
        codigo_cliente = self._extrair_campo(
            texto,
            self.PATTERN_CODIGO_CLIENTE,
            'codigo_cliente'
        )

        # Extrair nome do cliente (mais complexo - vem após código do cliente)
        nome_cliente = self._extrair_nome_cliente(texto, codigo_cliente)

        # Extrair vendedor
        vendedor = self._extrair_campo(
            texto,
            self.PATTERN_VENDEDOR,
            'vendedor'
        )

        # Extrair data
        data = self._extrair_campo(
            texto,
            self.PATTERN_DATA,
            'data'
        )

        # Criar DTO (validação automática no __post_init__)
        header_dto = OrcamentoHeaderDTO(
            numero_orcamento=numero_orcamento,
            codigo_cliente=codigo_cliente,
            nome_cliente=nome_cliente,
            vendedor=vendedor,
            data=data
        )

        # Logging do resultado
        if header_dto.is_valid:
            logger.info(f"Extração concluída com sucesso: {header_dto}")
        else:
            logger.warning(
                f"Extração concluída com {len(header_dto.errors)} erros: {header_dto.errors}"
            )

        return header_dto

    def _extrair_campo(self, texto: str, pattern: str, nome_campo: str) -> str:
        """
        Extrai um campo usando regex.

        Args:
            texto: Texto onde buscar
            pattern: Padrão regex
            nome_campo: Nome do campo (para logging)

        Returns:
            Valor extraído ou None se não encontrado
        """
        try:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                valor = match.group(1).strip()
                logger.debug(f"Campo '{nome_campo}' extraído: {valor}")
                return valor
            else:
                logger.warning(f"Campo '{nome_campo}' não encontrado no texto")
                return None
        except Exception as e:
            logger.error(f"Erro ao extrair campo '{nome_campo}': {str(e)}")
            return None

    def _extrair_nome_cliente(self, texto: str, codigo_cliente: str) -> str:
        """
        Extrai nome do cliente.

        O nome do cliente aparece após "Cliente:" e pode estar na mesma linha
        que outros campos (ex: "Cliente: NOME Forma de Pagto:").

        Args:
            texto: Texto completo
            codigo_cliente: Código do cliente (já extraído)

        Returns:
            Nome do cliente ou None se não encontrado
        """
        try:
            # Padrão: captura nome após "Cliente:" até encontrar "Forma de Pagto:" ou "Vendedor:"
            # Aceita letras maiúsculas, espaços e alguns caracteres especiais
            pattern = r'Cliente:\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]+?)(?=\s+(?:Forma de Pagto:|Vendedor:))'
            match = re.search(pattern, texto, re.IGNORECASE)

            if match:
                nome = match.group(1).strip()
                logger.debug(f"Campo 'nome_cliente' extraído: {nome}")
                return nome
            else:
                logger.warning("Campo 'nome_cliente' não encontrado no texto")
                return None
        except Exception as e:
            logger.error(f"Erro ao extrair campo 'nome_cliente': {str(e)}")
            return None


class PDFProductExtractor:
    """
    Extrator de produtos de orçamentos PMCELL.

    Esta classe extrai lista de produtos a partir do texto bruto extraído de PDFs.
    Utiliza expressões regulares e validação matemática para garantir precisão.

    Campos extraídos para cada produto:
    - Código do produto (5 dígitos)
    - Descrição do produto (texto entre código e "UN")
    - Quantidade (inteiro)
    - Valor unitário (Decimal)
    - Valor total (Decimal)

    A classe implementa:
    - Validação matemática: quantidade × valor_unitario = valor_total (tolerância 0.01)
    - Fail-safe: linhas inválidas não quebram extração, adicionam erro
    - Logging completo de todas as operações

    Examples:
        >>> extractor = PDFProductExtractor()
        >>> texto = "00010 FO11 --> FONE PMCELL UN 30 3,50 105,00"
        >>> produto = extractor._extrair_produto_linha(texto)
        >>> produto.codigo
        '00010'
        >>> produto.is_valid
        True
    """

    # Constantes
    TOLERANCIA_MATEMATICA = Decimal("0.01")

    # Padrões regex
    PATTERN_CODIGO = r'^\d{5}'  # Primeiros 5 dígitos da linha
    PATTERN_VALORES = r'(\d+)\s+(\d+,\d{2})\s+(\d+,\d{2})$'  # 3 últimos números
    PATTERN_UNIDADE = r'\s+UN\s+'  # Unidade "UN" para encontrar onde termina descrição

    # Marcadores de seção
    MARCADOR_INICIO_PRODUTOS = r'Código\s+Produto'  # Início da tabela
    MARCADOR_FIM_PRODUTOS = r'^VALOR\s+TOTAL'  # Fim da tabela (início de linha)

    def __init__(self):
        """Inicializa o extrator de produtos."""
        logger.info("PDFProductExtractor inicializado")

    def extrair_produtos(self, texto: str) -> List[ProdutoDTO]:
        """
        Extrai todos os produtos de um texto de PDF.

        Este método:
        1. Identifica a seção de produtos no texto
        2. Processa cada linha de produto
        3. Valida matematicamente cada produto
        4. Retorna lista de ProdutoDTOs

        Args:
            texto (str): Texto bruto extraído do PDF.

        Returns:
            List[ProdutoDTO]: Lista de produtos extraídos.
                Produtos inválidos têm errors populado.

        Examples:
            >>> extractor = PDFProductExtractor()
            >>> texto = "Código Produto Unid...\\n00010 FONE UN 30 3,50 105,00\\nVALOR TOTAL..."
            >>> produtos = extractor.extrair_produtos(texto)
            >>> len(produtos)
            1
            >>> produtos[0].codigo
            '00010'

        Note:
            - Não lança exceções (fail-safe)
            - Linhas inválidas são puladas
            - Logging completo de todas as operações
        """
        logger.info("Iniciando extração de produtos do texto")
        logger.debug(f"Tamanho do texto: {len(texto)} caracteres")

        # Identificar seção de produtos
        secao_produtos = self._identificar_secao_produtos(texto)

        if not secao_produtos:
            logger.warning("Seção de produtos não encontrada no texto")
            return []

        logger.debug(f"Seção de produtos identificada: {len(secao_produtos)} caracteres")

        # Processar cada linha
        linhas = secao_produtos.split('\n')
        produtos: List[ProdutoDTO] = []
        linhas_processadas = 0
        linhas_validas = 0
        linhas_invalidas = 0

        for i, linha in enumerate(linhas, 1):
            linha = linha.strip()

            # Pular linhas vazias
            if not linha:
                continue

            linhas_processadas += 1

            # Tentar extrair produto da linha
            produto = self._extrair_produto_linha(linha)

            if produto and produto.is_valid:
                produtos.append(produto)
                linhas_validas += 1
                logger.debug(f"Linha {i}: Produto extraído - {produto.codigo}")
            else:
                linhas_invalidas += 1
                if produto:
                    logger.debug(f"Linha {i}: Produto inválido - Erros: {produto.errors}")
                else:
                    logger.debug(f"Linha {i}: Não é linha de produto - '{linha[:50]}...'")

        # Logging do resultado
        logger.info(
            f"Extração concluída: {linhas_validas} produtos extraídos, "
            f"{linhas_invalidas} linhas inválidas, "
            f"{linhas_processadas} linhas processadas"
        )

        return produtos

    def _identificar_secao_produtos(self, texto: str) -> Optional[str]:
        """
        Identifica a seção de produtos no texto.

        A seção começa após "Código Produto Unid..." e termina antes de "VALOR TOTAL".

        Args:
            texto: Texto completo do PDF

        Returns:
            Texto da seção de produtos ou None se não encontrado
        """
        try:
            # Buscar início da seção (MULTILINE para casar com $ no final da linha)
            match_inicio = re.search(self.MARCADOR_INICIO_PRODUTOS, texto, re.IGNORECASE | re.MULTILINE)
            if not match_inicio:
                logger.warning("Marcador de início de produtos não encontrado")
                return None

            # Buscar fim da seção
            match_fim = re.search(self.MARCADOR_FIM_PRODUTOS, texto, re.IGNORECASE | re.MULTILINE)
            if not match_fim:
                logger.warning("Marcador de fim de produtos não encontrado")
                return None

            # Extrair seção entre marcadores
            inicio = match_inicio.end()
            fim = match_fim.start()

            secao = texto[inicio:fim].strip()
            logger.debug(f"Seção de produtos identificada: {len(secao)} caracteres")

            return secao

        except Exception as e:
            logger.error(f"Erro ao identificar seção de produtos: {str(e)}")
            return None

    def _extrair_produto_linha(self, linha: str) -> Optional[ProdutoDTO]:
        """
        Extrai produto de uma linha de texto.

        Estratégia:
        1. Extrair código (5 primeiros dígitos)
        2. Extrair 3 últimos números (quantidade, valor_unit, valor_total)
        3. Validar matematicamente
        4. Extrair descrição (texto entre código e "UN")

        Args:
            linha: Linha de texto contendo dados do produto

        Returns:
            ProdutoDTO ou None se linha não for produto válido

        Examples:
            >>> extractor = PDFProductExtractor()
            >>> linha = "00010 FO11 --> FONE PMCELL UN 30 3,50 105,00"
            >>> produto = extractor._extrair_produto_linha(linha)
            >>> produto.codigo
            '00010'
        """
        try:
            # 1. Extrair código (5 primeiros dígitos)
            match_codigo = re.match(self.PATTERN_CODIGO, linha)
            if not match_codigo:
                # Não é linha de produto (não começa com código)
                return None

            codigo = match_codigo.group()

            # 2. Extrair 3 últimos números
            match_valores = re.search(self.PATTERN_VALORES, linha)
            if not match_valores:
                logger.debug(f"Valores numéricos não encontrados na linha: {linha[:50]}...")
                return ProdutoDTO(codigo=codigo, errors=['valores_numericos'])

            quantidade_str = match_valores.group(1)
            valor_unitario_str = match_valores.group(2)
            valor_total_str = match_valores.group(3)

            # Converter para tipos apropriados
            quantidade = int(quantidade_str)
            valor_unitario = self._converter_valor_brasileiro(valor_unitario_str)
            valor_total = self._converter_valor_brasileiro(valor_total_str)

            # 3. Extrair descrição (entre código e "UN")
            # Remove código do início
            texto_sem_codigo = linha[len(codigo):].strip()

            # Encontra posição de "UN"
            match_un = re.search(self.PATTERN_UNIDADE, texto_sem_codigo)
            if not match_un:
                logger.debug(f"Unidade 'UN' não encontrada na linha: {linha[:50]}...")
                return ProdutoDTO(
                    codigo=codigo,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    valor_total=valor_total,
                    errors=['descricao']
                )

            # Extrai descrição (tudo antes de "UN")
            descricao = texto_sem_codigo[:match_un.start()].strip()

            # 4. Criar DTO (validação automática no __post_init__)
            produto = ProdutoDTO(
                codigo=codigo,
                descricao=descricao,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_total
            )

            return produto

        except Exception as e:
            logger.error(f"Erro ao extrair produto da linha '{linha[:50]}...': {str(e)}")
            return None

    def _converter_valor_brasileiro(self, valor_str: str) -> Decimal:
        """
        Converte valor no formato brasileiro (vírgula decimal) para Decimal.

        Args:
            valor_str: Valor como string (ex: "105,00", "3,50")

        Returns:
            Valor como Decimal

        Examples:
            >>> extractor = PDFProductExtractor()
            >>> extractor._converter_valor_brasileiro("105,00")
            Decimal('105.00')
            >>> extractor._converter_valor_brasileiro("3,50")
            Decimal('3.50')
        """
        # Remover pontos (separador de milhares) e substituir vírgula por ponto
        valor_normalizado = valor_str.replace('.', '').replace(',', '.')
        return Decimal(valor_normalizado)
