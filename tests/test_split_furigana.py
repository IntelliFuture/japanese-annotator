import pytest

from app.annotator import _split_furigana


class TestSplitFurigana:
    """Test kanji-level furigana splitting."""

    def test_kanji_kana(self):
        """食べる → 食(た) + べる"""
        result = _split_furigana("食べる", "たべる")
        assert result == [("食", "た"), ("べる", None)]

    def test_kana_kanji(self):
        """お花 → お + 花(はな)"""
        result = _split_furigana("お花", "おはな")
        assert result == [("お", None), ("花", "はな")]

    def test_kanji_kana_kanji(self):
        """受け取る → 受(う) + け + 取(と) + る"""
        result = _split_furigana("受け取る", "うけとる")
        assert result == [("受", "う"), ("け", None), ("取", "と"), ("る", None)]

    def test_kanji_kana_kanji_kana(self):
        """繰り返し → 繰(く) + り + 返(かえ) + し"""
        result = _split_furigana("繰り返し", "くりかえし")
        assert result == [("繰", "く"), ("り", None), ("返", "かえ"), ("し", None)]

    def test_kana_kanji_kana(self):
        """お見せ → お + 見(み) + せ"""
        result = _split_furigana("お見せ", "おみせ")
        assert result == [("お", None), ("見", "み"), ("せ", None)]

    def test_pure_kanji(self):
        """東京都 → whole reading applies"""
        result = _split_furigana("東京都", "とうきょうと")
        assert result == [("東京都", "とうきょうと")]

    def test_pure_kana(self):
        """ありがとう → no reading needed"""
        result = _split_furigana("ありがとう", "ありがとう")
        assert result == [("ありがとう", None)]

    def test_pure_katakana(self):
        """ラーメン → no reading needed"""
        result = _split_furigana("ラーメン", "らーめん")
        assert result == [("ラーメン", None)]

    def test_no_kanji(self):
        """Alphabetic/numeric text → no reading"""
        result = _split_furigana("hello", "hello")
        assert result == [("hello", None)]

    def test_okurigana_adjective(self):
        """高い → 高(たか) + い"""
        result = _split_furigana("高い", "たかい")
        assert result == [("高", "たか"), ("い", None)]

    def test_okurigana_verb(self):
        """走る → 走(はし) + る"""
        result = _split_furigana("走る", "はしる")
        assert result == [("走", "はし"), ("る", None)]

    def test_compound_kanji_with_okurigana(self):
        """落っこちる → 落(お) + っこちる"""
        result = _split_furigana("落っこちる", "おっこちる")
        assert result == [("落", "お"), ("っこちる", None)]


