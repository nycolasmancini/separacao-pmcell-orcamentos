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
"""
from django.urls import path
from core.presentation.web.views import (
    LoginView,
    DashboardView,
    LogoutView,
    UploadOrcamentoView,
    DetalhePedidoView,
    SepararItemView,
    MarcarParaCompraView,
    SubstituirItemView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('pedidos/novo/', UploadOrcamentoView.as_view(), name='upload_orcamento'),
    path('pedidos/<int:pedido_id>/', DetalhePedidoView.as_view(), name='detalhe_pedido'),
    path('pedidos/<int:pedido_id>/itens/<int:item_id>/separar/', SepararItemView.as_view(), name='separar_item'),
    path('pedidos/<int:pedido_id>/itens/<int:item_id>/marcar-compra/', MarcarParaCompraView.as_view(), name='marcar_compra'),
    path('pedidos/<int:pedido_id>/itens/<int:item_id>/substituir/', SubstituirItemView.as_view(), name='substituir_item'),
]
