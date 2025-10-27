# -*- coding: utf-8 -*-
"""
Django Admin para o sistema de separação de pedidos.
Fase 32: Implementar Sistema de Admin Django

Este módulo registra os modelos no Django Admin com customizações:
- UsuarioAdmin: Gestão de usuários
- ProdutoAdmin: Gestão de produtos
- PedidoAdmin: Gestão de pedidos com inline de itens
- ItemPedidoAdmin: Gestão de itens de pedidos
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from core.models import Usuario, Produto, Pedido, ItemPedido


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """
    Admin para o modelo Usuario.

    Features:
    - List view com campos principais
    - Filtros por tipo, ativo e is_admin
    - Busca por numero_login e nome
    - Ordenação por numero_login
    """

    list_display = ['numero_login', 'nome', 'tipo', 'ativo', 'is_admin', 'criado_em']
    list_filter = ['tipo', 'ativo', 'is_admin']
    search_fields = ['numero_login', 'nome']
    ordering = ['numero_login']
    readonly_fields = ['criado_em', 'atualizado_em']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('numero_login', 'nome', 'password')
        }),
        ('Tipo e Permissões', {
            'fields': ('tipo', 'ativo', 'is_admin')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    """
    Admin para o modelo Produto.

    Features:
    - List view com todos os campos principais
    - Busca por codigo e descricao
    - Ordenação por codigo
    """

    list_display = ['codigo', 'descricao', 'quantidade', 'valor_unitario', 'valor_total', 'criado_em']
    search_fields = ['codigo', 'descricao']
    ordering = ['codigo']
    readonly_fields = ['criado_em', 'atualizado_em']

    fieldsets = (
        ('Informações do Produto', {
            'fields': ('codigo', 'descricao')
        }),
        ('Valores', {
            'fields': ('quantidade', 'valor_unitario', 'valor_total')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


class ItemPedidoInline(admin.TabularInline):
    """
    Inline para exibir itens do pedido dentro do PedidoAdmin.
    """

    model = ItemPedido
    extra = 0
    fields = [
        'produto',
        'quantidade_solicitada',
        'quantidade_separada',
        'separado',
        'em_compra',
        'substituido',
        'produto_substituto'
    ]
    readonly_fields = ['separado_em', 'enviado_para_compra_em', 'realizado_em']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """
    Admin para o modelo Pedido.

    Features:
    - List view com campos principais e progresso visual
    - Filtros por status, logistica, embalagem e vendedor
    - Busca por numero_orcamento, nome_cliente e codigo_cliente
    - Inline de ItemPedido
    - Ação em lote para finalizar múltiplos pedidos
    """

    list_display = [
        'numero_orcamento',
        'nome_cliente',
        'vendedor',
        'status',
        'progresso_visual',
        'data_inicio',
        'data_finalizacao'
    ]
    list_filter = ['status', 'logistica', 'embalagem', 'vendedor']
    search_fields = ['numero_orcamento', 'nome_cliente', 'codigo_cliente']
    ordering = ['-criado_em']
    inlines = [ItemPedidoInline]
    readonly_fields = ['criado_em', 'data_inicio', 'data_finalizacao']
    actions = ['finalizar_pedidos']

    fieldsets = (
        ('Informações do Pedido', {
            'fields': ('numero_orcamento', 'codigo_cliente', 'nome_cliente', 'vendedor')
        }),
        ('Detalhes', {
            'fields': ('data', 'logistica', 'embalagem', 'status', 'observacoes')
        }),
        ('Datas', {
            'fields': ('criado_em', 'data_inicio', 'data_finalizacao'),
            'classes': ('collapse',)
        }),
    )

    def progresso_visual(self, obj):
        """
        Exibe o progresso do pedido de forma visual.

        Args:
            obj: Instância de Pedido

        Returns:
            HTML formatado com barra de progresso
        """
        total_itens = obj.itens.count()
        if total_itens == 0:
            return '0%'

        itens_separados = obj.itens.filter(separado=True).count()
        progresso = int((itens_separados / total_itens) * 100)

        # Escolher cor baseada no progresso
        if progresso == 100:
            cor = '#28a745'  # Verde
        elif progresso >= 50:
            cor = '#ffc107'  # Amarelo
        else:
            cor = '#dc3545'  # Vermelho

        return format_html(
            '<div style="width:100px; background-color:#f0f0f0; border-radius:3px;">'
            '<div style="width:{}%; background-color:{}; height:20px; border-radius:3px; text-align:center; color:white; font-weight:bold;">{}\u200A%</div>'
            '</div>',
            progresso, cor, progresso
        )

    progresso_visual.short_description = 'Progresso'

    def finalizar_pedidos(self, request, queryset):
        """
        Ação em lote para finalizar múltiplos pedidos.

        Args:
            request: HttpRequest
            queryset: QuerySet com pedidos selecionados
        """
        count = 0
        for pedido in queryset:
            if pedido.status != 'FINALIZADO':
                pedido.status = 'FINALIZADO'
                pedido.data_finalizacao = timezone.now()
                pedido.save()
                count += 1

        self.message_user(
            request,
            f'{count} pedido(s) finalizado(s) com sucesso.'
        )

    finalizar_pedidos.short_description = 'Finalizar pedidos selecionados'


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    """
    Admin para o modelo ItemPedido.

    Features:
    - List view com campos principais
    - Filtros por status (separado, em_compra, etc.)
    - Busca por pedido e produto
    """

    list_display = [
        'id',
        'pedido',
        'produto',
        'quantidade_solicitada',
        'quantidade_separada',
        'separado',
        'em_compra',
        'pedido_realizado',
        'substituido'
    ]
    list_filter = ['separado', 'em_compra', 'pedido_realizado', 'substituido']
    search_fields = [
        'pedido__numero_orcamento',
        'produto__descricao',
        'produto__codigo'
    ]
    ordering = ['-id']
    readonly_fields = ['separado_em', 'enviado_para_compra_em', 'realizado_em']

    fieldsets = (
        ('Pedido e Produto', {
            'fields': ('pedido', 'produto')
        }),
        ('Quantidades', {
            'fields': ('quantidade_solicitada', 'quantidade_separada')
        }),
        ('Status', {
            'fields': (
                'separado', 'separado_por', 'separado_em',
                'em_compra', 'enviado_para_compra_por', 'enviado_para_compra_em',
                'pedido_realizado', 'realizado_por', 'realizado_em'
            )
        }),
        ('Substituição', {
            'fields': ('substituido', 'produto_substituto'),
            'classes': ('collapse',)
        }),
    )
