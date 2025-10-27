# -*- coding: utf-8 -*-
"""
Repositório para Produto (Fase 9).

Este módulo implementa o padrão Repository para a entidade Produto.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from core.domain.produto.entities import Produto as ProdutoEntity
from core.infrastructure.persistence.models.produto import Produto as ProdutoDjango

# Configuração de logging
logger = logging.getLogger(__name__)


class ProdutoRepositoryInterface(ABC):
    """
    Interface do repositório de Produto (padrão Repository).

    Define operações de persistência para a entidade Produto.
    """

    @abstractmethod
    def save(self, produto: ProdutoEntity) -> ProdutoEntity:
        """
        Salva um produto no banco de dados.

        Args:
            produto (ProdutoEntity): Entidade Produto a ser salva

        Returns:
            ProdutoEntity: Produto salvo com ID atualizado
        """
        pass

    @abstractmethod
    def get_by_codigo(self, codigo: str) -> Optional[ProdutoEntity]:
        """
        Busca um produto pelo código.

        Args:
            codigo (str): Código do produto (5 dígitos)

        Returns:
            Optional[ProdutoEntity]: Produto encontrado ou None
        """
        pass

    @abstractmethod
    def get_by_id(self, produto_id: int) -> Optional[ProdutoEntity]:
        """
        Busca um produto pelo ID.

        Args:
            produto_id (int): ID do produto

        Returns:
            Optional[ProdutoEntity]: Produto encontrado ou None
        """
        pass

    @abstractmethod
    def get_all(self) -> List[ProdutoEntity]:
        """
        Retorna todos os produtos.

        Returns:
            List[ProdutoEntity]: Lista de produtos
        """
        pass

    @abstractmethod
    def delete(self, codigo: str) -> bool:
        """
        Deleta um produto pelo código.

        Args:
            codigo (str): Código do produto

        Returns:
            bool: True se deletado, False se não encontrado
        """
        pass


class DjangoProdutoRepository(ProdutoRepositoryInterface):
    """
    Implementação do repositório de Produto usando Django ORM.

    Esta classe implementa a interface ProdutoRepositoryInterface
    usando o Django ORM para persistência no banco de dados.
    """

    def save(self, produto: ProdutoEntity) -> ProdutoEntity:
        """
        Salva um produto no banco de dados.

        Se o produto já existe (tem ID), atualiza. Caso contrário, cria novo.

        Args:
            produto (ProdutoEntity): Entidade Produto a ser salva

        Returns:
            ProdutoEntity: Produto salvo com ID atualizado

        Example:
            >>> repo = DjangoProdutoRepository()
            >>> produto = Produto(codigo='00010', descricao='CABO USB', ...)
            >>> produto_salvo = repo.save(produto)
        """
        try:
            if produto.id:
                # Atualizar existente
                produto_django = ProdutoDjango.objects.get(id=produto.id)
                produto_django.codigo = produto.codigo
                produto_django.descricao = produto.descricao
                produto_django.quantidade = produto.quantidade
                produto_django.valor_unitario = produto.valor_unitario
                produto_django.valor_total = produto.valor_total
                produto_django.save()
                logger.info(f'Produto atualizado: {produto.codigo} - {produto.descricao}')
            else:
                # Criar novo
                produto_django = ProdutoDjango.from_entity(produto)
                produto_django.save()
                logger.info(f'Produto criado: {produto.codigo} - {produto.descricao}')

            return produto_django.to_entity()
        except Exception as e:
            logger.error(f'Erro ao salvar produto {produto.codigo}: {str(e)}')
            raise

    def get_by_codigo(self, codigo: str) -> Optional[ProdutoEntity]:
        """
        Busca um produto pelo código.

        Args:
            codigo (str): Código do produto (5 dígitos)

        Returns:
            Optional[ProdutoEntity]: Produto encontrado ou None

        Example:
            >>> repo = DjangoProdutoRepository()
            >>> produto = repo.get_by_codigo('00010')
        """
        try:
            produto_django = ProdutoDjango.objects.get(codigo=codigo)
            logger.info(f'Produto encontrado: {codigo}')
            return produto_django.to_entity()
        except ProdutoDjango.DoesNotExist:
            logger.warning(f'Produto não encontrado: {codigo}')
            return None

    def get_by_id(self, produto_id: int) -> Optional[ProdutoEntity]:
        """
        Busca um produto pelo ID.

        Args:
            produto_id (int): ID do produto

        Returns:
            Optional[ProdutoEntity]: Produto encontrado ou None

        Example:
            >>> repo = DjangoProdutoRepository()
            >>> produto = repo.get_by_id(1)
        """
        try:
            produto_django = ProdutoDjango.objects.get(id=produto_id)
            return produto_django.to_entity()
        except ProdutoDjango.DoesNotExist:
            return None

    def get_all(self) -> List[ProdutoEntity]:
        """
        Retorna todos os produtos ordenados por código.

        Returns:
            List[ProdutoEntity]: Lista de produtos

        Example:
            >>> repo = DjangoProdutoRepository()
            >>> produtos = repo.get_all()
        """
        produtos_django = ProdutoDjango.objects.all().order_by('codigo')
        return [p.to_entity() for p in produtos_django]

    def delete(self, codigo: str) -> bool:
        """
        Deleta um produto pelo código.

        Args:
            codigo (str): Código do produto

        Returns:
            bool: True se deletado, False se não encontrado

        Example:
            >>> repo = DjangoProdutoRepository()
            >>> deletado = repo.delete('00010')
        """
        try:
            produto_django = ProdutoDjango.objects.get(codigo=codigo)
            descricao = produto_django.descricao
            produto_django.delete()
            logger.info(f'Produto deletado: {codigo} - {descricao}')
            return True
        except ProdutoDjango.DoesNotExist:
            logger.warning(f'Tentativa de deletar produto inexistente: {codigo}')
            return False
