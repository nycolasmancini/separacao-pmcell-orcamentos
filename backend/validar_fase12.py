#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação da Fase 12: Extração de Produtos do PDF.

Este script testa o PDFProductExtractor com os 5 PDFs reais de orçamento.
"""

import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from core.infrastructure.pdf.parser import PDFParser, PDFProductExtractor


def validar_fase12():
    """Valida extração de produtos com 5 PDFs reais."""
    print("=" * 80)
    print("VALIDAÇÃO FASE 12: Extração de Produtos do PDF")
    print("=" * 80)
    print()

    # Diretório dos PDFs
    pdf_dir = ROOT_DIR.parent

    # Lista de PDFs para testar
    pdfs = [
        "Orcamento - 30567 - Rosana - R$ 105,00.pdf",
        "Orcamento - 30568 - Ponto do Celular - R$ 969,00.pdf",
        "Orcamento - 30582 - Infocel - R$ 1707,00.pdf",
        "Orcamento 30590 R$ 808,50.pdf",
        "Orcamento 30596 Ali R$ 1994,80.pdf"
    ]

    parser = PDFParser()
    extractor = PDFProductExtractor()

    total_pdfs = 0
    total_pdfs_sucesso = 0
    total_produtos = 0
    total_produtos_validos = 0

    for pdf_nome in pdfs:
        pdf_path = pdf_dir / pdf_nome

        if not pdf_path.exists():
            print(f"❌ PDF não encontrado: {pdf_nome}")
            continue

        total_pdfs += 1

        print(f"📄 Processando: {pdf_nome}")
        print("-" * 80)

        try:
            # Extrair texto
            texto = parser.extrair_texto(str(pdf_path))

            # Extrair produtos
            produtos = extractor.extrair_produtos(texto)

            total_produtos += len(produtos)
            produtos_validos = [p for p in produtos if p.is_valid]
            total_produtos_validos += len(produtos_validos)

            # Estatísticas
            print(f"  ✅ Produtos extraídos: {len(produtos)}")
            print(f"  ✅ Produtos válidos: {len(produtos_validos)}")

            if len(produtos_validos) < len(produtos):
                print(f"  ⚠️  Produtos inválidos: {len(produtos) - len(produtos_validos)}")

            # Mostrar primeiros 3 produtos
            print("  📦 Primeiros produtos:")
            for i, produto in enumerate(produtos[:3], 1):
                status = "✓" if produto.is_valid else "✗"
                print(f"     {status} {produto.codigo} - {produto.descricao[:40]}...")
                print(f"        Qtd: {produto.quantidade}, Valor Unit: R$ {produto.valor_unitario}, Total: R$ {produto.valor_total}")
                if not produto.is_valid:
                    print(f"        Erros: {produto.errors}")

            total_pdfs_sucesso += 1

        except Exception as e:
            print(f"  ❌ Erro ao processar PDF: {str(e)}")

        print()

    # Resumo final
    print("=" * 80)
    print("RESUMO DA VALIDAÇÃO")
    print("=" * 80)
    print(f"PDFs processados: {total_pdfs_sucesso}/{total_pdfs}")
    print(f"Produtos extraídos: {total_produtos}")
    print(f"Produtos válidos: {total_produtos_validos} ({total_produtos_validos/total_produtos*100:.1f}%)" if total_produtos > 0 else "Produtos válidos: 0")
    print()

    if total_pdfs_sucesso == total_pdfs and total_produtos_validos == total_produtos:
        print("✅ FASE 12: SUCESSO TOTAL (100% dos produtos válidos)")
        return True
    elif total_produtos_validos / total_produtos >= 0.95:
        print("⚠️  FASE 12: SUCESSO PARCIAL (>95% dos produtos válidos)")
        return True
    else:
        print("❌ FASE 12: NECESSITA AJUSTES")
        return False


if __name__ == "__main__":
    sucesso = validar_fase12()
    sys.exit(0 if sucesso else 1)
