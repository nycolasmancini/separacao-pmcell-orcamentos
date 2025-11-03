# -*- coding: utf-8 -*-
"""
Views web para o sistema de separação.
Fase 7: LoginView e Dashboard Placeholder
Fase 8: LogoutView
Fase 15: UploadOrcamentoView
Fase 30: WebSocket Broadcast
Fase 4 (Parser Integration): UploadOrcamentoView modificada para usar novo parser
"""
import logging
import tempfile
import os
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden, HttpResponseNotFound
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.presentation.web.forms import LoginForm, UploadOrcamentoForm
from core.presentation.web.decorators import login_required
from core.models import Usuario, Pedido, StatusPedidoChoices
from core.application.use_cases.criar_pedido import CriarPedidoUseCase
from core.application.use_cases.obter_metricas_tempo import ObterMetricasTempoUseCase
from core.application.dtos.pedido_dtos import CriarPedidoRequestDTO
from core.infrastructure.pdf.parser import PDFParser, PDFHeaderExtractor, PDFProductExtractor
from core.infrastructure.persistence.repositories.pedido_repository import DjangoPedidoRepository
from core.domain.pedido.value_objects import Logistica, Embalagem

# Fase 4: Import de exceções do novo parser service
from core.application.services.exceptions import (
    DuplicatePedidoError,
    VendedorNotFoundError,
    IntegrityValidationError
)
from core.infrastructure.parsers.pdf_orcamento_parser import ParserError

logger = logging.getLogger(__name__)


def _converter_tipo_usuario_seguro(tipo_str: str):
    """
    Converte string para TipoUsuario de forma segura, tratando valores legados.

    Args:
        tipo_str: String representando o tipo de usuário

    Returns:
        TipoUsuario: Enum correspondente, com fallback para SEPARADOR
    """
    from core.domain.usuario.entities import TipoUsuario

    # Mapeamento de valores legados/alternativos
    MAPA_TIPOS = {
        'ADMIN': TipoUsuario.ADMINISTRADOR,
        'ADMINISTRADOR': TipoUsuario.ADMINISTRADOR,
        'VENDEDOR': TipoUsuario.VENDEDOR,
        'SEPARADOR': TipoUsuario.SEPARADOR,
        'COMPRADORA': TipoUsuario.COMPRADORA,
    }

    tipo_convertido = MAPA_TIPOS.get(tipo_str.upper() if tipo_str else '', TipoUsuario.SEPARADOR)

    if tipo_str and tipo_str not in MAPA_TIPOS:
        logger.warning(
            f"Tipo de usuário '{tipo_str}' não reconhecido, usando fallback SEPARADOR"
        )

    return tipo_convertido


