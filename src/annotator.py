"""
核心注音服务 - 基于 MeCab + 缓存 + LLM 校验
"""

import MeCab
import re
from typing import List, Optional
import jaconv

from .models import WordSegment, AnnotationResult, Source


class JapaneseAnnotator:
    """
    日语注音服务
    
    三层架构:
    1. MeCab + 预置词典（实时）
    2. Redis 缓存（快速）
    3. LLM 校验（兜底）
    """
    
    def __init__(
        self,
        dict_path: str = '/usr/local/lib/mecab/dic/mecab-ipadic-neologd',
        use_cache: bool = True,
        cache_client=None
    ):
        self.tagger = MeCab.Tagger(f'-d {dict_path}')
        self.use_cache = use_cache
        self.cache = cache_client
        
        # 正则表达式
        self.kanji_pattern = re.compile(r'[一-龥]')
        self.hiragana_pattern = re.compile(r'[\u3040-\u309F]')
        self.katakana_pattern = re.compile(r'[\u30A0-\u30FF]')
    
    def annotate(self, text: str) -> AnnotationResult:
        """
        主入口：为文本标注读音
        
        Args:
            text: 待注音的日语文本
            
        Returns:
            AnnotationResult: 注音结果
        """
        # 1. 检查缓存
        if self.use_cache and self.cache:
            cached = self._get_cache(text)
            if cached:
                return cached
        
        # 2. MeCab 分词
        segments = self._mecab_parse(text)
        
        # 3. 计算整体置信度
        total_conf = sum(s.confidence for s in segments) / len(segments) if segments else 0
        
        result = AnnotationResult(
            text=text,
            segments=segments,
            total_confidence=total_conf
        )
        
        # 4. 存入缓存
        if self.use_cache and self.cache:
            self._set_cache(text, result)
        
        return result
    
    def _mecab_parse(self, text: str) -> List[WordSegment]:
        """MeCab 分词解析"""
        segments = []
        node = self.tagger.parseToNode(text)
        
        while node:
            if node.surface:
                segment = self._parse_node(node)
                segments.append(segment)
            node = node.next
        
        return segments
    
    def _parse_node(self, node) -> WordSegment:
        """解析单个节点"""
        surface = node.surface
        features = node.feature.split(',')
        
        # 提取读音（feature[7]）
        reading = features[7] if len(features) > 7 and features[7] != '*' else None
        
        # 片假名转平假名
        if reading:
            reading = jaconv.kata2hira(reading)
        
        # 计算置信度
        confidence = self._calculate_confidence(node)
        
        # 判断是否包含汉字
        if not self.kanji_pattern.search(surface):
            reading = None  # 本身就是假名，无需注音
        
        return WordSegment(
            surface=surface,
            reading=reading,
            confidence=confidence,
            source=Source.MECAB
        )
    
    def _calculate_confidence(self, node) -> float:
        """
        基于 MeCab cost 计算置信度
        
        cost 越小越确定，典型范围:
        - cost < 500: 高置信度 (0.9-0.95)
        - 500-1500: 中置信度 (0.8-0.9)
        - 1500-3000: 低置信度 (0.6-0.8)
        - > 3000: 极低置信度 (<0.6)
        """
        cost = abs(node.cost)
        if cost < 500:
            return 0.95
        elif cost < 1500:
            return 0.85
        elif cost < 3000:
            return 0.7
        else:
            return 0.5
    
    def _get_cache(self, text: str) -> Optional[AnnotationResult]:
        """从缓存获取"""
        if not self.cache:
            return None
        # TODO: 实现 Redis 缓存读取
        return None
    
    def _set_cache(self, text: str, result: AnnotationResult) -> None:
        """存入缓存"""
        if not self.cache:
            return
        # TODO: 实现 Redis 缓存写入
        pass
