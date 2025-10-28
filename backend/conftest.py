#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuração global do pytest
Fase 35: Desabilita debug toolbar durante testes
"""

import os

# Fase 35: Desabilitar debug toolbar durante execução de testes
# Isso DEVE ser definido ANTES do Django ser importado
os.environ['DISABLE_DEBUG_TOOLBAR'] = '1'
