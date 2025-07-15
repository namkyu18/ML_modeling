from flask import Flask, render_template, request, jsonify
import json
import plotly
import plotly.graph_objects as go
from stock_analyzer import StockAnalyzer

app = Flask(__name__)
analyzer = StockAnalyzer()

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/sector-overview')
def sector_overview():
    """섹터별 분석 현황"""
    sector_data = analyzer.get_sector_overview()
    return render_template('sector_overview.html', sectors=sector_data)

@app.route('/stock-analysis')
def stock_analysis():
    """개별 주식 분석 페이지"""
    return render_template('stock_analysis.html')

@app.route('/compare-stocks')
def compare_stocks():
    """주식 비교 분석 페이지"""
    return render_template('compare_stocks.html')

@app.route('/api/analyze-stock', methods=['POST'])
def analyze_stock():
    """주식 분석 API"""
    data = request.get_json()
    symbol = data.get('symbol', '').upper()
    period = data.get('period', '1y')
    
    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400
    
    try:
        # 주식 데이터 가져오기
        stock_data = analyzer.get_stock_data(symbol, period)
        if stock_data is None:
            return jsonify({'error': f'Cannot fetch data for {symbol}'}), 404
        
        # 기술적 지표 계산
        stock_data = analyzer.calculate_technical_indicators(stock_data)
        if stock_data is None:
            return jsonify({'error': 'Insufficient data for analysis'}), 400
        
        # 매매 신호 생성
        signals = analyzer.generate_trading_signals(stock_data, symbol)
        
        # 기본 정보 가져오기
        stock_info = analyzer.get_stock_info(symbol)
        
        # 차트 생성
        chart = analyzer.create_chart(stock_data, symbol)
        chart_json = json.dumps(chart, cls=plotly.utils.PlotlyJSONEncoder)
        
        # 최근 데이터
        latest_data = stock_data.iloc[-1]
        
        result = {
            'symbol': symbol,
            'company_name': stock_info.get('longName', symbol) if stock_info else symbol,
            'sector': stock_info.get('sector', 'N/A') if stock_info else 'N/A',
            'current_price': float(latest_data['Close']),
            'change_pct': float(((latest_data['Close'] - stock_data['Close'].iloc[-2]) / stock_data['Close'].iloc[-2]) * 100),
            'volume': int(latest_data['Volume']),
            'volume_ratio': float(signals['volume_ratio']),
            'signal': signals['signal'],
            'strength': signals['strength'],
            'buy_signals': signals['buy_signals'],
            'sell_signals': signals['sell_signals'],
            'reasons': signals['reasons'],
            'rsi': float(signals['rsi']),
            'macd': float(signals['macd']),
            'sma_20': float(latest_data['SMA_20']),
            'sma_50': float(latest_data['SMA_50']),
            'sma_200': float(latest_data['SMA_200']),
            'bb_upper': float(latest_data['BB_Upper']),
            'bb_lower': float(latest_data['BB_Lower']),
            'chart': chart_json
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare-stocks', methods=['POST'])
def api_compare_stocks():
    """주식 비교 분석 API"""
    data = request.get_json()
    symbols = data.get('symbols', [])
    period = data.get('period', '6m')
    
    if not symbols:
        return jsonify({'error': 'Symbols are required'}), 400
    
    try:
        # 심볼들을 대문자로 변환
        symbols = [s.upper() for s in symbols]
        
        # 비교 분석 수행
        comparison_data = analyzer.compare_stocks(symbols, period)
        
        # 결과 정리
        results = []
        for symbol, data in comparison_data.items():
            results.append({
                'symbol': symbol,
                'current_price': float(data['current_price']),
                'change_pct': float(data['change_pct']),
                'signal': data['signal'],
                'strength': data['strength'],
                'rsi': float(data['rsi']),
                'volume_ratio': float(data['volume_ratio'])
            })
        
        # 신호별로 정렬
        signal_order = {'BUY': 1, 'HOLD': 2, 'SELL': 3}
        results.sort(key=lambda x: (signal_order.get(x['signal'], 2), -x['strength']))
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sector-data')
def api_sector_data():
    """섹터 데이터 API"""
    try:
        sector_data = analyzer.get_sector_overview()
        return jsonify(sector_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-stock')
def search_stock():
    """주식 검색 API"""
    query = request.args.get('q', '').upper()
    
    # 간단한 검색 구현 (실제로는 더 복잡한 검색 로직이 필요)
    suggestions = []
    
    # 섹터 ETF 검색
    for symbol, info in analyzer.sector_etfs.items():
        if query in symbol or query in info['name'].upper():
            suggestions.append({
                'symbol': symbol,
                'name': f"{info['name']} ETF",
                'type': 'ETF'
            })
    
    # 개별 주식 검색 (주요 종목들)
    major_stocks = [
        ('AAPL', 'Apple Inc.'),
        ('MSFT', 'Microsoft Corporation'),
        ('GOOGL', 'Alphabet Inc.'),
        ('AMZN', 'Amazon.com Inc.'),
        ('TSLA', 'Tesla Inc.'),
        ('META', 'Meta Platforms Inc.'),
        ('NVDA', 'NVIDIA Corporation'),
        ('JPM', 'JPMorgan Chase & Co.'),
        ('JNJ', 'Johnson & Johnson'),
        ('V', 'Visa Inc.')
    ]
    
    for symbol, name in major_stocks:
        if query in symbol or query in name.upper():
            suggestions.append({
                'symbol': symbol,
                'name': name,
                'type': 'Stock'
            })
    
    return jsonify(suggestions[:10])  # 최대 10개 제안

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)