# -*- coding: utf-8 -*-
"""
Modelos Django para o sistema de separação de pedidos.
Fase 7: Modelo Usuario customizado
Fase 9: Modelo Produto
Fase 13: Modelos Pedido e ItemPedido
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password

# Import do modelo Produto (Fase 9)
from core.infrastructure.persistence.models.produto import Produto


class TipoUsuario(models.TextChoices):
    """Tipos de usuário no sistema."""
    VENDEDOR = 'VENDEDOR', 'Vendedor'
    SEPARADOR = 'SEPARADOR', 'Separador'
    COMPRADORA = 'COMPRADORA', 'Compradora'
    ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'


class UsuarioManager(BaseUserManager):
    """Manager customizado para o modelo Usuario."""

    def create_user(self, numero_login, pin, nome, tipo='SEPARADOR', **extra_fields):
        """
        Cria e salva um usuário regular.

        Args:
            numero_login: Número de login único
            pin: PIN de 4 dígitos
            nome: Nome completo
            tipo: Tipo de usuário
            **extra_fields: Campos adicionais

        Returns:
            Instância de Usuario criada
        """
        if not numero_login:
            raise ValueError('O número de login é obrigatório')
        if not pin:
            raise ValueError('O PIN é obrigatório')
        if len(pin) != 4 or not pin.isdigit():
            raise ValueError('O PIN deve ter exatamente 4 dígitos numéricos')

        usuario = self.model(
            numero_login=numero_login,
            nome=nome,
            tipo=tipo,
            **extra_fields
        )
        usuario.set_password(pin)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, numero_login, pin, nome, **extra_fields):
        """
        Cria e salva um superusuário.

        Args:
            numero_login: Número de login único
            pin: PIN de 4 dígitos
            nome: Nome completo
            **extra_fields: Campos adicionais

        Returns:
            Instância de Usuario admin criada
        """
        extra_fields.setdefault('is_admin', True)
        return self.create_user(
            numero_login=numero_login,
            pin=pin,
            nome=nome,
            tipo='ADMINISTRADOR',
            **extra_fields
        )


class Usuario(AbstractBaseUser):
    """
    Modelo customizado de usuário para o sistema de separação.

    Usa numero_login como identificador único ao invés de username/email.
    Autenticação feita com numero_login + PIN de 4 dígitos.
    """

    numero_login = models.IntegerField(
        unique=True,
        verbose_name='Número de Login',
        help_text='Número único para identificação do usuário'
    )
    nome = models.CharField(
        max_length=200,
        verbose_name='Nome Completo'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.SEPARADOR,
        verbose_name='Tipo de Usuário'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    is_admin = models.BooleanField(
        default=False,
        verbose_name='Administrador'
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'numero_login'
    REQUIRED_FIELDS = ['nome']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['numero_login']

    def __str__(self):
        return f"{self.numero_login} - {self.nome} ({self.get_tipo_display()})"

    def set_password(self, raw_password):
        """Define o PIN hashado."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Verifica se o PIN está correto."""
        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["password"])
        return check_password(raw_password, self.password, setter)

    @property
    def is_staff(self):
        """Usuários admin podem acessar o admin do Django."""
        return self.is_admin

    def has_perm(self, perm, obj=None):
        """Administradores têm todas as permissões."""
        return self.is_admin

    def has_module_perms(self, app_label):
        """Administradores têm permissão em todos os módulos."""
        return self.is_admin


# ==================== MODELOS PEDIDO (FASE 13) ====================

class LogisticaChoices(models.TextChoices):
    """Tipos de logística disponíveis."""
    CORREIOS = 'CORREIOS', 'Correios'
    MELHOR_ENVIO = 'MELHOR_ENVIO', 'Melhor Envio'
    ONIBUS = 'ONIBUS', 'Ônibus'
    RETIRA_LOJA = 'RETIRA_LOJA', 'Retira na Loja'
    MOTOBOY = 'MOTOBOY', 'Motoboy'


class EmbalagemChoices(models.TextChoices):
    """Tipos de embalagem disponíveis."""
    CAIXA = 'CAIXA', 'Caixa'
    SACOLA = 'SACOLA', 'Sacola'


