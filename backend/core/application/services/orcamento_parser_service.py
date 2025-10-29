# -*- coding: utf-8 -*-
"""
Serviço de aplicação para processar PDFs de orçamentos.

Este serviço orquestra as seguintes operações:
1. Upload e validação do arquivo PDF
2. Parsing via PDFOrcamentoParser
3. Criação/busca de Produtos no banco
4. Criação transacional de Pedido + ItemPedido
5. Logging de operações

Autor: Nycolas Mancini
Data: 2025-10-29
Fase 2: Service Layer com TDD
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional
from decimal import Decimal

from django.db import transaction
from django.core.files.uploadedfile import UploadedFile

# Imports dos models Django
from core.models import Usuario, Pedido, ItemPedido
from core.infrastructure.persistence.models.produto import Produto

# Import do parser validado
from core.infrastructure.parsers.pdf_orcamento_parser import (
    PDFOrcamentoParser,
    ParserError
)

# Import das exceções customizadas
from core.application.services.exceptions import (
    DuplicatePedidoError,
    VendedorNotFoundError,
    IntegrityValidationError
)

# Configuração de logging
logger = logging.getLogger(__name__)


class OrcamentoParserService:
    """
    Serviço de aplicação para processar PDFs de orçamentos.

    Responsabilidades:
    - Receber arquivo PDF uploaded
    - Chamar PDFOrcamentoParser para extração de dados
    - Buscar/criar Produtos no banco de dados
    - Criar Pedido e ItemPedido de forma transacional
    - Validar integridade dos dados
    - Logging de operações e erros

    Example:
        >>> service = OrcamentoParserService()
        >>> pedido = service.processar_pdf_e_criar_pedido(
        ...     pdf_file=pdf_uploaded,
        ...     vendedor=usuario_vendedor,
        ...     logistica='CORREIOS',
        ...     embalagem='CAIXA'
        ... )
    """

    def __init__(self):
        """Inicializa o serviço."""
        self.logger = logger

    @transaction.atomic
    def processar_pdf_e_criar_pedido(
        self,
        pdf_file: UploadedFile,
        vendedor: Usuario,
        logistica: str,
        embalagem: str,
        observacoes: Optional[str] = None
    ) -> Pedido:
        """
        Método principal que processa PDF e cria pedido.

        Este método é executado dentro de uma transação atômica (@transaction.atomic).
        Se qualquer erro ocorrer, todas as operações serão revertidas (rollback).

        Args:
            pdf_file: Arquivo PDF uploaded pelo usuário
            vendedor: Instância de Usuario (tipo VENDEDOR) - usado como fallback
            logistica: Tipo de logística (valor de LogisticaChoices)
            embalagem: Tipo de embalagem (valor de EmbalagemChoices)
            observacoes: Observações opcionais sobre o pedido

        Returns:
            Pedido: Instância do pedido criado com todos os itens

        Raises:
            ParserError: Se houver erro ao fazer parsing do PDF
            DuplicatePedidoError: Se orçamento já existe no banco
            VendedorNotFoundError: Se vendedor do PDF não existe no banco
            IntegrityValidationError: Se validação matemática falhar
            ValueError: Se dados inválidos forem fornecidos

        Example:
            >>> from django.core.files.uploadedfile import SimpleUploadedFile
            >>> pdf_file = SimpleUploadedFile("orc.pdf", b"conteudo", content_type="application/pdf")
            >>> pedido = service.processar_pdf_e_criar_pedido(
            ...     pdf_file=pdf_file,
            ...     vendedor=vendedor_obj,
            ...     logistica='CORREIOS',
            ...     embalagem='CAIXA',
            ...     observacoes='Urgente'
            ... )
        """
        try:
            # 1. Salvar PDF temporariamente para processamento
            temp_pdf_path = self._salvar_pdf_temporario(pdf_file)

            self.logger.info(f"Iniciando processamento de PDF: {pdf_file.name}")

            # 2. Fazer parsing do PDF
            parser = PDFOrcamentoParser(temp_pdf_path)
            orcamento = parser.parse()

            self.logger.info(
                f"PDF parseado com sucesso. Orçamento: {orcamento.numero}, "
                f"Produtos: {len(orcamento.produtos)}"
            )

            # 3. Validar integridade matemática
            if not parser.validar_integridade():
                soma_produtos = sum(p.valor_total for p in orcamento.produtos)
                raise IntegrityValidationError(
                    soma_produtos=soma_produtos,
                    valor_total=orcamento.valor_total
                )

            # 4. Verificar se orçamento já existe (duplicado)
            if Pedido.objects.filter(numero_orcamento=orcamento.numero).exists():
                raise DuplicatePedidoError(orcamento.numero)

            # 5. Buscar vendedor pelo nome (do PDF) no banco
            # Se não encontrado, lança exceção
            vendedor_obj = self._buscar_vendedor(orcamento.vendedor)

            # 6. Criar Pedido no banco
            pedido = Pedido.objects.create(
                numero_orcamento=orcamento.numero,
                codigo_cliente=orcamento.codigo_cliente,
                nome_cliente=orcamento.nome_cliente,
                vendedor=vendedor_obj,
                data=orcamento.data,
                logistica=logistica,
                embalagem=embalagem,
                status='EM_SEPARACAO',
                observacoes=observacoes or ''
            )

            self.logger.info(f"Pedido criado: ID={pedido.id}, Nº Orçamento={pedido.numero_orcamento}")

            # 7. Processar produtos e criar ItemPedido
            itens_criados = self._processar_produtos_e_criar_itens(orcamento.produtos, pedido)

            self.logger.info(
                f"Processamento concluído com sucesso. "
                f"Pedido: {pedido.numero_orcamento}, "
                f"Itens criados: {len(itens_criados)}"
            )

            # 8. Limpar arquivo temporário
            self._limpar_arquivo_temporario(temp_pdf_path)

            return pedido

        except (ParserError, DuplicatePedidoError, VendedorNotFoundError, IntegrityValidationError) as e:
            # Exceções conhecidas - apenas re-lançar (rollback automático)
            self.logger.error(f"Erro ao processar PDF: {str(e)}")
            raise

        except Exception as e:
            # Exceções inesperadas - logar e re-lançar como ParserError
            self.logger.error(f"Erro inesperado ao processar PDF: {str(e)}", exc_info=True)
            raise ParserError(f"Erro inesperado ao processar PDF: {str(e)}")

    def _salvar_pdf_temporario(self, pdf_file: UploadedFile) -> str:
        """
        Salva o PDF uploaded em arquivo temporário para processamento.

        Args:
            pdf_file: Arquivo uploaded

        Returns:
            str: Caminho do arquivo temporário

        Raises:
            ParserError: Se houver erro ao salvar arquivo
        """
        try:
            # Cria arquivo temporário com sufixo .pdf
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as temp_file:
                # Escreve conteúdo do upload
                for chunk in pdf_file.chunks():
                    temp_file.write(chunk)

                temp_path = temp_file.name

            self.logger.debug(f"PDF salvo temporariamente em: {temp_path}")
            return temp_path

        except Exception as e:
            raise ParserError(f"Erro ao salvar PDF temporário: {str(e)}")

    def _limpar_arquivo_temporario(self, temp_path: str) -> None:
        """
        Remove arquivo temporário após processamento.

        Args:
            temp_path: Caminho do arquivo temporário
        """
        try:
            Path(temp_path).unlink(missing_ok=True)
            self.logger.debug(f"Arquivo temporário removido: {temp_path}")
        except Exception as e:
            # Não é crítico, apenas logar warning
            self.logger.warning(f"Não foi possível remover arquivo temporário {temp_path}: {str(e)}")

    def _buscar_vendedor(self, nome_vendedor: str) -> Usuario:
        """
        Busca vendedor no banco de dados pelo nome.

        Args:
            nome_vendedor: Nome completo do vendedor (extraído do PDF)

        Returns:
            Usuario: Instância do vendedor encontrado

        Raises:
            VendedorNotFoundError: Se vendedor não for encontrado

        Note:
            A busca é case-insensitive e remove espaços extras
        """
        # Normaliza nome para busca (uppercase, sem espaços extras)
        nome_normalizado = ' '.join(nome_vendedor.upper().split())

        try:
            # Busca por nome exato (case-insensitive)
            vendedor = Usuario.objects.get(
                nome__iexact=nome_normalizado,
                tipo='VENDEDOR',
                ativo=True
            )
            return vendedor

        except Usuario.DoesNotExist:
            raise VendedorNotFoundError(nome_vendedor)

        except Usuario.MultipleObjectsReturned:
            # Se houver múltiplos, pega o primeiro ativo
            self.logger.warning(f"Múltiplos vendedores encontrados com nome '{nome_vendedor}'")
            return Usuario.objects.filter(
                nome__iexact=nome_normalizado,
                tipo='VENDEDOR',
                ativo=True
            ).first()

    def _processar_produtos_e_criar_itens(self, produtos_parser, pedido: Pedido) -> list:
        """
        Processa produtos do parser e cria ItemPedido.

        Para cada produto:
        1. Verifica se produto já existe no banco (por código)
        2. Se não existe, cria novo Produto
        3. Cria ItemPedido vinculado ao Pedido

        Args:
            produtos_parser: Lista de objetos Produto do parser
            pedido: Instância de Pedido Django

        Returns:
            list: Lista de ItemPedido criados

        Note:
            Esta função não cria produtos duplicados. Se o código já existe,
            reutiliza o produto existente.
        """
        itens_criados = []

        for produto_parser in produtos_parser:
            # 1. Buscar ou criar Produto
            produto_django, criado = Produto.objects.get_or_create(
                codigo=produto_parser.codigo,
                defaults={
                    'descricao': produto_parser.descricao,
                    'quantidade': int(produto_parser.quantidade),
                    'valor_unitario': Decimal(str(produto_parser.valor_unitario)),
                    'valor_total': Decimal(str(produto_parser.valor_total))
                }
            )

            if criado:
                self.logger.debug(f"Produto criado: {produto_django.codigo} - {produto_django.descricao}")
            else:
                self.logger.debug(f"Produto reutilizado: {produto_django.codigo}")

            # 2. Criar ItemPedido
            item = ItemPedido.objects.create(
                pedido=pedido,
                produto=produto_django,
                quantidade_solicitada=int(produto_parser.quantidade),
                quantidade_separada=0,
                separado=False
            )

            itens_criados.append(item)

        return itens_criados

    def validar_pdf(self, pdf_file: UploadedFile) -> dict:
        """
        Valida um PDF sem criar o pedido (dry-run).

        Útil para preview antes de salvar definitivamente.

        Args:
            pdf_file: Arquivo PDF uploaded

        Returns:
            dict: Informações extraídas do PDF
                {
                    'numero_orcamento': str,
                    'nome_cliente': str,
                    'vendedor': str,
                    'valor_total': Decimal,
                    'quantidade_produtos': int,
                    'integridade_ok': bool
                }

        Raises:
            ParserError: Se houver erro ao fazer parsing
        """
        try:
            temp_pdf_path = self._salvar_pdf_temporario(pdf_file)

            parser = PDFOrcamentoParser(temp_pdf_path)
            orcamento = parser.parse()

            resultado = {
                'numero_orcamento': orcamento.numero,
                'codigo_cliente': orcamento.codigo_cliente,
                'nome_cliente': orcamento.nome_cliente,
                'vendedor': orcamento.vendedor,
                'data': orcamento.data,
                'valor_total': orcamento.valor_total,
                'quantidade_produtos': len(orcamento.produtos),
                'integridade_ok': parser.validar_integridade(),
                'produtos': [
                    {
                        'codigo': p.codigo,
                        'descricao': p.descricao,
                        'quantidade': p.quantidade,
                        'valor_unitario': p.valor_unitario,
                        'valor_total': p.valor_total
                    }
                    for p in orcamento.produtos
                ]
            }

            self._limpar_arquivo_temporario(temp_pdf_path)

            return resultado

        except Exception as e:
            self.logger.error(f"Erro ao validar PDF: {str(e)}")
            raise ParserError(f"Erro ao validar PDF: {str(e)}")
