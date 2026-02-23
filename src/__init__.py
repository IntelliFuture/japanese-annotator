"""
Japanese Annotator - 日语分词注音服务
"""

from .annotator import JapaneseAnnotator
from .models import WordSegment, AnnotationResult

__version__ = "0.1.0"
__all__ = ["JapaneseAnnotator", "WordSegment", "AnnotationResult"]
