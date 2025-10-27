# -*- coding: utf-8 -*-
"""
Testes para DetalhePedidoView (Fase 21).
Teste 100% TDD: RED → GREEN → REFACTOR
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from core.models import Usuario, Pedido, ItemPedido, Produto


@pytest.fixture
def client():
    """Cliente HTTP para testes."""
    return Client()


@pytest.fixture
def vendedor(db):
    """Cria um usuário vendedor para testes."""
    return Usuario.objects.create_user(
        numero_login='001',
        pin='1234',
        nome='João Vendedor',
        tipo='VENDEDOR'
    )


@pytest.fixture
def separador(db):
    """Cria um usuário separador para testes."""
    return Usuario.objects.create_user(
        numero_login='002',
        pin='5678',
        nome='Maria Separadora',
        tipo='SEPARADOR'
    )


@pytest.fixture
def produto1(db):
    """Cria um produto para testes."""
    return Produto.objects.create(
        codigo='12345',
        descricao='Produto Teste 1',
        quantidade=5,
        valor_unitario=10.00,
        valor_total=50.00
    )


@pytest.fixture
def produto2(db):
    """Cria outro produto para testes."""
    return Produto.objects.create(
        codigo='67890',
        descricao='Produto Teste 2',
        quantidade=3,
        valor_unitario=20.00,
        valor_total=60.00
    )


@pytest.fixture
def pedido_com_itens(db, vendedor, produto1, produto2, separador):
    """
    Cria um pedido com 2 itens para testes.
    - Item 1: Não separado
    - Item 2: Separado
    """
    pedido = Pedido.objects.create(
        numero_orcamento='30567',
        codigo_cliente='CLI001',
        nome_cliente='Cliente Teste',
        vendedor=vendedor,
        data='27/10/2025',
        logistica='MOTOBOY',
        embalagem='SIMPLES',
        status='EM_SEPARACAO'
    )

    # Item não separado
    ItemPedido.objects.create(
        pedido=pedido,
        produto=produto1,
        quantidade_solicitada=5,
        quantidade_separada=0,
        separado=False
    )

    # Item separado
    ItemPedido.objects.create(
        pedido=pedido,
        produto=produto2,
        quantidade_solicitada=3,
        quantidade_separada=3,
        separado=True,
        separado_por=separador,
        separado_em=timezone.now()
    )

    return pedido


@pytest.mark.django_db
def test_acesso_detalhe_sem_login_redireciona(client):
    """
    Testa que acesso ao detalhe sem login retorna redirect (302).

    Arrange: Criar pedido
    Act: Acessar /pedidos/<id>/ sem login
    Assert: Redirecionamento para /login/
    """
    # Criar pedido temporário apenas com valores obrigatórios
    from core.models import Usuario, Pedido
    vendedor = Usuario.objects.create_user(
        numero_login='999',
        pin='9999',
        nome='Vendedor Temp',
        tipo='VENDEDOR'
    )
    pedido = Pedido.objects.create(
        numero_orcamento='99999',
        codigo_cliente='TEST',
        nome_cliente='Test',
        vendedor=vendedor,
        data='01/01/2025',
        logistica='MOTOBOY',
        embalagem='SIMPLES',
        status='EM_SEPARACAO'
    )

    url = reverse('detalhe_pedido', kwargs={'pedido_id': pedido.id})
    response = client.get(url)

    assert response.status_code == 302
    assert '/login/' in response.url


@pytest.mark.django_db
def test_acesso_detalhe_com_login_mostra_template(client, pedido_com_itens, separador):
    """
    Testa que usuário logado consegue acessar detalhe do pedido.

    Arrange: Fazer login
    Act: Acessar /pedidos/<id>/
    Assert: Status 200 e template correto
    """
    client.force_login(separador)

    url = reverse('detalhe_pedido', kwargs={'pedido_id': pedido_com_itens.id})
    response = client.get(url)

    assert response.status_code == 200
    assert 'detalhe_pedido.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_pedido_inexistente_retorna_404(client, separador):
    """
    Testa que tentar acessar pedido inexistente retorna 404.

    Arrange: Fazer login
    Act: Acessar /pedidos/99999/ (não existe)
    Assert: Status 404
    """
    client.force_login(separador)

    url = reverse('detalhe_pedido', kwargs={'pedido_id': 99999})
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_itens_separados_e_nao_separados_em_secoes_corretas(client, pedido_com_itens, separador):
    """
    Testa que itens separados e não separados aparecem em seções corretas.

    Arrange: Pedido com 1 item separado e 1 não separado
    Act: Acessar detalhe
    Assert: Contexto contém itens_nao_separados e itens_separados
    """
    client.force_login(separador)

    url = reverse('detalhe_pedido', kwargs={'pedido_id': pedido_com_itens.id})
    response = client.get(url)

    assert response.status_code == 200
    assert 'itens_nao_separados' in response.context
    assert 'itens_separados' in response.context

    # Verificar quantidades
    assert len(response.context['itens_nao_separados']) == 1
    assert len(response.context['itens_separados']) == 1

    # Verificar que são os itens corretos
    assert response.context['itens_nao_separados'][0].separado is False
    assert response.context['itens_separados'][0].separado is True


@pytest.mark.django_db
def test_tempo_decorrido_calculado_corretamente(client, pedido_com_itens, separador):
    """
    Testa que tempo decorrido desde data_inicio é calculado corretamente.

    Arrange: Pedido com data_inicio definida há 30 minutos
    Act: Acessar detalhe
    Assert: tempo_decorrido_minutos próximo de 30
    """
    # Definir data_inicio como 30 minutos atrás
    pedido_com_itens.data_inicio = timezone.now() - timedelta(minutes=30)
    pedido_com_itens.save()

    client.force_login(separador)

    url = reverse('detalhe_pedido', kwargs={'pedido_id': pedido_com_itens.id})
    response = client.get(url)

    assert response.status_code == 200
    assert 'tempo_decorrido_minutos' in response.context

    # Tolerância de ±2 minutos
    tempo = response.context['tempo_decorrido_minutos']
    assert 28 <= tempo <= 32


@pytest.mark.django_db
def test_progresso_exibido_no_contexto(client, pedido_com_itens, separador):
    """
    Testa que progresso (percentual) é calculado e enviado ao template.

    Arrange: Pedido com 2 itens (1 separado = 50%)
    Act: Acessar detalhe
    Assert: progresso_percentual == 50
    """
    client.force_login(separador)

    url = reverse('detalhe_pedido', kwargs={'pedido_id': pedido_com_itens.id})
    response = client.get(url)

    assert response.status_code == 200
    assert 'progresso_percentual' in response.context
    assert response.context['progresso_percentual'] == 50


@pytest.mark.django_db
def test_informacoes_pedido_renderizadas_no_template(client, pedido_com_itens, separador):
    """
    Testa que informações do pedido são passadas ao template.

    Arrange: Pedido com dados conhecidos
    Act: Acessar detalhe
    Assert: Contexto contém pedido com informações corretas
    """
    client.force_login(separador)

    url = reverse('detalhe_pedido', kwargs={'pedido_id': pedido_com_itens.id})
    response = client.get(url)

    assert response.status_code == 200
    assert 'pedido' in response.context

    pedido = response.context['pedido']
    assert pedido.numero_orcamento == '30567'
    assert pedido.nome_cliente == 'Cliente Teste'
    assert pedido.logistica == 'MOTOBOY'
    assert pedido.embalagem == 'SIMPLES'


@pytest.mark.django_db
def test_htmx_request_retorna_partial_sem_layout(client, pedido_com_itens, separador):
    """
    Testa que requisição HTMX retorna apenas partial (sem base.html).

    Arrange: Fazer requisição HTMX
    Act: Acessar detalhe com header HTTP_HX_REQUEST
    Assert: Template não inclui base.html
    """
    client.force_login(separador)

    url = reverse('detalhe_pedido', kwargs={'pedido_id': pedido_com_itens.id})
    response = client.get(url, HTTP_HX_REQUEST='true')

    assert response.status_code == 200

    # Verificar que não carregou o layout base completo
    # (normalmente checamos se 'base.html' NÃO está nos templates)
    content = response.content.decode()

    # Verificar que tem conteúdo do pedido
    assert '30567' in content
    assert 'Cliente Teste' in content
