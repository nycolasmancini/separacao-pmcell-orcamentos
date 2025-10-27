# -*- coding: utf-8 -*-
"""
Testes unitários para SubstituirItemUseCase (Fase 24).
"""
import pytest
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from core.application.use_cases.substituir_item import SubstituirItemUseCase
from core.domain.usuario.entities import Usuario as UsuarioDomain, TipoUsuario


@pytest.fixture
def separador_domain():
    """Fixture: entidade de domínio do usuário separador."""
    return UsuarioDomain(
        numero_login=1001,
        nome="João Separador",
        tipo=TipoUsuario.SEPARADOR
    )


@pytest.fixture
@pytest.mark.django_db
def separador(db):
    """Fixture: usuário separador no banco."""
    from core.models import Usuario
    return Usuario.objects.create_user(
        numero_login=1001,
        pin="1234",
        nome="João Separador",
        tipo="SEPARADOR"
    )


@pytest.fixture
@pytest.mark.django_db
def produto(db):
    """Fixture: produto no banco."""
    from core.infrastructure.persistence.models.produto import Produto
    return Produto.objects.create(
        codigo="USB001",
        descricao="CABO USB-C",
        quantidade=10,
        valor_unitario=Decimal("15.00"),
        valor_total=Decimal("150.00")
    )


@pytest.fixture
@pytest.mark.django_db
def vendedor(db):
    """Fixture: vendedor no banco."""
    from core.models import Usuario
    return Usuario.objects.create_user(
        numero_login=2001,
        pin="2222",
        nome="Vendedor Teste",
        tipo="VENDEDOR"
    )


@pytest.fixture
@pytest.mark.django_db
def pedido_com_itens(db, produto, vendedor):
    """Fixture: pedido com 3 itens no banco."""
    from core.models import Pedido, ItemPedido

    pedido = Pedido.objects.create(
        numero_orcamento="30567",
        codigo_cliente="CLI001",
        nome_cliente="Rosana",
        vendedor=vendedor,
        data="27/01/2025",
        logistica="CORREIOS",
        embalagem="CAIXA",
        status="EM_SEPARACAO"
    )

    # Criar 3 itens
    item1 = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=10,
        quantidade_separada=0,
        separado=False
    )
    item2 = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=20,
        quantidade_separada=0,
        separado=False
    )
    item3 = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=5,
        quantidade_separada=0,
        separado=False
    )

    return pedido


@pytest.mark.django_db
class TestSubstituirItemUseCase:
    """Testes para SubstituirItemUseCase."""

    def test_substituir_item_com_sucesso(self, pedido_com_itens, separador, separador_domain):
        """Testa substituição bem-sucedida de item."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens.first()

        result = use_case.execute(
            item_id=item.id,
            produto_substituto="CABO USB-C 2.0 TURBO",
            usuario=separador_domain
        )

        # Recarregar item do banco
        item.refresh_from_db()

        assert result.success is True
        assert item.substituido is True
        assert item.produto_substituto == "CABO USB-C 2.0 TURBO"
        assert item.separado is True  # Item deve ser marcado como separado
        assert item.separado_por == separador
        assert item.separado_em is not None

    def test_substituir_item_marca_como_separado_automaticamente(self, pedido_com_itens, separador, separador_domain):
        """Testa que substituir também marca como separado."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens.first()

        # Item ainda não foi separado
        assert item.separado is False

        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO USB TIPO C",
            usuario=separador_domain
        )

        item.refresh_from_db()

        # Após substituição, deve estar separado
        assert item.separado is True
        assert item.substituido is True

    def test_substituir_item_atualiza_progresso_pedido(self, pedido_com_itens, separador, separador_domain):
        """Testa que substituir atualiza o progresso do pedido."""
        use_case = SubstituirItemUseCase()

        # Progresso inicial: 0%
        itens_separados = pedido_com_itens.itens.filter(separado=True).count()
        total_itens = pedido_com_itens.itens.count()
        assert itens_separados == 0

        # Substituir primeiro item
        item = pedido_com_itens.itens.first()
        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO NOVO",
            usuario=separador_domain
        )

        # Progresso: 1/3 = 33.33%
        itens_separados = pedido_com_itens.itens.filter(separado=True).count()
        progresso = (itens_separados / total_itens) * 100
        assert progresso == pytest.approx(33.33, rel=0.01)

    def test_substituir_item_sem_produto_substituto_falha(self, pedido_com_itens, separador_domain):
        """Testa que substituir sem informar produto falha."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens.first()

        result = use_case.execute(
            item_id=item.id,
            produto_substituto="",  # Vazio
            usuario=separador_domain
        )

        assert result.success is False
        assert "produto substituto deve ser informado" in result.message.lower()

    def test_substituir_item_ja_separado(self, pedido_com_itens, separador, separador_domain):
        """Testa substituir item que já foi separado."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens.first()

        # Primeiro: marcar como separado normalmente
        item.separado = True
        item.separado_por = separador
        item.separado_em = timezone.now()
        item.save()

        # Depois: tentar substituir
        result = use_case.execute(
            item_id=item.id,
            produto_substituto="CABO NOVO",
            usuario=separador_domain
        )

        item.refresh_from_db()

        # Deve permitir (pode querer registrar substituição mesmo após separar)
        assert result.success is True
        assert item.substituido is True

    def test_substituir_item_ja_substituido_sobrescreve(self, pedido_com_itens, separador, separador_domain):
        """Testa substituir item que já foi substituído (sobrescreve)."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens.first()

        # Primeira substituição
        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO USB-C 1.0",
            usuario=separador_domain
        )

        item.refresh_from_db()
        assert item.produto_substituto == "CABO USB-C 1.0"

        # Segunda substituição (corrigir)
        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO USB-C 2.0",
            usuario=separador_domain
        )

        item.refresh_from_db()

        # Deve sobrescrever
        assert item.produto_substituto == "CABO USB-C 2.0"

    def test_substituir_item_nao_conta_para_compra(self, pedido_com_itens, separador, separador_domain):
        """Testa que item substituído não está em compra."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens.first()

        # Substituir item
        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO NOVO",
            usuario=separador_domain
        )

        item.refresh_from_db()

        # Item NÃO deve estar em compra
        assert item.em_compra is False
        assert item.substituido is True
        assert item.separado is True

    def test_substituir_item_registra_dados_separador(self, pedido_com_itens, separador, separador_domain):
        """Testa que substituir registra quem fez e quando."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens.first()

        antes = timezone.now()

        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO NOVO",
            usuario=separador_domain
        )

        depois = timezone.now()

        item.refresh_from_db()

        assert item.separado_por == separador
        assert item.separado_em >= antes
        assert item.separado_em <= depois