class LoginView(View):
    """
    View de login que usa numero_login + PIN.

    Methods:
        get: Renderiza o formulário de login
        post: Processa o login e cria sessão
    """

    template_name = 'login.html'
    form_class = LoginForm

    def get(self, request):
        """
        Renderiza a página de login.

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Página de login
        """
        # Se já está autenticado, redireciona para dashboard
        if 'usuario_id' in request.session:
            return redirect('dashboard')

        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """
        Processa o login e cria sessão.

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Redirect para dashboard ou login com erros
        """
        form = self.form_class(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        numero_login = form.cleaned_data['numero_login']
        pin = form.cleaned_data['pin']

        # Implementação direta de autenticação (sem LoginUseCase por simplicidade)
        # Rate limiting via cache
        cache_key = f'login_attempts_{numero_login}'
        attempts = cache.get(cache_key, 0)

        if attempts >= 5:
            messages.error(
                request,
                'Muitas tentativas de login. Conta bloqueada temporariamente. Aguarde 1 minuto.'
            )
            return render(request, self.template_name, {
                'form': form,
                'blocked': True
            })

        try:
            usuario = Usuario.objects.get(numero_login=numero_login)

            if not usuario.ativo:
                messages.error(request, 'Usuário inativo. Entre em contato com o administrador.')
                return render(request, self.template_name, {'form': form})

            if usuario.check_password(pin):
                # Login bem-sucedido - resetar tentativas
                cache.delete(cache_key)

                # Usar login() do Django para criar sessão corretamente
                login(request, usuario)

                # Criar dados customizados da sessão
                request.session['usuario_id'] = usuario.id
                request.session['numero_login'] = usuario.numero_login
                request.session['nome'] = usuario.nome
                request.session['tipo'] = usuario.tipo

                logger.info(
                    f"Login bem-sucedido: {usuario.numero_login} - {usuario.nome} ({usuario.tipo})"
                )
                return redirect('dashboard')
            else:
                # PIN incorreto - incrementar tentativas
                new_attempts = attempts + 1
                cache.set(cache_key, new_attempts, 60)  # 60 segundos

                remaining = 5 - new_attempts
                logger.warning(
                    f"Tentativa de login falhada para número {numero_login}. "
                    f"Tentativas: {new_attempts}/5"
                )

                if remaining > 0:
                    messages.error(
                        request,
                        f'Credenciais inválidas. {remaining} tentativa(s) restante(s).'
                    )
                else:
                    logger.error(
                        f"Usuário {numero_login} bloqueado temporariamente por excesso de tentativas"
                    )
                    messages.error(
                        request,
                        'Muitas tentativas de login. Conta bloqueada temporariamente. Aguarde 1 minuto.'
                    )

                return render(request, self.template_name, {'form': form})

        except Usuario.DoesNotExist:
            # Incrementar tentativas mesmo se usuário não existir (segurança)
            new_attempts = attempts + 1
            cache.set(cache_key, new_attempts, 60)

            remaining = 5 - new_attempts
            if remaining > 0:
                messages.error(
                    request,
                    f'Credenciais inválidas. {remaining} tentativa(s) restante(s).'
                )
            else:
                messages.error(
                    request,
                    'Muitas tentativas de login. Conta bloqueada temporariamente. Aguarde 1 minuto.'
                )

            return render(request, self.template_name, {'form': form})


class DashboardView(View):
    """
    View do dashboard principal - Fase 17 e Fase 19.

    Exibe cards de pedidos em separação com informações em tempo real:
    - Tempo decorrido desde início da separação
    - Progresso (itens separados/total)
    - Separadores ativos (usuários que estão separando)

    Fase 19 adiciona:
    - Paginação (10 pedidos por página)
    - Busca por número de orçamento ou nome de cliente
    - Filtro por vendedor
    - Suporte a requisições HTMX (retorna partial HTML)
    """

    template_name = 'dashboard.html'
    partial_template_name = 'partials/_pedidos_grid.html'
    items_per_page = 10

    def get(self, request):
        """
        Renderiza o dashboard com pedidos em separação.

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Dashboard com cards de pedidos
        """
        from django.core.paginator import Paginator
        from django.db.models import Q

        # Verificar se está autenticado
        if 'usuario_id' not in request.session:
            return redirect('login')

        # Obter query params
        search_query = request.GET.get('search', '').strip()
        vendedor_id = request.GET.get('vendedor', '').strip()
        page_number = request.GET.get('page', 1)

        # Buscar pedidos com filtros
        pedidos_queryset = self._get_pedidos_queryset()
        pedidos_queryset = self._apply_filters(pedidos_queryset, search_query, vendedor_id)

        # Paginar
        paginator = Paginator(pedidos_queryset, self.items_per_page)
        page_obj = paginator.get_page(page_number)

        # Processar pedidos da página atual
        pedidos_data = [self._build_pedido_data(pedido) for pedido in page_obj]

        # Buscar todos os vendedores para o filtro
        vendedores = self._get_vendedores()

        # Obter métricas de tempo (Fase 20)
        metricas_tempo = self._obter_metricas_tempo()

        # Obter métricas de pedidos (finalizados hoje + em aberto)
        from django.utils import timezone
        from datetime import datetime
        hoje = timezone.now().date()
        pedidos_finalizados_hoje = Pedido.objects.filter(
            status=StatusPedidoChoices.FINALIZADO,
            data_finalizacao__date=hoje
        ).count()
        pedidos_em_aberto = Pedido.objects.filter(
            status=StatusPedidoChoices.EM_SEPARACAO
        ).count()

        # Selecionar mensagem rotativa para empty state (Fase Mensagens Rotativas)
        import random
        # Usar data atual como seed para garantir consistência no mesmo dia
        random.seed(hoje.toordinal())

        # 7 mensagens criativas para empty state
        mensagens_empty_state = [
            {
                'titulo': 'Tudo certo por aqui!',
                'subtitulo': 'Nenhum pedido pendente. Aproveite o momento pra recarregar as energias ☕'
            },
            {
                'titulo': 'Tudo tranquilo na área de separação',
                'subtitulo': 'Nenhum pedido encontrado nos filtros aplicados. Que tal revisar ou aproveitar um café? ☕'
            },
            {
                'titulo': 'Hora do descanso merecido',
                'subtitulo': 'Nenhum pedido disponível. Use esse tempo pra alongar, respirar e voltar com tudo!'
            },
            {
                'titulo': 'Silêncio no estoque...',
                'subtitulo': 'Nenhum pedido em separação. Talvez seja o momento ideal para a Eliane pedir post-it rsrs'
            },
            {
                'titulo': 'Zerou a fila!',
                'subtitulo': 'Nenhum pedido pra separar. Pode comemorar (mas comemora baixo se o Zabin estiver perto)'
            },
            {
                'titulo': 'Fila zerada, energia recarregada',
                'subtitulo': 'Nenhum pedido em vista. Hora de alongar o mouse e dar aquele gole d\'água 💧'
            },
            {
                'titulo': 'Tudo sob controle',
                'subtitulo': 'Nenhum pedido para separar agora — sinal de que a equipe está mandando bem! 👏'
            }
        ]

        mensagem_do_dia = random.choice(mensagens_empty_state)

        # Buscar usuário completo para obter is_admin
        usuario_obj = Usuario.objects.get(id=request.session.get('usuario_id'))

        # Preparar contexto
        import time
        cache_bust = int(time.time())  # Timestamp para cache-busting de imagens

        context = {
            'usuario': {
                'nome': request.session.get('nome'),
                'numero_login': request.session.get('numero_login'),
                'tipo': request.session.get('tipo'),
                'is_admin': usuario_obj.is_admin,
            },
            'pedidos': {
                'results': pedidos_data,
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            },
            'vendedores': vendedores,
            'search_query': search_query,
            'vendedor_id': vendedor_id,
            'metricas_tempo': metricas_tempo,
            'pedidos_finalizados_hoje': pedidos_finalizados_hoje,
            'pedidos_em_aberto': pedidos_em_aberto,
            'mensagem_do_dia': mensagem_do_dia,  # Mensagens rotativas para empty state
            'cache_bust': cache_bust  # Para forçar reload de imagens estáticas
        }

        # Se for requisição HTMX, retornar apenas o partial
        if request.headers.get('HX-Request'):
            return render(request, self.partial_template_name, context)

        return render(request, self.template_name, context)

    def _get_pedidos_queryset(self):
        """
        Retorna QuerySet base de pedidos em separação.

        Returns:
            QuerySet: Pedidos em separação ordenados por mais antigos primeiro
        """
        from core.models import Pedido, StatusPedidoChoices

        return Pedido.objects.filter(
            status=StatusPedidoChoices.EM_SEPARACAO
        ).select_related('vendedor').prefetch_related(
            'itens',
            'itens__separado_por'
        ).order_by('data_inicio')  # Mais antigos primeiro

    def _apply_filters(self, queryset, search_query, vendedor_id):
        """
        Aplica filtros de busca e vendedor ao queryset.

        Args:
            queryset: QuerySet de pedidos
            search_query: Texto de busca (número orçamento ou cliente)
            vendedor_id: ID do vendedor para filtrar

        Returns:
            QuerySet: Queryset filtrado
        """
        from django.db.models import Q

        if search_query:
            queryset = queryset.filter(
                Q(numero_orcamento__icontains=search_query) |
                Q(nome_cliente__icontains=search_query)
            )

        if vendedor_id:
            try:
                queryset = queryset.filter(vendedor_id=int(vendedor_id))
            except (ValueError, TypeError):
                pass  # Ignorar IDs inválidos

        return queryset

    def _get_vendedores(self):
        """
        Retorna lista de vendedores para o filtro com cache (Fase 34).

        Returns:
            list: Lista de usuários vendedores (cacheada por 5 minutos)
        """
        from core.models import Usuario

        # Fase 34: Adicionar cache de 5 minutos
        vendedores_cache = cache.get('dashboard_vendedores')
        if vendedores_cache is not None:
            logger.debug("Vendedores carregados do cache")
            return vendedores_cache

        # Buscar do banco
        vendedores = list(Usuario.objects.filter(
            tipo='VENDEDOR',
            ativo=True
        ).order_by('nome').values('id', 'nome', 'numero_login'))

        # Cachear por 5 minutos (300 segundos)
        cache.set('dashboard_vendedores', vendedores, 300)
        logger.debug(f"Vendedores cacheados: {len(vendedores)} vendedores")

        return vendedores

    def _build_pedido_data(self, pedido):
        """
        Constrói dicionário com dados e métricas de um pedido.

        Args:
            pedido: Instância do modelo Pedido

        Returns:
            dict: Dados do pedido com métricas calculadas
        """
        itens = pedido.itens.all()

        # Extrair apenas o primeiro nome do vendedor
        vendedor_primeiro_nome = pedido.vendedor.nome.split()[0] if pedido.vendedor and pedido.vendedor.nome else ""

        return {
            'pedido': pedido,
            'vendedor_primeiro_nome': vendedor_primeiro_nome,
            'tempo_decorrido_minutos': self._calcular_tempo_decorrido(pedido),
            'total_itens': len(itens),
            'itens_separados': self._contar_itens_separados(itens),
            'progresso_percentual': self._calcular_progresso(itens),
            'separadores': self._get_separadores_ativos(itens)
        }

    def _calcular_tempo_decorrido(self, pedido):
        """
        Calcula tempo decorrido desde início da separação.

        Args:
            pedido: Instância do modelo Pedido

        Returns:
            int: Tempo em minutos
        """
        from django.utils import timezone
        tempo_decorrido = timezone.now() - pedido.data_inicio
        return int(tempo_decorrido.total_seconds() / 60)

    def _contar_itens_separados(self, itens):
        """
        Conta quantos itens foram separados ou substituídos.

        Itens substituídos também contam como "separados" pois
        representam itens resolvidos na separação.

        Args:
            itens: QuerySet de ItemPedido

        Returns:
            int: Número de itens separados ou substituídos
        """
        return sum(1 for item in itens if item.separado or item.substituido)

    def _calcular_progresso(self, itens):
        """
        Calcula progresso percentual da separação.

        Args:
            itens: QuerySet de ItemPedido

        Returns:
            int: Percentual de progresso (0-100)
        """
        total_itens = len(itens)
        if total_itens == 0:
            return 0

        itens_separados = self._contar_itens_separados(itens)
        return int((itens_separados / total_itens * 100))

    def _get_separadores_ativos(self, itens):
        """
        Identifica usuários que estão separando itens.

        Args:
            itens: QuerySet de ItemPedido

        Returns:
            list: Lista de usuários únicos que separaram itens
        """
        from core.models import Usuario

        separadores_ids = set()
        for item in itens:
            if item.separado and item.separado_por:
                separadores_ids.add(item.separado_por.id)

        return list(Usuario.objects.filter(id__in=separadores_ids))

    def _obter_metricas_tempo(self):
        """
        Obtém métricas de tempo médio de separação (Fase 20).

        Returns:
            dict: Dicionário com métricas formatadas para template
        """
        try:
            # Instanciar use case
            repository = DjangoPedidoRepository()
            use_case = ObterMetricasTempoUseCase(repository)

            # Executar use case
            metricas = use_case.execute()

            # Converter para dicionário formatado
            return use_case.to_dict(metricas)

        except Exception as e:
            logger.error(f"Erro ao obter métricas de tempo: {e}")
            # Retornar métricas vazias em caso de erro
            return {
                'tempo_medio_hoje_minutos': None,
                'tempo_medio_7dias_minutos': None,
                'percentual_diferenca': None,
                'tendencia': 'sem_dados',
                'tempo_hoje_formatado': 'Sem dados',
                'tempo_7dias_formatado': 'Sem dados',
                'percentual_formatado': '',
            }


class LogoutView(View):
    """
    View de logout - Fase 8.

    Limpa a sessão do usuário e redireciona para página de login.
    Aceita tanto GET (links) quanto POST (formulários).
    """

    def get(self, request):
        """
        Realiza logout via GET (usado por links).

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Redirect para login
        """
        return self._logout(request)

    def post(self, request):
        """
        Realiza logout via POST (usado por formulários).

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Redirect para login
        """
        return self._logout(request)

    def _logout(self, request):
        """
        Lógica compartilhada de logout.

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Redirect para login
        """
        # Capturar informações antes de limpar sessão
        usuario_numero = request.user.numero_login if request.user.is_authenticated else 'desconhecido'

        # Limpar sessão Django (usa o logout() do Django)
        logout(request)

        # Limpar dados customizados da sessão
        request.session.flush()

        logger.info(f"Logout realizado com sucesso para usuário {usuario_numero}")
        return redirect('login')


@method_decorator(login_required, name='dispatch')
class UploadOrcamentoView(View):
    """
    View para upload de PDF de orçamento e criação de pedido.

    Fase 15: Tela de Upload de PDF (UI)

    Methods:
        get: Renderiza formulário de upload
        post: Processa upload, extrai dados e cria pedido
    """

    template_name = 'upload_orcamento.html'
    form_class = UploadOrcamentoForm

    def get(self, request):
        """
        Renderiza a página de upload.

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Página de upload
        """
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'usuario': request.user
        })

    def post(self, request):
        """
        Processa upload de PDF e cria pedido usando novo parser service.

        FASE 4: Modificado para usar UploadOrcamentoForm.processar_pdf()
        que integra com OrcamentoParserService (Fases 1-3).

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Redirect para dashboard ou formulário com erros
        """
        form = self.form_class(request.POST, request.FILES)

        if not form.is_valid():
            logger.warning(f"Formulário de upload inválido: {form.errors}")
            return render(request, self.template_name, {'form': form, 'usuario': request.user})

        try:
            # FASE 4: Usar form.processar_pdf() que integra com OrcamentoParserService
            pedido = form.processar_pdf(vendedor=request.user)

            logger.info(
                f"Pedido criado com sucesso via novo parser: "
                f"{pedido.numero_orcamento} (ID: {pedido.id})"
            )

            # Fase 30: Broadcast evento WebSocket para dashboard
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'dashboard',
                    {
                        'type': 'pedido_criado',
                        'pedido_id': pedido.id
                    }
                )
                logger.info(f"Evento WebSocket enviado: pedido_criado (ID: {pedido.id})")
            except Exception as e:
                logger.warning(f"Erro ao enviar evento WebSocket pedido_criado: {e}")

            messages.success(
                request,
                f'Pedido #{pedido.numero_orcamento} criado com sucesso!'
            )
            return redirect('dashboard')

        except DuplicatePedidoError as e:
            # Orçamento duplicado - exibir mensagem amigável
            logger.warning(f"Tentativa de upload de orçamento duplicado: {e.numero_orcamento}")
            messages.error(
                request,
                f'Este orçamento já existe no sistema (#{e.numero_orcamento}). '
                f'Verifique o dashboard ou histórico.'
            )
            return render(request, self.template_name, {'form': form, 'usuario': request.user})

        except VendedorNotFoundError as e:
            # Vendedor do PDF não encontrado no sistema
            logger.error(f"Vendedor não encontrado no PDF: {e.nome_vendedor}")
            messages.error(
                request,
                f'Vendedor "{e.nome_vendedor}" não encontrado no sistema. '
                f'Entre em contato com o administrador.'
            )
            return render(request, self.template_name, {'form': form, 'usuario': request.user})

        except IntegrityValidationError as e:
            # Falha na validação matemática do PDF
            logger.error(f"Falha de integridade no PDF: {e.message}")
            messages.error(
                request,
                f'Erro na validação do PDF: {e.message}. '
                f'Verifique se o PDF está correto ou entre em contato com o suporte.'
            )
            return render(request, self.template_name, {'form': form, 'usuario': request.user})

        except ParserError as e:
            # Erro ao fazer parsing do PDF (corrompido, formato inválido, etc.)
            logger.error(f"Erro ao fazer parsing do PDF: {str(e)}")
            messages.error(
                request,
                f'Erro ao processar PDF: {str(e)}. '
                f'Verifique se o arquivo está correto e tente novamente.'
            )
            return render(request, self.template_name, {'form': form, 'usuario': request.user})

        except Exception as e:
            # Erro inesperado - logar com stacktrace
            logger.exception(f"Erro inesperado ao processar upload: {e}")
            messages.error(
                request,
                f'Erro inesperado ao processar PDF: {str(e)}. '
                f'Entre em contato com o suporte técnico.'
            )
            return render(request, self.template_name, {'form': form, 'usuario': request.user})


