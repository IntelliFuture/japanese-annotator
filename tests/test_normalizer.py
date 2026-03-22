from app.normalizer import normalize


class TestNormalize:
    def test_empty(self):
        assert normalize("") == ""

    def test_whitespace_only(self):
        assert normalize("   ") == ""

    def test_nfkc_fullwidth_digits(self):
        assert normalize("０１２３４５６７８９") == "0123456789"

    def test_nfkc_fullwidth_alpha(self):
        assert normalize("ＡＢＣＤ") == "ABCD"

    def test_halfwidth_katakana(self):
        assert normalize("ｶﾀｶﾅ") == "カタカナ"

    def test_hyphen_variants(self):
        assert normalize("A֊B") == "A-B"
        assert normalize("A‐B") == "A-B"

    def test_long_vowel_mark(self):
        assert normalize("ラ—メン") == "ラーメン"

    def test_tilde_removal(self):
        assert normalize("〜") == ""

    def test_fullwidth_space(self):
        assert normalize("A\u3000B") == "A B"

    def test_collapse_multiple_spaces(self):
        assert normalize("A   B") == "A B"

    def test_remove_space_between_cjk(self):
        assert normalize("東京 都") == "東京都"

    def test_keep_space_between_cjk_and_latin(self):
        """Space between CJK and Latin should be preserved."""
        result = normalize("東京 ABC")
        assert " " in result

    def test_combined(self):
        """Full-width digits + CJK space + half-width katakana."""
        assert normalize("１２３　ｶﾀｶﾅ") == "123 カタカナ"

    def test_no_change_needed(self):
        assert normalize("普通のテキスト") == "普通のテキスト"

    def test_strip_whitespace(self):
        assert normalize("  hello  ") == "hello"
