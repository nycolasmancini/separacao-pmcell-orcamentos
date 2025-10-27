# -*- coding: utf-8 -*-
"""
Caso de Uso: Criar Pedido a partir de PDF.

Este módulo implementa a lógica de criação de pedidos através da extração
de dados de orçamentos em PDF, validação e persistência.

Author: PMCELL
Date: 2025-01-25
"""

import logging
from typing import List

from core.application.dtos.pedido_dtos import CriarPedidoRequestDTO, CriarPedidoResponseDTO
from core.application.dtos.orcamento_dtos import OrcamentoHeaderDTO, ProdutoDTO
from core.domain.pedido.entities import Pedido, ItemPedido, ValidationError
from core.domain.produto.entities import Produto
from core.infrastructure.pdf.parser import PDFParser, PDFHeaderExtractor, PDFProductExtractor
from core.infrastructure.persistence.repositories.pedido_repository import PedidoRepositoryInterface

logger = logging.getLogger(__name__)


class CriarPedidoUseCase:
    """
    Caso de uso para criação de pedidos a partir de PDFs.

    Este use case orquestra o processo completo de criação de um pedido:
    1. Extração de texto do PDF
    2. Extração de dados do cabeçalho (número, cliente, vendedor)
    3. Extração de produtos (código, quantidade, valores)
    4. Validação de consistência matemática
    5. Criação de entidade Pedido com itens
    6. Validação de regras de negócio (embalagem, logística)
    7. Persistência no banco de dados
    8. Inicialização do cronômetro do pedido

    Attributes:
        pdf_parser: Parser para extração de texto do PDF
        header_extractor: Extrator de dados do cabeçalho
        product_extractor: Extrator de produtos
        pedido_repository: Repositório para persistência de pedidos

    Examples:
        >>> from core.domain.pedido.value_objects import Logistica, Embalagem
        >>> request = CriarPedidoRequestDTO(
        ...     pdf_path="/path/to/orcamento.pdf",
        ...     logistica=Logistica.CORREIOS,
        ...     embalagem=Embalagem.CAIXA,
        ...     usuario_criador_id=1
        ... )
        >>> use_case = CriarPedidoUseCase(parser, header_ext, product_ext, repo)
        >>> response = use_case.execute(request)
        >>> response.success
        True
    """

    # Constantes
    ERROR_PDF_EXTRACTION = "Falha na extração do PDF"
    ERROR_HEADER_INVALID = "Header do orçamento inválido"
    ERROR_PRODUCTS_INVALID = "Produtos inválidos encontrados no orçamento"
    ERROR_MATH_VALIDATION = "Validação matemática dos produtos falhou"
    ERROR_BUSINESS_RULES = "Validação de regras de negócio falhou"
    ERROR_PERSISTENCE = "Falha ao persistir pedido no banco de dados"

    def __init__(
        self,
        pdf_parser: PDFParser,
        header_extractor: PDFHeaderExtractor,
        product_extractor: PDFProductExtractor,
        pedido_repository: PedidoRepositoryInterface
    ):
        """
        Inicializa o caso de uso.

        Args:
            pdf_parser: Parser para extração de texto do PDF
            header_extractor: Extrator de dados do cabeçalho
            product_extractor: Extrator de produtos
            pedido_repository: Repositório para persistência
        """
        self.pdf_parser = pdf_parser
        self.header_extractor = header_extractor
        self.product_extractor = product_extractor
        self.pedido_repository = pedido_repository

        logger.info("CriarPedidoUseCase inicializado")

    def execute(self, request: CriarPedidoRequestDTO) -> CriarPedidoResponseDTO:
        """
        Executa o caso de uso de criação de pedido.

        Args:
            request: DTO contendo dados da requisição

        Returns:
            CriarPedidoResponseDTO: Resultado da operação

        Workflow:
            1. Extrair texto do PDF
            2. Extrair header (número, cliente, vendedor)
            3. Validar header
            4. Extrair produtos
            5. Validar produtos (incluindo validação matemática)
            6. Criar entidade Pedido
            7. Validar regras de negócio
            8. Persistir no repositório
            9. Retornar resposta

        Notes:
            - Todas as exceções são capturadas e retornadas como ResponseDTO
            - Logging completo em cada etapa
            - Fail-safe: sempre retorna ResponseDTO válido
        """
        logger.info(
            f"Iniciando criação de pedido a partir de PDF: {request.pdf_path}"
        )

        try:
            # Etapa 1: Extrair texto do PDF
            texto_pdf = self._extrair_texto_pdf(request.pdf_path)
            if texto_pdf is None:
                return self._criar_response_erro(
                    self.ERROR_PDF_EXTRACTION,
                    ["Arquivo PDF inacessível ou corrompido"]
                )

            # Etapa 2: Extrair header
            header = self._extrair_header(texto_pdf)
            if not self._validar_header(header):
                return self._criar_response_erro(
                    self.ERROR_HEADER_INVALID,
                    header.errors
                )

            # Etapa 3: Extrair produtos
            produtos = self._extrair_produtos(texto_pdf)
            if not self._validar_produtos(produtos):
                return self._criar_response_erro(
                    self.ERROR_PRODUCTS_INVALID,
                    self._coletar_erros_produtos(produtos)
                )

            # Etapa 4: Criar entidade Pedido
            pedido = self._criar_pedido(header, produtos, request)
            if pedido is None:
                return self._criar_response_erro(
                    self.ERROR_BUSINESS_RULES,
                    ["Falha ao criar pedido com os dados fornecidos"]
                )

            # Etapa 5: Persistir pedido
            pedido_salvo = self._persistir_pedido(pedido)
            if pedido_salvo is None:
                return self._criar_response_erro(
                    self.ERROR_PERSISTENCE,
                    ["Falha ao salvar pedido no banco de dados"]
                )

            # Sucesso!
            logger.info(
                f"Pedido {pedido_salvo.numero_orcamento} criado com sucesso. "
                f"{len(pedido_salvo.itens)} itens adicionados"
            )

            return CriarPedidoResponseDTO(
                success=True,
                pedido=pedido_salvo,
                error_message=None,
                validation_errors=[]
            )

        except Exception as e:
            logger.error(f"Erro inesperado ao criar pedido: {str(e)}", exc_info=True)
            return self._criar_response_erro(
                f"Erro inesperado: {str(e)}",
                [str(e)]
            )

    def _extrair_texto_pdf(self, pdf_path: str) -> str:
        """
        Extrai texto do PDF usando PDFParser.

        Args:
            pdf_path: Caminho para o arquivo PDF

        Returns:
            Texto extraído ou None se falhou
        """
        try:
            logger.debug(f"Extraindo texto do PDF: {pdf_path}")
            texto = self.pdf_parser.extrair_texto(pdf_path)
            logger.info(f"Texto extraído com sucesso ({len(texto)} caracteres)")
            return texto
        except Exception as e:
            logger.error(f"Falha ao extrair texto do PDF: {str(e)}", exc_info=True)
            return None

    def _extrair_header(self, texto: str) -> OrcamentoHeaderDTO:
        """
        Extrai dados do cabeçalho do orçamento.

        Args:
            texto: Texto completo do PDF

        Returns:
            OrcamentoHeaderDTO com dados extraídos
        """
        logger.debug("Extraindo header do orçamento")
        header = self.header_extractor.extrair_header(texto)
        logger.info(f"Header extraído: {header}")
        return header

    def _validar_header(self, header: OrcamentoHeaderDTO) -> bool:
        """
        Valida se header foi extraído corretamente.

        Args:
            header: DTO do header

        Returns:
            True se válido, False caso contrário
        """
        is_valid = header.is_valid
        if not is_valid:
            logger.warning(f"Header inválido. Erros: {header.errors}")
        return is_valid

    def _extrair_produtos(self, texto: str) -> List[ProdutoDTO]:
        """
        Extrai lista de produtos do orçamento.

        Args:
            texto: Texto completo do PDF

        Returns:
            Lista de ProdutoDTO
        """
        logger.debug("Extraindo produtos do orçamento")
        produtos = self.product_extractor.extrair_produtos(texto)
        logger.info(f"{len(produtos)} produtos extraídos")
        return produtos

    def _validar_produtos(self, produtos: List[ProdutoDTO]) -> bool:
        """
        Valida se todos os produtos foram extraídos corretamente.

        Args:
            produtos: Lista de produtos extraídos

        Returns:
            True se todos válidos, False caso contrário
        """
        if not produtos:
            logger.warning("Nenhum produto encontrado no PDF")
            return False

        produtos_invalidos = [p for p in produtos if not p.is_valid]

        if produtos_invalidos:
            logger.warning(
                f"{len(produtos_invalidos)} produtos inválidos encontrados"
            )
            return False

        logger.info(f"Todos os {len(produtos)} produtos são válidos")
        return True

    def _coletar_erros_produtos(self, produtos: List[ProdutoDTO]) -> List[str]:
        """
        Coleta todos os erros de validação dos produtos.

        Args:
            produtos: Lista de produtos

        Returns:
            Lista de strings com erros
        """
        erros = []
        for produto in produtos:
            if not produto.is_valid:
                erros.extend([
                    f"Produto {produto.codigo}: {erro}"
                    for erro in produto.errors
                ])
        return erros

    def _criar_pedido(
        self,
        header: OrcamentoHeaderDTO,
        produtos: List[ProdutoDTO],
        request: CriarPedidoRequestDTO
    ) -> Pedido:
        """
        Cria entidade Pedido a partir dos dados extraídos.

        Args:
            header: Dados do cabeçalho
            produtos: Lista de produtos
            request: Request original com dados de logística

        Returns:
            Pedido criado ou None se falhou
        """
        try:
            logger.debug("Criando entidade Pedido")

            # Criar pedido
            pedido = Pedido(
                numero_orcamento=header.numero_orcamento,
                codigo_cliente=header.codigo_cliente,
                nome_cliente=header.nome_cliente,
                vendedor=header.vendedor,
                data=header.data,
                logistica=request.logistica,
                embalagem=request.embalagem,
                observacoes=request.observacoes
            )

            # Adicionar itens
            for produto_dto in produtos:
                produto_entity = produto_dto.to_entity()
                item = ItemPedido(
                    produto=produto_entity,
                    quantidade_solicitada=produto_entity.quantidade
                )
                pedido.adicionar_item(item)

            logger.info(
                f"Pedido criado: {pedido.numero_orcamento} "
                f"com {len(pedido.itens)} itens"
            )

            return pedido

        except ValidationError as e:
            logger.error(f"Erro de validação ao criar pedido: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao criar pedido: {str(e)}", exc_info=True)
            return None

    def _persistir_pedido(self, pedido: Pedido) -> Pedido:
        """
        Persiste pedido no banco de dados via repositório.

        Args:
            pedido: Entidade Pedido a ser salva

        Returns:
            Pedido salvo com ID ou None se falhou
        """
        try:
            logger.debug(f"Persistindo pedido {pedido.numero_orcamento}")
            pedido_id = self.pedido_repository.save(pedido)
            pedido.id = pedido_id
            logger.info(f"Pedido {pedido.numero_orcamento} salvo com ID {pedido_id}")
            return pedido
        except Exception as e:
            logger.error(f"Falha ao persistir pedido: {str(e)}", exc_info=True)
            return None

    def _criar_response_erro(
        self,
        error_message: str,
        validation_errors: List[str]
    ) -> CriarPedidoResponseDTO:
        """
        Cria um ResponseDTO de erro.

        Args:
            error_message: Mensagem de erro principal
            validation_errors: Lista de erros de validação

        Returns:
            CriarPedidoResponseDTO com success=False
        """
        logger.error(f"Erro na criação de pedido: {error_message}")
        return CriarPedidoResponseDTO(
            success=False,
            pedido=None,
            error_message=error_message,
            validation_errors=validation_errors
        )