@method_decorator(login_required, name='dispatch')
class DetalhePedidoView(View):
    """
    View para exibir detalhes de um pedido específico.

    Fase 21: Visualização detalhada com itens separados e não separados.
    Fase 39b: Lista corrida única com itens ordenados por estado.

    Methods:
        get: Renderiza template com detalhes do pedido
    """

    template_name = 'detalhe_pedido.html'

    def get(self, request, pedido_id):
        """
        Renderiza detalhes de um pedido.

        Fase 39b: Retorna lista única de itens ordenados por estado:
        1. Aguardando separação (alfabética)
        2. Enviados para compras (alfabética)
        3. Substituídos (alfabética)
        4. Separados (alfabética)

        Args:
            request: HttpRequest
            pedido_id: ID do pedido

        Returns:
            HttpResponse: Template renderizado ou 404
        """
        from django.shortcuts import get_object_or_404
        from core.models import Pedido
        from core.infrastructure.persistence.repositories.pedido_repository import (
            DjangoPedidoRepository
        )

        logger.info(f"Usuário {request.user.nome} acessou detalhes do pedido #{pedido_id}")

        # Buscar pedido com otimizações de query
        pedido = get_object_or_404(
            Pedido.objects.select_related('vendedor'),
            id=pedido_id
        )

        # Fase 39b: Usar repositório para obter itens ordenados por estado
        repository = DjangoPedidoRepository()
        itens = repository.obter_itens_ordenados_por_estado(pedido_id)

        # Calcular métricas
        tempo_decorrido_minutos = self._calcular_tempo_decorrido(pedido)
        progresso_percentual = self._calcular_progresso(itens)

        # Calcular contadores para o template
        total_itens = len(itens)
        itens_separados_count = sum(1 for item in itens if item.separado)

        context = {
            'pedido': pedido,
            'itens': itens,  # Fase 39b: Lista única ordenada
            'tempo_decorrido_minutos': tempo_decorrido_minutos,
            'progresso_percentual': progresso_percentual,
            'total_itens': total_itens,
            'itens_separados_count': itens_separados_count,
            'usuario': request.user
        }

        logger.debug(
            f"Pedido #{pedido_id}: {len(itens)} itens ordenados por estado, "
            f"progresso {progresso_percentual}%"
        )

        return render(request, self.template_name, context)

    def _calcular_tempo_decorrido(self, pedido):
        """
        Calcula tempo decorrido desde início da separação.

        Args:
            pedido: Instância do modelo Pedido

        Returns:
            int: Tempo em minutos
        """
        from django.utils import timezone

        if not pedido.data_inicio:
            return 0

        tempo_decorrido = timezone.now() - pedido.data_inicio
        return int(tempo_decorrido.total_seconds() / 60)

    def _calcular_progresso(self, itens):
        """
        Calcula progresso percentual da separação.

        Conta itens separados E substituídos, pois ambos representam
        itens "resolvidos" na separação.

        Args:
            itens: Lista de ItemPedido

        Returns:
            int: Percentual de progresso (0-100)
        """
        total_itens = len(itens)
        if total_itens == 0:
            return 0

        # Contar itens separados OU substituídos
        itens_concluidos = sum(1 for item in itens if item.separado or item.substituido)
        return int((itens_concluidos / total_itens) * 100)


# ==================== FASE 22: SEPARAR ITEM ====================

@method_decorator(login_required, name='dispatch')
class SepararItemView(View):
    """
    View para marcar um item como separado via HTMX (Fase 22).

    Endpoint HTMX: POST /pedidos/{pedido_id}/itens/{item_id}/separar/

    Responsabilidades:
    - Validar que requisição vem de HTMX
    - Buscar pedido e item
    - Marcar item como separado
    - Retornar partial atualizado (_item_pedido.html)
    - Atualizar progresso do pedido

    Methods:
        post: Processa marcação de item como separado
    """

    def post(self, request, pedido_id, item_id):
        """
        Marca um item como separado.

        Args:
            request: HttpRequest (deve ter header HX-Request)
            pedido_id: ID do pedido
            item_id: ID do item a ser marcado

        Returns:
            HttpResponse com partial HTML atualizado ou erro 400/404
        """
        # Validar que é requisição HTMX
        if not request.headers.get('HX-Request'):
            logger.warning(f"Tentativa de acesso não-HTMX ao endpoint separar_item")
            return render(request, 'partials/_erro.html', {
                'mensagem': 'Requisição inválida'
            }, status=400)

        # Buscar pedido
        from core.models import Pedido, ItemPedido as ItemPedidoDjango
        try:
            pedido = Pedido.objects.prefetch_related('itens__produto').get(id=pedido_id)
        except Pedido.DoesNotExist:
            logger.warning(f"Pedido {pedido_id} não encontrado")
            return render(request, 'partials/_erro.html', {
                'mensagem': f'Pedido não encontrado (ID: {pedido_id})'
            }, status=404)

        # Buscar item
        try:
            item = ItemPedidoDjango.objects.select_related('produto').get(
                id=item_id,
                pedido=pedido
            )
        except ItemPedidoDjango.DoesNotExist:
            logger.warning(f"Item {item_id} não encontrado no pedido {pedido_id}")
            return render(request, 'partials/_erro.html', {
                'mensagem': f'Item não encontrado (ID: {item_id})'
            }, status=404)

        # Verificar se item já está separado
        # Se sim, desmarcar (toggle behavior)
        from django.utils import timezone
        if item.separado:
            logger.info(f"Item {item_id} já está separado, desmarcando...")

            # Desmarcar item e remover TODAS as marcações
            # Campos de separação
            item.separado = False
            item.quantidade_separada = 0
            item.separado_por = None
            item.separado_em = None

            # Campos de compra
            item.em_compra = False
            item.enviado_para_compra_por = None
            item.enviado_para_compra_em = None

            # Campos de substituição
            item.substituido = False
            item.produto_substituto = None

            # Campos de pedido realizado
            item.pedido_realizado = False
            item.realizado_por = None
            item.realizado_em = None

            item.save()

            logger.info(
                f"Item {item_id} desmarcado - todas as marcações removidas no pedido {pedido_id}"
            )
        else:
            # Marcar item como separado
            item.separado = True
            item.quantidade_separada = item.quantidade_solicitada
            item.separado_por = request.user
            item.separado_em = timezone.now()

            # Fase 43a: Desmarcar compra quando item é separado
            # Item separado não deve mais aparecer no painel de compras
            if item.em_compra:
                logger.info(
                    f"Item {item_id} estava em compra - desmarcando automaticamente"
                )
                item.em_compra = False
                item.enviado_para_compra_por = None
                item.enviado_para_compra_em = None

            item.save()

            logger.info(
                f"Item {item_id} marcado como separado por {request.user.nome} "
                f"no pedido {pedido_id}"
            )

        # Calcular progresso atualizado
        # Força refresh do queryset para pegar valores atualizados do banco
        pedido.refresh_from_db()
        itens = list(pedido.itens.all())
        progresso_percentual = self._calcular_progresso(itens)

        # Calcular contadores para WebSocket
        itens_separados_count = sum(1 for i in itens if i.separado)
        total_itens_count = len(itens)

        logger.info(
            f"Progresso do pedido {pedido_id} atualizado: {progresso_percentual}% "
            f"({itens_separados_count}/{total_itens_count})"
        )

        # Fase 30: Broadcast evento WebSocket para dashboard
        # Fase 38: Adicionar flag item_separado para corrigir bug de desmarcação
        # Fase 43a: Adicionar flag em_compra para sinalizar remoção do painel de compras
        # Payload enriquecido com contadores e item_id para atualizações em tempo real
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'item_separado',
                    'pedido_id': pedido.id,
                    'progresso': progresso_percentual,
                    'itens_separados': itens_separados_count,
                    'total_itens': total_itens_count,
                    'item_id': item_id,
                    'item_separado': item.separado,  # Fase 38: Flag para determinar container destino
                    'em_compra': item.em_compra  # Fase 43a: Flag para remover do painel de compras
                }
            )
            logger.info(
                f"Evento WebSocket enviado: item_separado "
                f"(pedido_id={pedido.id}, progresso={progresso_percentual}%, "
                f"itens={itens_separados_count}/{total_itens_count}, "
                f"item_id={item_id}, item_separado={item.separado}, em_compra={item.em_compra})"
            )
        except Exception as e:
            logger.warning(f"Erro ao enviar evento WebSocket item_separado: {e}")

        # Fase 37 - Correção de Bug: Quando item é DESMARCADO (separado → False),
        # retornar apenas confirmação sem HTML para evitar swap in-place do HTMX.
        # JavaScript irá buscar HTML fresco via GET.
        if not item.separado:
            # Item foi DESMARCADO - retornar apenas confirmação
            from django.http import HttpResponse
            response = HttpResponse(status=200)
            response['HX-Trigger'] = 'itemDesmarcado'
            response['X-Item-Id'] = str(item_id)
            response['X-Item-State-Changed'] = 'nao-separado'

            logger.info(
                f"Item {item_id} desmarcado - retornando confirmação "
                f"(JavaScript buscará HTML fresco)"
            )

            return response

        # Item foi MARCADO como separado - renderizar partial atualizado normalmente
        response = render(request, 'partials/_item_pedido.html', {
            'item': item,
            'pedido': pedido,
            'progresso_percentual': progresso_percentual
        })

        # Adicionar headers customizados (Fase 37 - Animações)
        response['HX-Trigger'] = 'itemSeparado'
        response['X-Item-State-Changed'] = 'separado'

        return response

    def _calcular_progresso(self, itens):
        """
        Calcula progresso percentual da separação.

        Conta itens separados E substituídos, pois ambos representam
        itens "resolvidos" na separação.

        Args:
            itens: Lista de ItemPedido

        Returns:
            int: Percentual de progresso (0-100)
        """
        total_itens = len(itens)
        if total_itens == 0:
            return 0

        # Contar itens separados OU substituídos
        itens_concluidos = sum(1 for item in itens if item.separado or item.substituido)
        return int((itens_concluidos / total_itens) * 100)


