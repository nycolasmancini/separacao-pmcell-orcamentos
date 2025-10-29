# -*- coding: utf-8 -*-
"""
Repositório para Pedido (Fase 13).

Este módulo implementa o padrão Repository para a entidade Pedido.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from django.db.models import Avg, ExpressionWrapper, F, fields
from django.db.models.functions import Extract
from django.db.utils import IntegrityError
from django.utils import timezone
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

    @abstractmethod
    def calcular_tempo_medio_finalizacao(
        self,
        data_inicio: datetime,
        data_fim: datetime
    ) -> Optional[float]:
        """
        Calcula tempo médio de finalização (em minutos) dos pedidos finalizados
        dentro de um período.

        Args:
            data_inicio: Data/hora de início do período (inclusivo)
            data_fim: Data/hora de fim do período (inclusivo)

        Returns:
            Tempo médio em minutos (float) ou None se não houver pedidos
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
                pedido_django.data_inicio = pedido.data_inicio
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
        except IntegrityError as e:
            # Tratar especificamente erro de orçamento duplicado
            if 'numero_orcamento' in str(e):
                logger.error(f"Orçamento {pedido.numero_orcamento} já existe no sistema")
                raise ValueError(f"Orçamento {pedido.numero_orcamento} já cadastrado no sistema")
            else:
                logger.error(f"Erro de integridade ao salvar pedido: {e}")
                raise ValueError(f"Erro de integridade no banco de dados: {e}")
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

        # Buscar ou criar produto automaticamente
        produto_django, created = ProdutoDjango.objects.get_or_create(
            codigo=item_entity.produto.codigo,
            defaults={
                'descricao': item_entity.produto.descricao,
                'quantidade': item_entity.produto.quantidade,
                'valor_unitario': item_entity.produto.valor_unitario,
                'valor_total': item_entity.produto.valor_total
            }
        )
        if created:
            logger.info(
                f"Produto {produto_django.codigo} criado automaticamente: "
                f"{produto_django.descricao} (Qtd: {produto_django.quantidade}, "
                f"Valor Unit: R$ {produto_django.valor_unitario})"
            )

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

    def calcular_tempo_medio_finalizacao(
        self,
        data_inicio: datetime,
        data_fim: datetime
    ) -> Optional[float]:
        """
        Calcula tempo médio de finalização (em minutos) dos pedidos finalizados
        dentro de um período.

        Args:
            data_inicio: Data/hora de início do período (inclusivo)
            data_fim: Data/hora de fim do período (inclusivo)

        Returns:
            Tempo médio em minutos (float) ou None se não houver pedidos
        """
        try:
            # Buscar pedidos finalizados no período
            pedidos = PedidoDjango.objects.filter(
                status='FINALIZADO',
                data_finalizacao__isnull=False,
                data_finalizacao__gte=data_inicio,
                data_finalizacao__lte=data_fim
            ).only('data_inicio', 'data_finalizacao')

            if not pedidos.exists():
                logger.info(
                    f"Nenhum pedido finalizado encontrado entre "
                    f"{data_inicio} e {data_fim}"
                )
                return None

            # Calcular duração de cada pedido em minutos
            duracoes_minutos = []
            for pedido in pedidos:
                duracao = pedido.data_finalizacao - pedido.data_inicio
                duracao_minutos = duracao.total_seconds() / 60.0
                duracoes_minutos.append(duracao_minutos)

            # Calcular média
            tempo_medio_minutos = sum(duracoes_minutos) / len(duracoes_minutos)

            logger.info(
                f"Tempo médio calculado: {tempo_medio_minutos:.2f} minutos "
                f"(período: {data_inicio} a {data_fim}, {len(duracoes_minutos)} pedidos)"
            )

            return tempo_medio_minutos

        except Exception as e:
            logger.error(f"Erro ao calcular tempo médio: {e}")
            raise

    def obter_itens_ordenados_por_estado(self, pedido_id: int) -> List:
        """
        Retorna itens do pedido ordenados por estado em lista corrida (Fase 39a).

        Ordem de prioridade:
        1. Aguardando separação (separado=False, em_compra=False)
        2. Enviados para compra (em_compra=True)
        3. Substituídos (separado=True, substituido=True)
        4. Separados (separado=True, substituido=False)

        Dentro de cada grupo, ordenação alfabética por descrição do produto.

        Args:
            pedido_id: ID do pedido

        Returns:
            Lista de ItemPedidoDjango ordenados por estado

        Example:
            >>> repository = DjangoPedidoRepository()
            >>> itens = repository.obter_itens_ordenados_por_estado(pedido_id=1)
            >>> for item in itens:
            ...     print(f"{item.produto.descricao}: {item.separado}, {item.em_compra}")
        """
        from django.db.models import Case, When, IntegerField

        try:
            itens = ItemPedidoDjango.objects.filter(pedido_id=pedido_id).select_related(
                'produto', 'pedido', 'separado_por'
            ).annotate(
                # Calcular prioridade de ordenação baseada no estado
                ordem_prioridade=Case(
                    # Aguardando: separado=False AND em_compra=False
                    When(separado=False, em_compra=False, then=1),
                    # Em compra: em_compra=True
                    When(em_compra=True, then=2),
                    # Substituído: separado=True AND substituido=True
                    When(separado=True, substituido=True, then=3),
                    # Separado (não substituído): separado=True AND substituido=False
                    When(separado=True, substituido=False, then=4),
                    default=5,  # Fallback para casos não mapeados
                    output_field=IntegerField()
                )
            ).order_by('ordem_prioridade', 'produto__descricao')

            logger.debug(
                f"Itens do pedido {pedido_id} ordenados por estado: "
                f"{itens.count()} itens encontrados"
            )

            return list(itens)

        except Exception as e:
            logger.error(
                f"Erro ao obter itens ordenados do pedido {pedido_id}: {e}"
            )
            raise
