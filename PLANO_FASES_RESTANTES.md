# Plano de Implementação - Fases Restantes (PDF Parser Integration)

## ✅ Fase 1 COMPLETA - Parser Layer
**Commit:** `a65f0fc`  
**Status:** 29 testes unitários passando (100%)  
**Arquivos:**
- `backend/core/infrastructure/parsers/pdf_orcamento_parser.py`
- `backend/core/tests/unit/test_pdf_orcamento_parser.py`

---

## 📋 Fase 2 - Service Layer (PRÓXIMA)

### Objetivo
Criar camada de serviço que orquestra:
1. Upload do PDF
2. Parsing via `PDFOrcamentoParser`
3. Criação transacional de Pedido + ItemPedido
4. Criação/busca de Produtos no banco

### Arquivos a Criar

#### 1. Service Implementation
**Arquivo:** `backend/core/application/services/orcamento_parser_service.py`

```python
class OrcamentoParserService:
    """
    Serviço de aplicação para processar PDFs de orçamentos.
    
    Responsabilidades:
    - Receber arquivo PDF
    - Chamar PDFOrcamentoParser
    - Criar/buscar Produtos no banco
    - Criar Pedido e ItemPedido de forma transacional
    - Logging de operações
    """
    
    @transaction.atomic
    def processar_pdf_e_criar_pedido(
        self, 
        pdf_file: UploadedFile,
        vendedor: Usuario,
        logistica: str,
        embalagem: str,
        observacoes: str = None
    ) -> Pedido:
        """
        Método principal que processa PDF e cria pedido.
        
        Args:
            pdf_file: Arquivo PDF uploaded
            vendedor: Usuário vendedor
            logistica: Tipo de logística
            embalagem: Tipo de embalagem
            observacoes: Observações opcionais
            
        Returns:
            Pedido criado
            
        Raises:
            ParserError: Se parsing falhar
            ValidationError: Se dados inválidos
            DuplicatePedidoError: Se orçamento já existe
        """
        pass
```

#### 2. Integration Tests
**Arquivo:** `backend/core/tests/integration/test_orcamento_parser_service.py`

**8 Testes a Implementar:**

1. `test_processar_pdf_valido_cria_pedido_completo()`
   - Upload PDF válido
   - Verifica criação de Pedido com todos os campos
   - Verifica criação de todos os ItemPedido
   - Verifica criação/busca de Produtos

2. `test_processar_pdf_com_produtos_existentes()`
   - Produtos já existem no banco
   - Verifica que reutiliza produtos existentes
   - Não cria duplicatas

3. `test_processar_pdf_duplicado_lanca_excecao()`
   - Orçamento já existe (mesmo numero_orcamento)
   - Deve lançar `DuplicatePedidoError`

4. `test_processar_pdf_invalido_rollback_transacao()`
   - PDF com erro de parsing
   - Verifica rollback transacional
   - Nenhum Pedido/ItemPedido criado

5. `test_processar_pdf_vendedor_nao_encontrado()`
   - Nome do vendedor no PDF não existe no banco
   - Deve lançar `VendedorNotFoundError`

6. `test_processar_pdf_validacao_integridade_falha()`
   - Soma produtos ≠ valor total
   - Deve lançar `IntegrityValidationError`

7. `test_processar_pdf_logging_correto()`
   - Verifica logs de sucesso
   - Verifica logs de erro

8. `test_processar_pdf_arquivo_corrompido()`
   - PDF corrompido/ilegível
   - Deve lançar `ParserError`

### Comando para Rodar Testes
```bash
cd backend
pytest core/tests/integration/test_orcamento_parser_service.py -v
```

---

## 📋 Fase 3 - Form Modification

### Objetivo
Modificar `UploadOrcamentoForm` para aceitar PDF e auto-preencher campos

### Arquivo a Modificar
**Arquivo:** `backend/core/presentation/web/forms.py`

```python
class UploadOrcamentoForm(forms.Form):
    """Formulário para upload de PDF de orçamento."""
    
    pdf_file = forms.FileField(
        label='Arquivo PDF do Orçamento',
        required=True,
        widget=forms.FileInput(attrs={
            'accept': '.pdf,application/pdf',
        })
    )
    
    def clean_pdf_file(self):
        """Valida PDF: tamanho, extensão, mime-type."""
        pass
        
    def processar_pdf(self, vendedor):
        """
        Processa PDF usando OrcamentoParserService.
        
        Returns:
            Pedido criado
        """
        pass
```