class MarcarParaCompraView(View):
    """
    View HTMX para marcar item para compra (Fase 23).

    Endpoint: POST /pedidos/<pedido_id>/itens/<item_id>/marcar-compra/

    Esta view permite que separadores marquem itens faltantes para serem
    comprados, enviando-os ao painel de compras sem alterar o progresso do pedido.

    Methods:
        post: Marca item para compra e retorna partial HTML atualizado
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, pedido_id, item_id):
        """
        Marca item para compra via HTMX.

        Args:
            request: HttpRequest (deve ter HX-Request header)
            pedido_id: ID do pedido
            item_id: ID do item a ser marcado

        Returns:
            HttpResponse: Partial HTML do item atualizado ou erro
        """
        # Validar que é requisição HTMX ou AJAX (para testes)
        is_htmx = request.headers.get('HX-Request')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not (is_htmx or is_ajax):
            logger.warning(
                f"Tentativa de marcar item para compra sem HTMX: "
                f"pedido={pedido_id}, item={item_id}"
            )
            from django.http import JsonResponse
            return JsonResponse(
                {'erro': 'Requisição inválida'},
                status=400
            )

        logger.info(
            f"Marcando item para compra: pedido={pedido_id}, "
            f"item={item_id}, usuario={request.user.id}"
        )

        # Buscar pedido e item (similar a SepararItemView)
        from core.models import Pedido, ItemPedido as ItemPedidoModel
        from django.utils import timezone

        try:
            item = ItemPedidoModel.objects.select_related(
                'produto',
                'pedido',
                'enviado_para_compra_por'
            ).get(id=item_id, pedido_id=pedido_id)

        except ItemPedidoModel.DoesNotExist:
            logger.error(f"Item {item_id} não encontrado no pedido {pedido_id}")
            return render(
                request,
                'partials/_erro.html',
                {'mensagem': 'Item não encontrado'},
                status=400
            )

        # Validar regras de negócio
        if item.separado:
            logger.warning(
                f"Tentativa de marcar item já separado para compra: item={item_id}"
            )
            return render(
                request,
                'partials/_erro.html',
                {'mensagem': 'Item já foi separado'},
                status=400
            )

        if item.em_compra:
            logger.warning(
                f"Tentativa de marcar item já em compra: item={item_id}"
            )
            return render(
                request,
                'partials/_erro.html',
                {'mensagem': 'Item já está marcado para compra'},
                status=400
            )

        # Marcar item para compra
        item.em_compra = True
        item.enviado_para_compra_por = request.user
        item.enviado_para_compra_em = timezone.now()
        item.save()

        logger.info(
            f"Item {item_id} marcado para compra com sucesso "
            f"por {request.user.nome}"
        )

        # Fase 41: Broadcast evento WebSocket item_marcado_compra (Fase 41a)
        try:
            channel_layer = get_channel_layer()

            pedido = item.pedido
            pedido.refresh_from_db()

            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'item_marcado_compra',
                    'item_id': item_id,
                    'pedido_id': pedido.id,
                    'numero_orcamento': pedido.numero_orcamento,
                    'nome_cliente': pedido.nome_cliente,
                    'produto_codigo': item.produto.codigo,
                    'produto_descricao': item.produto.descricao,
                    'quantidade_solicitada': item.quantidade_solicitada,
                    'enviado_por': request.user.nome,
                    'enviado_em': item.enviado_para_compra_em.strftime('%d/%m/%Y %H:%M') if item.enviado_para_compra_em else ''
                }
            )
            logger.info(
                f"Evento WebSocket enviado: item_marcado_compra "
                f"(pedido_id={pedido.id}, item_id={item_id})"
            )
        except Exception as e:
            logger.warning(f"Erro ao enviar evento WebSocket marcar_compra: {e}")

        # Renderizar badge específico para atualização local via HTMX (Fase 42a)
        return render(
            request,
            'partials/_badge_compra_item.html',
            {
                'item': item
            }
        )


class DesmarcarCompraView(View):
    """
    View HTMX para desmarcar item de compra (Fase 42b).

    Endpoint: POST /pedidos/<pedido_id>/itens/<item_id>/desmarcar-compra/

    Esta view permite desmarcar um item que havia sido enviado para compra,
    removendo-o do painel de compras e limpando os campos relacionados.

    Methods:
        post: Desmarca item de compra e retorna partial HTML atualizado
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, pedido_id, item_id):
        """
        Desmarca item de compra via HTMX.

        Args:
            request: HttpRequest (deve ter HX-Request header)
            pedido_id: ID do pedido
            item_id: ID do item a ser desmarcado

        Returns:
            HttpResponse: Partial HTML do badge limpo ou erro
        """
        # Validar que é requisição HTMX ou AJAX (para testes)
        is_htmx = request.headers.get('HX-Request')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not (is_htmx or is_ajax):
            logger.warning(
                f"Tentativa de desmarcar item sem HTMX: "
                f"pedido={pedido_id}, item={item_id}"
            )
            from django.http import JsonResponse
            return JsonResponse(
                {'erro': 'Requisição inválida'},
                status=400
            )

        logger.info(
            f"Desmarcando item de compra: pedido={pedido_id}, "
            f"item={item_id}, usuario={request.user.id}"
        )

        # Buscar item
        from core.models import ItemPedido as ItemPedidoModel

        try:
            item = ItemPedidoModel.objects.select_related(
                'produto',
                'pedido'
            ).get(id=item_id, pedido_id=pedido_id)

        except ItemPedidoModel.DoesNotExist:
            logger.error(f"Item {item_id} não encontrado no pedido {pedido_id}")
            return render(
                request,
                'partials/_erro.html',
                {'mensagem': 'Item não encontrado'},
                status=400
            )

        # Limpar campos de compra
        item.em_compra = False
        item.enviado_para_compra_por = None
        item.enviado_para_compra_em = None
        item.save()

        logger.info(
            f"Item {item_id} desmarcado de compra com sucesso "
            f"por {request.user.nome}"
        )

        # Fase 42b: Broadcast evento WebSocket item_desmarcado_compra
        try:
            channel_layer = get_channel_layer()

            pedido = item.pedido
            pedido.refresh_from_db()

            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'item_desmarcado_compra',
                    'item_id': item_id,
                    'pedido_id': pedido.id,
                    'numero_orcamento': pedido.numero_orcamento,
                    'produto_codigo': item.produto.codigo,
                    'produto_descricao': item.produto.descricao,
                    'desmarcado_por': request.user.nome
                }
            )
            logger.info(
                f"Evento WebSocket enviado: item_desmarcado_compra "
                f"(pedido_id={pedido.id}, item_id={item_id})"
            )
        except Exception as e:
            logger.warning(f"Erro ao enviar evento WebSocket desmarcar_compra: {e}")

        # Renderizar badge limpo para atualização local via HTMX (Fase 42b)
        return render(
            request,
            'partials/_badge_compra_item.html',
            {
                'item': item
            }
        )


class SubstituirItemView(View):
    """
    View HTMX para substituir item por produto alternativo (Fase 24).

    Endpoints:
        GET /pedidos/<pedido_id>/itens/<item_id>/substituir/ - Retorna modal HTML
        POST /pedidos/<pedido_id>/itens/<item_id>/substituir/ - Processa substituição

    Esta view permite que separadores substituam um produto faltante por
    outro similar, registrando a substituição e marcando o item como separado.

    Methods:
        get: Retorna modal HTML para capturar produto substituto
        post: Substitui item e retorna partial HTML atualizado
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, pedido_id, item_id):
        """
        Retorna o modal HTML para substituição (HTMX).

        Args:
            request: HttpRequest
            pedido_id: ID do pedido
            item_id: ID do item

        Returns:
            HttpResponse: Modal HTML
        """
        # Buscar item para pegar nome do produto original
        from core.models import ItemPedido as ItemPedidoModel

        try:
            item = ItemPedidoModel.objects.select_related('produto').get(
                id=item_id,
                pedido_id=pedido_id
            )
        except ItemPedidoModel.DoesNotExist:
            from django.http import HttpResponse
            return HttpResponse("Item não encontrado", status=404)

        return render(
            request,
            'partials/_modal_substituir.html',
            {
                'pedido_id': pedido_id,
                'item_id': item_id,
                'produto_original': item.produto.descricao
            }
        )

    def post(self, request, pedido_id, item_id):
        """
        Substitui item por produto alternativo via HTMX.

        Args:
            request: HttpRequest (deve ter HX-Request header)
            pedido_id: ID do pedido
            item_id: ID do item a ser substituído

        Expected POST data:
            produto_substituto: Nome do produto que substitui o original

        Returns:
            HttpResponse: Partial HTML do item atualizado ou erro
        """
        # Validar que é requisição HTMX
        if not request.headers.get('HX-Request'):
            logger.warning(
                f"Tentativa de substituir item sem HTMX: "
                f"pedido={pedido_id}, item={item_id}"
            )
            from django.http import JsonResponse
            return JsonResponse(
                {'erro': 'Requisição inválida'},
                status=400
            )

        # Obter produto_substituto do POST
        produto_substituto = request.POST.get('produto_substituto', '').strip()

        if not produto_substituto:
            logger.warning(
                f"Tentativa de substituir item sem informar produto substituto: "
                f"item={item_id}"
            )
            return render(
                request,
                'partials/_erro.html',
                {'mensagem': 'O nome do produto substituto deve ser informado'},
                status=400
            )

        logger.info(
            f"Substituindo item: pedido={pedido_id}, "
            f"item={item_id}, produto='{produto_substituto}', usuario={request.user.id}"
        )

        # Executar use case
        from core.application.use_cases.substituir_item import SubstituirItemUseCase
        from core.domain.usuario.entities import Usuario as UsuarioDomain, TipoUsuario

        # Converter usuário Django em entidade de domínio
        usuario_domain = UsuarioDomain(
            numero_login=request.user.numero_login,
            nome=request.user.nome,
            tipo=_converter_tipo_usuario_seguro(request.user.tipo)
        )

        use_case = SubstituirItemUseCase()
        result = use_case.execute(
            item_id=item_id,
            produto_substituto=produto_substituto,
            usuario=usuario_domain
        )

        if not result.success:
            logger.error(
                f"Erro ao substituir item {item_id}: {result.message}"
            )
            return render(
                request,
                'partials/_erro.html',
                {'mensagem': result.message},
                status=400
            )

        logger.info(
            f"Item {item_id} substituído com sucesso por {request.user.nome}"
        )

        # Buscar item atualizado para renderizar
        from core.models import ItemPedido as ItemPedidoModel

        item = ItemPedidoModel.objects.select_related(
            'produto',
            'pedido',
            'separado_por'
        ).get(id=item_id)

        # Fase 35: Broadcast evento WebSocket para atualização em tempo real
        try:
            channel_layer = get_channel_layer()

            # Calcular progresso atualizado (item substituído conta como separado)
            pedido = item.pedido
            pedido.refresh_from_db()
            itens = list(pedido.itens.all())
            itens_separados_count = sum(1 for i in itens if i.separado)
            total_itens_count = len(itens)
            progresso_percentual = int((itens_separados_count / total_itens_count) * 100) if total_itens_count > 0 else 0

            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'item_separado',
                    'pedido_id': pedido.id,
                    'progresso': progresso_percentual,
                    'itens_separados': itens_separados_count,
                    'total_itens': total_itens_count,
                    'item_id': item_id
                }
            )
            logger.info(
                f"Evento WebSocket enviado: item_substituido "
                f"(pedido_id={pedido.id}, item_id={item_id}, progresso={progresso_percentual}%)"
            )
        except Exception as e:
            logger.warning(f"Erro ao enviar evento WebSocket substituir_item: {e}")

        # Renderizar partial atualizado do item
        response = render(
            request,
            'partials/_item_pedido.html',
            {
                'item': item,
                'pedido': item.pedido
            }
        )

        # Fase 37: Adicionar header customizado para indicar mudança de estado (animações)
        # Item substituído deve se comportar como item separado (vai para seção "Itens Separados")
        response['HX-Trigger'] = 'itemSeparado'
        response['X-Item-State-Changed'] = 'separado'

        return response


class FinalizarPedidoView(View):
    """
    View HTMX para finalizar pedido quando progresso = 100% (Fase 25).

    Endpoints:
        GET /pedidos/<pedido_id>/finalizar/ - Retorna modal de confirmação HTML
        POST /pedidos/<pedido_id>/finalizar/ - Processa finalização

    Esta view permite finalizar um pedido quando todos os itens foram separados,
    mudando o status para FINALIZADO e registrando o tempo total.

    Methods:
        get: Retorna modal HTML de confirmação
        post: Finaliza pedido e redireciona para dashboard
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, pedido_id):
        """
        Retorna o modal HTML de confirmação (HTMX).

        Args:
            request: HttpRequest
            pedido_id: ID do pedido a ser finalizado

        Returns:
            HttpResponse: Modal HTML de confirmação
        """
        from core.models import Pedido as PedidoModel
        from django.http import HttpResponse

        try:
            pedido = PedidoModel.objects.select_related('vendedor').prefetch_related(
                'itens'
            ).get(id=pedido_id)
        except PedidoModel.DoesNotExist:
            return HttpResponse("Pedido não encontrado", status=404)

        # Calcular tempo decorrido
        if pedido.data_inicio:
            from django.utils import timezone
            tempo_decorrido = (timezone.now() - pedido.data_inicio).total_seconds() / 60
            tempo_decorrido_minutos = int(tempo_decorrido)
        else:
            tempo_decorrido_minutos = 0

        return render(
            request,
            'partials/_modal_finalizar.html',
            {
                'pedido': pedido,
                'tempo_decorrido_minutos': tempo_decorrido_minutos
            }
        )

    def post(self, request, pedido_id):
        """
        Finaliza o pedido via HTMX.

        Args:
            request: HttpRequest (deve ter HX-Request header)
            pedido_id: ID do pedido a ser finalizado

        Returns:
            HttpResponse: Redirect para dashboard ou erro
        """
        logger.info(
            f"Finalizando pedido: pedido={pedido_id}, usuario={request.user.id}"
        )

        # Executar use case
        from core.application.use_cases.finalizar_pedido import FinalizarPedidoUseCase
        from core.infrastructure.persistence.repositories.pedido_repository import (
            DjangoPedidoRepository
        )

        repository = DjangoPedidoRepository()
        use_case = FinalizarPedidoUseCase(repository)

        result = use_case.execute(
            pedido_id=pedido_id,
            usuario_nome=request.user.nome
        )

        if not result.sucesso:
            logger.error(
                f"Erro ao finalizar pedido {pedido_id}: {result.mensagem}"
            )
            messages.error(request, result.mensagem)

            # Se for HTMX, retornar erro apropriado
            if request.headers.get('HX-Request'):
                return render(
                    request,
                    'partials/_erro.html',
                    {'mensagem': result.mensagem},
                    status=400
                )

            return redirect('detalhe_pedido', pedido_id=pedido_id)

        logger.info(
            f"Pedido {pedido_id} finalizado com sucesso. "
            f"Tempo: {result.tempo_total_minutos:.1f} minutos"
        )

        # Fase 30: Broadcast evento WebSocket para dashboard
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'pedido_finalizado',
                    'pedido_id': pedido_id
                }
            )
            logger.info(f"Evento WebSocket enviado: pedido_finalizado (pedido_id={pedido_id})")
        except Exception as e:
            logger.warning(f"Erro ao enviar evento WebSocket pedido_finalizado: {e}")

        # Mensagem de sucesso
        messages.success(
            request,
            f'Pedido finalizado com sucesso! '
            f'Tempo total: {result.tempo_total_minutos:.1f} minutos'
        )

        # Se for HTMX, usar header para redirect client-side
        if request.headers.get('HX-Request'):
            from django.http import HttpResponse
            response = HttpResponse(status=200)
            response['HX-Redirect'] = reverse('dashboard')
            return response

        # Redirect normal
        return redirect('dashboard')


