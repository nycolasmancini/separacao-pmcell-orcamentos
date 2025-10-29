# -*- coding: utf-8 -*-
"""
Testes unitários para o PDF Orcamento Parser.
Fase 1: 12 testes unitários com edge cases.

Seguindo TDD: estes testes devem FALHAR primeiro,
depois implementamos o parser até todos passarem.
"""
import pytest
from decimal import Decimal
from pathlib import Path

# Import será do parser Django-adapted (ainda não existe)
from core.infrastructure.parsers.pdf_orcamento_parser import (
    PDFOrcamentoParser,
    Produto,
    Orcamento,
    ParserError
)


class TestConverterValorBrasileiro:
    """Testes para conversão de valores brasileiros."""

    def test_converter_valor_com_milhar(self):
        """Converte valor com ponto de milhar e vírgula decimal."""
        parser = PDFOrcamentoParser()
        resultado = parser.converter_valor_brasileiro("1.405,00")
        assert resultado == Decimal("1405.00")

    def test_converter_valor_sem_milhar(self):
        """Converte valor sem ponto de milhar."""
        parser = PDFOrcamentoParser()
        resultado = parser.converter_valor_brasileiro("270,00")
        assert resultado == Decimal("270.00")

    def test_converter_valor_decimal_unico(self):
        """Converte valor com um dígito decimal."""
        parser = PDFOrcamentoParser()
        resultado = parser.converter_valor_brasileiro("0,90")
        assert resultado == Decimal("0.90")

    def test_converter_valor_inteiro(self):
        """Converte valor inteiro sem vírgula."""
        parser = PDFOrcamentoParser()
        resultado = parser.converter_valor_brasileiro("300")
        assert resultado == Decimal("300")

    def test_converter_valor_multiplos_milhares(self):
        """Converte valor com múltiplos pontos de milhar."""
        parser = PDFOrcamentoParser()
        resultado = parser.converter_valor_brasileiro("11.462,30")
        assert resultado == Decimal("11462.30")


class TestValidarMatematica:
    """Testes para validação matemática determinística."""

    def test_validar_matematica_correta(self):
        """Valida equação correta: 300 × 0,90 = 270,00."""
        parser = PDFOrcamentoParser()
        quant = Decimal("300")
        unit = Decimal("0.90")
        total = Decimal("270.00")

        assert parser.validar_matematica(quant, unit, total, Decimal("0.01")) is True

    def test_validar_matematica_incorreta(self):
        """Rejeita equação incorreta: 300 × 0,90 ≠ 280,00."""
        parser = PDFOrcamentoParser()
        quant = Decimal("300")
        unit = Decimal("0.90")
        total = Decimal("280.00")

        assert parser.validar_matematica(quant, unit, total, Decimal("0.01")) is False

    def test_validar_matematica_com_tolerancia(self):
        """Aceita diferença dentro da tolerância (0,01)."""
        parser = PDFOrcamentoParser()
        quant = Decimal("300")
        unit = Decimal("0.90")
        total = Decimal("270.01")  # Diferença de 0,01

        assert parser.validar_matematica(quant, unit, total, Decimal("0.01")) is True

    def test_validar_matematica_acima_tolerancia(self):
        """Rejeita diferença acima da tolerância."""
        parser = PDFOrcamentoParser()
        quant = Decimal("300")
        unit = Decimal("0.90")
        total = Decimal("270.05")  # Diferença de 0,05

        assert parser.validar_matematica(quant, unit, total, Decimal("0.01")) is False


