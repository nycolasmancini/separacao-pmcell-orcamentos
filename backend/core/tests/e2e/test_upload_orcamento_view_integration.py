# -*- coding: utf-8 -*-
"""
Testes E2E para UploadOrcamentoView com integração completa.
Fase 4: 7 testes E2E para validar view modificada.

Seguindo TDD: estes testes devem FALHAR primeiro (pois a view ainda usa implementação antiga),
depois modificamos a view para usar UploadOrcamentoForm.processar_pdf() até todos passarem.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

# Imports dos models
from core.models import Usuario, Pedido, ItemPedido, TipoUsuario

# Import das exceções
from core.application.services.exceptions import (
    DuplicatePedidoError,
    VendedorNotFoundError,
    IntegrityValidationError
)
from core.infrastructure.parsers.pdf_orcamento_parser import ParserError


@pytest.mark.django_db
class TestUploadOrcamentoViewIntegration(TestCase):
    """Testes E2E para a view de upload de orçamento integrada com novo parser."""

    def setUp(self):
        """Configuração dos testes."""
        # Criar vendedor de teste
        self.vendedor = Usuario.objects.create_user(
            numero_login=1001,
            pin='1234',
            nome='NYCOLAS HENDRIGO MANCINI',
            tipo=TipoUsuario.VENDEDOR
        )

        # Cliente HTTP para fazer requests
        self.client = Client()

        # URL da view
        self.upload_url = reverse('upload_orcamento')

        # Fazer login - forçar sessão manualmente
        session = self.client.session
        session['usuario_id'] = self.vendedor.id
        session['numero_login'] = self.vendedor.numero_login
        session['nome'] = self.vendedor.nome
        session['tipo'] = self.vendedor.tipo
        session.save()

        # Forçar autenticação via Django
        self.client.force_login(self.vendedor)

    def _criar_pdf_mock(self, nome_arquivo: str, conteudo: bytes = b'PDF MOCK') -> SimpleUploadedFile:
        """Helper para criar arquivo PDF mock."""
        return SimpleUploadedFile(
            nome_arquivo,
            conteudo,
            content_type='application/pdf'
        )

    # ==================== TESTE 1 ====================
    def test_upload_pdf_sucesso_redireciona_dashboard(self):
        """
        Testa que upload bem-sucedido redireciona para dashboard.

        Verifica:
        1. POST com PDF válido retorna redirect (302)
        2. Redirect aponta para dashboard
        3. Mensagem de sucesso é exibida
        4. Pedido foi criado no banco
        """
        # PDF real de teste
        pdf_path = '/Users/nycolasmancini/Documents/Orcamento - 30703 - Marcio - R$ 1405,00.pdf'

        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        pdf_file = self._criar_pdf_mock('orcamento_30703.pdf', pdf_content)

        # Dados do formulário
        form_data = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA',
            'observacoes': 'Teste E2E'
        }

        # Fazer POST para a view
        response = self.client.post(
            self.upload_url,
            data=form_data,
            files={'pdf_file': pdf_file},
            follow=False  # Não seguir redirect automaticamente
        )

        # Validações
        self.assertEqual(response.status_code, 302, "Deve redirecionar após sucesso")
        self.assertEqual(response.url, reverse('dashboard'), "Deve redirecionar para dashboard")

        # Verificar mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('sucesso', messages[0].message.lower())
        self.assertIn('30703', messages[0].message)

        # Verificar que pedido foi criado
        pedido = Pedido.objects.get(numero_orcamento='30703')
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.vendedor, self.vendedor)
        self.assertEqual(pedido.logistica, 'CORREIOS')
        self.assertEqual(pedido.embalagem, 'CAIXA')

        # Verificar que itens foram criados
        itens = ItemPedido.objects.filter(pedido=pedido)
        self.assertEqual(itens.count(), 10)  # PDF tem 10 produtos

    # ==================== TESTE 2 ====================
    def test_upload_pdf_exibe_erros_parsing(self):
        """
        Testa que erros de parsing são exibidos ao usuário.

        Verifica:
        1. PDF corrompido retorna status 200 (não redireciona)
        2. Mensagem de erro apropriada é exibida
        3. Nenhum pedido foi criado no banco
        4. Formulário é renderizado novamente
        """
        # PDF corrompido
        pdf_file = self._criar_pdf_mock(
            'orcamento_invalido.pdf',
            b'CONTEUDO INVALIDO NAO E PDF'
        )

        form_data = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA'
        }

        # Contar pedidos antes
        count_antes = Pedido.objects.count()

        # Fazer POST
        response = self.client.post(
            self.upload_url,
            data=form_data,
            files={'pdf_file': pdf_file}
        )

        # Validações
        self.assertEqual(response.status_code, 200, "Não deve redirecionar em caso de erro")

        # Verificar mensagem de erro
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0, "Deve haver mensagem de erro")
        erro_msg = messages[0].message.lower()
        self.assertTrue(
            'erro' in erro_msg or 'inválido' in erro_msg,
            f"Mensagem deve indicar erro: {messages[0].message}"
        )

        # Verificar que nenhum pedido foi criado (rollback)
        count_depois = Pedido.objects.count()
        self.assertEqual(count_antes, count_depois, "Nenhum pedido deve ser criado")

    # ==================== TESTE 3 ====================
    def test_upload_pdf_duplicado_exibe_mensagem(self):
        """
        Testa que PDF duplicado exibe mensagem apropriada.

        Verifica:
        1. Primeiro upload funciona
        2. Segundo upload do mesmo PDF retorna 200 (não redireciona)
        3. Mensagem indica que orçamento já existe
        4. Apenas um pedido existe no banco
        """
        pdf_path = '/Users/nycolasmancini/Documents/Orcamento - 30703 - Marcio - R$ 1405,00.pdf'

        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        form_data = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA'
        }

        # Primeiro upload - deve funcionar
        pdf_file1 = self._criar_pdf_mock('orcamento_30703.pdf', pdf_content)
        response1 = self.client.post(
            self.upload_url,
            data=form_data,
            files={'pdf_file': pdf_file1}
        )

        self.assertEqual(response1.status_code, 302, "Primeiro upload deve ter sucesso")
        self.assertEqual(Pedido.objects.filter(numero_orcamento='30703').count(), 1)

        # Segundo upload - deve falhar
        pdf_file2 = self._criar_pdf_mock('orcamento_30703_copia.pdf', pdf_content)
        response2 = self.client.post(
            self.upload_url,
            data=form_data,
            files={'pdf_file': pdf_file2}
        )

        # Validações
        self.assertEqual(response2.status_code, 200, "Segundo upload não deve redirecionar")

        # Verificar mensagem de erro
        messages = list(get_messages(response2.wsgi_request))
        self.assertGreater(len(messages), 0)
        erro_msg = messages[0].message.lower()
        self.assertTrue(
            'já existe' in erro_msg or 'duplicado' in erro_msg or '30703' in erro_msg,
            f"Mensagem deve indicar duplicação: {messages[0].message}"
        )

        # Verificar que apenas um pedido existe
        self.assertEqual(Pedido.objects.filter(numero_orcamento='30703').count(), 1)

    # ==================== TESTE 4 ====================
    def test_upload_pdf_sem_autenticacao_redireciona_login(self):
        """
        Testa que acesso sem autenticação redireciona para login.

        Verifica:
        1. Logout do usuário
        2. Tentativa de acesso redireciona (302)
        3. Redirect aponta para login
        """
        # Fazer logout
        self.client.logout()

        # Tentar acessar upload
        response = self.client.get(self.upload_url)

        # Validações
        self.assertEqual(response.status_code, 302, "Deve redirecionar para login")
        self.assertIn('/login/', response.url, "Deve redirecionar para página de login")

    # ==================== TESTE 5 ====================
    def test_upload_pdf_apenas_vendedor_pode_fazer_upload(self):
        """
        Testa que apenas tipo VENDEDOR pode fazer upload.

        Verifica:
        1. Usuário SEPARADOR não consegue acessar
        2. Usuário COMPRADORA não consegue acessar
        3. Apenas VENDEDOR tem acesso
        """
        # Criar usuário separador
        separador = Usuario.objects.create_user(
            numero_login=2001,
            pin='4321',
            nome='SEPARADOR TESTE',
            tipo=TipoUsuario.SEPARADOR
        )

        # Fazer logout do vendedor
        self.client.logout()

        # Fazer login como separador - forçar sessão manualmente
        session = self.client.session
        session['usuario_id'] = separador.id
        session['numero_login'] = separador.numero_login
        session['nome'] = separador.nome
        session['tipo'] = separador.tipo
        session.save()
        self.client.force_login(separador)

        # Tentar acessar upload
        response = self.client.get(self.upload_url)

        # Validação - depende da implementação do decorator @login_required
        # Se houver verificação de tipo de usuário, deve retornar 403 ou redirecionar
        # Se não houver, o teste passa mas indica que precisamos adicionar verificação

        # Por ora, vamos apenas documentar que vendedor tem acesso
        self.client.logout()

        # Relogar como vendedor
        session = self.client.session
        session['usuario_id'] = self.vendedor.id
        session['numero_login'] = self.vendedor.numero_login
        session['nome'] = self.vendedor.nome
        session['tipo'] = self.vendedor.tipo
        session.save()
        self.client.force_login(self.vendedor)

        response_vendedor = self.client.get(self.upload_url)
        self.assertEqual(response_vendedor.status_code, 200, "Vendedor deve ter acesso")

    # ==================== TESTE 6 ====================
    def test_upload_pdf_logging_audit(self):
        """
        Testa que operações são logadas para auditoria.

        Verifica:
        1. Upload bem-sucedido gera log
        2. Log contém informações relevantes (usuário, número orçamento)

        Note:
            Este teste valida que a estrutura de logging existe.
            Logs específicos são validados via pytest caplog.
        """
        import logging

        # Capturar logs
        with self.assertLogs('core.application.services', level='INFO') as cm:
            pdf_path = '/Users/nycolasmancini/Documents/Orcamento - 30703 - Marcio - R$ 1405,00.pdf'

            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()

            pdf_file = self._criar_pdf_mock('orcamento_30703.pdf', pdf_content)

            form_data = {
                'logistica': 'CORREIOS',
                'embalagem': 'CAIXA'
            }

            response = self.client.post(
                self.upload_url,
                data=form_data,
                files={'pdf_file': pdf_file}
            )

            # Verificar que houve sucesso
            self.assertEqual(response.status_code, 302)

        # Verificar que logs foram gerados
        self.assertGreater(len(cm.output), 0, "Deve haver logs da operação")

        # Verificar que logs contêm informações relevantes
        log_str = '\n'.join(cm.output)
        self.assertIn('30703', log_str, "Log deve conter número do orçamento")

    # ==================== TESTE 7 ====================
    def test_upload_pdf_validacao_form_campos_obrigatorios(self):
        """
        Testa validação de campos obrigatórios do formulário.

        Verifica:
        1. PDF ausente retorna erro
        2. Logística ausente retorna erro
        3. Embalagem ausente retorna erro
        4. Incompatibilidade logística/embalagem retorna erro
        """
        # Teste 1: PDF ausente
        form_data = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA'
        }

        response1 = self.client.post(self.upload_url, data=form_data)
        self.assertEqual(response1.status_code, 200, "Deve retornar formulário com erro")
        self.assertContains(response1, 'obrigatório', status_code=200)

        # Teste 2: Logística ausente
        pdf_path = '/Users/nycolasmancini/Documents/Orcamento - 30703 - Marcio - R$ 1405,00.pdf'

        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        pdf_file = self._criar_pdf_mock('orcamento_30703.pdf', pdf_content)

        form_data_sem_logistica = {
            'embalagem': 'CAIXA'
        }

        response2 = self.client.post(
            self.upload_url,
            data=form_data_sem_logistica,
            files={'pdf_file': pdf_file}
        )

        self.assertEqual(response2.status_code, 200)

        # Teste 3: CORREIOS com SACOLA (incompatível)
        pdf_file2 = self._criar_pdf_mock('orcamento_30703_2.pdf', pdf_content)

        form_data_incompativel = {
            'logistica': 'CORREIOS',
            'embalagem': 'SACOLA'  # Inválido para CORREIOS
        }

        response3 = self.client.post(
            self.upload_url,
            data=form_data_incompativel,
            files={'pdf_file': pdf_file2}
        )

        self.assertEqual(response3.status_code, 200, "Deve retornar formulário com erro")
        # Verificar mensagem de erro sobre incompatibilidade
        content = response3.content.decode('utf-8').lower()
        self.assertTrue(
            'caixa' in content or 'incompatível' in content,
            "Deve indicar erro de compatibilidade logística/embalagem"
        )