class ReabrirPedidoView(View):
    """
    View para reabrir pedido finalizado, retornando-o ao status EM_SEPARACAO.

    Permite que pedidos finalizados sejam reabertos para correções.
    Remove da visualização de histórico e retorna ao dashboard ativo.

    Endpoints:
        POST /pedidos/<pedido_id>/reabrir/ - Reabre pedido finalizado
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, pedido_id):
        """
        Reabre pedido finalizado via POST.

        Args:
            request: HttpRequest object
            pedido_id: ID do pedido a ser reaberto

        Returns:
            HttpResponse com redirect para dashboard ou mensagem de erro
        """
        logger.info(f"[ReabrirPedidoView] Iniciando reabertura do pedido {pedido_id}")

        try:
            # Buscar pedido
            pedido = Pedido.objects.get(id=pedido_id)

            # Validar se pedido está finalizado
            if pedido.status != StatusPedidoChoices.FINALIZADO:
                mensagem = f"Pedido #{pedido.numero_orcamento} não está finalizado e não pode ser reaberto."
                logger.warning(f"[ReabrirPedidoView] {mensagem} Status atual: {pedido.status}")
                messages.warning(request, mensagem)
                return redirect('detalhe_pedido', pedido_id=pedido_id)

            # Reabrir pedido usando método do model
            pedido.reabrir()

            logger.info(
                f"[ReabrirPedidoView] Pedido {pedido_id} (#{pedido.numero_orcamento}) "
                f"reaberto com sucesso. Status: {pedido.status}"
            )

            # Broadcast evento WebSocket para dashboard
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'dashboard',
                    {
                        'type': 'pedido_reaberto',
                        'pedido_id': pedido_id
                    }
                )
                logger.info(f"[ReabrirPedidoView] Evento WebSocket enviado: pedido_reaberto (pedido_id={pedido_id})")
            except Exception as e:
                logger.warning(f"[ReabrirPedidoView] Erro ao enviar evento WebSocket pedido_reaberto: {e}")

            # Mensagem de sucesso
            messages.success(
                request,
                f'Pedido #{pedido.numero_orcamento} reaberto com sucesso! '
                f'Agora você pode fazer as correções necessárias.'
            )

            # Redirect para dashboard (pedido agora aparece em "Em Separação")
            return redirect('dashboard')

        except Pedido.DoesNotExist:
            mensagem = f"Pedido {pedido_id} não encontrado."
            logger.error(f"[ReabrirPedidoView] {mensagem}")
            messages.error(request, mensagem)
            return redirect('historico')
        except Exception as e:
            mensagem = f"Erro ao reabrir pedido: {str(e)}"
            logger.error(f"[ReabrirPedidoView] {mensagem}", exc_info=True)
            messages.error(request, mensagem)
            return redirect('detalhe_pedido', pedido_id=pedido_id)


class PainelComprasView(View):
    """
    View do Painel de Compras (Fase 26).

    Exibe todos os itens que foram enviados para compra pelos separadores,
    agrupados por pedido, para visualização pela compradora.

    Methods:
        get: Renderiza o painel com itens agrupados por pedido
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        """
        Renderiza o painel de compras com paginação (Fase 34).

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Página do painel de compras com itens agrupados e paginados
        """
        from core.models import ItemPedido as ItemPedidoModel
        from itertools import groupby
        from operator import attrgetter
        from django.core.paginator import Paginator

        logger.info(
            f"Acessando painel de compras: usuario={request.user.numero_login}"
        )

        # Buscar todos os itens marcados para compra
        itens_em_compra = ItemPedidoModel.objects.filter(
            em_compra=True
        ).select_related(
            'pedido',
            'pedido__vendedor',
            'produto',
            'enviado_para_compra_por'
        ).order_by(
            'pedido__numero_orcamento',
            'id'
        )

        total_itens = itens_em_compra.count()
        logger.info(f"Total de itens em compra: {total_itens}")

        # Fase 34: Adicionar paginação (20 itens por página)
        page_number = request.GET.get('page', 1)
        paginator = Paginator(itens_em_compra, 20)  # 20 itens por página
        page_obj = paginator.get_page(page_number)

        # Agrupar itens da página atual por pedido
        itens_agrupados = []
        for pedido, itens in groupby(page_obj, key=attrgetter('pedido')):
            itens_lista = list(itens)
            itens_agrupados.append((pedido, itens_lista))

        return render(
            request,
            'painel_compras.html',
            {
                'usuario': request.user,
                'itens_compra': itens_agrupados,
                'total_itens': total_itens,
                'page_obj': page_obj,  # Fase 34: Adicionar objeto de paginação
            }
        )


class MarcarPedidoRealizadoView(View):
    """
    View para marcar item como pedido realizado (Fase 27).

    Permite que a compradora marque um item de compra como "pedido realizado",
    atualizando seu status visual e salvando metadados (usuário, timestamp).

    Methods:
        post: Marca item como realizado e retorna badge atualizado (HTMX)
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, item_id):
        """
        Marca item como pedido realizado.

        Args:
            request: HttpRequest (deve conter HX-Request header)
            item_id: ID do ItemPedido a ser marcado

        Returns:
            HttpResponse: Badge atualizado (HTML parcial para HTMX)
                         ou erro 403/404

        Raises:
            403: Se usuário não for COMPRADORA
            404: Se item não existir
        """
        from core.models import ItemPedido as ItemPedidoModel

        # Validar permissão: apenas compradora pode marcar
        if request.user.tipo != 'COMPRADORA':
            logger.warning(
                f"Tentativa de marcar pedido realizado por usuário não autorizado: "
                f"usuario={request.user.numero_login} tipo={request.user.tipo}"
            )
            return HttpResponseForbidden(
                "Apenas a compradora pode marcar itens como pedido realizado."
            )

        # Buscar item
        try:
            item = ItemPedidoModel.objects.select_related(
                'produto', 'pedido'
            ).get(id=item_id)
        except ItemPedidoModel.DoesNotExist:
            logger.error(f"Item não encontrado: item_id={item_id}")
            return HttpResponseNotFound("Item não encontrado.")

        # Marcar como realizado
        item.marcar_realizado(request.user)

        logger.info(
            f"Item marcado como pedido realizado: "
            f"item_id={item.id} produto={item.produto.descricao} "
            f"pedido={item.pedido.numero_orcamento} "
            f"usuario={request.user.numero_login}"
        )

        # Fase 43c: Emitir evento WebSocket para sincronizar badge em tempo real
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'dashboard',
            {
                'type': 'item_pedido_realizado',
                'pedido_id': item.pedido.id,
                'item_id': item.id,
                'pedido_realizado': item.pedido_realizado
            }
        )

        logger.info(
            f"[WebSocket] Evento 'item_pedido_realizado' emitido: "
            f"item_id={item.id} pedido_realizado={item.pedido_realizado}"
        )

        # Renderizar badge atualizado (partial HTML para HTMX)
        return render(
            request,
            'partials/badge_status_compra.html',
            {
                'item': item,
                'pedido_realizado': True
            }
        )


class PedidoCardPartialView(View):
    """
    View para retornar apenas o HTML de um card de pedido (Fase 30).

    Esta view é usada pelo JavaScript WebSocket para adicionar novos cards
    ao dashboard via HTMX quando um pedido é criado em tempo real.

    Methods:
        get: Retorna HTML parcial do card de um pedido específico
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, pedido_id):
        """
        Retorna HTML parcial de um card de pedido.

        Args:
            request: HttpRequest
            pedido_id: ID do pedido a ser renderizado

        Returns:
            HttpResponse: HTML parcial do card (sem layout base)
                         ou erro 404

        Raises:
            404: Se pedido não existir
        """
        from core.models import Pedido as PedidoModel
        from django.utils import timezone
        from django.db.models import Count, Q

        # Buscar pedido
        try:
            pedido = PedidoModel.objects.select_related('vendedor').get(id=pedido_id)
        except PedidoModel.DoesNotExist:
            logger.error(f"Pedido não encontrado para card partial: pedido_id={pedido_id}")
            return HttpResponseNotFound("Pedido não encontrado.")

        # Calcular dados do card (mesmo formato usado no dashboard)
        tempo_decorrido = timezone.now() - pedido.data_inicio
        tempo_decorrido_minutos = int(tempo_decorrido.total_seconds() / 60)

        # Contar itens separados ou substituídos
        itens = pedido.itens.all()
        total_itens = itens.count()
        # Contar separados OU substituídos (Q object para OR lógico)
        from django.db.models import Q
        itens_concluidos = itens.filter(Q(separado=True) | Q(substituido=True)).count()
        progresso_percentual = int((itens_concluidos / total_itens * 100)) if total_itens > 0 else 0

        # Buscar separadores ativos (usuários do tipo SEPARADOR que têm sessões ativas)
        # Por simplicidade, retornar lista vazia (feature futura)
        separadores = []

        # Preparar contexto
        pedido_data = {
            'pedido': pedido,
            'tempo_decorrido_minutos': tempo_decorrido_minutos,
            'progresso_percentual': progresso_percentual,
            'itens_separados': itens_concluidos,  # Itens separados + substituídos
            'total_itens': total_itens,
            'separadores': separadores
        }

        logger.info(
            f"Card partial renderizado: pedido_id={pedido_id} "
            f"progresso={progresso_percentual}%"
        )

        # Renderizar apenas o partial (sem base.html)
        return render(
            request,
            'partials/_card_pedido.html',
            {'pedido_data': pedido_data}
        )


