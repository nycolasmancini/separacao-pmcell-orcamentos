# -*- coding: utf-8 -*-
"""
Testes unitários para a entidade Produto (Fase 9).

Este módulo testa a entidade de domínio Produto seguindo TDD rigoroso.
Todos os testes foram escritos ANTES da implementação (RED phase).
"""

import pytest
from decimal import Decimal
from core.domain.produto.entities import Produto


class TestProdutoCriacao:
    """Testes de criação da entidade Produto."""

    def test_produto_creation_with_valid_data(self):
        """Testa criação de produto com todos os dados válidos."""
        produto = Produto(
            codigo='00010',
            descricao='CABO USB TIPO C',
            quantidade=10,
            valor_unitario=Decimal('1.40'),
            valor_total=Decimal('14.00')
        )

        assert produto.codigo == '00010'
        assert produto.descricao == 'CABO USB TIPO C'
        assert produto.quantidade == 10
        assert produto.valor_unitario == Decimal('1.40')
        assert produto.valor_total == Decimal('14.00')

    def test_produto_required_fields(self):
        """Testa que todos os campos são obrigatórios."""
        # Testar falta de código
        with pytest.raises((TypeError, ValueError)):
            Produto(
                descricao='CABO USB',
                quantidade=10,
                valor_unitario=Decimal('1.40'),
                valor_total=Decimal('14.00')
            )

        # Testar falta de descrição
        with pytest.raises((TypeError, ValueError)):
            Produto(
                codigo='00010',
                quantidade=10,
                valor_unitario=Decimal('1.40'),
                valor_total=Decimal('14.00')
            )


class TestProdutoValidacoes:
    """Testes de validações da entidade Produto."""

    def test_produto_codigo_must_be_5_digits(self):
        """Testa que código deve ter exatamente 5 dígitos."""
        # Código com menos de 5 dígitos
        with pytest.raises(ValueError, match='.*5 dígitos.*'):
            Produto(
                codigo='123',
                descricao='CABO USB',
                quantidade=10,
                valor_unitario=Decimal('1.40'),
                valor_total=Decimal('14.00')
            )

        # Código com mais de 5 dígitos
        with pytest.raises(ValueError, match='.*5 dígitos.*'):
            Produto(
                codigo='123456',
                descricao='CABO USB',
                quantidade=10,
                valor_unitario=Decimal('1.40'),
                valor_total=Decimal('14.00')
            )

        # Código não numérico
        with pytest.raises(ValueError, match='.*5 dígitos.*'):
            Produto(
                codigo='ABCDE',
                descricao='CABO USB',
                quantidade=10,
                valor_unitario=Decimal('1.40'),
                valor_total=Decimal('14.00')
            )

    def test_produto_mathematical_validation_correct(self):
        """Testa validação matemática com cálculo correto."""
        produto = Produto(
            codigo='00010',
            descricao='CABO USB',
            quantidade=10,
            valor_unitario=Decimal('1.40'),
            valor_total=Decimal('14.00')
        )

        assert produto.validar_calculo() is True

        # Teste com valores decimais complexos
        produto2 = Produto(
            codigo='00020',
            descricao='PELÍCULA',
            quantidade=15,
            valor_unitario=Decimal('3.33'),
            valor_total=Decimal('49.95')
        )

        assert produto2.validar_calculo() is True

    def test_produto_mathematical_validation_fails_with_wrong_total(self):
        """Testa que validação matemática falha com total incorreto."""
        with pytest.raises(ValueError, match='.*validação matemática.*'):
            Produto(
                codigo='00010',
                descricao='CABO USB',
                quantidade=10,
                valor_unitario=Decimal('1.40'),
                valor_total=Decimal('15.00')  # Errado (deveria ser 14.00)
            )

        with pytest.raises(ValueError, match='.*validação matemática.*'):
            Produto(
                codigo='00020',
                descricao='PELÍCULA',
                quantidade=15,
                valor_unitario=Decimal('3.33'),
                valor_total=Decimal('50.00')  # Errado (deveria ser 49.95)
            )

    def test_produto_decimal_precision(self):
        """Testa valores monetários com precisão decimal."""
        produto = Produto(
            codigo='00010',
            descricao='CABO USB',
            quantidade=3,
            valor_unitario=Decimal('1.33'),
            valor_total=Decimal('3.99')
        )

        assert produto.validar_calculo() is True
        assert produto.valor_unitario == Decimal('1.33')
        assert produto.valor_total == Decimal('3.99')

        # Teste com muitas casas decimais (deve falhar na validação matemática)
        with pytest.raises(ValueError, match='.*validação matemática.*'):
            Produto(
                codigo='00020',
                descricao='PELÍCULA',
                quantidade=3,
                valor_unitario=Decimal('1.33'),
                valor_total=Decimal('4.00')  # Errado (3 * 1.33 = 3.99)
            )


class TestProdutoRepositorio:
    """Testes de integração com repositório (Django Model)."""

    @pytest.mark.django_db
    def test_produto_repository_save_and_retrieve(self):
        """Testa salvar e recuperar produto do banco via repositório."""
        from core.infrastructure.persistence.repositories.produto_repository import (
            DjangoProdutoRepository
        )

        repo = DjangoProdutoRepository()

        # Criar produto
        produto = Produto(
            codigo='00010',
            descricao='CABO USB TIPO C',
            quantidade=10,
            valor_unitario=Decimal('1.40'),
            valor_total=Decimal('14.00')
        )

        # Salvar no banco
        produto_salvo = repo.save(produto)
        assert produto_salvo.codigo == '00010'

        # Recuperar do banco
        produto_recuperado = repo.get_by_codigo('00010')
        assert produto_recuperado is not None
        assert produto_recuperado.codigo == '00010'
        assert produto_recuperado.descricao == 'CABO USB TIPO C'
        assert produto_recuperado.quantidade == 10
        assert produto_recuperado.valor_unitario == Decimal('1.40')
        assert produto_recuperado.valor_total == Decimal('14.00')

    @pytest.mark.django_db
    def test_produto_django_model_integration(self):
        """Testa integração com modelo Django."""
        from core.infrastructure.persistence.models.produto import Produto as ProdutoDjango

        # Criar via Django Model
        produto_django = ProdutoDjango.objects.create(
            codigo='00020',
            descricao='PELÍCULA 3D',
            quantidade=20,
            valor_unitario=Decimal('5.50'),
            valor_total=Decimal('110.00')
        )

        # Converter para entidade de domínio
        produto_entidade = produto_django.to_entity()

        assert produto_entidade.codigo == '00020'
        assert produto_entidade.descricao == 'PELÍCULA 3D'
        assert produto_entidade.quantidade == 20
        assert produto_entidade.valor_unitario == Decimal('5.50')
        assert produto_entidade.valor_total == Decimal('110.00')
        assert produto_entidade.validar_calculo() is True
