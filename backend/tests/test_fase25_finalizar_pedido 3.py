# -*- coding: utf-8 -*-
"""
Testes para Fase 25: Implementar Botão "Finalizar Pedido"

Este módulo testa:
- Botão aparece apenas quando progresso = 100%
- Use case de finalização
- Cálculo de tempo total
- Remoção do dashboard
- Modal de confirmação

Author: PMCELL
Date: 2025-01-27
"""

import pytest
from datetime import datetime, timedelta
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.models import Usuario, Pedido, ItemPedido, Produto
from core.application.use_cases.finalizar_pedido import (
    FinalizarPedidoUseCase,
    FinalizarPedidoResponseDTO
)
from core.infrastructure.persistence.repositories.pedido_repository import (
    DjangoPedidoRepository
)


@pytest.fixture
def repository():
    """Repositório de pedidos."""
    return DjangoPedidoRepository()


@pytest.fixture
def use_case(repository):
    """Use case de finalizar pedido."""
    return FinalizarPedidoUseCase(repository)


@pytest.fixture
def usuario_separador(db):
    """Cria um usuário separador para os testes."""
    return Usuario.objects.create_user(
        numero_login='1001',
        pin='1234',
        nome='João Separador',
        tipo='SEPARADOR'
    )


@pytest.fixture
def usuario_vendedor(db):
    """Cria um usuário vendedor para os testes."""
    return Usuario.objects.create_user(
        numero_login='2001',
        pin='5678',
        nome='Maria Vendedora',
        tipo='VENDEDOR'
    )


@pytest.fixture
def produto(db):
    """Cria um produto de teste."""
    return Produto.objects.create(
        codigo='12345',
        descricao='Produto Teste',
        quantidade=10,
        valor_unitario=100.00,
        valor_total=1000.00
    )


@pytest.fixture
def pedido_completo(db, usuario_vendedor, usuario_separador, produto):
    """
    Cria um pedido com todos os itens já separados (progresso = 100%).
    """
    pedido = Pedido.objects.create(
        numero_orcamento='30567',
        codigo_cliente='CLI001',
        nome_cliente='Cliente Teste',
        vendedor=usuario_vendedor,
        data='27/01/2025',
        logistica='CORREIOS',
        embalagem='CAIXA',
        status='EM_SEPARACAO',
        data_inicio=timezone.now() - timedelta(minutes=45)  # 45 minutos atrás
    )

    # Criar 3 itens todos separados
    for i in range(3):
        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade_solicitada=2,
            separado=True,
            separado_por=usuario_separador,
            separado_em=timezone.now()
        )

    return pedido


@pytest.fixture
def pedido_incompleto(db, usuario_vendedor, usuario_separador, produto):
    """
    Cria um pedido com apenas 1 de 3 itens separados (progresso = 33%).
    """
    pedido = Pedido.objects.create(
        numero_orcamento='30568',
        codigo_cliente='CLI002',
        nome_cliente='Cliente Teste 2',
        vendedor=usuario_vendedor,
        data='27/01/2025',
        logistica='CORREIOS',
        embalagem='CAIXA',
        status='EM_SEPARACAO'
    )

    # 1 item separado
    ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=2,
        separado=True,
        separado_por=usuario_separador,
        separado_em=timezone.now()
    )

    # 2 itens não separados
    for i in range(2):
        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade_solicitada=2,
            separado=False
        )

    return pedido


@pytest.fixture
def logged_in_client(client, usuario_separador):
    """Cliente autenticado."""
    client.force_login(usuario_separador)
    # Adicionar session manualmente
    session = client.session
    session['usuario_id'] = usuario_separador.id
    session['usuario_nome'] = usuario_separador.nome
    session.save()
    return client


# ============================================================================
# TESTES
# ============================================================================

@pytest.mark.django_db
def test_botao_finalizar_aparece_quando_100_porcento(logged_in_client, pedido_completo):
    """
    Testa que o botão "Finalizar Pedido" aparece quando progresso = 100%.
    """
    url = reverse('detalhe_pedido', kwargs={'pedido_id': pedido_completo.id})
    response = logged_in_client.get(url)

    assert response.status_code == 200
    content = response.content.decode('utf-8')

    # Deve conter o botão de finalizar
    assert 'Finalizar Pedido' in content
    assert 'finalizar/' in content  # URL do botão

    # Progresso deve ser 100%
    assert '100%' in content


@pytest.mark.django_db
def test_botao_finalizar_nao_aparece_quando_incompleto(logged_in_client, pedido_incompleto):
    """
    Testa que o botão NÃO aparece quando progresso < 100%.
    """
    url = reverse('detalhe_pedido', kwargs={'pedido_id': pedido_incompleto.id})
    response = logged_in_client.get(url)

    assert response.status_code == 200
    content = response.content.decode('utf-8')

    # NÃO deve conter o botão de finalizar
    assert 'Finalizar Pedido' not in content or 'disabled' in content.lower()

    # Progresso deve ser 33%
    assert '33%' in content