class HistoricoView(View):
    """
    View do histórico de pedidos finalizados - Fase 31.

    Exibe lista de pedidos finalizados com:
    - Data e hora de finalização
    - Tempo total de separação
    - Vendedor, cliente, número do pedido
    - Quem finalizou o pedido

    Funcionalidades:
    - Paginação (20 pedidos por página)
    - Busca por número de orçamento ou nome de cliente
    - Filtro por vendedor
    - Filtro por data de finalização
    - Suporte a requisições HTMX (retorna partial HTML)
    """

    template_name = 'historico.html'
    partial_template_name = 'partials/_historico_grid.html'
    items_per_page = 20

    @method_decorator(login_required)
    def get(self, request):
        """
        Renderiza o histórico com pedidos finalizados.

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Histórico com lista de pedidos finalizados
        """
        from django.core.paginator import Paginator
        from django.db.models import Q
        from core.domain.pedido.value_objects import StatusPedido

        # Obter query params
        search_query = request.GET.get('busca', '').strip()
        vendedor_id = request.GET.get('vendedor', '').strip()
        data_filter = request.GET.get('data', '').strip()
        page_number = request.GET.get('page', 1)

        # Buscar pedidos finalizados
        pedidos_queryset = self._get_pedidos_finalizados()

        # Aplicar filtros
        pedidos_queryset = self._apply_filters(
            pedidos_queryset,
            search_query,
            vendedor_id,
            data_filter
        )

        # Paginar
        paginator = Paginator(pedidos_queryset, self.items_per_page)
        page_obj = paginator.get_page(page_number)

        # Processar pedidos da página atual
        pedidos_processados = []
        for pedido in page_obj:
            pedido_data = self._build_pedido_data(pedido)
            pedidos_processados.append(pedido_data)

        # Obter lista de vendedores para o dropdown
        vendedores = self._get_vendedores()

        context = {
            'pedidos': page_obj,
            'pedidos_processados': pedidos_processados,
            'page_obj': page_obj,
            'vendedores': vendedores,
            'search_query': search_query,
            'vendedor_id': vendedor_id,
            'data_filter': data_filter,
            'usuario': request.user,
        }

        # Se for requisição HTMX, retornar apenas o grid
        if request.headers.get('HX-Request'):
            return render(request, self.partial_template_name, context)

        return render(request, self.template_name, context)

    def _get_pedidos_finalizados(self):
        """
        Busca todos os pedidos finalizados.

        Returns:
            QuerySet: Pedidos finalizados ordenados por data de finalização DESC
        """
        from core.models import Pedido
        from core.domain.pedido.value_objects import StatusPedido

        return (
            Pedido.objects
            .filter(status=StatusPedido.FINALIZADO.value)
            .select_related('vendedor')
            .prefetch_related('itens')
            .order_by('-data_finalizacao')
        )

    def _apply_filters(self, queryset, search_query, vendedor_id, data_filter):
        """
        Aplica filtros de busca, vendedor e data ao queryset.

        Args:
            queryset: QuerySet de pedidos
            search_query: Termo de busca (número ou cliente)
            vendedor_id: ID do vendedor para filtrar
            data_filter: Data para filtrar (YYYY-MM-DD)

        Returns:
            QuerySet: Pedidos filtrados
        """
        from django.db.models import Q

        # Filtro de busca (número ou cliente)
        if search_query:
            queryset = queryset.filter(
                Q(numero_orcamento__icontains=search_query) |
                Q(nome_cliente__icontains=search_query)
            )

        # Filtro de vendedor
        if vendedor_id:
            queryset = queryset.filter(vendedor_id=vendedor_id)

        # Filtro de data
        if data_filter:
            try:
                from datetime import datetime
                from django.utils import timezone
                # Parse YYYY-MM-DD
                data_obj = datetime.strptime(data_filter, '%Y-%m-%d').date()
                # Filtrar pedidos finalizados nessa data
                queryset = queryset.filter(
                    data_finalizacao__date=data_obj
                )
            except ValueError:
                logger.warning(f"Data inválida no filtro: {data_filter}")

        return queryset

    def _build_pedido_data(self, pedido):
        """
        Constrói dict com dados processados do pedido.

        Args:
            pedido: Instância de Pedido

        Returns:
            dict: Dados do pedido formatados
        """
        # Calcular tempo total de separação
        tempo_total_minutos = self._calcular_tempo_total(pedido)

        # Contar itens
        total_itens = pedido.itens.count()
        itens_separados = pedido.itens.filter(separado=True).count()

        # Pegar apenas primeiro nome do vendedor
        vendedor_nome = 'N/A'
        if pedido.vendedor:
            vendedor_nome = pedido.vendedor.nome.split()[0]

        return {
            'id': pedido.id,
            'numero_orcamento': pedido.numero_orcamento,
            'nome_cliente': pedido.nome_cliente,
            'vendedor': vendedor_nome,
            'data_finalizacao': pedido.data_finalizacao,
            'tempo_total_minutos': tempo_total_minutos,
            'tempo_total_formatado': self._formatar_tempo(tempo_total_minutos),
            'total_itens': total_itens,
            'itens_separados': itens_separados,
            'observacoes': pedido.observacoes or '',
        }

    def _calcular_tempo_total(self, pedido):
        """
        Calcula tempo total de separação em minutos.

        Args:
            pedido: Instância de Pedido

        Returns:
            int: Tempo total em minutos
        """
        if not pedido.data_finalizacao or not pedido.data_inicio:
            return 0

        delta = pedido.data_finalizacao - pedido.data_inicio
        return int(delta.total_seconds() / 60)

    def _formatar_tempo(self, minutos):
        """
        Formata tempo em string legível (ex: "1h 30min").

        Args:
            minutos: Tempo em minutos

        Returns:
            str: Tempo formatado
        """
        if minutos < 60:
            return f"{minutos} min"

        horas = minutos // 60
        mins = minutos % 60

        if mins == 0:
            return f"{horas}h"

        return f"{horas}h {mins}min"

    def _get_vendedores(self):
        """
        Busca lista de vendedores para o filtro com cache (Fase 34).

        Returns:
            list: Vendedores que têm pedidos finalizados (cacheado por 5 minutos)
        """
        from core.models import Usuario, Pedido
        from core.domain.pedido.value_objects import StatusPedido

        # Fase 34: Cache de 5 minutos
        vendedores_cache = cache.get('historico_vendedores')
        if vendedores_cache is not None:
            logger.debug("Vendedores do histórico carregados do cache")
            return vendedores_cache

        # Buscar vendedores que têm pedidos finalizados
        vendedor_ids = (
            Pedido.objects
            .filter(status=StatusPedido.FINALIZADO.value)
            .values_list('vendedor_id', flat=True)
            .distinct()
        )

        vendedores = list(Usuario.objects.filter(
            id__in=vendedor_ids
        ).order_by('nome').values('id', 'nome', 'numero_login'))

        # Cachear por 5 minutos
        cache.set('historico_vendedores', vendedores, 300)
        logger.debug(f"Vendedores do histórico cacheados: {len(vendedores)} vendedores")

        return vendedores


# ==================== FASE 33: MÉTRICAS AVANÇADAS ====================

