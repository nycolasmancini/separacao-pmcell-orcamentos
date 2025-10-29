# -*- coding: utf-8 -*-
"""
Repositório para Pedido (Fase 13).

Este módulo implementa o padrão Repository para a entidade Pedido.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from core.domain.pedido.entities import Pedido as PedidoEntity
from core.models import Pedido as PedidoDjango, ItemPedido as ItemPedidoDjango, Usuario

# Configuração de logging
logger = logging.getLogger(__name__)


class PedidoRepositoryInterface(ABC):
    """
    Interface do repositório de Pedido (padrão Repository).

    Define operações de persistência para a entidade Pedido.
    """

    @abstractmethod
    def save(self, pedido: PedidoEntity) -> PedidoEntity:
        """
        Salva um pedido no banco de dados.

        Args:
            pedido: Entidade Pedido a ser salva

        Returns:
            Pedido salvo com ID atualizado
        """
        pass

    @abstractmethod
    def get_by_id(self, pedido_id: int) -> Optional[PedidoEntity]:
        """
        Busca um pedido pelo ID.

        Args:
            pedido_id: ID do pedido

        Returns:
            Pedido encontrado ou None
        """
        pass

    @abstractmethod
    def get_by_numero_orcamento(self, numero_orcamento: str) -> Optional[PedidoEntity]:
        """
        Busca um pedido pelo número do orçamento.

        Args:
            numero_orcamento: Número único do orçamento

        Returns:
            Pedido encontrado ou None
        """
        pass

    @abstractmethod
    def get_em_separacao(self) -> List[PedidoEntity]:
        """
        Retorna todos os pedidos em separação.

        Returns:
            Lista de pedidos com status EM_SEPARACAO
        """
        pass

    @abstractmethod
    def get_all(self) -> List[PedidoEntity]:
        """
        Retorna todos os pedidos.

        Returns:
            Lista de todos os pedidos
        """
        pass

    @abstractmethod
    def delete(self, pedido_id: int) -> bool:
        """
        Deleta um pedido pelo ID.

        Args:
            pedido_id: ID do pedido

        Returns:
            True se deletado com sucesso, False caso contrário
        """
        pass


class DjangoPedidoRepository(PedidoRepositoryInterface):
    """
    Implementação do repositório de Pedido usando Django ORM.

    Converte entre entidades de domínio e modelos Django.
    """

    def save(self, pedido: PedidoEntity) -> PedidoEntity:
        """
        Salva um pedido no banco de dados.

        Args:
            pedido: Entidade Pedido a ser salva

        Returns:
            Pedido salvo com ID atualizado

        Raises:
            Exception: Se houver erro ao salvar
        """
        try:
            # Buscar vendedor
            vendedor = Usuario.objects.get(nome=pedido.vendedor)

            # Verificar se é update ou create
            if pedido.id:
                pedido_django = PedidoDjango.objects.get(id=pedido.id)
                pedido_django.numero_orcamento = pedido.numero_orcamento
                pedido_django.codigo_cliente = pedido.codigo_cliente
                pedido_django.nome_cliente = pedido.nome_cliente
                pedido_django.vendedor = vendedor
                pedido_django.data = pedido.data
                pedido_django.logistica = pedido.logistica.value
                pedido_django.embalagem = pedido.embalagem.value
                pedido_django.status = pedido.status.value
                pedido_django.observacoes = pedido.observacoes
                pedido_django.data_finalizacao = pedido.data_finalizacao
            else:
                # Criar novo pedido
                pedido_django = PedidoDjango.from_entity(pedido, vendedor)

            pedido_django.save()

            # Salvar itens
            for item_entity in pedido.itens:
                self._save_item(item_entity, pedido_django)

            logger.info(
                f"Pedido {pedido_django.numero_orcamento} salvo com sucesso "
                f"(ID: {pedido_django.id})"
            )

            # Retornar entidade atualizada
            return pedido_django.to_entity()

        except Usuario.DoesNotExist:
            logger.error(f"Vendedor '{pedido.vendedor}' não encontrado")
            raise ValueError(f"Vendedor '{pedido.vendedor}' não encontrado")
        except Exception as e:
            logger.error(f"Erro ao salvar pedido: {e}")
            raise

    def _save_item(self, item_entity, pedido_django):
        """
        Salva um item do pedido.

        Args:
            item_entity: Entidade ItemPedido
            pedido_django: Modelo Django Pedido
        """
        from core.infrastructure.persistence.models.produto import Produto as ProdutoDjango

        # Buscar produto
        produto_django = ProdutoDjango.objects.get(codigo=item_entity.produto.codigo)

        # Buscar usuário que separou (se houver)
        separado_por = None
        if item_entity.separado_por:
            separado_por = Usuario.objects.get(nome=item_entity.separado_por)

        # Verificar se é update ou create
        if item_entity.id:
            item_django = ItemPedidoDjango.objects.get(id=item_entity.id)
            item_django.quantidade_solicitada = item_entity.quantidade_solicitada
            item_django.quantidade_separada = item_entity.quantidade_separada
            item_django.separado = item_entity.separado
            item_django.separado_por = separado_por
            item_django.separado_em = item_entity.separado_em
        else:
            item_django = ItemPedidoDjango.from_entity(
                item_entity,
                pedido_django,
                produto_django,
                separado_por
            )

        item_django.save()

    def get_by_id(self, pedido_id: int) -> Optional[PedidoEntity]:
        """
        Busca um pedido pelo ID.

        Args:
            pedido_id: ID do pedido

        Returns:
            Pedido encontrado ou None
        """
        try:
            pedido_django = PedidoDjango.objects.prefetch_related('itens').get(id=pedido_id)
            logger.info(f"Pedido encontrado: ID {pedido_id}")
            return pedido_django.to_entity()
        except PedidoDjango.DoesNotExist:
            logger.warning(f"Pedido com ID {pedido_id} não encontrado")
            return None

    def get_by_numero_orcamento(self, numero_orcamento: str) -> Optional[PedidoEntity]:
        """
        Busca um pedido pelo número do orçamento.

        Args:
            numero_orcamento: Número único do orçamento

        Returns:
            Pedido encontrado ou None
        """
        try:
            pedido_django = PedidoDjango.objects.prefetch_related('itens').get(
                numero_orcamento=numero_orcamento
            )
            logger.info(f"Pedido encontrado: orçamento {numero_orcamento}")
            return pedido_django.to_entity()
        except PedidoDjango.DoesNotExist:
            logger.warning(f"Pedido com orçamento {numero_orcamento} não encontrado")
            return None

    def get_em_separacao(self) -> List[PedidoEntity]:
        """
        Retorna todos os pedidos em separação.

        Returns:
            Lista de pedidos com status EM_SEPARACAO
        """
        pedidos_django = PedidoDjango.objects.filter(
            status='EM_SEPARACAO'
        ).prefetch_related('itens').order_by('-criado_em')

        pedidos = [p.to_entity() for p in pedidos_django]
        logger.info(f"{len(pedidos)} pedidos em separação encontrados")
        return pedidos

    def get_all(self) -> List[PedidoEntity]:
        """
        Retorna todos os pedidos.

        Returns:
            Lista de todos os pedidos
        """
        pedidos_django = PedidoDjango.objects.prefetch_related('itens').order_by('-criado_em')
        pedidos = [p.to_entity() for p in pedidos_django]
        logger.info(f"{len(pedidos)} pedidos encontrados")
        return pedidos

    def delete(self, pedido_id: int) -> bool:
        """
        Deleta um pedido pelo ID.

        Args:
            pedido_id: ID do pedido

        Returns:
            True se deletado com sucesso, False caso contrário
        """
        try:
            pedido = PedidoDjango.objects.get(id=pedido_id)
            numero_orcamento = pedido.numero_orcamento
            pedido.delete()
            logger.info(f"Pedido {numero_orcamento} (ID: {pedido_id}) deletado com sucesso")
            return True
        except PedidoDjango.DoesNotExist:
            logger.warning(f"Pedido com ID {pedido_id} não encontrado para deleção")
            return False