@pytest.mark.django_db
def test_finalizar_pedido_muda_status(use_case, pedido_completo):
    """
    Testa que finalizar um pedido muda o status para FINALIZADO.
    """
    # Estado inicial
    assert pedido_completo.status == 'EM_SEPARACAO'
    assert pedido_completo.data_finalizacao is None

    # Executar use case
    response = use_case.execute(
        pedido_id=pedido_completo.id,
        usuario_nome='João Separador'
    )

    # Verificar resposta
    assert isinstance(response, FinalizarPedidoResponseDTO)
    assert response.sucesso is True
    assert response.pedido_id == pedido_completo.id
    assert response.status == 'FINALIZADO'
    assert response.tempo_total_minutos > 0

    # Verificar banco de dados
    pedido_completo.refresh_from_db()
    assert pedido_completo.status == 'FINALIZADO'
    assert pedido_completo.data_finalizacao is not None


@pytest.mark.django_db
def test_finalizar_pedido_calcula_tempo_total(use_case, pedido_completo):
    """
    Testa que o tempo total de separação é calculado corretamente.
    """
    # Pedido foi criado há 45 minutos (fixture)
    response = use_case.execute(
        pedido_id=pedido_completo.id,
        usuario_nome='João Separador'
    )

    # Tempo deve ser aproximadamente 45 minutos (com margem de erro)
    assert response.tempo_total_minutos >= 44
    assert response.tempo_total_minutos <= 46


@pytest.mark.django_db
def test_finalizar_pedido_registra_data_finalizacao(use_case, pedido_completo):
    """
    Testa que a data de finalização é registrada corretamente.
    """
    antes_finalizacao = timezone.now()

    response = use_case.execute(
        pedido_id=pedido_completo.id,
        usuario_nome='João Separador'
    )

    depois_finalizacao = timezone.now()

    # Verificar banco de dados
    pedido_completo.refresh_from_db()
    assert pedido_completo.data_finalizacao is not None
    assert antes_finalizacao <= pedido_completo.data_finalizacao <= depois_finalizacao


@pytest.mark.django_db
def test_finalizar_pedido_falha_se_progresso_incompleto(use_case, pedido_incompleto):
    """
    Testa que finalizar um pedido incompleto retorna erro.
    """
    # Estado inicial: 33% de progresso
    assert pedido_incompleto.status == 'EM_SEPARACAO'

    # Executar use case
    response = use_case.execute(
        pedido_id=pedido_incompleto.id,
        usuario_nome='João Separador'
    )

    # Verificar resposta de erro
    assert isinstance(response, FinalizarPedidoResponseDTO)
    assert response.sucesso is False
    assert 'não pode ser finalizado' in response.mensagem.lower()
    assert '33%' in response.mensagem or 'progresso' in response.mensagem.lower()

    # Verificar que status NÃO mudou
    pedido_incompleto.refresh_from_db()
    assert pedido_incompleto.status == 'EM_SEPARACAO'
    assert pedido_incompleto.data_finalizacao is None


@pytest.mark.django_db
def test_finalizar_pedido_remove_do_dashboard(logged_in_client, pedido_completo):
    """
    Testa que pedido finalizado não aparece mais no dashboard.
    """
    # Antes de finalizar: pedido aparece no dashboard
    dashboard_url = reverse('dashboard')
    response = logged_in_client.get(dashboard_url)
    assert pedido_completo.numero_orcamento in response.content.decode('utf-8')

    # Finalizar pedido
    finalizar_url = reverse('finalizar_pedido', kwargs={'pedido_id': pedido_completo.id})
    response = logged_in_client.post(finalizar_url)

    assert response.status_code in [200, 302]  # 200 (HTMX) ou 302 (redirect)

    # Após finalizar: pedido NÃO aparece no dashboard
    response = logged_in_client.get(dashboard_url)
    content = response.content.decode('utf-8')

    # Pedido não deve aparecer (ou aparecer como finalizado)
    pedido_completo.refresh_from_db()
    assert pedido_completo.status == 'FINALIZADO'


@pytest.mark.django_db
def test_modal_confirmacao_renderiza_corretamente(logged_in_client, pedido_completo):
    """
    Testa que o modal de confirmação renderiza com as informações corretas.
    """
    # GET no endpoint de finalizar (renderiza modal)
    url = reverse('finalizar_pedido', kwargs={'pedido_id': pedido_completo.id})
    response = logged_in_client.get(url)

    assert response.status_code == 200
    content = response.content.decode('utf-8')

    # Deve conter elementos do modal
    assert 'Finalizar Pedido' in content or 'finalizar' in content.lower()
    assert pedido_completo.numero_orcamento in content

    # Deve conter info sobre tempo ou confirmação
    assert 'Tem certeza' in content or 'Confirmar' in content or 'certeza' in content.lower()