@method_decorator(login_required, name='dispatch')
class MetricasView(View):
    """
    View para exibir métricas avançadas de performance (Fase 33).

    URL: /metricas/

    Responsabilidades:
    - Calcular tempo médio por separador
    - Gerar ranking de separadores (mais rápido → mais lento)
    - Listar top 10 produtos mais separados
    - Listar top 10 produtos mais enviados para compra
    - Gerar dados para gráfico de pedidos por dia (últimos 30 dias)

    Methods:
        get: Renderiza página de métricas com todos os dados
    """

    template_name = 'metricas.html'

    def get(self, request):
        """
        Renderiza página de métricas.

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Página de métricas com dados calculados
        """
        logger.info(f"Usuário {request.user.nome} acessou métricas")

        metricas = {
            'tempo_medio_separadores': self._calcular_tempo_medio_por_separador(),
            'ranking_separadores': self._obter_ranking_separadores(),
            'produtos_mais_separados': self._obter_produtos_mais_separados(),
            'produtos_mais_enviados_compra': self._obter_produtos_mais_enviados_compra(),
            'grafico_pedidos_30_dias': self._obter_pedidos_ultimos_30_dias()
        }

        context = {
            'metricas': metricas,
            'usuario': request.user
        }

        return render(request, self.template_name, context)

    def _calcular_tempo_medio_por_separador(self):
        """
        Calcula tempo médio de separação por separador usando agregações Django.

        Fase 34: Otimizado com agregações para evitar loops e queries N+1.

        Returns:
            list: Lista de dicts com {separador, tempo_medio_minutos, total_pedidos}
        """
        from core.models import Pedido, ItemPedido
        from core.domain.pedido.value_objects import StatusPedido
        from django.db.models import Avg, Count, F, ExpressionWrapper, DurationField, FloatField, Q
        from django.db.models.functions import Extract

        # Usar agregação Django para calcular tempo médio por separador
        # Estratégia: Agrupar por separador e calcular média de tempo dos pedidos
        resultado_query = (
            ItemPedido.objects
            .filter(
                separado=True,
                separado_por__isnull=False,
                pedido__status=StatusPedido.FINALIZADO.value,
                pedido__data_inicio__isnull=False,
                pedido__data_finalizacao__isnull=False
            )
            .values('separado_por__nome')  # Agrupar por separador
            .annotate(
                # Contar pedidos distintos (cada separador pode ter separado vários pedidos)
                total_pedidos=Count('pedido', distinct=True),
                # Calcular tempo médio usando ExpressionWrapper
                # Nota: Usamos subquery para pegar tempo do pedido
            )
        )

        # Processar resultado e calcular tempo médio manualmente
        # (devido à limitação de calcular diferença de timestamps em agregações)
        separadores_pedidos = {}

        itens = ItemPedido.objects.filter(
            separado=True,
            separado_por__isnull=False,
            pedido__status=StatusPedido.FINALIZADO.value,
            pedido__data_inicio__isnull=False,
            pedido__data_finalizacao__isnull=False
        ).select_related('separado_por', 'pedido').values(
            'separado_por__nome',
            'pedido__id',
            'pedido__data_inicio',
            'pedido__data_finalizacao'
        ).distinct()

        # Agrupar por separador
        for item in itens:
            separador = item['separado_por__nome']
            pedido_id = item['pedido__id']

            if separador not in separadores_pedidos:
                separadores_pedidos[separador] = {}

            # Evitar contar o mesmo pedido duas vezes
            if pedido_id not in separadores_pedidos[separador]:
                tempo_minutos = (
                    item['pedido__data_finalizacao'] - item['pedido__data_inicio']
                ).total_seconds() / 60
                separadores_pedidos[separador][pedido_id] = tempo_minutos

        # Calcular médias
        resultado = []
        for separador, pedidos_dict in separadores_pedidos.items():
            total_pedidos = len(pedidos_dict)
            if total_pedidos > 0:
                tempo_total = sum(pedidos_dict.values())
                tempo_medio = tempo_total / total_pedidos
                resultado.append({
                    'separador': separador,
                    'tempo_medio_minutos': round(tempo_medio, 1),
                    'total_pedidos': total_pedidos
                })

        logger.debug(f"Tempo médio calculado para {len(resultado)} separadores")
        return resultado

    def _obter_ranking_separadores(self):
        """
        Obtém ranking de separadores ordenado por velocidade (mais rápido primeiro).

        Returns:
            list: Lista ordenada por tempo_medio_minutos (crescente)
        """
        tempo_medio = self._calcular_tempo_medio_por_separador()

        # Ordenar por tempo médio (crescente = mais rápido primeiro)
        ranking = sorted(tempo_medio, key=lambda x: x['tempo_medio_minutos'])

        logger.debug(f"Ranking gerado com {len(ranking)} separadores")
        return ranking

    def _obter_produtos_mais_separados(self):
        """
        Obtém top 10 produtos mais separados.

        Returns:
            list: Lista de dicts com {produto, total_separado}
        """
        from core.models import ItemPedido
        from django.db.models import Sum

        produtos = (
            ItemPedido.objects
            .filter(separado=True)
            .values('produto__descricao')
            .annotate(total_separado=Sum('quantidade_separada'))
            .order_by('-total_separado')[:10]
        )

        resultado = [
            {
                'produto': p['produto__descricao'],
                'total_separado': p['total_separado']
            }
            for p in produtos
        ]

        logger.debug(f"Top {len(resultado)} produtos mais separados")
        return resultado

    def _obter_produtos_mais_enviados_compra(self):
        """
        Obtém top 10 produtos mais enviados para compra.

        Returns:
            list: Lista de dicts com {produto, total_enviado}
        """
        from core.models import ItemPedido
        from django.db.models import Sum

        produtos = (
            ItemPedido.objects
            .filter(em_compra=True)
            .values('produto__descricao')
            .annotate(total_enviado=Sum('quantidade_solicitada'))
            .order_by('-total_enviado')[:10]
        )

        resultado = [
            {
                'produto': p['produto__descricao'],
                'total_enviado': p['total_enviado']
            }
            for p in produtos
        ]

        logger.debug(f"Top {len(resultado)} produtos mais enviados para compra")
        return resultado

    def _obter_pedidos_ultimos_30_dias(self):
        """
        Obtém dados para gráfico de pedidos por dia (últimos 30 dias).

        Returns:
            dict: {labels: [datas], data: [quantidades]}
        """
        from core.models import Pedido
        from core.domain.pedido.value_objects import StatusPedido
        from datetime import timedelta
        from collections import defaultdict
        from django.db.models import Count

        hoje = timezone.now().date()
        inicio = hoje - timedelta(days=29)  # 30 dias incluindo hoje

        # Buscar pedidos finalizados nos últimos 30 dias
        pedidos = (
            Pedido.objects
            .filter(
                status=StatusPedido.FINALIZADO.value,
                data_finalizacao__date__gte=inicio,
                data_finalizacao__date__lte=hoje
            )
            .values('data_finalizacao__date')
            .annotate(total=Count('id'))
        )

        # Criar dict com contagens por dia
        pedidos_por_dia = defaultdict(int)
        for p in pedidos:
            data = p['data_finalizacao__date']
            pedidos_por_dia[data] = p['total']

        # Gerar arrays para os últimos 30 dias (garantir todos os dias mesmo sem pedidos)
        labels = []
        data = []

        for i in range(30):
            data_atual = inicio + timedelta(days=i)
            labels.append(data_atual.strftime('%d/%m'))
            data.append(pedidos_por_dia[data_atual])

        total_pedidos = sum(data)
        logger.debug(f"Gráfico gerado: {total_pedidos} pedidos nos últimos 30 dias")

        return {
            'labels': labels,
            'data': data,
            'total_pedidos': total_pedidos
        }


# ==========================================================
# PAINEL DE ADMINISTRAÇÃO DE USUÁRIOS
# ==========================================================

