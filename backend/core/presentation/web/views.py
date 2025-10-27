# -*- coding: utf-8 -*-
"""
Views web para o sistema de separação.
Fase 7: LoginView e Dashboard Placeholder
Fase 8: LogoutView
Fase 15: UploadOrcamentoView
Fase 30: WebSocket Broadcast
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
from core.models import Usuario
from core.application.use_cases.criar_pedido import CriarPedidoUseCase
from core.application.use_cases.obter_metricas_tempo import ObterMetricasTempoUseCase
from core.application.dtos.pedido_dtos import CriarPedidoRequestDTO
from core.infrastructure.pdf.parser import PDFParser, PDFHeaderExtractor, PDFProductExtractor
from core.infrastructure.persistence.repositories.pedido_repository import DjangoPedidoRepository
from core.domain.pedido.value_objects import Logistica, Embalagem

logger = logging.getLogger(__name__)


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
                messages.success(request, f'Bem-vindo, {usuario.nome}!')
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

        # Preparar contexto
        context = {
            'usuario': {
                'nome': request.session.get('nome'),
                'numero_login': request.session.get('numero_login'),
                'tipo': request.session.get('tipo'),
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
            'metricas_tempo': metricas_tempo
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

        return {
            'pedido': pedido,
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
        Conta quantos itens foram separados.

        Args:
            itens: QuerySet de ItemPedido

        Returns:
            int: Número de itens separados
        """
        return sum(1 for item in itens if item.separado)

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
    """

    def post(self, request):
        """
        Realiza logout do usuário.

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
        messages.success(request, 'Logout realizado com sucesso!')
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
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """
        Processa upload de PDF e cria pedido.

        Args:
            request: HttpRequest

        Returns:
            HttpResponse: Redirect para dashboard ou formulário com erros
        """
        form = self.form_class(request.POST, request.FILES)

        if not form.is_valid():
            logger.warning(f"Formulário de upload inválido: {form.errors}")
            return render(request, self.template_name, {'form': form})

        # Extrair dados do formulário
        pdf_file = form.cleaned_data['pdf_file']
        logistica = Logistica(form.cleaned_data['logistica'])
        embalagem = Embalagem(form.cleaned_data['embalagem'])
        observacoes = form.cleaned_data.get('observacoes', '')

        # Salvar arquivo temporariamente
        temp_file = None
        try:
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                for chunk in pdf_file.chunks():
                    tmp.write(chunk)
                temp_file = tmp.name

            logger.info(f"Arquivo PDF salvo temporariamente: {temp_file}")

            # Criar DTO de request
            request_dto = CriarPedidoRequestDTO(
                pdf_path=temp_file,
                logistica=logistica,
                embalagem=embalagem,
                usuario_criador_id=request.user.id,
                observacoes=observacoes
            )

            # Executar use case
            pdf_parser = PDFParser()
            header_extractor = PDFHeaderExtractor()
            product_extractor = PDFProductExtractor()
            pedido_repository = DjangoPedidoRepository()

            use_case = CriarPedidoUseCase(
                pdf_parser=pdf_parser,
                header_extractor=header_extractor,
                product_extractor=product_extractor,
                pedido_repository=pedido_repository
            )

            response_dto = use_case.execute(request_dto)

            if response_dto.success:
                logger.info(
                    f"Pedido criado com sucesso: {response_dto.pedido.numero_orcamento} "
                    f"(ID: {response_dto.pedido.id})"
                )

                # Fase 30: Broadcast evento WebSocket para dashboard
                try:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'dashboard',
                        {
                            'type': 'pedido_criado',
                            'pedido_id': response_dto.pedido.id
                        }
                    )
                    logger.info(f"Evento WebSocket enviado: pedido_criado (ID: {response_dto.pedido.id})")
                except Exception as e:
                    logger.warning(f"Erro ao enviar evento WebSocket pedido_criado: {e}")

                messages.success(
                    request,
                    f'Pedido #{response_dto.pedido.numero_orcamento} criado com sucesso!'
                )
                return redirect('dashboard')
            else:
                logger.error(
                    f"Erro ao criar pedido: {response_dto.error_message}. "
                    f"Validações: {response_dto.validation_errors}"
                )
                messages.error(
                    request,
                    f'Erro ao criar pedido: {response_dto.error_message}'
                )

                # Adicionar erros de validação ao contexto
                context = {
                    'form': form,
                    'validation_errors': response_dto.validation_errors
                }
                return render(request, self.template_name, context)

        except Exception as e:
            logger.exception(f"Erro inesperado ao processar upload: {e}")
            messages.error(
                request,
                f'Erro ao processar PDF: {str(e)}'
            )
            return render(request, self.template_name, {'form': form})

        finally:
            # Limpar arquivo temporário
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    logger.debug(f"Arquivo temporário removido: {temp_file}")
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo temporário {temp_file}: {e}")


