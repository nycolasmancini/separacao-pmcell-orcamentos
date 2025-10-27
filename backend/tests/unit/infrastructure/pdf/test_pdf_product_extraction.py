# -*- coding: utf-8 -*-
"""
Testes para extração de produtos do PDF (Fase 12).

Este módulo testa o PDFProductExtractor, que extrai produtos de um PDF de orçamento
e valida matematicamente cada produto (quantidade × valor_unitario = valor_total).
"""

import pytest
from decimal import Decimal
from core.infrastructure.pdf.parser import PDFProductExtractor
from core.application.dtos.orcamento_dtos import ProdutoDTO


class TestPDFProductExtraction:
    """Testes para extração de produtos do PDF."""

    def setup_method(self):
        """Setup executado antes de cada teste."""
        self.extractor = PDFProductExtractor()

    def test_extract_single_product_line(self):
        """
        Testa extração de uma linha de produto válida.

        Given: Uma linha de produto formatada corretamente
        When: Extrair produto da linha
        Then: Produto deve ter todos os campos corretos
        """
        linha = "00010 FO11 --> FONE PMCELL UN 30 3,50 105,00"

        produto = self.extractor._extrair_produto_linha(linha)

        assert produto is not None
        assert produto.codigo == "00010"
        assert "FONE PMCELL" in produto.descricao
        assert produto.quantidade == 30
        assert produto.valor_unitario == Decimal("3.50")
        assert produto.valor_total == Decimal("105.00")
        assert produto.is_valid

    def test_extract_codigo_produto(self):
        """
        Testa extração do código do produto (5 dígitos).

        Given: Linhas com diferentes códigos
        When: Extrair código
        Then: Código deve ter exatamente 5 dígitos
        """
        linhas = [
            "00010 FO11 --> FONE PMCELL UN 30 3,50 105,00",
            "00032 CB14 --> CABO PMCELL P2XP2 C UN 10 1,40 14,00",
            "01798 TPU --> SAMSUNG A32 4G UN 200 1,60 320,00"
        ]

        for linha in linhas:
            produto = self.extractor._extrair_produto_linha(linha)
            assert produto is not None
            assert len(produto.codigo) == 5
            assert produto.codigo.isdigit()

    def test_extract_descricao_produto(self):
        """
        Testa extração da descrição do produto (entre código e "UN").

        Given: Linhas com diferentes descrições
        When: Extrair descrição
        Then: Descrição deve estar correta e sem espaços extras
        """
        linhas_esperadas = [
            ("00010 FO11 --> FONE PMCELL UN 30 3,50 105,00", "FO11 --> FONE PMCELL"),
            ("00032 CB14 --> CABO PMCELL P2XP2 C UN 10 1,40 14,00", "CB14 --> CABO PMCELL P2XP2 C"),
            ("00819 PELICULA 3D --> IP 12 PRO MAX UN 05 1,20 6,00", "PELICULA 3D --> IP 12 PRO MAX")
        ]

        for linha, descricao_esperada in linhas_esperadas:
            produto = self.extractor._extrair_produto_linha(linha)
            assert produto is not None
            assert produto.descricao.strip() == descricao_esperada

    def test_extract_valores_numericos(self):
        """
        Testa extração dos 3 últimos números (quantidade, valor_unit, valor_total).

        Given: Linha com valores numéricos
        When: Extrair valores
        Then: Valores devem estar corretos e com tipos apropriados
        """
        linha = "00010 FO11 --> FONE PMCELL UN 30 3,50 105,00"

        produto = self.extractor._extrair_produto_linha(linha)

        assert produto is not None
        assert isinstance(produto.quantidade, int)
        assert isinstance(produto.valor_unitario, Decimal)
        assert isinstance(produto.valor_total, Decimal)
        assert produto.quantidade == 30
        assert produto.valor_unitario == Decimal("3.50")
        assert produto.valor_total == Decimal("105.00")

    def test_mathematical_validation_passes(self):
        """
        Testa validação matemática: qtd × valor_unit = valor_total (tolerância 0.01).

        Given: Produtos com cálculos corretos
        When: Validar matematicamente
        Then: Validação deve passar para todos
        """
        linhas_validas = [
            "00010 FO11 --> FONE PMCELL UN 30 3,50 105,00",      # 30 × 3.50 = 105.00
            "00032 CB14 --> CABO PMCELL UN 10 1,40 14,00",       # 10 × 1.40 = 14.00
            "00819 PELICULA 3D --> IP 12 UN 05 1,20 6,00",       # 5 × 1.20 = 6.00
            "01798 TPU --> SAMSUNG A32 4G UN 200 1,60 320,00"    # 200 × 1.60 = 320.00
        ]

        for linha in linhas_validas:
            produto = self.extractor._extrair_produto_linha(linha)
            assert produto is not None
            assert produto.is_valid
            assert len(produto.errors) == 0

            # Validar cálculo manualmente
            calculo = Decimal(str(produto.quantidade)) * produto.valor_unitario
            diferenca = abs(calculo - produto.valor_total)
            assert diferenca <= Decimal("0.01")

    def test_extract_all_products_from_text(self):
        """
        Testa extração de múltiplos produtos de um texto completo.

        Given: Texto de PDF com múltiplos produtos
        When: Extrair todos os produtos
        Then: Deve retornar lista com todos os produtos válidos
        """
        texto_pdf = """
Código Produto Unid. Quant. Valor Total
00010 FO11 --> FONE PMCELL UN 30 3,50 105,00
00032 CB14 --> CABO PMCELL P2XP2 C UN 10 1,40 14,00
00819 PELICULA 3D --> IP 12 PRO MAX UN 05 1,20 6,00
VALOR TOTAL    R$ 125,00
        """

        produtos = self.extractor.extrair_produtos(texto_pdf)

        assert len(produtos) == 3
        assert produtos[0].codigo == "00010"
        assert produtos[1].codigo == "00032"
        assert produtos[2].codigo == "00819"
        assert all(p.is_valid for p in produtos)

    def test_products_with_special_chars_in_description(self):
        """
        Testa produtos com caracteres especiais na descrição (-->, /, -, etc).

        Given: Linhas com caracteres especiais variados
        When: Extrair produtos
        Then: Caracteres especiais devem ser preservados na descrição
        """
        linhas_especiais = [
            ("00010 FO11 --> FONE PMCELL UN 30 3,50 105,00", "-->"),
            ("00255 CJ-42 -->> CARREGADOR 66W TC UN 10 12,00 120,00", "-->>"),
            ("01306 CB --> TYPE C / TYPE C UN 15 2,00 30,00", "/"),
            ("04672 SP42 --- SUPORTE MOTO G35 UN 5 1,50 7,50", "---")
        ]

        for linha, char_especial in linhas_especiais:
            produto = self.extractor._extrair_produto_linha(linha)
            assert produto is not None
            assert char_especial in produto.descricao

    def test_invalid_line_adds_to_errors(self):
        """
        Testa fail-safe: linha inválida não quebra extração, adiciona erro.

        Given: Linha mal formatada ou inválida
        When: Tentar extrair produto
        Then: Não deve lançar exceção, mas deve retornar None ou produto com errors
        """
        linhas_invalidas = [
            "Esta linha não é um produto",
            "12345",  # Só código, sem descrição
            "00010 PRODUTO INCOMPLETO",  # Sem valores numéricos
            "",  # Linha vazia
            "INVALIDO SEM CÓDIGO UN 10 1,00 10,00"  # Sem código válido
        ]

        for linha in linhas_invalidas:
            # Não deve lançar exceção
            produto = self.extractor._extrair_produto_linha(linha)

            # Deve retornar None para linhas completamente inválidas
            if produto is None:
                assert True  # Comportamento esperado
            else:
                # Ou deve ter erros se retornou produto parcial
                assert not produto.is_valid
                assert len(produto.errors) > 0