@method_decorator(login_required, name='dispatch')
class AdminPanelView(View):
    """
    View para listar todos os usuários do sistema.

    Apenas administradores podem acessar.
    """

    template_name = 'admin_panel.html'

    def dispatch(self, request, *args, **kwargs):
        """Verificar se o usuário é administrador."""
        usuario = Usuario.objects.get(id=request.session.get('usuario_id'))

        if not usuario.is_admin:
            messages.error(request, 'Acesso negado. Apenas administradores podem acessar esta página.')
            return redirect('dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Renderiza a lista de usuários."""
        # Buscar usuários ativos e inativos separadamente
        usuarios_ativos = Usuario.objects.filter(ativo=True).order_by('numero_login')
        usuarios_inativos = Usuario.objects.filter(ativo=False).order_by('numero_login')

        # Estatísticas (todos os usuários)
        total_usuarios = Usuario.objects.count()
        total_ativos = usuarios_ativos.count()
        total_inativos = usuarios_inativos.count()

        por_tipo = {
            'VENDEDOR': Usuario.objects.filter(tipo='VENDEDOR').count(),
            'SEPARADOR': Usuario.objects.filter(tipo='SEPARADOR').count(),
            'COMPRADORA': Usuario.objects.filter(tipo='COMPRADORA').count(),
            'ADMINISTRADOR': Usuario.objects.filter(tipo='ADMINISTRADOR').count(),
        }

        context = {
            'usuarios_ativos': usuarios_ativos,
            'usuarios_inativos': usuarios_inativos,
            'total_usuarios': total_usuarios,
            'total_ativos': total_ativos,
            'total_inativos': total_inativos,
            'estatisticas': por_tipo,
        }

        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class CriarUsuarioView(View):
    """
    View para criar novo usuário.

    Apenas administradores podem acessar.
    """

    template_name = 'criar_usuario.html'
    form_class = None  # Será importado dinamicamente

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.presentation.web.forms import CriarUsuarioForm
        self.form_class = CriarUsuarioForm

    def dispatch(self, request, *args, **kwargs):
        """Verificar se o usuário é administrador."""
        usuario = Usuario.objects.get(id=request.session.get('usuario_id'))

        if not usuario.is_admin:
            messages.error(request, 'Acesso negado. Apenas administradores podem acessar esta página.')
            return redirect('dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Renderiza o formulário de criação."""
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Processa a criação do usuário."""
        form = self.form_class(request.POST)

        if form.is_valid():
            try:
                # Extrair dados
                numero_login = form.cleaned_data['numero_login']
                nome = form.cleaned_data['nome']
                tipo = form.cleaned_data['tipo']
                pin = form.cleaned_data['pin']

                # Criar usuário
                if tipo == 'ADMINISTRADOR':
                    usuario = Usuario.objects.create_superuser(
                        numero_login=numero_login,
                        nome=nome,
                        pin=pin
                    )
                else:
                    usuario = Usuario.objects.create_user(
                        numero_login=numero_login,
                        nome=nome,
                        tipo=tipo,
                        pin=pin
                    )

                logger.info(f"Usuário criado: {usuario.numero_login} - {usuario.nome} ({usuario.tipo})")
                messages.success(request, f'Usuário {usuario.nome} criado com sucesso!')

                return redirect('admin_panel')

            except Exception as e:
                logger.error(f"Erro ao criar usuário: {str(e)}")
                messages.error(request, f'Erro ao criar usuário: {str(e)}')

        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class EditarUsuarioView(View):
    """
    View para editar usuário existente.

    Apenas administradores podem acessar.
    """

    template_name = 'editar_usuario.html'
    form_class = None  # Será importado dinamicamente

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.presentation.web.forms import EditarUsuarioForm
        self.form_class = EditarUsuarioForm

    def dispatch(self, request, *args, **kwargs):
        """Verificar se o usuário é administrador."""
        usuario = Usuario.objects.get(id=request.session.get('usuario_id'))

        if not usuario.is_admin:
            messages.error(request, 'Acesso negado. Apenas administradores podem acessar esta página.')
            return redirect('dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, user_id):
        """Renderiza o formulário de edição preenchido."""
        from django.shortcuts import get_object_or_404

        # Buscar usuário a ser editado
        usuario_editado = get_object_or_404(Usuario, id=user_id)

        # Preencher formulário com dados atuais
        form = self.form_class(
            usuario_id=user_id,
            initial={
                'nome': usuario_editado.nome,
                'tipo': usuario_editado.tipo,
                'ativo': usuario_editado.ativo,
            }
        )

        context = {
            'form': form,
            'usuario_editado': usuario_editado,
        }

        return render(request, self.template_name, context)

    def post(self, request, user_id):
        """Processa a edição do usuário."""
        from django.shortcuts import get_object_or_404

        # Buscar usuário a ser editado
        usuario_editado = get_object_or_404(Usuario, id=user_id)

        # Não permitir editar a si mesmo (evitar lock-out acidental)
        usuario_logado = Usuario.objects.get(id=request.session.get('usuario_id'))
        if usuario_editado.id == usuario_logado.id:
            messages.warning(request, 'Você não pode editar seu próprio usuário através desta tela.')
            return redirect('admin_panel')

        form = self.form_class(request.POST, usuario_id=user_id)

        if form.is_valid():
            try:
                # Extrair dados
                nome = form.cleaned_data['nome']
                tipo = form.cleaned_data['tipo']
                ativo = form.cleaned_data.get('ativo', False)
                pin = form.cleaned_data.get('pin')

                # Atualizar usuário
                usuario_editado.nome = nome
                usuario_editado.tipo = tipo
                usuario_editado.ativo = ativo

                # Atualizar PIN se fornecido
                if pin:
                    usuario_editado.set_password(pin)

                usuario_editado.save()

                logger.info(f"Usuário editado: {usuario_editado.numero_login} - {usuario_editado.nome} ({usuario_editado.tipo})")
                messages.success(request, f'Usuário {usuario_editado.nome} atualizado com sucesso!')

                return redirect('admin_panel')

            except Exception as e:
                logger.error(f"Erro ao editar usuário: {str(e)}")
                messages.error(request, f'Erro ao editar usuário: {str(e)}')

        context = {
            'form': form,
            'usuario_editado': usuario_editado,
        }

        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class DeletarUsuarioView(View):
    """
    View para deletar usuário (soft delete - marca como inativo).

    Apenas administradores podem acessar.
    POST only - requer confirmação.
    """

    def dispatch(self, request, *args, **kwargs):
        """Verificar se o usuário é administrador."""
        usuario = Usuario.objects.get(id=request.session.get('usuario_id'))

        if not usuario.is_admin:
            messages.error(request, 'Acesso negado. Apenas administradores podem acessar esta página.')
            return redirect('dashboard')

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, user_id):
        """Marca o usuário como inativo (soft delete)."""
        from django.shortcuts import get_object_or_404

        # Buscar usuário a ser deletado
        usuario_deletado = get_object_or_404(Usuario, id=user_id)

        # Não permitir deletar a si mesmo
        usuario_logado = Usuario.objects.get(id=request.session.get('usuario_id'))
        if usuario_deletado.id == usuario_logado.id:
            messages.error(request, 'Você não pode deletar seu próprio usuário!')
            return redirect('admin_panel')

        try:
            # Soft delete - marcar como inativo
            nome_usuario = usuario_deletado.nome
            usuario_deletado.ativo = False
            usuario_deletado.save()

            logger.info(f"Usuário deletado (soft delete): {usuario_deletado.numero_login} - {nome_usuario}")
            messages.success(request, f'Usuário {nome_usuario} foi desativado com sucesso!')

        except Exception as e:
            logger.error(f"Erro ao deletar usuário: {str(e)}")
            messages.error(request, f'Erro ao deletar usuário: {str(e)}')

        return redirect('admin_panel')


@method_decorator(login_required, name='dispatch')
class ReativarUsuarioView(View):
    """
    View para reativar usuário (ativo=True).

    Apenas administradores podem acessar.
    POST only - ação direta.
    """

    def dispatch(self, request, *args, **kwargs):
        """Verificar se o usuário é administrador."""
        usuario = Usuario.objects.get(id=request.session.get('usuario_id'))

        if not usuario.is_admin:
            messages.error(request, 'Acesso negado. Apenas administradores podem acessar esta página.')
            return redirect('dashboard')

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, user_id):
        """Reativa o usuário (marca como ativo=True)."""
        from django.shortcuts import get_object_or_404

        # Buscar usuário a ser reativado
        usuario_reativado = get_object_or_404(Usuario, id=user_id)

        try:
            # Reativar - marcar como ativo
            nome_usuario = usuario_reativado.nome
            usuario_reativado.ativo = True
            usuario_reativado.save()

            logger.info(f"Usuário reativado: {usuario_reativado.numero_login} - {nome_usuario}")
            messages.success(request, f'Usuário {nome_usuario} foi reativado com sucesso!')

        except Exception as e:
            logger.error(f"Erro ao reativar usuário: {str(e)}")
            messages.error(request, f'Erro ao reativar usuário: {str(e)}')

        return redirect('admin_panel')


# ==========================================================
# FASE 35: ATUALIZAÇÃO EM TEMPO REAL DO ESTADO DE ITENS
# ==========================================================

@method_decorator(login_required, name='dispatch')
class ItemPedidoPartialView(View):
    """
    View para retornar HTML parcial de um item específico (Fase 35).

    Esta view é usada pelo WebSocket para atualizar o estado visual
    dos itens em tempo real para múltiplos usuários simultâneos.

    Endpoint: GET /pedidos/<pedido_id>/itens/<item_id>/html/

    Funcionalidades:
    - Retorna apenas o partial _item_pedido.html (sem layout base)
    - Reflete estado atual do item (separado/não separado/em compra)
    - Permite sincronização visual entre múltiplos usuários

    Methods:
        get: Retorna HTML parcial do item atualizado
    """

    def get(self, request, pedido_id, item_id):
        """
        Retorna HTML parcial de um item específico.

        Args:
            request: HttpRequest
            pedido_id: ID do pedido
            item_id: ID do item

        Returns:
            HttpResponse: HTML parcial do item (sem layout base)
            404: Se pedido ou item não existirem, ou se item não pertencer ao pedido

        Uso típico (via WebSocket):
        1. Usuário A marca item como separado
        2. Backend envia evento WebSocket com item_id
        3. Usuário B recebe evento e busca HTML atualizado via esta view
        4. Usuário B vê o item atualizado em tempo real
        """
        from django.shortcuts import get_object_or_404
        from core.models import ItemPedido as ItemPedidoModel, Pedido as PedidoModel

        # Buscar pedido e validar existência
        pedido = get_object_or_404(PedidoModel, id=pedido_id)

        # Buscar item e validar que pertence ao pedido
        item = get_object_or_404(
            ItemPedidoModel.objects.select_related('produto', 'separado_por'),
            id=item_id,
            pedido=pedido
        )

        logger.debug(
            f"HTML parcial solicitado: pedido_id={pedido_id}, item_id={item_id}, "
            f"separado={item.separado}, usuario={request.user.nome}"
        )

        # Renderizar apenas o partial (sem base.html)
        return render(
            request,
            'partials/_item_pedido.html',
            {
                'item': item,
                'pedido': pedido
            }
        )


# ==================== VIEWS DE TEMA / PERSONALIZAÇÃO ====================

def dynamic_theme_css(request):
    """
    View que serve o CSS dinâmico com as cores do tema ativo.

    Esta view renderiza o template theme.css com as variáveis CSS
    baseadas no tema configurado no banco de dados. O resultado
    é cacheável e tem content-type text/css.

    Returns:
        HttpResponse com content-type text/css
    """
    from django.http import HttpResponse
    from django.template import loader
    from core.models import ThemeConfiguration

    # Obter tema ativo
    theme = ThemeConfiguration.get_active_theme()

    # Renderizar template CSS com contexto do tema
    template = loader.get_template('theme.css')
    context = {
        'theme': {
            'primary_color': theme.primary_color,
            'primary_hover': theme.primary_hover,
            'vendedor_color': theme.vendedor_color,
            'separador_color': theme.separador_color,
            'compradora_color': theme.compradora_color,
            'admin_color': theme.admin_color,
            'success_color': theme.success_color,
            'warning_color': theme.warning_color,
            'info_color': theme.info_color,
        }
    }

    css_content = template.render(context)

    # Retornar como CSS com cache headers
    response = HttpResponse(css_content, content_type='text/css')
    response['Cache-Control'] = 'public, max-age=3600'  # Cache por 1 hora
    return response


@method_decorator(login_required, name='dispatch')
class ConfigurarCoresView(View):
    """
    View para configurar cores do tema.

    Permite que administradores personalizem as cores do sistema.
    Inclui funcionalidade de salvar e resetar para cores padrão.
    """

    def get(self, request):
        """Exibe o formulário de configuração de cores."""
        # Apenas administradores podem acessar
        if not request.user.is_admin:
            return HttpResponseForbidden("Apenas administradores podem acessar esta página.")

        # Obter tema ativo
        from core.models import ThemeConfiguration
        theme = ThemeConfiguration.get_active_theme()

        # Preencher form com cores atuais
        from core.presentation.web.forms import ThemeConfigurationForm
        form = ThemeConfigurationForm(initial={
            'primary_color': theme.primary_color,
            'primary_hover': theme.primary_hover,
            'vendedor_color': theme.vendedor_color,
            'separador_color': theme.separador_color,
            'compradora_color': theme.compradora_color,
            'admin_color': theme.admin_color,
            'success_color': theme.success_color,
            'warning_color': theme.warning_color,
            'info_color': theme.info_color,
        })

        return render(request, 'configurar_cores.html', {
            'form': form,
            'theme': theme
        })

    def post(self, request):
        """Salva as cores configuradas ou reseta para padrão."""
        # Apenas administradores podem modificar
        if not request.user.is_admin:
            return HttpResponseForbidden("Apenas administradores podem modificar as cores.")

        from core.models import ThemeConfiguration
        from core.presentation.web.forms import ThemeConfigurationForm

        # Verificar se é um reset
        if 'reset' in request.POST:
            theme = ThemeConfiguration.get_active_theme()
            theme.reset_to_default()

            # Invalidar cache
            cache.delete('theme_colors')

            messages.success(request, 'Cores resetadas para o padrão com sucesso!')
            return redirect('configurar_cores')

        # Processar formulário normal
        form = ThemeConfigurationForm(request.POST)

        if form.is_valid():
            theme = ThemeConfiguration.get_active_theme()

            # Atualizar cores
            theme.primary_color = form.cleaned_data['primary_color']
            theme.primary_hover = form.cleaned_data['primary_hover']
            theme.vendedor_color = form.cleaned_data['vendedor_color']
            theme.separador_color = form.cleaned_data['separador_color']
            theme.compradora_color = form.cleaned_data['compradora_color']
            theme.admin_color = form.cleaned_data['admin_color']
            theme.success_color = form.cleaned_data['success_color']
            theme.warning_color = form.cleaned_data['warning_color']
            theme.info_color = form.cleaned_data['info_color']

            theme.save()

            # Invalidar cache para forçar reload das cores
            cache.delete('theme_colors')

            messages.success(request, 'Cores atualizadas com sucesso!')

            # Broadcast via WebSocket para atualizar todas as páginas abertas
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'pedidos',
                {
                    'type': 'theme_updated',
                    'message': 'reload_css'
                }
            )

            return redirect('configurar_cores')

        # Se form inválido, renderizar com erros
        theme = ThemeConfiguration.get_active_theme()
        return render(request, 'configurar_cores.html', {
            'form': form,
            'theme': theme
        })
