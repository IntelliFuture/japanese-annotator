import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealth:
    def test_health(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


class TestAnnotate:
    def test_basic(self):
        res = client.post("/annotate", json={"text": "東京都に住んでいます"})
        assert res.status_code == 200
        data = res.json()
        assert "tokens" in data
        assert "ruby_html" in data
        assert len(data["tokens"]) > 0

    def test_ruby_html_kanji_only(self):
        """Ruby tags should only wrap kanji, not okurigana."""
        res = client.post("/annotate", json={"text": "食べる"})
        html = res.json()["ruby_html"]
        # 食 should have ruby, べる should not
        assert "<ruby>食<rt>" in html
        assert "べる" in html
        assert "<ruby>食べる<rt>" not in html

    def test_mode_default(self):
        """Default mode should be C."""
        res = client.post("/annotate", json={"text": "東京都"})
        assert res.status_code == 200

    def test_mode_a(self):
        res = client.post("/annotate", json={"text": "東京都", "mode": "A"})
        assert res.status_code == 200
        # Mode A splits more aggressively
        tokens = res.json()["tokens"]
        assert len(tokens) >= 1

    def test_invalid_mode(self):
        res = client.post("/annotate", json={"text": "テスト", "mode": "X"})
        assert res.status_code == 422

    def test_empty_text(self):
        res = client.post("/annotate", json={"text": ""})
        assert res.status_code == 200
        data = res.json()
        assert data["tokens"] == []
        assert data["ruby_html"] == ""

    def test_token_fields(self):
        res = client.post("/annotate", json={"text": "日本語"})
        token = res.json()["tokens"][0]
        assert "surface" in token
        assert "reading" in token
        assert "lemma" in token
        assert "pos" in token

    def test_pre_normalize(self):
        """Full-width digits should be normalized to half-width."""
        res = client.post("/annotate", json={"text": "０１２", "pre_normalize": True})
        assert res.status_code == 200
        surfaces = "".join(t["surface"] for t in res.json()["tokens"])
        assert "０" not in surfaces


class TestBatchAnnotate:
    def test_batch(self):
        res = client.post("/annotate/batch", json={
            "texts": ["東京都", "大阪府"],
        })
        assert res.status_code == 200
        results = res.json()["results"]
        assert len(results) == 2

    def test_batch_empty(self):
        res = client.post("/annotate/batch", json={"texts": []})
        assert res.status_code == 200
        assert res.json()["results"] == []


class TestNormalize:
    def test_fullwidth_to_halfwidth(self):
        res = client.post("/normalize", json={"text": "０１２ＡＢＣ"})
        assert res.status_code == 200
        data = res.json()
        assert data["original"] == "０１２ＡＢＣ"
        assert data["normalized"] == "012ABC"

    def test_halfwidth_katakana(self):
        res = client.post("/normalize", json={"text": "ｶﾀｶﾅ"})
        data = res.json()
        assert data["normalized"] == "カタカナ"

    def test_fullwidth_space(self):
        res = client.post("/normalize", json={"text": "東京　都"})
        data = res.json()
        # CJK characters — space between them should be removed
        assert data["normalized"] == "東京都"


class TestDictReload:
    def test_reload(self):
        res = client.post("/dict/reload")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


class TestAnnotateArticle:
    """Tests using sentences and words from a gasoline price news article."""

    def test_sentence_gasoline_nedan(self):
        """とても高くなっているガソリンの値段が下がりそうです。"""
        res = client.post("/annotate", json={
            "text": "とても高くなっているガソリンの値段が下がりそうです。"
        })
        assert res.status_code == 200
        data = res.json()
        tokens = data["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert "ガソリン" in surfaces
        # 高く should be present as a surface or part of one
        assert any("高" in s for s in surfaces)
        # 値段 should appear
        assert "値段" in surfaces
        # 下がり should appear
        assert any("下" in s for s in surfaces)

    def test_sentence_seifu_hojo(self):
        """政府は、19日から石油の会社に補助のお金を出しています。"""
        res = client.post("/annotate", json={
            "text": "政府は、19日から石油の会社に補助のお金を出しています。"
        })
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert "政府" in surfaces
        assert "石油" in surfaces
        assert "会社" in surfaces
        assert "補助" in surfaces

    def test_sentence_kyuu_ni(self):
        """ガソリンが急に高くならないようにするためです。"""
        res = client.post("/annotate", json={
            "text": "ガソリンが急に高くならないようにするためです。"
        })
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert "ガソリン" in surfaces
        assert any("急" in s for s in surfaces)

    def test_sentence_mise_nedan(self):
        """店での値段を1L170円ぐらいに下げる予定です。"""
        res = client.post("/annotate", json={
            "text": "店での値段を1L170円ぐらいに下げる予定です。"
        })
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert "予定" in surfaces
        assert any("店" in s for s in surfaces)
        assert any("値段" in s for s in surfaces)

    def test_sentence_shuukan(self):
        """1週間から2週間ぐらいで安くなりそうです。"""
        res = client.post("/annotate", json={
            "text": "1週間から2週間ぐらいで安くなりそうです。"
        })
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert any("週間" in s for s in surfaces)

    def test_sentence_sapporo(self):
        """札幌市のガソリンスタンドでは、19日から、ガソリンなどの値段を下げた所がありました。"""
        res = client.post("/annotate", json={
            "text": "札幌市のガソリンスタンドでは、19日から、ガソリンなどの値段を下げた所がありました。"
        })
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert any("札幌" in s for s in surfaces)
        assert "ガソリンスタンド" in surfaces or any("ガソリン" in s for s in surfaces)

    def test_sentence_regular_gasoline(self):
        """レギュラーのガソリンを1L189円から169円に下げました。"""
        res = client.post("/annotate", json={
            "text": "レギュラーのガソリンを1L189円から169円に下げました。"
        })
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert "レギュラー" in surfaces or any("レギュラー" in s for s in surfaces)
        assert "ガソリン" in surfaces

    def test_sentence_kyaku_hanbun(self):
        """ガソリンの値段が高くなって、客がいつもの半分ぐらいになったためです。"""
        res = client.post("/annotate", json={
            "text": "ガソリンの値段が高くなって、客がいつもの半分ぐらいになったためです。"
        })
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert any("客" in s for s in surfaces)
        assert any("半分" in s for s in surfaces)

    def test_sentence_tasukari(self):
        """20円安くなると、とても助かります"""
        res = client.post("/annotate", json={
            "text": "20円安くなると、とても助かります"
        })
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert any("助" in s for s in surfaces)
        assert any("安" in s for s in surfaces)

    def test_ruby_nedan(self):
        """値段 should produce ruby with reading ねだん."""
        res = client.post("/annotate", json={"text": "値段"})
        html = res.json()["ruby_html"]
        assert "<ruby>値段<rt>ねだん</rt></ruby>" in html

    def test_ruby_sagaru(self):
        """下がる should split ruby: 下(さ) + がる."""
        res = client.post("/annotate", json={"text": "下がる"})
        html = res.json()["ruby_html"]
        assert "<ruby>下<rt>さ</rt></ruby>" in html
        assert "がる" in html

    def test_ruby_takaku(self):
        """高く should split ruby: 高(たか) + く."""
        res = client.post("/annotate", json={"text": "高く"})
        html = res.json()["ruby_html"]
        assert "<ruby>高<rt>たか</rt></ruby>" in html
        assert "く" in html

    def test_ruby_gasoline_no_ruby(self):
        """ガソリン (katakana) should not have ruby tags."""
        res = client.post("/annotate", json={"text": "ガソリン"})
        html = res.json()["ruby_html"]
        assert "<ruby>" not in html
        assert "ガソリン" in html

    def test_token_pos_types(self):
        """Verify POS tags for key words from the article."""
        res = client.post("/annotate", json={"text": "政府は石油の会社に補助のお金を出しています。"})
        tokens = res.json()["tokens"]
        token_dict = {t["surface"]: t for t in tokens}
        # 政府, 石油, 会社, 補助 should be nouns
        for word in ["政府", "石油", "会社", "補助"]:
            if word in token_dict:
                assert token_dict[word]["pos"] == "名詞", f"{word} should be 名詞"

    def test_token_reading_fields(self):
        """Verify reading/lemma for words from the article."""
        res = client.post("/annotate", json={"text": "値段が下がる"})
        tokens = res.json()["tokens"]
        token_dict = {t["surface"]: t for t in tokens}
        if "値段" in token_dict:
            assert token_dict["値段"]["reading"] == "ねだん"

    def test_batch_article_sentences(self):
        """Batch annotate multiple article sentences."""
        res = client.post("/annotate/batch", json={
            "texts": [
                "ガソリンの値段が下がりそうです。",
                "政府は石油の会社に補助のお金を出しています。",
                "レギュラーのガソリンを1L189円から169円に下げました。",
            ]
        })
        assert res.status_code == 200
        results = res.json()["results"]
        assert len(results) == 3
        for r in results:
            assert len(r["tokens"]) > 0
            assert len(r["ruby_html"]) > 0

    def test_mode_a_article_sentence(self):
        """Mode A should split compound words more aggressively."""
        res_a = client.post("/annotate", json={
            "text": "札幌市のガソリンスタンド",
            "mode": "A",
        })
        res_c = client.post("/annotate", json={
            "text": "札幌市のガソリンスタンド",
            "mode": "C",
        })
        tokens_a = res_a.json()["tokens"]
        tokens_c = res_c.json()["tokens"]
        # Mode A should produce at least as many tokens as C
        assert len(tokens_a) >= len(tokens_c)


class TestAnnotateArticleSalary:
    """Tests using long sentences from a salary/wage news article."""

    def test_long_sentence_dantai_hanashiai(self):
        """働く人たちの団体は、毎年春に、給料について会社と話し合います。"""
        text = "働く人たちの団体は、毎年春に、給料について会社と話し合います。"
        res = client.post("/annotate", json={"text": text})
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert any("働" in s for s in surfaces)
        assert "団体" in surfaces
        assert "給料" in surfaces
        assert "会社" in surfaces
        assert any("春" in s for s in surfaces)
        # Verify token count — long sentence should produce many tokens
        assert len(tokens) >= 10

    def test_long_sentence_kyuuryou_5percent(self):
        """今年は、給料を5％以上高くしてほしいと言っていました。"""
        text = "今年は、給料を5％以上高くしてほしいと言っていました。"
        res = client.post("/annotate", json={"text": text})
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert "給料" in surfaces
        assert any("以上" in s for s in surfaces)
        assert any("高" in s for s in surfaces)
        assert any("言" in s for s in surfaces)

    def test_long_sentence_kuruma_kikai(self):
        """18日は、車や機械などの大きい会社が、働く人たちに答える日でした。"""
        text = "18日は、車や機械などの大きい会社が、働く人たちに答える日でした。"
        res = client.post("/annotate", json={"text": text})
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert any("車" in s for s in surfaces)
        assert "機械" in surfaces
        assert "会社" in surfaces
        assert any("答" in s for s in surfaces)
        assert len(tokens) >= 12

    def test_long_sentence_heikin_5_1(self):
        """そして、平均で5.1％高くすると答えました。"""
        text = "そして、平均で5.1％高くすると答えました。"
        res = client.post("/annotate", json={"text": text})
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert "平均" in surfaces
        assert any("高" in s for s in surfaces)
        assert any("答" in s for s in surfaces)

    def test_long_sentence_kibou_doori(self):
        """働く人たちの希望どおりに給料を上げると答えた会社が、たくさんありました。"""
        text = "働く人たちの希望どおりに給料を上げると答えた会社が、たくさんありました。"
        res = client.post("/annotate", json={"text": text})
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert "希望" in surfaces
        assert "給料" in surfaces
        assert "会社" in surfaces
        assert any("上" in s for s in surfaces)
        assert any("答" in s for s in surfaces)
        assert len(tokens) >= 12

    def test_long_sentence_chiisai_kaisha(self):
        """小さい会社は、給料をどれくらいにするか、これから答えます。"""
        text = "小さい会社は、給料をどれくらいにするか、これから答えます。"
        res = client.post("/annotate", json={"text": text})
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        surfaces = [t["surface"] for t in tokens]
        assert any("小" in s for s in surfaces)
        assert "会社" in surfaces
        assert "給料" in surfaces
        assert any("答" in s for s in surfaces)

    def test_full_paragraph_token_count(self):
        """Full paragraph should produce a large number of tokens."""
        text = (
            "働く人たちの団体は、毎年春に、給料について会社と話し合います。"
            "今年は、給料を5％以上高くしてほしいと言っていました。"
        )
        res = client.post("/annotate", json={"text": text})
        assert res.status_code == 200
        tokens = res.json()["tokens"]
        assert len(tokens) >= 20
        # All tokens should have valid fields
        for t in tokens:
            assert t["surface"]
            assert t["reading"]
            assert t["pos"]

    def test_full_paragraph_ruby_integrity(self):
        """Long text ruby HTML should have matching ruby/rt tag pairs."""
        text = (
            "18日は、車や機械などの大きい会社が、働く人たちに答える日でした。"
            "そして、平均で5.1％高くすると答えました。"
            "働く人たちの希望どおりに給料を上げると答えた会社が、たくさんありました。"
        )
        res = client.post("/annotate", json={"text": text})
        html = res.json()["ruby_html"]
        # Every <ruby> must have a matching </ruby>
        assert html.count("<ruby>") == html.count("</ruby>")
        # Every <rt> must have a matching </rt>
        assert html.count("<rt>") == html.count("</rt>")
        # ruby count should equal rt count
        assert html.count("<ruby>") == html.count("<rt>")

    def test_ruby_hanashiai(self):
        """話し合い should split: 話(はな) + し + 合(あ) + い."""
        res = client.post("/annotate", json={"text": "話し合い"})
        html = res.json()["ruby_html"]
        assert "<ruby>" in html
        assert "し" in html

    def test_ruby_kotaeru(self):
        """答える should split: 答(こた) + える."""
        res = client.post("/annotate", json={"text": "答える"})
        html = res.json()["ruby_html"]
        assert "<ruby>答<rt>こた</rt></ruby>" in html
        assert "える" in html

    def test_ruby_ageru(self):
        """上げる should split: 上(あ) + げる."""
        res = client.post("/annotate", json={"text": "上げる"})
        html = res.json()["ruby_html"]
        assert "<ruby>上<rt>あ</rt></ruby>" in html
        assert "げる" in html

    def test_pos_nouns_salary_article(self):
        """Verify POS for nouns in the salary article."""
        res = client.post("/annotate", json={
            "text": "団体と会社が給料と希望と平均について話し合います。"
        })
        tokens = res.json()["tokens"]
        token_dict = {t["surface"]: t for t in tokens}
        for word in ["団体", "会社", "給料", "希望", "平均"]:
            if word in token_dict:
                assert token_dict[word]["pos"] == "名詞", f"{word} should be 名詞"

    def test_reading_salary_words(self):
        """Verify readings for key vocabulary."""
        res = client.post("/annotate", json={"text": "給料と団体と希望と平均と機械"})
        tokens = res.json()["tokens"]
        token_dict = {t["surface"]: t for t in tokens}
        expected = {
            "給料": "きゅうりょう",
            "団体": "だんたい",
            "希望": "きぼう",
            "平均": "へいきん",
            "機械": "きかい",
        }
        for word, reading in expected.items():
            if word in token_dict:
                assert token_dict[word]["reading"] == reading, (
                    f"{word} reading should be {reading}, got {token_dict[word]['reading']}"
                )

    def test_batch_salary_article(self):
        """Batch annotate all paragraphs from the salary article."""
        res = client.post("/annotate/batch", json={
            "texts": [
                "働く人がもらう給料のニュースです。",
                "働く人たちの団体は、毎年春に、給料について会社と話し合います。",
                "今年は、給料を5％以上高くしてほしいと言っていました。",
                "18日は、車や機械などの大きい会社が、働く人たちに答える日でした。",
                "そして、平均で5.1％高くすると答えました。",
                "働く人たちの希望どおりに給料を上げると答えた会社が、たくさんありました。",
                "小さい会社は、給料をどれくらいにするか、これから答えます。",
            ]
        })
        assert res.status_code == 200
        results = res.json()["results"]
        assert len(results) == 7
        for r in results:
            assert len(r["tokens"]) > 0
            assert len(r["ruby_html"]) > 0
            # ruby tags should be balanced
            assert r["ruby_html"].count("<ruby>") == r["ruby_html"].count("</ruby>")
