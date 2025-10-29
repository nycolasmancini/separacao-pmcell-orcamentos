# -*- coding: utf-8 -*-
"""
Testes unitários para validar existência e estrutura das classes CSS de animação.

Este módulo testa:
1. Existência de variáveis CSS configuráveis
2. Definição de keyframes necessários
3. Existência de classes de animação
"""

import pytest
import os
import re
from pathlib import Path


class TestItemAnimationsCSS:
    """Testes para validar estrutura CSS de animações de itens."""

    @pytest.fixture
    def animations_css_path(self):
        """Retorna o caminho para o arquivo animations.css"""
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        css_path = base_dir / 'static' / 'css' / 'animations.css'
        return css_path

    @pytest.fixture
    def animations_css_content(self, animations_css_path):
        """Lê o conteúdo do arquivo animations.css"""
        assert animations_css_path.exists(), f"Arquivo {animations_css_path} não encontrado"
        with open(animations_css_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_arquivo_animations_css_existe(self, animations_css_path):
        """Testa se o arquivo animations.css existe"""
        assert animations_css_path.exists(), \
            f"Arquivo {animations_css_path} não encontrado"

    def test_variavel_css_animation_speed_fast_existe(self, animations_css_content):
        """Testa se a variável CSS --animation-speed-fast está definida"""
        assert '--animation-speed-fast' in animations_css_content, \
            "Variável CSS --animation-speed-fast não encontrada"

        # Validar que o valor está entre 200-300ms
        pattern = r'--animation-speed-fast:\s*(2\d{2}|300)ms'
        assert re.search(pattern, animations_css_content), \
            "Variável --animation-speed-fast deve estar entre 200-300ms"

    def test_keyframe_item_fade_out_existe(self, animations_css_content):
        """Testa se o keyframe itemFadeOut está definido"""
        assert '@keyframes itemFadeOut' in animations_css_content or \
               '@keyframes item-fade-out' in animations_css_content, \
            "Keyframe itemFadeOut não encontrado"

        # Validar que tem transições de opacity
        assert 'opacity' in animations_css_content, \
            "Keyframe itemFadeOut deve incluir transições de opacity"

    def test_keyframe_item_slide_in_existe(self, animations_css_content):
        """Testa se o keyframe itemSlideIn está definido"""
        assert '@keyframes itemSlideIn' in animations_css_content or \
               '@keyframes item-slide-in' in animations_css_content, \
            "Keyframe itemSlideIn não encontrado"

    def test_classe_item_fade_out_existe(self, animations_css_content):
        """Testa se a classe .item-fade-out está definida"""
        assert '.item-fade-out' in animations_css_content, \
            "Classe .item-fade-out não encontrada"

        # Validar que a classe usa animation
        fade_out_section = self._extract_css_rule(animations_css_content, '.item-fade-out')
        assert 'animation' in fade_out_section, \
            "Classe .item-fade-out deve ter propriedade animation"

    def test_classe_item_slide_in_existe(self, animations_css_content):
        """Testa se a classe .item-slide-in está definida"""
        assert '.item-slide-in' in animations_css_content, \
            "Classe .item-slide-in não encontrada"

        # Validar que a classe usa animation
        slide_in_section = self._extract_css_rule(animations_css_content, '.item-slide-in')
        assert 'animation' in slide_in_section, \
            "Classe .item-slide-in deve ter propriedade animation"

    def test_item_container_tem_transicao(self, animations_css_content):
        """Testa se .item-container tem transição CSS para movimento fluido"""
        assert '.item-container' in animations_css_content, \
            "Classe .item-container não encontrada"

        # Validar que tem transition
        container_section = self._extract_css_rule(animations_css_content, '.item-container')
        assert 'transition' in container_section, \
            "Classe .item-container deve ter propriedade transition"

    def test_prefers_reduced_motion_existe(self, animations_css_content):
        """Testa se há suporte para prefers-reduced-motion"""
        assert '@media (prefers-reduced-motion' in animations_css_content, \
            "Media query @media (prefers-reduced-motion) não encontrada"

    def test_animacoes_tem_forwards_ou_backwards(self, animations_css_content):
        """Testa se animações têm fill-mode definido (forwards/backwards)"""
        # Extrair regras de animation
        animation_rules = re.findall(r'animation:([^;]+);', animations_css_content)

        # Deve ter pelo menos 2 regras de animation (fade-out e slide-in)
        assert len(animation_rules) >= 2, \
            "Deve haver pelo menos 2 regras de animation definidas"

        # Pelo menos uma deve ter 'forwards' ou 'both'
        has_fill_mode = any('forwards' in rule or 'both' in rule for rule in animation_rules)
        assert has_fill_mode, \
            "Pelo menos uma animation deve ter fill-mode 'forwards' ou 'both'"

    def test_ease_timing_function_presente(self, animations_css_content):
        """Testa se há uso de timing functions suaves (ease, ease-out, etc)"""
        timing_functions = ['ease', 'ease-out', 'ease-in-out', 'cubic-bezier']

        has_timing = any(func in animations_css_content for func in timing_functions)
        assert has_timing, \
            "Deve haver pelo menos uma timing function suave (ease, ease-out, etc)"

    def test_transform_usado_em_animacoes(self, animations_css_content):
        """Testa se animações usam transform (melhor performance que top/left)"""
        # Keyframes devem usar transform ao invés de position
        assert 'transform' in animations_css_content, \
            "Animações devem usar 'transform' para melhor performance"

    def _extract_css_rule(self, css_content: str, selector: str) -> str:
        """
        Extrai conteúdo de uma regra CSS específica.

        Args:
            css_content: Conteúdo completo do CSS
            selector: Seletor CSS a buscar

        Returns:
            Conteúdo da regra CSS (entre { e })
        """
        pattern = rf'{re.escape(selector)}\s*\{{([^}}]+)\}}'
        match = re.search(pattern, css_content, re.DOTALL)

        if match:
            return match.group(1)
        return ""


class TestAnimationPerformance:
    """Testes para validar boas práticas de performance em animações"""

    def test_animacoes_nao_usam_width_height(self):
        """
        Testa se animações NÃO usam width/height diretamente
        (causa reflow - mal para performance)
        """
        animations_css_path = Path(__file__).resolve().parent.parent.parent.parent / \
                              'static' / 'css' / 'animations.css'

        with open(animations_css_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extrair keyframes
        keyframes = re.findall(r'@keyframes [^{]+\{([^}]+)\}', content, re.DOTALL)

        for keyframe in keyframes:
            # Animações não devem mudar width/height diretamente (causa reflow)
            # OK: max-height, scale
            # NOT OK: height, width
            assert 'height:' not in keyframe or 'max-height' in keyframe, \
                "Keyframes não devem animar 'height' diretamente (use max-height ou scale)"

            assert 'width:' not in keyframe or 'max-width' in keyframe, \
                "Keyframes não devem animar 'width' diretamente (use max-width ou scale)"

    def test_animacoes_usam_will_change_ou_transform(self):
        """
        Testa se animações usam 'will-change' ou 'transform' para otimização
        """
        animations_css_path = Path(__file__).resolve().parent.parent.parent.parent / \
                              'static' / 'css' / 'animations.css'

        with open(animations_css_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Deve ter pelo menos um 'transform' ou 'will-change'
        has_optimization = 'transform' in content or 'will-change' in content
        assert has_optimization, \
            "Animações devem usar 'transform' ou 'will-change' para otimização"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
