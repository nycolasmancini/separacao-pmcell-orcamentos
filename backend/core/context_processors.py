# -*- coding: utf-8 -*-
"""
Context processors para injetar variáveis em todos os templates.
"""
from django.core.cache import cache
from core.models import ThemeConfiguration


def theme_colors(request):
    """
    Context processor que injeta as cores do tema ativo em todos os templates.

    Este processor utiliza cache para evitar queries desnecessárias ao banco.
    O cache é invalidado quando o tema é atualizado.

    Returns:
        dict: Dicionário com variáveis de tema para usar nos templates
    """
    # Tentar obter do cache primeiro (performance)
    theme_vars = cache.get('theme_colors')

    if theme_vars is None:
        # Cache miss - buscar do banco
        theme = ThemeConfiguration.get_active_theme()
        theme_vars = theme.to_css_variables()

        # Adicionar também os valores hex para uso direto nos templates
        theme_vars.update({
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
        })

        # Cachear por 1 hora (será invalidado manualmente quando tema mudar)
        cache.set('theme_colors', theme_vars, 3600)

    return theme_vars