class StatusPedidoChoices(models.TextChoices):
    """Estados possíveis de um pedido."""
    EM_SEPARACAO = 'EM_SEPARACAO', 'Em Separação'
    FINALIZADO = 'FINALIZADO', 'Finalizado'
    CANCELADO = 'CANCELADO', 'Cancelado'


class Pedido(models.Model):
    """
    Modelo Django para Pedido.

    Representa um pedido de separação criado a partir de um orçamento PDF.
    """
    numero_orcamento = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número do Orçamento',
        help_text='Número único do orçamento (ex: 30567)'
    )
    codigo_cliente = models.CharField(
        max_length=50,
        verbose_name='Código do Cliente'
    )
    nome_cliente = models.CharField(
        max_length=200,
        verbose_name='Nome do Cliente'
    )
    vendedor = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='pedidos_vendedor',
        verbose_name='Vendedor',
        help_text='Vendedor responsável pelo pedido'
    )
    data = models.CharField(
        max_length=10,
        verbose_name='Data do Orçamento',
        help_text='Data no formato DD/MM/AAAA'
    )
    logistica = models.CharField(
        max_length=20,
        choices=LogisticaChoices.choices,
        verbose_name='Tipo de Logística'
    )
    embalagem = models.CharField(
        max_length=10,
        choices=EmbalagemChoices.choices,
        verbose_name='Tipo de Embalagem'
    )
    status = models.CharField(
        max_length=20,
        choices=StatusPedidoChoices.choices,
        default=StatusPedidoChoices.EM_SEPARACAO,
        verbose_name='Status do Pedido'
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observações'
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    data_inicio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Início da Separação'
    )
    data_finalizacao = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data de Finalização'
    )

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['numero_orcamento']),
            models.Index(fields=['status']),
            models.Index(fields=['-criado_em']),
            # Fase 34: Índices de performance
            models.Index(fields=['data_finalizacao']),  # Usado no HistoricoView
            models.Index(fields=['vendedor']),  # Usado em filtros
            models.Index(fields=['data_inicio']),  # Usado no Dashboard
            models.Index(fields=['status', 'data_inicio']),  # Índice composto para Dashboard
        ]

    def __str__(self):
        return f"Pedido {self.numero_orcamento} - {self.nome_cliente}"

    def to_entity(self):
        """
        Converte o modelo Django em entidade de domínio.

        Returns:
            Instância de Pedido do domínio
        """
        from core.domain.pedido.entities import Pedido as PedidoDomain
        from core.domain.pedido.value_objects import Logistica, Embalagem, StatusPedido

        # Converter itens
        itens_domain = [item.to_entity() for item in self.itens.all()]

        return PedidoDomain(
            id=self.id,
            numero_orcamento=self.numero_orcamento,
            codigo_cliente=self.codigo_cliente,
            nome_cliente=self.nome_cliente,
            vendedor=self.vendedor.nome,
            data=self.data,
            logistica=Logistica(self.logistica),
            embalagem=Embalagem(self.embalagem),
            status=StatusPedido(self.status),
            observacoes=self.observacoes,
            itens=itens_domain,
            criado_em=self.criado_em,
            data_inicio=self.data_inicio,
            data_finalizacao=self.data_finalizacao
        )

    @staticmethod
    def from_entity(pedido_entity, vendedor_usuario):
        """
        Cria um modelo Django a partir da entidade de domínio.

        Args:
            pedido_entity: Instância de Pedido do domínio
            vendedor_usuario: Instância de Usuario (vendedor)

        Returns:
            Instância de Pedido Django
        """
        return Pedido(
            id=pedido_entity.id,
            numero_orcamento=pedido_entity.numero_orcamento,
            codigo_cliente=pedido_entity.codigo_cliente,
            nome_cliente=pedido_entity.nome_cliente,
            vendedor=vendedor_usuario,
            data=pedido_entity.data,
            logistica=pedido_entity.logistica.value,
            embalagem=pedido_entity.embalagem.value,
            status=pedido_entity.status.value,
            observacoes=pedido_entity.observacoes,
            criado_em=pedido_entity.criado_em,
            data_inicio=pedido_entity.data_inicio,
            data_finalizacao=pedido_entity.data_finalizacao
        )


