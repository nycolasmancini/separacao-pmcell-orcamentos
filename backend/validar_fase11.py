#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação da Fase 11 - Extração de Cabeçalho de PDFs.

Testa o PDFParser e PDFHeaderExtractor com os 5 PDFs reais de orçamento.
"""

import os
import sys

# Configurar PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.infrastructure.pdf.parser import PDFParser, PDFHeaderExtractor


def validar_pdfs():
    """Valida extração de cabeçalho em todos os PDFs de exemplo."""

    # Diretório com PDFs
    pdf_dir = "/Users/nycolasmancini/Desktop/separacao-pmcell/orcamentos-modelo/"

    # Lista de PDFs para testar
    pdfs = [
        "Orcamento - 30567 - Rosana - R$ 105,00.pdf",
        "Orcamento - 30568 - Ponto do Celular - R$ 969,00.pdf",
        "Orcamento - 30582 - Infocel - R$ 1707,00.pdf",
        "Orcamento 30590 R$ 808,50.pdf",
        "Orcamento 30596 Ali R$ 1994,80.pdf"
    ]

    parser = PDFParser()
    extractor = PDFHeaderExtractor()

    print("=" * 80)
    print("VALIDAÇÃO DA FASE 11 - EXTRAÇÃO DE CABEÇALHO DE PDFs")
    print("=" * 80)
    print()

    resultados = []

    for pdf_filename in pdfs:
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        print(f"📄 Processando: {pdf_filename}")
        print("-" * 80)

        try:
            # Extrair texto do PDF
            texto = parser.extrair_texto(pdf_path)
            print(f"   ✓ Texto extraído: {len(texto)} caracteres")

            # Extrair cabeçalho
            header = extractor.extrair_header(texto)

            # Exibir resultados
            print(f"   Número Orçamento: {header.numero_orcamento}")
            print(f"   Código Cliente:   {header.codigo_cliente}")
            print(f"   Nome Cliente:     {header.nome_cliente}")
            print(f"   Vendedor:         {header.vendedor}")
            print(f"   Data:             {header.data}")
            print(f"   Válido:           {'✅ SIM' if header.is_valid else '❌ NÃO'}")

            if not header.is_valid:
                print(f"   Erros:            {', '.join(header.errors)}")

            resultados.append({
                'pdf': pdf_filename,
                'valido': header.is_valid,
                'header': header
            })

        except Exception as e:
            print(f"   ❌ ERRO: {str(e)}")
            resultados.append({
                'pdf': pdf_filename,
                'valido': False,
                'erro': str(e)
            })

        print()

    # Resumo final
    print("=" * 80)
    print("RESUMO DA VALIDAÇÃO")
    print("=" * 80)

    total = len(resultados)
    validos = sum(1 for r in resultados if r['valido'])

    print(f"Total de PDFs testados: {total}")
    print(f"PDFs com sucesso:       {validos}")
    print(f"Taxa de sucesso:        {(validos/total)*100:.1f}%")
    print()

    if validos == total:
        print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
        print("   Todos os PDFs foram processados corretamente.")
        return True
    else:
        print("⚠️  VALIDAÇÃO PARCIAL")
        print(f"   {total - validos} PDF(s) com problemas.")
        return False


if __name__ == "__main__":
    sucesso = validar_pdfs()
    sys.exit(0 if sucesso else 1)