class TestEncontrarValoresDeterministicos:
    """Testes para busca reversa de valores validados."""

    def test_encontrar_valores_simples(self):
        """Encontra valores em linha simples sem números na descrição."""
        parser = PDFOrcamentoParser()
        linha = "PELICULA VIDRO TEMPERADO 300 0,90 270,00"

        resultado = parser.encontrar_valores_deterministicos(linha)

        assert resultado is not None
        quant, unit, total, idx = resultado
        assert quant == Decimal("300")
        assert unit == Decimal("0.90")
        assert total == Decimal("270.00")

    def test_encontrar_valores_com_numeros_na_descricao(self):
        """Encontra valores corretos mesmo com números na descrição (EDGE CASE CRÍTICO)."""
        parser = PDFOrcamentoParser()
        # "27 MODELOS" e "50UN" estão na descrição
        # Valores reais: 1350 × 3,50 = 4725,00
        linha = "AVELUDADA (27 MODELOS) 50UN CADA 1350 3,50 4725,00"

        resultado = parser.encontrar_valores_deterministicos(linha)

        assert resultado is not None
        quant, unit, total, idx = resultado
        # Deve pegar os 3 ÚLTIMOS números que validam
        assert quant == Decimal("1350")
        assert unit == Decimal("3.50")
        assert total == Decimal("4725.00")

    def test_encontrar_valores_nao_encontrados(self):
        """Retorna None quando não há 3 números válidos."""
        parser = PDFOrcamentoParser()
        linha = "PRODUTO SEM VALORES"

        resultado = parser.encontrar_valores_deterministicos(linha)

        assert resultado is None

    def test_encontrar_valores_matematica_invalida(self):
        """Retorna None quando nenhuma combinação valida matematicamente."""
        parser = PDFOrcamentoParser()
        linha = "PRODUTO 100 200 500"  # 100 × 200 ≠ 500

        resultado = parser.encontrar_valores_deterministicos(linha)

        assert resultado is None


class TestProcessarLinhaProduto:
    """Testes para processamento de linha completa de produto."""

    def test_processar_linha_valida_simples(self):
        """Processa linha válida com estrutura simples."""
        parser = PDFOrcamentoParser()
        linha = "01234 PELICULA VIDRO TEMPERADO 300 0,90 270,00 UN"

        produto = parser.processar_linha_produto(linha)

        assert produto is not None
        assert produto.codigo == "01234"
        assert produto.descricao == "PELICULA VIDRO TEMPERADO"
        assert produto.unidade == "UN"
        assert produto.quantidade == Decimal("300")
        assert produto.valor_unitario == Decimal("0.90")
        assert produto.valor_total == Decimal("270.00")
        assert produto.validacao_matematica is True

    def test_processar_linha_descricao_com_numeros(self):
        """Processa linha com números na descrição (EDGE CASE CRÍTICO)."""
        parser = PDFOrcamentoParser()
        linha = "01689 AVELUDADA (27 MODELOS) 50UN CADA 1350 3,50 4725,00 UN"

        produto = parser.processar_linha_produto(linha)

        assert produto is not None
        assert produto.codigo == "01689"
        # Descrição DEVE incluir os números do texto livre
        assert "27 MODELOS" in produto.descricao
        assert "50UN CADA" in produto.descricao
        # Valores devem ser os 3 últimos validados
        assert produto.quantidade == Decimal("1350")
        assert produto.valor_unitario == Decimal("3.50")
        assert produto.valor_total == Decimal("4725.00")

    def test_processar_linha_sem_marcador_un(self):
        """Rejeita linha sem marcador ' UN' isolado."""
        parser = PDFOrcamentoParser()
        linha = "01234 PELICULA VIDRO TEMPERADO 300 0,90 270,00"  # Sem UN

        produto = parser.processar_linha_produto(linha)

        assert produto is None

    def test_processar_linha_sem_codigo(self):
        """Rejeita linha sem código de 5 dígitos."""
        parser = PDFOrcamentoParser()
        linha = "PELICULA VIDRO TEMPERADO UN 300 0,90 270,00"

        produto = parser.processar_linha_produto(linha)

        assert produto is None

    def test_processar_linha_un_na_descricao(self):
        """Processa corretamente linha com 'UN' dentro da descrição."""
        parser = PDFOrcamentoParser()
        # "50UN" está na descrição, mas " UN" isolado no final
        linha = "01689 CAPA 50UN NO PACOTE 100 2,00 200,00 UN"

        produto = parser.processar_linha_produto(linha)

        assert produto is not None
        assert "50UN NO PACOTE" in produto.descricao
        assert produto.quantidade == Decimal("100")