### Testes a Criar
**Arquivo:** `backend/core/tests/unit/test_upload_orcamento_form.py`

**6 Testes:**
1. `test_form_valido_com_pdf()`
2. `test_form_arquivo_muito_grande()`
3. `test_form_arquivo_nao_pdf()`
4. `test_form_pdf_parsing_error()`
5. `test_form_campos_opcionais()`
6. `test_form_validacao_logistica_embalagem()`

---

## 📋 Fase 4 - View Implementation

### Objetivo
Atualizar view para processar upload de PDF

### Arquivo a Modificar
**Arquivo:** View correspondente (identificar qual)

### Testes E2E a Criar
**Arquivo:** `backend/core/tests/e2e/test_novo_orcamento_view.py`

**7 Testes:**
1. `test_upload_pdf_sucesso_redireciona()`
2. `test_upload_pdf_exibe_erros_parsing()`
3. `test_upload_pdf_preview_dados_extraidos()`
4. `test_upload_pdf_sem_autenticacao()`
5. `test_upload_pdf_usuario_nao_vendedor()`
6. `test_upload_pdf_duplicado_exibe_mensagem()`
7. `test_upload_pdf_logging_audit()`

---

## 📋 Fase 5 - Regression Tests

### Objetivo
Garantir que nada quebrou e PDFs reais funcionam end-to-end

### Arquivo a Criar
**Arquivo:** `backend/core/tests/regression/test_pdf_parser_regression.py`

**7 Testes (1 por PDF + 1 geral):**
1. `test_pdf_30703_marcio_10_produtos()`
2. `test_pdf_30724_ali_12_produtos()`
3. `test_pdf_30722_contemner_1_produto()`
4. `test_pdf_30754_alexandre_60_produtos()`
5. `test_pdf_30737_bruna_31_produtos()`
6. `test_pdf_30734_joao_57_produtos()`
7. `test_todos_pdfs_batch()`

---

## 🎯 Checklist de Finalização

- [ ] Fase 2: Service Layer (8 testes)
- [ ] Fase 3: Form Modification (6 testes)
- [ ] Fase 4: View Implementation (7 testes)
- [ ] Fase 5: Regression Tests (7 testes)
- [ ] Todos os 57 testes passando (29 + 28)
- [ ] Commit final com documentação completa
- [ ] Atualizar README com instruções de uso

---

## 📝 Notas de Implementação

### Exceções Customizadas a Criar
```python
class DuplicatePedidoError(Exception):
    """Orçamento já existe no sistema."""
    pass

class VendedorNotFoundError(Exception):
    """Vendedor não encontrado no sistema."""
    pass

class IntegrityValidationError(Exception):
    """Falha na validação de integridade."""
    pass
```

### Dependências
- ✅ PyPDF2 (já instalado)
- ✅ pytest-django (já instalado)
- ✅ Decimal (stdlib)

### Estrutura de Diretórios Final
```
backend/
├── core/
│   ├── application/
│   │   ├── dtos/
│   │   │   └── orcamento_dtos.py ✅
│   │   └── services/
│   │       └── orcamento_parser_service.py ⏳
│   ├── infrastructure/
│   │   └── parsers/
│   │       └── pdf_orcamento_parser.py ✅
│   └── tests/
│       ├── unit/
│       │   ├── test_pdf_orcamento_parser.py ✅ (29 tests)
│       │   └── test_upload_orcamento_form.py ⏳
│       ├── integration/
│       │   └── test_orcamento_parser_service.py ⏳
│       ├── e2e/
│       │   └── test_novo_orcamento_view.py ⏳
│       └── regression/
│           └── test_pdf_parser_regression.py ⏳
```

---

## 🚀 Próximo Passo Imediato

**Comece pela Fase 2 - Service Layer:**

1. Criar `test_orcamento_parser_service.py` com 8 testes (FAIL)
2. Implementar `OrcamentoParserService` até todos passarem (PASS)
3. Commit Fase 2
4. Repetir para Fases 3, 4, 5

**Comando para iniciar:**
```bash
cd backend
touch core/tests/integration/test_orcamento_parser_service.py
touch core/application/services/orcamento_parser_service.py
```

---

**Última atualização:** 2025-10-29  
**Status:** Fase 1 completa, Fase 2-5 pendentes
