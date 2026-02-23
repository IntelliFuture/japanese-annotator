"""
单元测试
"""

import pytest
from src.annotator import JapaneseAnnotator
from src.models import WordSegment, AnnotationResult


class TestJapaneseAnnotator:
    """注音服务测试"""
    
    @pytest.fixture
    def annotator(self):
        """创建注音器实例"""
        return JapaneseAnnotator(cache_client=None)
    
    def test_simple_sentence(self, annotator):
        """测试简单句子注音"""
        result = annotator.annotate("日本語")
        
        assert isinstance(result, AnnotationResult)
        assert result.text == "日本語"
        assert len(result.segments) > 0
        
        # 检查是否有读音
        first_word = result.segments[0]
        assert first_word.surface == "日本語"
        assert first_word.reading == "にほんご"
        assert first_word.confidence > 0.9
    
    def test_mixed_kanji_kana(self, annotator):
        """测试汉字假名混合"""
        result = annotator.annotate("日本語を学習します")
        
        surfaces = [s.surface for s in result.segments]
        assert "日本語" in surfaces
        assert "を" in surfaces
        assert "学習" in surfaces
        
        # 检查注音
        for seg in result.segments:
            if seg.surface == "日本語":
                assert seg.reading == "にほんご"
            elif seg.surface == "を":
                assert seg.reading is None  # 助词无需注音
    
    def test_pure_kana(self, annotator):
        """测试纯假名文本"""
        result = annotator.annotate("ありがとう")
        
        for seg in result.segments:
            # 纯假名无需注音
            if not annotator._contains_kanji(seg.surface):
                assert seg.reading is None or seg.reading == seg.surface
    
    def test_hiragana_conversion(self, annotator):
        """测试片假名转平假名"""
        # 片假名词汇
        result = annotator.annotate("カタカナ")
        
        # 应该转为平假名注音
        katagana_seg = next(
            (s for s in result.segments if s.surface == "カタカナ"), 
            None
        )
        if katagana_seg:
            assert katagana_seg.reading == "かたかな"
    
    def test_confidence_calculation(self, annotator):
        """测试置信度计算"""
        # 常见词：高置信度
        result = annotator.annotate("日本")
        assert all(s.confidence >= 0.9 for s in result.segments)
        
        # 整体置信度
        assert 0 < result.total_confidence <= 1
    
    def test_empty_string(self, annotator):
        """测试空字符串"""
        result = annotator.annotate("")
        assert result.text == ""
        assert len(result.segments) == 0
        assert result.total_confidence == 0
    
    def test_long_sentence(self, annotator):
        """测试长句子"""
        text = "私は毎日日本語を勉強しています"
        result = annotator.annotate(text)
        
        assert result.text == text
        assert len(result.segments) > 5
        assert result.total_confidence > 0.8
    
    def test_contains_kanji(self, annotator):
        """测试汉字检测"""
        assert annotator._contains_kanji("日本語") == True
        assert annotator._contains_kanji("にほんご") == False
        assert annotator._contains_kanji("hello") == False
        assert annotator._contains_kanji("混じり") == True


class TestWordSegment:
    """单词片段模型测试"""
    
    def test_to_ruby(self):
        """测试 ruby 标签生成"""
        seg = WordSegment(surface="日本語", reading="にほんご")
        html = seg.to_ruby()
        assert "<ruby>" in html
        assert "日本語" in html
        assert "にほんご" in html
        assert "<rt>" in html
    
    def test_is_kanji(self):
        """测试汉字判断"""
        seg_with_reading = WordSegment(surface="日本", reading="にほん")
        assert seg_with_reading.is_kanji() == True
        
        seg_no_reading = WordSegment(surface="です")
        assert seg_no_reading.is_kanji() == False
    
    def test_to_dict(self):
        """测试字典转换"""
        seg = WordSegment(
            surface="テスト",
            reading="てすと",
            confidence=0.95
        )
        d = seg.to_dict()
        assert d['surface'] == "テスト"
        assert d['reading'] == "てすと"
        assert d['confidence'] == 0.95


class TestAnnotationResult:
    """注音结果模型测试"""
    
    @pytest.fixture
    def sample_result(self):
        """创建示例结果"""
        segments = [
            WordSegment(surface="日本語", reading="にほんご"),
            WordSegment(surface="を"),
            WordSegment(surface="学習", reading="がくしゅう"),
        ]
        return AnnotationResult(
            text="日本語を学習",
            segments=segments,
            total_confidence=0.95
        )
    
    def test_get_reading(self, sample_result):
        """测试获取完整读音"""
        reading = sample_result.get_reading()
        assert "にほんご" in reading
        assert "がくしゅう" in reading
    
    def test_to_html(self, sample_result):
        """测试 HTML 生成"""
        html = sample_result.to_html()
        assert "<ruby>" in html
        assert "日本語" in html
        assert "にほんご" in html
    
    def test_to_json(self, sample_result):
        """测试 JSON 转换"""
        json_data = sample_result.to_json()
        assert json_data['text'] == "日本語を学習"
        assert 'reading' in json_data
        assert 'segments' in json_data
        assert len(json_data['segments']) == 3