@method_decorator(login_required, name='dispatch')
class DetalhePedidoView(View):
    """
    View para exibir detalhes de um pedido específico.

    Fase 21: Visualização detalhada com itens separados e não separados.

    Methods:
        get: Renderiza template com detalhes do pedido
    """

    template_name = 'detalhe_pedido.html'

    def get(self, request, pedido_id):
        """
        Renderiza detalhes de um pedido.

        Args:
            request: HttpRequest
            pedido_id: ID do pedido

        Returns:
            HttpResponse: Template renderizado ou 404
        """
        from django.shortcuts import get_object_or_404
        from core.models import Pedido
        from django.utils import timezone

        logger.info(f"Usuário {request.user.nome} acessou detalhes do pedido #{pedido_id}")

        # Buscar pedido com otimizações de query
        pedido = get_object_or_404(
            Pedido.objects.select_related('vendedor').prefetch_related('itens__produto'),
            id=pedido_id
        )

        # Separar itens em duas listas
        itens = list(pedido.itens.all())
        itens_nao_separados = [item for item in itens if not item.separado]
        itens_separados = [item for item in itens if item.separado]

        # Calcular métricas
        tempo_decorrido_minutos = self._calcular_tempo_decorrido(pedido)
        progresso_percentual = self._calcular_progresso(itens)

        context = {
            'pedido': pedido,
            'itens_nao_separados': itens_nao_separados,
            'itens_separados': itens_separados,
            'tempo_decorrido_minutos': tempo_decorrido_minutos,
            'progresso_percentual': progresso_percentual,
            'usuario': request.user
        }

        logger.debug(
            f"Pedido #{pedido_id}: {len(itens_nao_separados)} não separados, "
            f"{len(itens_separados)} separados, progresso {progresso_percentual}%"
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

        Args:
            itens: Lista de ItemPedido

        Returns:
            int: Percentual de progresso (0-100)
        """
        total_itens = len(itens)
        if total_itens == 0:
            return 0

        itens_separados = sum(1 for item in itens if item.separado)
        return int((itens_separados / total_itens) * 100)


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
        if item.separado:
            logger.warning(f"Item {item_id} já está separado")
            return render(request, 'partials/_erro.html', {
                'mensagem': 'Item já está marcado como separado'
            }, status=400)

        # Marcar item como separado
        from django.utils import timezone
        item.separado = True
        item.quantidade_separada = item.quantidade_solicitada
        item.separado_por = request.user
        item.separado_em = timezone.now()
        item.save()

        logger.info(
            f"Item {item_id} marcado como separado por {request.user.nome} "
            f"no pedido {pedido_id}"
        )

        # Calcular progresso atualizado
        itens = list(pedido.itens.all())
        progresso_percentual = self._calcular_progresso(itens)

        logger.info(
            f"Progresso do pedido {pedido_id} atualizado: {progresso_percentual}%"
        )

        # Fase 30: Broadcast evento WebSocket para dashboard
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'item_separado',
                    'pedido_id': pedido.id,
                    'progresso': progresso_percentual
                }
            )
            logger.info(
                f"Evento WebSocket enviado: item_separado "
                f"(pedido_id={pedido.id}, progresso={progresso_percentual}%)"
            )
        except Exception as e:
            logger.warning(f"Erro ao enviar evento WebSocket item_separado: {e}")

        # Renderizar partial atualizado do item
        return render(request, 'partials/_item_pedido.html', {
            'item': item,
            'pedido': pedido,
            'progresso_percentual': progresso_percentual
        })

    def _calcular_progresso(self, itens):
        """
        Calcula progresso percentual da separação.

        Args:
            itens: Lista de ItemPedido

        Returns:
            int: Percentual de progresso (0-100)
        """
        total_itens = len(itens)
        if total_itens == 0:
            return 0

        itens_separados = sum(1 for item in itens if item.separado)
        return int((itens_separados / total_itens) * 100)


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
        # Validar que é requisição HTMX
        if not request.headers.get('HX-Request'):
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

        # Renderizar partial atualizado do item
        return render(
            request,
            'partials/_item_pedido.html',
            {
                'item': item,
                'pedido': item.pedido
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
            tipo=TipoUsuario(request.user.tipo)
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

        # Renderizar partial atualizado do item
        return render(
            request,
            'partials/_item_pedido.html',
            {
                'item': item,
                'pedido': item.pedido
            }
        )


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

        # Contar itens separados
        itens = pedido.itens.all()
        total_itens = itens.count()
        itens_separados = itens.filter(separado=True).count()
        progresso_percentual = int((itens_separados / total_itens * 100)) if total_itens > 0 else 0

        # Buscar separadores ativos (usuários do tipo SEPARADOR que têm sessões ativas)
        # Por simplicidade, retornar lista vazia (feature futura)
        separadores = []

        # Preparar contexto
        pedido_data = {
            'pedido': pedido,
            'tempo_decorrido_minutos': tempo_decorrido_minutos,
            'progresso_percentual': progresso_percentual,
            'itens_separados': itens_separados,
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

        return {
            'id': pedido.id,
            'numero_orcamento': pedido.numero_orcamento,
            'nome_cliente': pedido.nome_cliente,
            'vendedor': pedido.vendedor.nome if pedido.vendedor else 'N/A',
            'data_finalizacao': pedido.data_finalizacao,
            'tempo_total_minutos': tempo_total_minutos,
            'tempo_total_formatado': self._formatar_tempo(tempo_total_minutos),
            'total_itens': total_itens,
            'itens_separados': itens_separados,
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
