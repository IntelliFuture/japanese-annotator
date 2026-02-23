"""
核心注音服务 - 基于 fugashi (MeCab wrapper) + 缓存 + LLM 校验
"""

from typing import List, Optional
import jaconv
from fugashi import Tagger

from .models import WordSegment, AnnotationResult, Source


class JapaneseAnnotator:
    """
    日语注音服务 - fugashi 实现
    
    三层架构:
    1. fugashi + UniDic（实时）
    2. Redis 缓存（快速）
    3. LLM 校验（兜底）
    """
    
    def __init__(self, cache_client=None):
        """
        初始化注音服务
        
        Args:
            cache_client: Redis 客户端（可选）
        """
        # 使用 UniDic-lite（轻量版，快速启动）
        # 如需完整版：Tagger('-d /path/to/unidic')
        self.tagger = Tagger()
        self.cache = cache_client
    
    def annotate(self, text: str) -> AnnotationResult:
        """
        为文本标注读音
        
        Args:
            text: 待注音的日语文本
            
        Returns:
            AnnotationResult: 注音结果
        """
        # 1. 检查缓存
        if self.cache:
            cached = self._get_cache(text)
            if cached:
                return cached
        
        # 2. fugashi 分词注音
        segments = self._fugashi_parse(text)
        
        # 3. 计算整体置信度
        total_conf = (
            sum(s.confidence for s in segments) / len(segments)
            if segments else 0
        )
        
        result = AnnotationResult(
            text=text,
            segments=segments,
            total_confidence=total_conf
        )
        
        # 4. 存入缓存
        if self.cache:
            self._set_cache(text, result)
        
        return result
    
    def _fugashi_parse(self, text: str) -> List[WordSegment]:
        """
        使用 fugashi 解析文本
        
        fugashi 特点：
        - word.surface: 表层文字
        - word.feature.pron: 读音（片假名）
        - word.pos: 词性
        - word.feature.lemma: 词干
        """
        segments = []
        
        for word in self.tagger(text):
            surface = word.surface
            
            # 获取读音（UniDic 提供）
            reading = None
            if hasattr(word.feature, 'pron') and word.feature.pron:
                # 片假名转平假名
                reading = jaconv.kata2hira(word.feature.pron)
            
            # 判断是否包含汉字
            # 如果读音和表层相同，说明是假名，无需注音
            if reading == surface or not self._contains_kanji(surface):
                reading = None
            
            # 计算置信度
            confidence = self._calculate_confidence(word, reading)
            
            segments.append(WordSegment(
                surface=surface,
                reading=reading,
                confidence=confidence,
                source=Source.MECAB
            ))
        
        return segments
    
    def _contains_kanji(self, text: str) -> bool:
        """判断是否包含汉字"""
        # CJK 统一汉字范围
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def _calculate_confidence(self, word, reading: Optional[str]) -> float:
        """
        计算置信度
        
        fugashi/UniDic 质量较高，默认高置信度
        仅在以下情况降低置信度：
        - 无读音信息
        - 未登录词特征
        """
        # 有读音的汉字词：高置信度
        if reading and self._contains_kanji(word.surface):
            return 0.92
        
        # 假名：无需注音，高置信度
        if not self._contains_kanji(word.surface):
            return 0.95
        
        # 无读音信息：低置信度（需 LLM 校验）
        return 0.6
    
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