class TestSplitFuriganaArticle:
    """Tests using words from a gasoline price news article."""

    def test_sagari(self):
        """下がり → 下(さ) + がり"""
        result = _split_furigana("下がり", "さがり")
        assert result == [("下", "さ"), ("がり", None)]

    def test_sageru(self):
        """下げる → 下(さ) + げる"""
        result = _split_furigana("下げる", "さげる")
        assert result == [("下", "さ"), ("げる", None)]

    def test_sage(self):
        """下げ → 下(さ) + げ"""
        result = _split_furigana("下げ", "さげ")
        assert result == [("下", "さ"), ("げ", None)]

    def test_okane(self):
        """お金 → お + 金(かね)"""
        result = _split_furigana("お金", "おかね")
        assert result == [("お", None), ("金", "かね")]

    def test_dashi(self):
        """出し → 出(だ) + し"""
        result = _split_furigana("出し", "だし")
        assert result == [("出", "だ"), ("し", None)]

    def test_takaku(self):
        """高く → 高(たか) + く"""
        result = _split_furigana("高く", "たかく")
        assert result == [("高", "たか"), ("く", None)]

    def test_yasuku(self):
        """安く → 安(やす) + く"""
        result = _split_furigana("安く", "やすく")
        assert result == [("安", "やす"), ("く", None)]

    def test_ire(self):
        """入れ → 入(い) + れ"""
        result = _split_furigana("入れ", "いれ")
        assert result == [("入", "い"), ("れ", None)]

    def test_tasukari(self):
        """助かり → 助(たす) + かり"""
        result = _split_furigana("助かり", "たすかり")
        assert result == [("助", "たす"), ("かり", None)]

    def test_hanashi(self):
        """話して → 話(はな) + して"""
        result = _split_furigana("話して", "はなして")
        assert result == [("話", "はな"), ("して", None)]

    def test_nedan(self):
        """値段 → pure kanji, whole reading"""
        result = _split_furigana("値段", "ねだん")
        assert result == [("値段", "ねだん")]

    def test_seifu(self):
        """政府 → pure kanji"""
        result = _split_furigana("政府", "せいふ")
        assert result == [("政府", "せいふ")]

    def test_sekiyu(self):
        """石油 → pure kanji"""
        result = _split_furigana("石油", "せきゆ")
        assert result == [("石油", "せきゆ")]

    def test_kaisha(self):
        """会社 → pure kanji"""
        result = _split_furigana("会社", "かいしゃ")
        assert result == [("会社", "かいしゃ")]

    def test_hojo(self):
        """補助 → pure kanji"""
        result = _split_furigana("補助", "ほじょ")
        assert result == [("補助", "ほじょ")]

    def test_yotei(self):
        """予定 → pure kanji"""
        result = _split_furigana("予定", "よてい")
        assert result == [("予定", "よてい")]

    def test_shuukan(self):
        """週間 → pure kanji"""
        result = _split_furigana("週間", "しゅうかん")
        assert result == [("週間", "しゅうかん")]

    def test_hanbun(self):
        """半分 → pure kanji"""
        result = _split_furigana("半分", "はんぶん")
        assert result == [("半分", "はんぶん")]

    def test_sapporoshi(self):
        """札幌市 → pure kanji"""
        result = _split_furigana("札幌市", "さっぽろし")
        assert result == [("札幌市", "さっぽろし")]

    def test_gasoline_katakana(self):
        """ガソリン → pure kana, no reading"""
        result = _split_furigana("ガソリン", "がそりん")
        assert result == [("ガソリン", None)]

    def test_gasoline_stand_katakana(self):
        """ガソリンスタンド → pure kana, no reading"""
        result = _split_furigana("ガソリンスタンド", "がそりんすたんど")
        assert result == [("ガソリンスタンド", None)]

    def test_regular_katakana(self):
        """レギュラー → pure kana, no reading"""
        result = _split_furigana("レギュラー", "れぎゅらー")
        assert result == [("レギュラー", None)]


class TestSplitFuriganaSalaryArticle:
    """Tests using words from a salary/wage news article."""

    def test_hataraku(self):
        """働く → 働(はたら) + く"""
        result = _split_furigana("働く", "はたらく")
        assert result == [("働", "はたら"), ("く", None)]

    def test_hanashiai(self):
        """話し合い → 話(はな) + し + 合(あ) + い"""
        result = _split_furigana("話し合い", "はなしあい")
        assert result == [("話", "はな"), ("し", None), ("合", "あ"), ("い", None)]

    def test_kotaeru(self):
        """答える → 答(こた) + える"""
        result = _split_furigana("答える", "こたえる")
        assert result == [("答", "こた"), ("える", None)]

    def test_kotae(self):
        """答え → 答(こた) + え"""
        result = _split_furigana("答え", "こたえ")
        assert result == [("答", "こた"), ("え", None)]

    def test_ageru(self):
        """上げる → 上(あ) + げる"""
        result = _split_furigana("上げる", "あげる")
        assert result == [("上", "あ"), ("げる", None)]

    def test_ookii(self):
        """大きい → 大(おお) + きい"""
        result = _split_furigana("大きい", "おおきい")
        assert result == [("大", "おお"), ("きい", None)]

    def test_chiisai(self):
        """小さい → 小(ちい) + さい"""
        result = _split_furigana("小さい", "ちいさい")
        assert result == [("小", "ちい"), ("さい", None)]

    def test_it(self):
        """言っ → 言(い) + っ"""
        result = _split_furigana("言っ", "いっ")
        assert result == [("言", "い"), ("っ", None)]

    def test_kyuuryou(self):
        """給料 → pure kanji"""
        result = _split_furigana("給料", "きゅうりょう")
        assert result == [("給料", "きゅうりょう")]

    def test_dantai(self):
        """団体 → pure kanji"""
        result = _split_furigana("団体", "だんたい")
        assert result == [("団体", "だんたい")]

    def test_kibou(self):
        """希望 → pure kanji"""
        result = _split_furigana("希望", "きぼう")
        assert result == [("希望", "きぼう")]

    def test_heikin(self):
        """平均 → pure kanji"""
        result = _split_furigana("平均", "へいきん")
        assert result == [("平均", "へいきん")]

    def test_kikai(self):
        """機械 → pure kanji"""
        result = _split_furigana("機械", "きかい")
        assert result == [("機械", "きかい")]

    def test_news_katakana(self):
        """ニュース → pure kana, no reading"""
        result = _split_furigana("ニュース", "にゅーす")
        assert result == [("ニュース", None)]
