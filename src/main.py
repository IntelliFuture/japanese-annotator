"""
Flask API 入口
"""

from flask import Flask, request, jsonify
from .annotator import JapaneseAnnotator

app = Flask(__name__)
annotator = JapaneseAnnotator()


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'version': '0.1.0'})


@app.route('/annotate', methods=['POST'])
def annotate():
    """
    注音 API
    
    Request:
        POST /annotate
        Content-Type: application/json
        
        {
            "text": "日本語を学習します"
        }
    
    Response:
        {
            "text": "日本語を学習します",
            "reading": "にほんごをがくしゅうします",
            "confidence": 0.95,
            "segments": [...]
        }
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text field'}), 400
    
    text = data['text']
    result = annotator.annotate(text)
    
    return jsonify(result.to_json())


@app.route('/annotate/html', methods=['POST'])
def annotate_html():
    """
    返回 HTML ruby 标签格式
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text field'}), 400
    
    text = data['text']
    result = annotator.annotate(text)
    
    return jsonify({
        'text': text,
        'html': result.to_html()
    })


def main():
    """开发模式运行"""
    app.run(host='0.0.0.0', port=8080, debug=True)


if __name__ == '__main__':
    main()