class ItemPedido(models.Model):
    """
    Modelo Django para ItemPedido.

    Representa um item (produto) dentro de um pedido.
    """
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Pedido'
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        verbose_name='Produto'
    )
    quantidade_solicitada = models.IntegerField(
        verbose_name='Quantidade Solicitada',
        help_text='Quantidade no orçamento'
    )
    quantidade_separada = models.IntegerField(
        default=0,
        verbose_name='Quantidade Separada'
    )
    separado = models.BooleanField(
        default=False,
        verbose_name='Separado'
    )
    separado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens_separados',
        verbose_name='Separado Por'
    )
    separado_em = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Separado Em'
    )
    em_compra = models.BooleanField(
        default=False,
        verbose_name='Em Compra',
        help_text='Item marcado para ser comprado'
    )
    enviado_para_compra_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens_enviados_compra',
        verbose_name='Enviado para Compra Por'
    )
    enviado_para_compra_em = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Enviado para Compra Em'
    )
    substituido = models.BooleanField(
        default=False,
        verbose_name='Substituído',
        help_text='Item foi substituído por outro produto'
    )
    produto_substituto = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Produto Substituto',
        help_text='Nome do produto que substituiu o original'
    )
    pedido_realizado = models.BooleanField(
        default=False,
        verbose_name='Pedido Realizado',
        help_text='Compradora marcou que o pedido foi realizado'
    )
    realizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens_pedido_realizado',
        verbose_name='Pedido Realizado Por'
    )
    realizado_em = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Pedido Realizado Em'
    )

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'
        ordering = ['id']
        indexes = [
            models.Index(fields=['pedido', 'separado']),
            # Fase 34: Índices de performance
            models.Index(fields=['em_compra']),  # Usado no PainelComprasView
            models.Index(fields=['pedido_realizado']),  # Usado nas métricas
            models.Index(fields=['separado_por']),  # Usado em filtros e métricas
        ]

    def __str__(self):
        return f"Item {self.id} - {self.produto.descricao} (Pedido {self.pedido.numero_orcamento})"

    def marcar_realizado(self, usuario):
        """
        Marca o item como pedido realizado pela compradora.

        Args:
            usuario: Instância de Usuario (compradora)
        """
        from django.utils import timezone
        self.pedido_realizado = True
        self.realizado_por = usuario
        self.realizado_em = timezone.now()
        self.save()

    def to_entity(self):
        """
        Converte o modelo Django em entidade de domínio.

        Returns:
            Instância de ItemPedido do domínio
        """
        from core.domain.pedido.entities import ItemPedido as ItemPedidoDomain

        return ItemPedidoDomain(
            id=self.id,
            produto=self.produto.to_entity(),
            quantidade_solicitada=self.quantidade_solicitada,
            quantidade_separada=self.quantidade_separada,
            separado=self.separado,
            separado_por=self.separado_por.nome if self.separado_por else None,
            separado_em=self.separado_em,
            em_compra=self.em_compra,
            enviado_para_compra_por=self.enviado_para_compra_por.nome if self.enviado_para_compra_por else None,
            enviado_para_compra_em=self.enviado_para_compra_em,
            substituido=self.substituido,
            produto_substituto=self.produto_substituto
        )

    @staticmethod
    def from_entity(item_entity, pedido_django, produto_django, separado_por_usuario=None, enviado_para_compra_por_usuario=None):
        """
        Cria um modelo Django a partir da entidade de domínio.

        Args:
            item_entity: Instância de ItemPedido do domínio
            pedido_django: Instância de Pedido Django
            produto_django: Instância de Produto Django
            separado_por_usuario: Instância de Usuario (opcional)
            enviado_para_compra_por_usuario: Instância de Usuario (opcional)

        Returns:
            Instância de ItemPedido Django
        """
        return ItemPedido(
            id=item_entity.id,
            pedido=pedido_django,
            produto=produto_django,
            quantidade_solicitada=item_entity.quantidade_solicitada,
            quantidade_separada=item_entity.quantidade_separada,
            separado=item_entity.separado,
            separado_por=separado_por_usuario,
            separado_em=item_entity.separado_em,
            em_compra=item_entity.em_compra,
            enviado_para_compra_por=enviado_para_compra_por_usuario,
            enviado_para_compra_em=item_entity.enviado_para_compra_em,
            substituido=item_entity.substituido,
            produto_substituto=item_entity.produto_substituto
        )
