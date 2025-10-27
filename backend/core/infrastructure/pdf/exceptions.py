# -*- coding: utf-8 -*-
"""
Exceções customizadas para o módulo de PDF.

Este módulo define exceções específicas para tratamento de erros
durante o processo de extração de dados de PDFs.
"""


class InvalidPDFError(Exception):
    """
    Exceção lançada quando o arquivo não é um PDF válido.

    Esta exceção é lançada quando:
    - O arquivo não possui formato PDF
    - O arquivo não possui extensão .pdf
    - O arquivo possui formato incorreto

    Examples:
        >>> raise InvalidPDFError("Arquivo não é um PDF válido")
    """
    pass


class PDFExtractionError(Exception):
    """
    Exceção lançada quando ocorre erro durante a extração de dados do PDF.

    Esta exceção é lançada quando:
    - O PDF está corrompido
    - Ocorre erro durante a leitura do arquivo
    - O pdfplumber não consegue processar o arquivo

    Examples:
        >>> raise PDFExtractionError("Erro ao extrair texto do PDF")
    """
    pass