class TestExtrairHeader:
    """Testes para extração de informações do header."""

    def test_extrair_header_completo(self):
        """Extrai todas as informações do header."""
        parser = PDFOrcamentoParser()
        parser.texto_completo = """
        Cliente:002633
        MARCIO DOS SANTOS SILVA
        NYCOLAS HENDRIGO MANCINI27/10/25Orçamento Nº:
        30703
        VALOR TOTAL R$ 1.405,00
        Condição de Pagto: À VISTA
        Forma de Pagto: PIX
        """

        header = parser.extrair_header()

        assert header['codigo_cliente'] == '002633'
        assert header['nome_cliente'] == 'MARCIO DOS SANTOS SILVA'
        assert header['vendedor'] == 'NYCOLAS HENDRIGO MANCINI'
        assert header['data'] == '27/10/25'
        assert header['numero'] == '30703'
        assert header['valor_total'] == '1.405,00'
        assert header['condicao_pagamento'] == 'À VISTA'
        assert header['forma_pagamento'] == 'PIX'

    def test_extrair_header_nome_sem_cnpj(self):
        """Extrai nome de cliente sem número CNPJ/CPF (EDGE CASE)."""
        parser = PDFOrcamentoParser()
        parser.texto_completo = """
        Cliente:003456
        ALI KHALIL FADEL
        NYCOLAS HENDRIGO MANCINI28/10/25Orçamento Nº:
        30724
        """

        header = parser.extrair_header()

        assert header['codigo_cliente'] == '003456'
        assert header['nome_cliente'] == 'ALI KHALIL FADEL'

    def test_extrair_header_parcial(self):
        """Extrai header mesmo com campos opcionais faltando."""
        parser = PDFOrcamentoParser()
        parser.texto_completo = """
        Cliente:001234
        TESTE CLIENTE
        30500
        VALOR TOTAL R$ 500,00
        """

        header = parser.extrair_header()

        assert header['codigo_cliente'] == '001234'
        assert header['nome_cliente'] == 'TESTE CLIENTE'
        assert header['numero'] == '30500'
        assert header['valor_total'] == '500,00'
        # Campos opcionais devem estar ausentes ou None
        assert header.get('condicao_pagamento') is None
        assert header.get('forma_pagamento') is None


class TestParseCompleto:
    """Testes para parsing completo de PDF."""

    @pytest.fixture
    def pdf_path_marcio(self):
        """Caminho para PDF de teste (Marcio - 10 produtos)."""
        return '/Users/nycolasmancini/Documents/Orcamento - 30703 - Marcio - R$ 1405,00.pdf'

    def test_parse_pdf_completo(self, pdf_path_marcio):
        """Parse completo de PDF real com validação."""
        parser = PDFOrcamentoParser(pdf_path_marcio)

        orcamento = parser.parse()

        # Validações do orçamento
        assert orcamento.numero == '30703'
        assert orcamento.codigo_cliente == '002633'
        # Nome do cliente pode variar, apenas verifica que não está vazio
        assert len(orcamento.nome_cliente) > 0
        assert orcamento.valor_total == Decimal("1405.00")

        # Validações dos produtos
        assert len(orcamento.produtos) == 10

        # Todos os produtos devem ter validação matemática = True
        for produto in orcamento.produtos:
            assert produto.validacao_matematica is True

        # Validação de integridade
        assert parser.validar_integridade() is True

    def test_parse_pdf_inexistente(self):
        """Lança erro ao tentar abrir PDF inexistente."""
        parser = PDFOrcamentoParser('/caminho/invalido.pdf')

        with pytest.raises(ParserError):
            parser.parse()

    def test_parse_pdf_sem_produtos(self):
        """Parse de PDF sem produtos válidos retorna lista vazia."""
        # Este teste requer mock ou PDF de teste especial
        # Por ora, marcamos como exemplo de estrutura
        pass


