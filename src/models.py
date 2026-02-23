"""
数据模型定义
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class Source(Enum):
    """注音来源"""
    MECAB = "mecab"
    CACHE = "cache"
    LLM = "llm"
    MANUAL = "manual"


@dataclass
class WordSegment:
    """
    单词片段，用于存放汉字和读音对
    
    示例:
        食べる → [WordSegment("食", "た"), WordSegment("べる")]
    """
    surface: str                    # 表层文字
    reading: Optional[str] = None   # 读音（假名），None 表示本身就是假名
    confidence: float = 1.0         # 置信度
    source: Source = Source.MECAB   # 来源
    
    def is_kanji(self) -> bool:
        """是否包含汉字"""
        return self.reading is not None
    
    def to_ruby(self) -> str:
        """生成 HTML ruby 标签"""
        if self.is_kanji():
            return f'<ruby>{self.surface}<rt>{self.reading}</rt></ruby>'
        return self.surface
    
    def to_dict(self) -> dict:
        """转为字典"""
        return {
            'surface': self.surface,
            'reading': self.reading,
            'confidence': self.confidence,
            'source': self.source.value
        }


@dataclass
class AnnotationResult:
    """注音结果"""
    text: str                       # 原始文本
    segments: List[WordSegment]     # 分词结果
    total_confidence: float         # 整体置信度
    
    def get_reading(self) -> str:
        """获取完整读音"""
        return ''.join(
            s.reading or s.surface for s in self.segments
        )
    
    def to_html(self) -> str:
        """生成 HTML"""
        return ''.join(s.to_ruby() for s in self.segments)
    
    def to_json(self) -> dict:
        """转为 JSON"""
        return {
            'text': self.text,
            'reading': self.get_reading(),
            'confidence': self.total_confidence,
            'segments': [s.to_dict() for s in self.segments]
        }
