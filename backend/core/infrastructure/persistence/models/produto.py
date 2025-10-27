# -*- coding: utf-8 -*-
"""
Modelo Django para Produto (Fase 9).

Este módulo define o modelo Django que persiste a entidade Produto no banco de dados.
"""

from decimal import Decimal
from django.db import models
from core.domain.produto.entities import Produto as ProdutoEntity


class Produto(models.Model):
    """
    Modelo Django para persistência de Produto.

    Fields:
        codigo (CharField): Código do produto (5 dígitos, único)
        descricao (CharField): Descrição do produto
        quantidade (IntegerField): Quantidade do produto
        valor_unitario (DecimalField): Valor unitário (2 casas decimais)
        valor_total (DecimalField): Valor total (2 casas decimais)
        criado_em (DateTimeField): Data de criação (auto)
        atualizado_em (DateTimeField): Data de atualização (auto)
    """

    codigo = models.CharField(
        max_length=5,
        unique=True,
        db_index=True,
        help_text='Código do produto (5 dígitos numéricos)'
    )
    descricao = models.CharField(
        max_length=255,
        help_text='Descrição do produto'
    )
    quantidade = models.IntegerField(
        help_text='Quantidade do produto'
    )
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Valor unitário do produto'
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Valor total (quantidade × valor_unitario)'
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        help_text='Data de criação do registro'
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        help_text='Data de última atualização'
    )

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['codigo']
        db_table = 'core_produto'

    def __str__(self):
        """Representação em string do produto."""
        return f'{self.codigo} - {self.descricao}'

    def to_entity(self) -> ProdutoEntity:
        """
        Converte o modelo Django para a entidade de domínio.

        Returns:
            ProdutoEntity: Entidade de domínio Produto

        Example:
            >>> produto_django = Produto.objects.get(codigo='00010')
            >>> produto_entity = produto_django.to_entity()
        """
        return ProdutoEntity(
            id=self.id,
            codigo=self.codigo,
            descricao=self.descricao,
            quantidade=self.quantidade,
            valor_unitario=self.valor_unitario,
            valor_total=self.valor_total
        )

    @staticmethod
    def from_entity(entity: ProdutoEntity) -> 'Produto':
        """
        Cria um modelo Django a partir de uma entidade de domínio.

        Args:
            entity (ProdutoEntity): Entidade de domínio Produto

        Returns:
            Produto: Modelo Django Produto

        Example:
            >>> from core.domain.produto.entities import Produto as ProdutoEntity
            >>> entity = ProdutoEntity(codigo='00010', descricao='CABO USB', ...)
            >>> produto_django = Produto.from_entity(entity)
            >>> produto_django.save()
        """
        produto_dict = {
            'codigo': entity.codigo,
            'descricao': entity.descricao,
            'quantidade': entity.quantidade,
            'valor_unitario': entity.valor_unitario,
            'valor_total': entity.valor_total
        }

        if entity.id:
            produto_dict['id'] = entity.id

        return Produto(**produto_dict)