class TestValidarIntegridade:
    """Testes para validação de integridade do orçamento."""

    def test_validar_integridade_ok(self):
        """Valida integridade quando soma dos produtos = valor total."""
        parser = PDFOrcamentoParser()

        # Mock de orçamento válido
        produtos = [
            Produto(
                codigo='01234',
                descricao='PRODUTO 1',
                unidade='UN',
                quantidade=Decimal('10'),
                valor_unitario=Decimal('10.00'),
                valor_total=Decimal('100.00'),
                linha_original='',
                validacao_matematica=True
            ),
            Produto(
                codigo='05678',
                descricao='PRODUTO 2',
                unidade='UN',
                quantidade=Decimal('5'),
                valor_unitario=Decimal('20.00'),
                valor_total=Decimal('100.00'),
                linha_original='',
                validacao_matematica=True
            )
        ]

        parser.orcamento = Orcamento(
            numero='30000',
            codigo_cliente='000001',
            nome_cliente='TESTE',
            vendedor='VENDEDOR TESTE',
            data='01/01/25',
            valor_total=Decimal('200.00'),  # 100 + 100
            produtos=produtos
        )

        assert parser.validar_integridade() is True

    def test_validar_integridade_falha_soma(self):
        """Detecta falha quando soma dos produtos ≠ valor total."""
        parser = PDFOrcamentoParser()

        produtos = [
            Produto(
                codigo='01234',
                descricao='PRODUTO 1',
                unidade='UN',
                quantidade=Decimal('10'),
                valor_unitario=Decimal('10.00'),
                valor_total=Decimal('100.00'),
                linha_original='',
                validacao_matematica=True
            )
        ]

        parser.orcamento = Orcamento(
            numero='30000',
            codigo_cliente='000001',
            nome_cliente='TESTE',
            vendedor='VENDEDOR TESTE',
            data='01/01/25',
            valor_total=Decimal('500.00'),  # ≠ 100
            produtos=produtos
        )

        assert parser.validar_integridade() is False

    def test_validar_integridade_falha_produto_invalido(self):
        """Detecta falha quando produto tem validacao_matematica = False."""
        parser = PDFOrcamentoParser()

        produtos = [
            Produto(
                codigo='01234',
                descricao='PRODUTO INVALIDO',
                unidade='UN',
                quantidade=Decimal('10'),
                valor_unitario=Decimal('10.00'),
                valor_total=Decimal('100.00'),
                linha_original='',
                validacao_matematica=False  # INVÁLIDO
            )
        ]

        parser.orcamento = Orcamento(
            numero='30000',
            codigo_cliente='000001',
            nome_cliente='TESTE',
            vendedor='VENDEDOR TESTE',
            data='01/01/25',
            valor_total=Decimal('100.00'),
            produtos=produtos
        )

        assert parser.validar_integridade() is False


class TestExtrairDescricaoProduto:
    """Testes para extração de descrição de produto."""

    def test_extrair_descricao_simples(self):
        """Extrai descrição simples sem números."""
        parser = PDFOrcamentoParser()
        texto = "01234 PELICULA VIDRO TEMPERADO 300 0,90 270,00"
        codigo = "01234"
        numeros = [Decimal("300"), Decimal("0.90"), Decimal("270.00")]
        idx_inicio = 0

        descricao = parser.extrair_descricao_produto(texto, codigo, numeros, idx_inicio)

        assert descricao == "PELICULA VIDRO TEMPERADO"

    def test_extrair_descricao_preserva_numeros_texto(self):
        """Preserva números que fazem parte do texto livre (EDGE CASE CRÍTICO)."""
        parser = PDFOrcamentoParser()
        texto = "01689 AVELUDADA (27 MODELOS) 50UN CADA 1350 3,50 4725,00"
        codigo = "01689"
        # Todos os números extraídos
        numeros = [Decimal("27"), Decimal("50"), Decimal("1350"), Decimal("3.50"), Decimal("4725.00")]
        idx_inicio = 2  # Começa em 1350 (os 3 últimos validados)

        descricao = parser.extrair_descricao_produto(texto, codigo, numeros, idx_inicio)

        # Deve preservar "27 MODELOS" e "50UN CADA"
        assert "27" in descricao or "MODELOS" in descricao
        assert "50UN" in descricao or "CADA" in descricao
        # Não deve conter os valores validados
        assert "1350" not in descricao
        assert "3,50" not in descricao
        assert "4725" not in descricao
