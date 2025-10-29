# -*- coding: utf-8 -*-
"""
URLs do app core.
Fase 7: Login e Dashboard
Fase 8: Logout
Fase 15: Upload Orçamento
Fase 21: Detalhe do Pedido
Fase 22: Separar Item
Fase 23: Marcar para Compra
Fase 24: Substituir Item
Fase 25: Finalizar Pedido
Fase 26: Painel de Compras
Fase 27: Marcar Pedido Realizado
Fase 30: Card Partial (WebSocket)
Fase 31: Histórico de Pedidos
"""
from django.urls import path
from django.views.generic import RedirectView
from core.presentation.web.views import (
    LoginView,
    DashboardView,
    LogoutView,
    UploadOrcamentoView,
    DetalhePedidoView,
    SepararItemView,
    MarcarParaCompraView,
    SubstituirItemView,
    FinalizarPedidoView,
    PainelComprasView,
    MarcarPedidoRealizadoView,
    PedidoCardPartialView,
    HistoricoView,
    MetricasView,
    AdminPanelView,
    CriarUsuarioView,
    ItemPedidoPartialView  # Fase 35
)

urlpatterns = [
    # Raiz redireciona para login
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('historico/', HistoricoView.as_view(), name='historico'),  # Fase 31
    path('metricas/', MetricasView.as_view(), name='metricas'),  # Fase 33
    path('compras/', PainelComprasView.as_view(), name='painel_compras'),
    path('usuarios/', AdminPanelView.as_view(), name='admin_panel'),  # Painel Admin
    path('usuarios/criar/', CriarUsuarioView.as_view(), name='criar_usuario'),  # Criar Usuário
    path('compras/itens/<int:item_id>/marcar-realizado/', MarcarPedidoRealizadoView.as_view(), name='marcar_realizado'),
    path('pedidos/novo/', UploadOrcamentoView.as_view(), name='upload_orcamento'),
    path('pedidos/<int:pedido_id>/', DetalhePedidoView.as_view(), name='detalhe_pedido'),
    path('pedidos/<int:pedido_id>/card/', PedidoCardPartialView.as_view(), name='pedido_card_partial'),  # Fase 30
    path('pedidos/<int:pedido_id>/itens/<int:item_id>/html/', ItemPedidoPartialView.as_view(), name='item_pedido_partial'),  # Fase 35
    path('pedidos/<int:pedido_id>/itens/<int:item_id>/separar/', SepararItemView.as_view(), name='separar_item'),
    path('pedidos/<int:pedido_id>/itens/<int:item_id>/marcar-compra/', MarcarParaCompraView.as_view(), name='marcar_compra'),
    path('pedidos/<int:pedido_id>/itens/<int:item_id>/substituir/', SubstituirItemView.as_view(), name='substituir_item'),
    path('pedidos/<int:pedido_id>/finalizar/', FinalizarPedidoView.as_view(), name='finalizar_pedido'),
]
