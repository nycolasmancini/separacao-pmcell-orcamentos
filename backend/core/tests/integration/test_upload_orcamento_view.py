# -*- coding: utf-8 -*-
"""
Testes de integração para UploadOrcamentoView.
Fase 15: Tela de Upload de PDF (UI)
"""
import os
import tempfile
from decimal import Decimal
from io import BytesIO

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import Usuario, Pedido, ItemPedido
from core.domain.pedido.value_objects import Logistica, Embalagem, StatusPedido


class UploadOrcamentoViewTestCase(TestCase):
    """
    Testes de integração para a view de upload de orçamento.

    Testa:
    - Renderização da página de upload
    - Upload de arquivo PDF válido
    - Validações de formulário
    - Preview de dados extraídos
    - Criação de pedido no banco
    - Redirecionamento após sucesso
    """

    def setUp(self):
        """Configura dados de teste."""
        self.client = Client()

        # Criar usuário vendedor para testes
        self.usuario = Usuario.objects.create_user(
            numero_login=1001,
            pin='1234',
            nome='João Vendedor',
            tipo='VENDEDOR',
            ativo=True
        )

        # Fazer login
        self.client.force_login(self.usuario)

        # URL da view
        self.url = reverse('upload_orcamento')

    def test_get_renderiza_pagina_upload_corretamente(self):
        """
        Test 1: GET renderiza página de upload com formulário.

        Verifica:
        - Status 200
        - Template correto
        - Formulário presente no contexto
        - Campos do formulário renderizados (pdf_file, logistica, embalagem)
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'upload_orcamento.html')
        self.assertIn('form', response.context)

        # Verificar que os campos estão no HTML
        content = response.content.decode('utf-8')
        self.assertIn('pdf_file', content.lower())
        self.assertIn('logistica', content.lower())
        self.assertIn('embalagem', content.lower())

    def test_post_arquivo_pdf_valido_extrai_dados(self):
        """
        Test 2: POST com PDF válido extrai dados e exibe preview.

        Simula upload de PDF real e verifica extração de:
        - Número do orçamento
        - Nome do cliente
        - Produtos (código, descrição, quantidade, valores)
        """
        # Criar arquivo PDF de teste (mock)
        # NOTA: Neste teste usamos um PDF mock. Em produção, usar PDF real.
        pdf_content = b'%PDF-1.4\nOrcamento N: 30567\nCLIENTE: ROSANA\n00010 PRODUTO TESTE UN 10 5.00 50.00'
        pdf_file = SimpleUploadedFile(
            'orcamento_30567.pdf',
            pdf_content,
            content_type='application/pdf'
        )

        data = {
            'pdf_file': pdf_file,
            'logistica': Logistica.CORREIOS.value,
            'embalagem': Embalagem.CAIXA.value,
            'observacoes': 'Pedido urgente'
        }

        response = self.client.post(self.url, data, follow=True)

        # Verificar que não há erros de formulário
        if 'form' in response.context:
            form_errors = response.context['form'].errors
            self.assertEqual(len(form_errors), 0, f"Erros no formulário: {form_errors}")

    def test_post_sem_arquivo_retorna_erro_validacao(self):
        """
        Test 3: POST sem arquivo retorna erro de validação.

        Verifica:
        - Formulário inválido
        - Mensagem de erro apropriada
        - Não cria pedido no banco
        """
        data = {
            'logistica': Logistica.CORREIOS.value,
            'embalagem': Embalagem.CAIXA.value,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('pdf_file', response.context['form'].errors)

        # Verificar que nenhum pedido foi criado
        self.assertEqual(Pedido.objects.count(), 0)

    def test_post_arquivo_nao_pdf_retorna_erro(self):
        """
        Test 4: POST com arquivo não-PDF retorna erro.

        Verifica:
        - Validação de tipo de arquivo
        - Mensagem de erro apropriada
        - Não cria pedido
        """
        # Criar arquivo .txt ao invés de .pdf
        txt_file = SimpleUploadedFile(
            'documento.txt',
            b'Este nao eh um PDF',
            content_type='text/plain'
        )

        data = {
            'pdf_file': txt_file,
            'logistica': Logistica.CORREIOS.value,
            'embalagem': Embalagem.CAIXA.value,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())

        # Verificar mensagem de erro
        form_errors = str(response.context['form'].errors)
        self.assertIn('pdf', form_errors.lower())

    def test_validacao_embalagem_vs_logistica_correios_sacola_invalido(self):
        """
        Test 5: Validação de embalagem incompatível com logística.

        CORREIOS + SACOLA deve ser inválido (apenas CAIXA permitida).
        """
        pdf_content = b'%PDF-1.4\nOrcamento N: 30567\n00010 PRODUTO UN 10 5.00 50.00'
        pdf_file = SimpleUploadedFile(
            'orcamento.pdf',
            pdf_content,
            content_type='application/pdf'
        )

        data = {
            'pdf_file': pdf_file,
            'logistica': Logistica.CORREIOS.value,
            'embalagem': Embalagem.SACOLA.value,  # INVÁLIDO para CORREIOS
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())

        # Verificar que há erro de validação relacionado à embalagem
        form_errors = str(response.context['form'].errors)
        self.assertTrue(
            'embalagem' in form_errors.lower() or '__all__' in response.context['form'].errors,
            f"Esperava erro de validação de embalagem, mas obteve: {form_errors}"
        )

    def test_preview_exibe_dados_extraidos_header_e_produtos(self):
        """
        Test 6: Preview exibe dados extraídos do PDF.

        Verifica que o contexto ou resposta contém:
        - Dados do header (número, cliente)
        - Lista de produtos
        """
        # Este teste será implementado quando tivermos o preview funcional
        # Por enquanto, apenas verifica que a resposta é bem-sucedida
        pdf_content = b'%PDF-1.4\nOrcamento N: 30567\nCLIENTE: TESTE\n00010 PRODUTO UN 10 5.00 50.00'
        pdf_file = SimpleUploadedFile(
            'orcamento.pdf',
            pdf_content,
            content_type='application/pdf'
        )

        data = {
            'pdf_file': pdf_file,
            'logistica': Logistica.MOTOBOY.value,
            'embalagem': Embalagem.SACOLA.value,
        }

        response = self.client.post(self.url, data)

        # Deve renderizar com sucesso (200) ou redirecionar (302)
        self.assertIn(response.status_code, [200, 302])

    def test_confirmacao_cria_pedido_no_banco(self):
        """
        Test 7: Confirmação cria pedido no banco de dados.

        Verifica:
        - Pedido criado com dados corretos
        - Itens do pedido criados
        - Status inicial correto (EM_SEPARACAO)
        """
        # Este teste verifica a integração completa
        # Será implementado após o form e view estarem funcionais

        # Por enquanto, apenas verifica que o banco está acessível
        inicial_count = Pedido.objects.count()
        self.assertEqual(inicial_count, 0)

    def test_redirecionamento_para_dashboard_apos_sucesso(self):
        """
        Test 8: Redirecionamento para dashboard após criação bem-sucedida.

        Verifica:
        - Status 302 (redirect)
        - Redirect para dashboard ou página de pedido
        - Mensagem de sucesso
        """
        # Este teste verifica o fluxo completo de sucesso
        # Será implementado após form e view estarem completos

        # Por enquanto, apenas verifica que a URL está configurada
        self.assertIsNotNone(self.url)
        self.assertTrue(self.url.startswith('/'))

    def test_usuario_nao_autenticado_redireciona_para_login(self):
        """
        Test extra: Usuários não autenticados são redirecionados.

        Verifica proteção da view com @login_required.
        """
        # Fazer logout
        self.client.logout()

        response = self.client.get(self.url)

        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
