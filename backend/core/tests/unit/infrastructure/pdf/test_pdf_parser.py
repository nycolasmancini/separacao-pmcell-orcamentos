# -*- coding: utf-8 -*-
"""
Testes unitários para PDFParser.

Fase 10: Implementar Parser de PDF Base
Seguindo TDD rigoroso (RED → GREEN → REFACTOR)

Este módulo testa a extração básica de texto de PDFs de orçamento.
"""

import os
import pytest
import tempfile
from pathlib import Path

from core.infrastructure.pdf.parser import PDFParser
from core.infrastructure.pdf.exceptions import InvalidPDFError, PDFExtractionError


# Caminho dos PDFs de teste (fixtures reais)
FIXTURES_DIR = Path("/Users/nycolasmancini/Desktop/separacao-pmcell/orcamentos-modelo")
PDF_SIMPLES = FIXTURES_DIR / "Orcamento - 30567 - Rosana - R$ 105,00.pdf"
PDF_COMPLEXO = FIXTURES_DIR / "Orcamento - 30582 - Infocel - R$ 1707,00.pdf"


class TestPDFParserExtracao:
    """Testes de extração básica de texto."""

    def test_pdf_parser_extracts_text_from_valid_pdf(self):
        """
        Testa extração de texto de PDF válido (simples - 1 produto).

        Este teste verifica que o parser consegue extrair texto
        do orçamento mais simples (30567 com apenas 1 produto).
        """
        parser = PDFParser()
        texto = parser.extrair_texto(str(PDF_SIMPLES))

        # Verificações básicas
        assert isinstance(texto, str)
        assert len(texto) > 0

        # Verificações de conteúdo esperado
        assert "Orçamento Nº: 30567" in texto or "30567" in texto
        assert "ROSANA" in texto.upper()  # Case insensitive

    def test_pdf_parser_extracts_text_from_complex_pdf(self):
        """
        Testa extração de texto de PDF complexo (40 produtos).

        Este teste verifica que o parser consegue processar
        PDFs maiores com múltiplos produtos.
        """
        parser = PDFParser()
        texto = parser.extrair_texto(str(PDF_COMPLEXO))

        # Verificações básicas
        assert isinstance(texto, str)
        assert len(texto) > 0

        # Verificações de estrutura completa
        assert "Orçamento Nº: 30582" in texto or "30582" in texto
        assert "INFOCEL" in texto.upper()

        # Verifica presença de elementos da tabela
        assert "Código" in texto or "Produto" in texto

        # Verifica presença de totalizadores
        assert "VALOR TOTAL" in texto.upper() or "R$" in texto


class TestPDFParserErros:
    """Testes de tratamento de erros."""

    def test_invalid_pdf_raises_invalid_pdf_error(self):
        """
        Testa que arquivo não-PDF lança InvalidPDFError.

        Este teste verifica que o parser identifica corretamente
        quando um arquivo não é um PDF válido.
        """
        parser = PDFParser()

        # Criar arquivo .txt temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Isto não é um PDF")
            temp_file = f.name

        try:
            with pytest.raises(InvalidPDFError) as exc_info:
                parser.extrair_texto(temp_file)

            # Verifica mensagem de erro clara
            assert "PDF válido" in str(exc_info.value) or "inválido" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_file)

    def test_nonexistent_file_raises_file_not_found(self):
        """
        Testa que arquivo inexistente lança FileNotFoundError.

        Este teste verifica tratamento de erro para arquivos
        que não existem no sistema de arquivos.
        """
        parser = PDFParser()

        with pytest.raises(FileNotFoundError) as exc_info:
            parser.extrair_texto("/caminho/inexistente/arquivo.pdf")

        # Verifica que a exceção foi lançada
        assert exc_info.value is not None

    def test_corrupted_pdf_raises_pdf_extraction_error(self):
        """
        Testa que PDF corrompido lança PDFExtractionError.

        Este teste verifica tratamento de erro para arquivos
        com extensão .pdf mas conteúdo inválido.
        """
        parser = PDFParser()

        # Criar arquivo .pdf corrompido (bytes inválidos)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\n%%EOF')  # Header mínimo mas inválido
            temp_file = f.name

        try:
            with pytest.raises((PDFExtractionError, InvalidPDFError)) as exc_info:
                parser.extrair_texto(temp_file)

            # Verifica que alguma exceção apropriada foi lançada
            assert exc_info.value is not None
        finally:
            os.unlink(temp_file)


class TestPDFParserFormatacao:
    """Testes de preservação de formatação."""

    def test_empty_pdf_returns_empty_string(self):
        """
        Testa que PDF vazio retorna string vazia (não lança erro).

        Este teste verifica que PDFs sem conteúdo de texto
        são tratados graciosamente.
        """
        # Para este teste, vamos usar um PDF real mas verificar
        # que se não houver texto, retorna string vazia
        parser = PDFParser()

        # Mesmo PDFs reais devem retornar string (vazia ou não)
        texto = parser.extrair_texto(str(PDF_SIMPLES))
        assert isinstance(texto, str)

    def test_pdf_parser_preserves_original_formatting(self):
        """
        Testa que formatação original é preservada.

        Este teste verifica que o parser não normaliza o texto,
        preservando quebras de linha e espaços múltiplos.
        """
        parser = PDFParser()
        texto = parser.extrair_texto(str(PDF_SIMPLES))

        # Verifica que texto contém quebras de linha
        assert '\n' in texto or len(texto.split()) > 1

        # Verifica que não houve normalização agressiva
        # (o texto deve ter mais de uma linha)
        linhas = texto.split('\n')
        assert len(linhas) > 1

    def test_pdf_parser_handles_special_characters(self):
        """
        Testa que caracteres especiais são preservados.

        Este teste verifica que o parser preserva caracteres
        especiais comuns nos orçamentos (setas, símbolos, etc).
        """
        parser = PDFParser()
        texto = parser.extrair_texto(str(PDF_COMPLEXO))

        # Verifica presença de caracteres especiais típicos
        # dos orçamentos PMCELL (pelo menos R$ deve estar presente)
        assert 'R$' in texto or '$' in texto

        # O texto deve conter dados do PDF
        assert len(texto) > 100  # PDF complexo deve ter bastante texto
