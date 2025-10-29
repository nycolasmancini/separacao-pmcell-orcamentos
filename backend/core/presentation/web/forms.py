# -*- coding: utf-8 -*-
"""
Formulários web para o sistema de separação.
Fase 7: LoginForm
Fase 15: UploadOrcamentoForm
"""
from django import forms
from django.core.exceptions import ValidationError

from core.domain.pedido.value_objects import Logistica, Embalagem


# Constantes
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = ['application/pdf']


class LoginForm(forms.Form):
    """
    Formulário de login com numero_login e PIN.

    Fields:
        numero_login: Número inteiro de identificação
        pin: PIN de 4 dígitos (password input)
    """

    numero_login = forms.IntegerField(
        label='Número de Login',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
            'placeholder': 'Digite seu número',
            'autofocus': True,
        }),
        error_messages={
            'required': 'O número de login é obrigatório',
            'invalid': 'Digite um número válido',
            'min_value': 'O número deve ser maior que zero',
        }
    )

    pin = forms.CharField(
        label='PIN',
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
            'placeholder': '••••',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric',
        }),
        error_messages={
            'required': 'O PIN é obrigatório',
            'max_length': 'O PIN deve ter exatamente 4 dígitos',
            'min_length': 'O PIN deve ter exatamente 4 dígitos',
        }
    )

    def clean_pin(self):
        """
        Valida que o PIN tem exatamente 4 dígitos numéricos.

        Returns:
            str: PIN validado

        Raises:
            ValidationError: Se o PIN não for válido
        """
        pin = self.cleaned_data.get('pin', '')

        if not pin:
            raise ValidationError('O PIN é obrigatório')

        if len(pin) != 4:
            raise ValidationError('O PIN deve ter exatamente 4 dígitos')

        if not pin.isdigit():
            raise ValidationError('O PIN deve conter apenas números')

        return pin

    def clean_numero_login(self):
        """
        Valida o número de login.

        Returns:
            int: Número de login validado

        Raises:
            ValidationError: Se o número não for válido
        """
        numero = self.cleaned_data.get('numero_login')

        if numero is None:
            raise ValidationError('O número de login é obrigatório')

        if numero < 1:
            raise ValidationError('O número de login deve ser maior que zero')

        return numero


class UploadOrcamentoForm(forms.Form):
    """
    Formulário para upload de PDF de orçamento e criação de pedido.

    Fields:
        pdf_file: Arquivo PDF do orçamento (max 10MB)
        logistica: Tipo de logística (CORREIOS, MELHOR_ENVIO, etc.)
        embalagem: Tipo de embalagem (CAIXA, SACOLA)
        observacoes: Observações adicionais (opcional)
    """

    pdf_file = forms.FileField(
        label='Arquivo PDF do Orçamento',
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none',
            'accept': '.pdf,application/pdf',
        }),
        error_messages={
            'required': 'O arquivo PDF é obrigatório',
            'invalid': 'Arquivo inválido',
        }
    )

    logistica = forms.ChoiceField(
        label='Tipo de Logística',
        required=True,
        choices=[(log.value, log.value.replace('_', ' ').title()) for log in Logistica],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
        }),
        error_messages={
            'required': 'O tipo de logística é obrigatório',
            'invalid_choice': 'Selecione uma opção válida de logística',
        }
    )

    embalagem = forms.ChoiceField(
        label='Tipo de Embalagem',
        required=True,
        choices=[(emb.value, emb.value.title()) for emb in Embalagem],
        widget=forms.RadioSelect(attrs={
            'class': 'focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300',
        }),
        error_messages={
            'required': 'O tipo de embalagem é obrigatório',
            'invalid_choice': 'Selecione uma opção válida de embalagem',
        }
    )

    observacoes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
            'rows': 3,
            'placeholder': 'Observações adicionais (opcional)...',
        })
    )

    def clean_pdf_file(self):
        """
        Valida o arquivo PDF.

        Returns:
            UploadedFile: Arquivo validado

        Raises:
            ValidationError: Se o arquivo não for válido
        """
        pdf_file = self.cleaned_data.get('pdf_file')

        if not pdf_file:
            raise ValidationError('O arquivo PDF é obrigatório')

        # Validar extensão
        if not pdf_file.name.lower().endswith('.pdf'):
            raise ValidationError('O arquivo deve ser um PDF (.pdf)')

        # Validar tamanho (max 10MB)
        if pdf_file.size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(f'O arquivo é muito grande. Tamanho máximo: {max_mb}MB')

        # Validar mime type
        if hasattr(pdf_file, 'content_type') and pdf_file.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError('O arquivo deve ser um PDF válido')

        return pdf_file

    def clean(self):
        """
        Validação customizada do formulário completo.

        Verifica compatibilidade entre logística e embalagem.

        Returns:
            dict: Dados validados

        Raises:
            ValidationError: Se houver incompatibilidade
        """
        cleaned_data = super().clean()
        logistica_value = cleaned_data.get('logistica')
        embalagem_value = cleaned_data.get('embalagem')

        if logistica_value and embalagem_value:
            try:
                logistica = Logistica(logistica_value)
                embalagem = Embalagem(embalagem_value)

                # Verificar se a logística exige CAIXA
                if Logistica.requer_caixa(logistica) and embalagem != Embalagem.CAIXA:
                    raise ValidationError(
                        f'O tipo de logística "{logistica.value}" aceita apenas embalagem CAIXA. '
                        f'SACOLA não é permitida para este tipo de envio.'
                    )

            except ValueError as e:
                raise ValidationError(f'Valores inválidos de logística ou embalagem: {e}')

        return cleaned_data

    def processar_pdf(self, vendedor):
        """
        Processa o PDF usando OrcamentoParserService e cria o pedido.

        Args:
            vendedor: Instância de Usuario (tipo VENDEDOR)

        Returns:
            Pedido: Instância do pedido criado

        Raises:
            ParserError: Se houver erro ao processar o PDF
            DuplicatePedidoError: Se o orçamento já existe
            VendedorNotFoundError: Se o vendedor não for encontrado
            IntegrityValidationError: Se a validação matemática falhar

        Example:
            >>> form = UploadOrcamentoForm(data=form_data, files={'pdf_file': pdf_file})
            >>> if form.is_valid():
            ...     pedido = form.processar_pdf(vendedor=request.user)
        """
        from core.application.services.orcamento_parser_service import OrcamentoParserService

        if not self.is_valid():
            raise ValidationError('Formulário contém erros. Valide os campos antes de processar.')

        # Obter dados limpos
        pdf_file = self.cleaned_data['pdf_file']
        logistica = self.cleaned_data['logistica']
        embalagem = self.cleaned_data['embalagem']
        observacoes = self.cleaned_data.get('observacoes', '')

        # Criar instância do serviço
        service = OrcamentoParserService()

        # Processar PDF e criar pedido
        pedido = service.processar_pdf_e_criar_pedido(
            pdf_file=pdf_file,
            vendedor=vendedor,
            logistica=logistica,
            embalagem=embalagem,
            observacoes=observacoes
        )

        return pedido


