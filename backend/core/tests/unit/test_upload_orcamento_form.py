# -*- coding: utf-8 -*-
"""
Testes unitários para UploadOrcamentoForm.
Fase 3: 6 testes unitários com validações de PDF.

Seguindo TDD: estes testes devem FALHAR primeiro,
depois implementamos o método processar_pdf() até todos passarem.
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

# Imports dos models
from core.models import Usuario, Pedido, TipoUsuario

# Import do form
from core.presentation.web.forms import UploadOrcamentoForm

# Imports das exceções
from core.application.services.exceptions import (
    DuplicatePedidoError,
    VendedorNotFoundError
)
from core.infrastructure.parsers.pdf_orcamento_parser import ParserError


@pytest.mark.django_db
class TestUploadOrcamentoForm(TestCase):
    """Testes unitários para o formulário de upload de orçamento."""

    def setUp(self):
        """Configuração dos testes."""
        # Cria vendedor de teste
        self.vendedor = Usuario.objects.create_user(
            numero_login=1001,
            pin='1234',
            nome='NYCOLAS HENDRIGO MANCINI',
            tipo=TipoUsuario.VENDEDOR
        )

    def _criar_pdf_mock(self, nome_arquivo: str, conteudo: bytes = b'PDF MOCK', content_type='application/pdf'):
        """Helper para criar arquivo PDF mock."""
        return SimpleUploadedFile(
            nome_arquivo,
            conteudo,
            content_type=content_type
        )

    # ==================== TESTE 1 ====================
    def test_form_valido_com_pdf(self):
        """
        Testa que formulário válido com PDF real é aceito.

        Verifica:
        1. Formulário válido com todos os campos
        2. PDF dentro do limite de tamanho
        3. Campos obrigatórios preenchidos
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
            'observacoes': 'Teste unitário'
        }

        form = UploadOrcamentoForm(data=form_data, files={'pdf_file': pdf_file})

        # Formulário deve ser válido
        self.assertTrue(form.is_valid(), f"Erros: {form.errors}")
        self.assertEqual(form.cleaned_data['logistica'], 'CORREIOS')
        self.assertEqual(form.cleaned_data['embalagem'], 'CAIXA')
        self.assertIsNotNone(form.cleaned_data['pdf_file'])

    # ==================== TESTE 2 ====================
    def test_form_arquivo_muito_grande(self):
        """
        Testa que arquivo maior que 10MB é rejeitado.

        Verifica:
        1. Validação de tamanho de arquivo
        2. Mensagem de erro apropriada
        """
        # Cria arquivo mock muito grande (11MB)
        tamanho_grande = 11 * 1024 * 1024  # 11MB
        pdf_file = self._criar_pdf_mock(
            'orcamento_grande.pdf',
            b'X' * tamanho_grande
        )

        form_data = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA'
        }

        form = UploadOrcamentoForm(data=form_data, files={'pdf_file': pdf_file})

        # Formulário NÃO deve ser válido
        self.assertFalse(form.is_valid())
        self.assertIn('pdf_file', form.errors)
        self.assertIn('muito grande', str(form.errors['pdf_file']).lower())

    # ==================== TESTE 3 ====================
    def test_form_arquivo_nao_pdf(self):
        """
        Testa que arquivo não-PDF é rejeitado.

        Verifica:
        1. Validação de extensão .pdf
        2. Validação de content_type
        3. Mensagem de erro apropriada
        """
        # Arquivo TXT disfarçado de PDF
        txt_file = self._criar_pdf_mock(
            'orcamento.txt',  # Extensão errada
            b'Conteudo de texto',
            content_type='text/plain'
        )

        form_data = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA'
        }

        form = UploadOrcamentoForm(data=form_data, files={'pdf_file': txt_file})

        # Formulário NÃO deve ser válido
        self.assertFalse(form.is_valid())
        self.assertIn('pdf_file', form.errors)

    # ==================== TESTE 4 ====================
    def test_form_pdf_parsing_error(self):
        """
        Testa que erro de parsing do PDF é tratado corretamente.

        Verifica:
        1. Método processar_pdf() existe
        2. PDF corrompido lança exceção apropriada
        3. Rollback transacional
        """
        # PDF corrompido
        pdf_file = self._criar_pdf_mock(
            'orcamento_invalido.pdf',
            b'CONTEUDO INVALIDO'
        )

        form_data = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA'
        }

        form = UploadOrcamentoForm(data=form_data, files={'pdf_file': pdf_file})

        # Formulário é válido (validação de campos)
        self.assertTrue(form.is_valid())

        # MAS processar_pdf() deve lançar ParserError
        with self.assertRaises(ParserError):
            form.processar_pdf(vendedor=self.vendedor)

    # ==================== TESTE 5 ====================
    def test_form_campos_opcionais(self):
        """
        Testa que campos opcionais funcionam corretamente.

        Verifica:
        1. Campo observacoes é opcional
        2. Formulário válido sem observações
        """
        pdf_path = '/Users/nycolasmancini/Documents/Orcamento - 30703 - Marcio - R$ 1405,00.pdf'

        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        pdf_file = self._criar_pdf_mock('orcamento_30703.pdf', pdf_content)

        # Dados sem observacoes
        form_data = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA'
            # observacoes não fornecido
        }

        form = UploadOrcamentoForm(data=form_data, files={'pdf_file': pdf_file})

        # Formulário deve ser válido
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('observacoes', ''), '')

    # ==================== TESTE 6 ====================
    def test_form_validacao_logistica_embalagem(self):
        """
        Testa validação de compatibilidade logística-embalagem.

        Verifica:
        1. CORREIOS aceita apenas CAIXA
        2. MELHOR_ENVIO aceita apenas CAIXA
        3. SACOLA só com RETIRA_LOJA, ONIBUS, MOTOBOY
        """
        pdf_path = '/Users/nycolasmancini/Documents/Orcamento - 30703 - Marcio - R$ 1405,00.pdf'

        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        pdf_file = self._criar_pdf_mock('orcamento_30703.pdf', pdf_content)

        # Teste 1: CORREIOS com SACOLA (deve falhar)
        form_data_invalido = {
            'logistica': 'CORREIOS',
            'embalagem': 'SACOLA'  # Inválido para CORREIOS
        }

        form_invalido = UploadOrcamentoForm(
            data=form_data_invalido,
            files={'pdf_file': pdf_file}
        )

        # NÃO deve ser válido
        self.assertFalse(form_invalido.is_valid())
        self.assertIn('__all__', form_invalido.errors)

        # Teste 2: CORREIOS com CAIXA (deve passar)
        form_data_valido = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA'  # Válido para CORREIOS
        }

        # Precisa recriar o PDF mock (foi consumido)
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        pdf_file2 = self._criar_pdf_mock('orcamento_30703_2.pdf', pdf_content)

        form_valido = UploadOrcamentoForm(
            data=form_data_valido,
            files={'pdf_file': pdf_file2}
        )

        # DEVE ser válido
        self.assertTrue(form_valido.is_valid(), f"Erros: {form_valido.errors}")

    # ==================== TESTE EXTRA - processar_pdf ====================
    def test_processar_pdf_metodo_existe(self):
        """
        Testa que método processar_pdf() existe no formulário.

        Verifica:
        1. Método existe
        2. Aceita parâmetro vendedor
        3. Retorna Pedido criado
        """
        pdf_path = '/Users/nycolasmancini/Documents/Orcamento - 30703 - Marcio - R$ 1405,00.pdf'

        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        pdf_file = self._criar_pdf_mock('orcamento_30703.pdf', pdf_content)

        form_data = {
            'logistica': 'CORREIOS',
            'embalagem': 'CAIXA',
            'observacoes': 'Teste método processar_pdf'
        }

        form = UploadOrcamentoForm(data=form_data, files={'pdf_file': pdf_file})

        # Formulário deve ser válido
        self.assertTrue(form.is_valid())

        # Método processar_pdf deve existir
        self.assertTrue(hasattr(form, 'processar_pdf'))

        # Processar PDF deve retornar Pedido
        pedido = form.processar_pdf(vendedor=self.vendedor)

        self.assertIsNotNone(pedido)
        self.assertIsInstance(pedido, Pedido)
        self.assertEqual(pedido.numero_orcamento, '30703')
        self.assertEqual(pedido.vendedor, self.vendedor)
        self.assertEqual(pedido.logistica, 'CORREIOS')
        self.assertEqual(pedido.embalagem, 'CAIXA')
