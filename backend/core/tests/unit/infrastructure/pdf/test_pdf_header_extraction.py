# -*- coding: utf-8 -*-
"""
Testes para extração de cabeçalho de PDFs de orçamento.

Este módulo contém testes unitários para a classe PDFHeaderExtractor,
responsável por extrair dados estruturados do cabeçalho de orçamentos PMCELL.

Segue metodologia TDD (Test-Driven Development):
- RED: Testes criados primeiro (devem FALHAR)
- GREEN: Implementação mínima para passar
- REFACTOR: Melhorias mantendo testes passando
"""

import pytest
from core.infrastructure.pdf.parser import PDFHeaderExtractor
from core.application.dtos.orcamento_dtos import OrcamentoHeaderDTO


class TestPDFHeaderExtraction:
    """Testes para extração de dados do cabeçalho de orçamentos."""

    @pytest.fixture
    def extractor(self):
        """Fixture que retorna uma instância do extrator."""
        return PDFHeaderExtractor()

    @pytest.fixture
    def texto_completo(self):
        """Fixture com texto completo de um orçamento válido."""
        return """
        PMCELL São Paulo
        V. Zabin Tecnologia e Comercio Eireili
        CNPJ: 29.734.462/0003-86

        Orçamento Nº: 30567

        Código: 001007    Data: 22/10/25
        Cliente: ROSANA DE CASSIA SINEZIO
        Vendedor: NYCOLAS HENDRIGO MANCINI

        Condição de Pagamento:
        Forma de Pagamento:
        Validade do Orçamento: 22/10/25 - 0 dia(s)

        Código Produto                     Unid. Quant. Valor   Total
        00010  FO11 --> FONE PMCELL       UN    30     3,50    105,00

        VALOR TOTAL    R$ 105,00
        DESCONTO       R$ 0,00
        VALOR A PAGAR  R$ 105,00
        """

    def test_extract_numero_orcamento(self, extractor, texto_completo):
        """
        Testa extração do número do orçamento.

        Verifica se o número do orçamento (5 dígitos) é extraído corretamente.
        """
        header = extractor.extrair_header(texto_completo)
        assert header.numero_orcamento == "30567"

    def test_extract_codigo_cliente(self, extractor, texto_completo):
        """
        Testa extração do código do cliente.

        Verifica se o código do cliente (6 dígitos) é extraído corretamente.
        """
        header = extractor.extrair_header(texto_completo)
        assert header.codigo_cliente == "001007"

    def test_extract_nome_cliente(self, extractor, texto_completo):
        """
        Testa extração do nome do cliente.

        Verifica se o nome completo do cliente é extraído corretamente.
        """
        header = extractor.extrair_header(texto_completo)
        assert header.nome_cliente == "ROSANA DE CASSIA SINEZIO"

    def test_extract_vendedor(self, extractor, texto_completo):
        """
        Testa extração do nome do vendedor.

        Verifica se o nome do vendedor é extraído corretamente.
        """
        header = extractor.extrair_header(texto_completo)
        assert header.vendedor == "NYCOLAS HENDRIGO MANCINI"

    def test_extract_data(self, extractor, texto_completo):
        """
        Testa extração da data.

        Verifica se a data é extraída corretamente no formato DD/MM/AA.
        """
        header = extractor.extrair_header(texto_completo)
        assert header.data == "22/10/25"

    def test_extract_all_header_fields(self, extractor, texto_completo):
        """
        Testa extração completa do cabeçalho.

        Verifica se todos os campos obrigatórios são extraídos e o DTO é válido.
        """
        header = extractor.extrair_header(texto_completo)

        # Verificar todos os campos
        assert header.numero_orcamento == "30567"
        assert header.codigo_cliente == "001007"
        assert header.nome_cliente == "ROSANA DE CASSIA SINEZIO"
        assert header.vendedor == "NYCOLAS HENDRIGO MANCINI"
        assert header.data == "22/10/25"

        # Verificar que não há erros
        assert header.is_valid is True
        assert len(header.errors) == 0

    def test_missing_field_adds_to_errors(self, extractor):
        """
        Testa que campo faltante é adicionado à lista de erros.

        Verifica comportamento fail-safe: campo não encontrado não lança exceção,
        mas adiciona o campo à lista de erros.
        """
        # Texto sem número de orçamento e código de cliente
        texto_incompleto = """
        Cliente: ROSANA DE CASSIA SINEZIO Forma de Pagto:
        Vendedor: NYCOLAS HENDRIGO MANCINI Validade do Orçamento: 22/10/25
        Data: 22/10/25
        """

        header = extractor.extrair_header(texto_incompleto)

        # Deve ter erros
        assert header.is_valid is False

        # Campos faltantes devem estar em errors
        assert 'numero_orcamento' in header.errors
        assert 'codigo_cliente' in header.errors

        # Campos presentes devem ter sido extraídos
        assert header.nome_cliente == "ROSANA DE CASSIA SINEZIO"
        assert header.vendedor == "NYCOLAS HENDRIGO MANCINI"
        assert header.data == "22/10/25"

    def test_multiple_pdfs(self, extractor):
        """
        Testa extração com múltiplos PDFs de formatos diferentes.

        Verifica robustez do extrator com diferentes variações de PDFs reais.
        """
        # Texto do orçamento 30568 (formato real com campos na mesma linha)
        texto_orcamento_30568 = """
        Orçamento Nº: 30568
        Código: 000001    Data: 22/10/25    Condição de Pagto:
        Cliente: CLIENTE ATACADO Forma de Pagto:
        Vendedor: NYCOLAS HENDRIGO MANCINI Validade do Orçamento: 22/10/25
        """

        header = extractor.extrair_header(texto_orcamento_30568)

        assert header.numero_orcamento == "30568"
        assert header.codigo_cliente == "000001"
        assert header.nome_cliente == "CLIENTE ATACADO"
        assert header.vendedor == "NYCOLAS HENDRIGO MANCINI"
        assert header.data == "22/10/25"
        assert header.is_valid is True

        # Texto do orçamento 30582 (cliente com razão social longa)
        texto_orcamento_30582 = """
        Orçamento Nº: 30582
        Código: 000435    Data: 22/10/25    Condição de Pagto:
        Cliente: INFOCEL CELULARES ASSISTENCIA E SUPRIMENTOS LTDA Forma de Pagto:
        Vendedor: NYCOLAS HENDRIGO MANCINI Validade do Orçamento: 22/10/25
        """

        header2 = extractor.extrair_header(texto_orcamento_30582)

        assert header2.numero_orcamento == "30582"
        assert header2.codigo_cliente == "000435"
        assert header2.nome_cliente == "INFOCEL CELULARES ASSISTENCIA E SUPRIMENTOS LTDA"
        assert header2.vendedor == "NYCOLAS HENDRIGO MANCINI"
        assert header2.data == "22/10/25"
        assert header2.is_valid is True