class CriarUsuarioForm(forms.Form):
    """
    Formulário para criar novo usuário.

    Fields:
        numero_login: Número único de identificação
        nome: Nome completo do usuário
        pin: PIN de 4 dígitos
        pin_confirmacao: Confirmação do PIN
        tipo: Tipo de usuário (VENDEDOR, SEPARADOR, COMPRADORA, ADMINISTRADOR)
    """

    numero_login = forms.IntegerField(
        label='Número de Login',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
            'placeholder': 'Ex: 101',
            'autofocus': True,
        }),
        error_messages={
            'required': 'O número de login é obrigatório',
            'invalid': 'Digite um número válido',
            'min_value': 'O número deve ser maior que zero',
        }
    )

    nome = forms.CharField(
        label='Nome Completo',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
            'placeholder': 'Nome completo do usuário',
        }),
        error_messages={
            'required': 'O nome é obrigatório',
            'max_length': 'O nome é muito longo (máximo 200 caracteres)',
        }
    )

    tipo = forms.ChoiceField(
        label='Tipo de Usuário',
        choices=[
            ('VENDEDOR', 'Vendedor'),
            ('SEPARADOR', 'Separador'),
            ('COMPRADORA', 'Compradora'),
            ('ADMINISTRADOR', 'Administrador'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
        }),
        error_messages={
            'required': 'O tipo de usuário é obrigatório',
        }
    )

    pin = forms.CharField(
        label='PIN (4 dígitos)',
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
            'placeholder': '••••',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric',
        }),
        error_messages={
            'required': 'O PIN é obrigatório',
            'max_length': 'O PIN deve ter exatamente 4 dígitos',
            'min_length': 'O PIN deve ter exatamente 4 dígitos',
        }
    )

    pin_confirmacao = forms.CharField(
        label='Confirmar PIN',
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all',
            'placeholder': '••••',
            'maxlength': '4',
            'pattern': '[0-9]{4}',
            'inputmode': 'numeric',
        }),
        error_messages={
            'required': 'A confirmação do PIN é obrigatória',
            'max_length': 'O PIN deve ter exatamente 4 dígitos',
            'min_length': 'O PIN deve ter exatamente 4 dígitos',
        }
    )

    def clean_pin(self):
        """Valida que o PIN tem exatamente 4 dígitos numéricos."""
        pin = self.cleaned_data.get('pin', '')

        if not pin:
            raise ValidationError('O PIN é obrigatório')

        if len(pin) != 4:
            raise ValidationError('O PIN deve ter exatamente 4 dígitos')

        if not pin.isdigit():
            raise ValidationError('O PIN deve conter apenas números')

        return pin

    def clean_numero_login(self):
        """Valida que o número de login é único."""
        from core.models import Usuario

        numero = self.cleaned_data.get('numero_login')

        if numero is None:
            raise ValidationError('O número de login é obrigatório')

        if numero < 1:
            raise ValidationError('O número de login deve ser maior que zero')

        # Verificar se já existe
        if Usuario.objects.filter(numero_login=numero).exists():
            raise ValidationError(f'Já existe um usuário com o número de login {numero}')

        return numero

    def clean(self):
        """Valida que os PINs conferem."""
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        pin_confirmacao = cleaned_data.get('pin_confirmacao')

        if pin and pin_confirmacao and pin != pin_confirmacao:
            raise ValidationError('Os PINs não conferem. Digite o mesmo PIN nos dois campos.')

        return cleaned_data
