#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Validação E2E - Fase 24: Substituir Item

Valida que a funcionalidade de substituição de itens está completa e funcional.
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')
django.setup()

from django.db import connection
from core.models import Usuario, Pedido, ItemPedido
from core.infrastructure.persistence.models.produto import Produto
from core.application.use_cases.substituir_item import SubstituirItemUseCase
from core.domain.usuario.entities import Usuario as UsuarioDomain, TipoUsuario


def print_status(msg, status="✓"):
    """Imprime mensagem com status colorido."""
    colors = {"✓": "\033[92m", "✗": "\033[91m", "→": "\033[94m"}
    reset = "\033[0m"
    print(f"{colors.get(status, '')}{status} {msg}{reset}")


def validar_migration_aplicada():
    """Valida que migration 0005 foi aplicada."""
    print_status("Validando migration 0005_adicionar_campos_substituicao...", "→")

    # Usar sintaxe SQLite
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(core_itempedido)")
        columns = [row[1] for row in cursor.fetchall()]

    assert 'substituido' in columns, "Campo 'substituido' não encontrado"
    assert 'produto_substituto' in columns, "Campo 'produto_substituto' não encontrado"
    print_status("Migration aplicada corretamente")


def validar_use_case():
    """Valida o Use Case de Substituição."""
    print_status("Validando SubstituirItemUseCase...", "→")

    # Criar dados de teste
    usuario_django = Usuario.objects.create_user(
        numero_login=9001,
        pin="1111",
        nome="Validador",
        tipo="SEPARADOR"
    )

    vendedor = Usuario.objects.create_user(
        numero_login=9002,
        pin="2222",
        nome="Vendedor Validador",
        tipo="VENDEDOR"
    )

    produto = Produto.objects.create(
        codigo="VAL001",
        descricao="PRODUTO VALIDAÇÃO",
        quantidade=10,
        valor_unitario=Decimal("100.00"),
        valor_total=Decimal("1000.00")
    )

    pedido = Pedido.objects.create(
        numero_orcamento="99999",
        codigo_cliente="VAL001",
        nome_cliente="Cliente Validação",
        vendedor=vendedor,
        data="27/01/2025",
        logistica="CORREIOS",
        embalagem="CAIXA"
    )

    item = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=5
    )

    # Executar use case
    usuario_domain = UsuarioDomain(
        numero_login=9001,
        nome="Validador",
        tipo=TipoUsuario.SEPARADOR
    )

    use_case = SubstituirItemUseCase()
    result = use_case.execute(
        item_id=item.id,
        produto_substituto="PRODUTO SUBSTITUTO VALIDAÇÃO",
        usuario=usuario_domain
    )

    # Validações
    assert result.success is True, "Use case deveria retornar sucesso"

    item.refresh_from_db()
    assert item.substituido is True, "Item deveria estar marcado como substituído"
    assert item.produto_substituto == "PRODUTO SUBSTITUTO VALIDAÇÃO", "Produto substituto incorreto"
    assert item.separado is True, "Item deveria estar marcado como separado"
    assert item.separado_por == usuario_django, "Separador incorreto"

    # Cleanup
    pedido.delete()
    usuario_django.delete()
    vendedor.delete()
    produto.delete()

    print_status("Use Case validado com sucesso")


def validar_view_existe():
    """Valida que a view foi criada."""
    print_status("Validando SubstituirItemView...", "→")

    from core.presentation.web.views import SubstituirItemView

    view = SubstituirItemView()
    assert hasattr(view, 'get'), "View deveria ter método GET"
    assert hasattr(view, 'post'), "View deveria ter método POST"

    print_status("View criada corretamente")


def validar_url_configurada():
    """Valida que a URL foi configurada."""
    print_status("Validando URL 'substituir_item'...", "→")

    from django.urls import reverse, NoReverseMatch

    try:
        url = reverse('substituir_item', kwargs={'pedido_id': 1, 'item_id': 1})
        assert '/substituir/' in url, "URL deveria conter '/substituir/'"
        print_status(f"URL configurada: {url}")
    except NoReverseMatch:
        raise AssertionError("URL 'substituir_item' não encontrada")


def validar_templates_existem():
    """Valida que os templates foram criados."""
    print_status("Validando templates...", "→")

    import os

    modal_path = "templates/partials/_modal_substituir.html"
    item_path = "templates/partials/_item_pedido.html"

    assert os.path.exists(modal_path), f"Template {modal_path} não encontrado"
    assert os.path.exists(item_path), f"Template {item_path} não encontrado"

    # Verificar se _item_pedido.html contém referências à substituição
    with open(item_path, 'r') as f:
        content = f.read()
        assert 'substituido' in content.lower(), "Template deveria mencionar 'substituído'"
        assert 'Marcar como Substituído' in content or 'substituir_item' in content, \
            "Template deveria ter opção de substituir"

    print_status("Templates criados e atualizados")


def main():
    """Executa todas as validações."""
    print("\n" + "="*60)
    print("  VALIDAÇÃO E2E - FASE 24: MARCAR COMO SUBSTITUÍDO")
    print("="*60 + "\n")

    try:
        validar_migration_aplicada()
        validar_use_case()
        validar_view_existe()
        validar_url_configurada()
        validar_templates_existem()

        print("\n" + "="*60)
        print_status("TODAS AS 5 VALIDAÇÕES PASSARAM! ✓✓✓", "✓")
        print("="*60 + "\n")

        return 0

    except AssertionError as e:
        print_status(f"ERRO: {e}", "✗")
        return 1
    except Exception as e:
        print_status(f"ERRO INESPERADO: {e}", "✗")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
