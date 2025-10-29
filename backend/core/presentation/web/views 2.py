# -*- coding: utf-8 -*-
"""
Views web para o sistema de separação.
Fase 7: LoginView e Dashboard Placeholder
Fase 8: LogoutView
Fase 15: UploadOrcamentoView
"""
import logging
import tempfile
import os
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.utils.decorators import method_decorator

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
        Retorna lista de vendedores para o filtro.

        Returns:
            QuerySet: Usuários vendedores
        """
        from core.models import Usuario

        return Usuario.objects.filter(
            tipo='VENDEDOR',
            ativo=True
        ).order_by('nome')

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
                {'erro': 'Item não encontrado'},
                status=404
            )

        # Validar regras de negócio
        if item.separado:
            logger.warning(
                f"Tentativa de marcar item já separado para compra: item={item_id}"
            )
            return render(
                request,
                'partials/_erro.html',
                {'erro': 'Item já foi separado'},
                status=400
            )

        if item.em_compra:
            logger.warning(
                f"Tentativa de marcar item já em compra: item={item_id}"
            )
            return render(
                request,
                'partials/_erro.html',
                {'erro': 'Item já está marcado para compra'},
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
