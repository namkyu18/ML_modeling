import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import ta
from datetime import datetime, timedelta

class StockAnalyzer:
    def __init__(self):
        # 사용자가 관심있어하는 섹터 ETF들
        self.sector_etfs = {
            'XLC': {'name': 'Communication', 'top_holdings': ['META', 'GOOGL', 'NFLX', 'EA', 'TTWO', 'T', 'DIS', 'CMCSA']},
            'XLY': {'name': 'Consumer Discretionary', 'top_holdings': ['AMZN', 'TSLA', 'HD', 'BKNG', 'MCD', 'TJX', 'LOW']},
            'XLP': {'name': 'Consumer Staples', 'top_holdings': ['COST', 'WMT', 'PG', 'PM', 'KO', 'MDLZ']},
            'XLE': {'name': 'Energy', 'top_holdings': ['XOM', 'CVX', 'COP', 'WMB', 'EOG']},
            'XLF': {'name': 'Financials', 'top_holdings': ['BRK-B', 'JPM', 'V', 'MA', 'BAC']},
            'XLV': {'name': 'Healthcare', 'top_holdings': ['LLY', 'JNJ', 'ABBV', 'UNH', 'ABT', 'MRK', 'ISRG', 'BSX', 'TMO', 'AMGN']},
            'XLI': {'name': 'Industrials', 'top_holdings': ['GE', 'RTX', 'UBER', 'CAT', 'BA', 'HON', 'GEV']},
            'XLB': {'name': 'Materials', 'top_holdings': ['LIN', 'SHW', 'ECL', 'NEM', 'CTVA', 'APD']},
            'XLRE': {'name': 'Real Estate', 'top_holdings': ['AMT', 'PLD', 'WELL', 'EQIX', 'DLR', 'O', 'SPG', 'PSA', 'CCI', 'CBRE']},
            'XLK': {'name': 'Technology', 'top_holdings': ['MSFT', 'NVDA', 'AAPL', 'AVGO', 'ORCL', 'PLTR', 'IBM', 'CSCO']},
            'XLU': {'name': 'Utilities', 'top_holdings': ['NEE', 'SO', 'CEG', 'DUK', 'VST', 'AEP']}
        }
        
        # 최근 섹터 분석 데이터 (50일선, 200일선 위 주식 비율)
        self.sector_analysis = {
            'XLC': {'50_day': 55, '200_day': 73},
            'XLY': {'50_day': 42, '200_day': 58},
            'XLP': {'50_day': 37, '200_day': 58},
            'XLE': {'50_day': 23, '200_day': 55},
            'XLF': {'50_day': 31, '200_day': 85},
            'XLV': {'50_day': 48, '200_day': 56},
            'XLI': {'50_day': 38, '200_day': 71},
            'XLB': {'50_day': 57, '200_day': 86},
            'XLRE': {'50_day': 35, '200_day': 48},
            'XLK': {'50_day': 57, '200_day': 74},
            'XLU': {'50_day': 100, '200_day': 93}
        }
    
    def get_stock_data(self, symbol, period='1y'):
        """주식 데이터 가져오기"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period)
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def get_stock_info(self, symbol):
        """주식 기본 정보 가져오기"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return info
        except Exception as e:
            print(f"Error fetching info for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, data):
        """기술적 지표 계산"""
        if data is None or len(data) < 50:
            return None
        
        # 이동평균선
        data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
        data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
        data['SMA_200'] = ta.trend.sma_indicator(data['Close'], window=200)
        
        # 볼린저 밴드
        bollinger = ta.volatility.BollingerBands(data['Close'])
        data['BB_Upper'] = bollinger.bollinger_hband()
        data['BB_Lower'] = bollinger.bollinger_lband()
        data['BB_Middle'] = bollinger.bollinger_mavg()
        
        # RSI
        data['RSI'] = ta.momentum.rsi(data['Close'])
        
        # MACD
        macd = ta.trend.MACD(data['Close'])
        data['MACD'] = macd.macd()
        data['MACD_Signal'] = macd.macd_signal()
        data['MACD_Hist'] = macd.macd_diff()
        
        # 거래량 이동평균
        data['Volume_MA'] = ta.trend.sma_indicator(data['Volume'], window=20)
        
        return data
    
    def generate_trading_signals(self, data, symbol):
        """매매 신호 생성"""
        if data is None or len(data) < 200:
            return {'signal': 'HOLD', 'reason': 'Insufficient data', 'strength': 0}
        
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        signals = []
        buy_signals = 0
        sell_signals = 0
        
        # 1. 이동평균선 신호
        if latest['Close'] > latest['SMA_50'] and latest['SMA_50'] > latest['SMA_200']:
            buy_signals += 2
            signals.append("상승 추세: 주가가 50일선과 200일선 위에 있음")
        elif latest['Close'] < latest['SMA_50'] and latest['SMA_50'] < latest['SMA_200']:
            sell_signals += 2
            signals.append("하락 추세: 주가가 50일선과 200일선 아래에 있음")
        
        # 2. 골든크로스/데드크로스
        if prev['SMA_50'] <= prev['SMA_200'] and latest['SMA_50'] > latest['SMA_200']:
            buy_signals += 3
            signals.append("골든크로스: 50일선이 200일선을 상향 돌파")
        elif prev['SMA_50'] >= prev['SMA_200'] and latest['SMA_50'] < latest['SMA_200']:
            sell_signals += 3
            signals.append("데드크로스: 50일선이 200일선을 하향 돌파")
        
        # 3. RSI 신호
        if latest['RSI'] < 30:
            buy_signals += 1
            signals.append("RSI 과매도: RSI가 30 이하")
        elif latest['RSI'] > 70:
            sell_signals += 1
            signals.append("RSI 과매수: RSI가 70 이상")
        
        # 4. 볼린저 밴드 신호
        if latest['Close'] <= latest['BB_Lower']:
            buy_signals += 1
            signals.append("볼린저 밴드: 주가가 하단 밴드 근처")
        elif latest['Close'] >= latest['BB_Upper']:
            sell_signals += 1
            signals.append("볼린저 밴드: 주가가 상단 밴드 근처")
        
        # 5. MACD 신호
        if latest['MACD'] > latest['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
            buy_signals += 1
            signals.append("MACD 상승 신호")
        elif latest['MACD'] < latest['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
            sell_signals += 1
            signals.append("MACD 하락 신호")
        
        # 6. 섹터 분석 반영
        if symbol in self.sector_analysis:
            sector_data = self.sector_analysis[symbol]
            if sector_data['50_day'] > 60 and sector_data['200_day'] > 70:
                buy_signals += 1
                signals.append(f"섹터 강세: 50일선 위 {sector_data['50_day']}%, 200일선 위 {sector_data['200_day']}%")
            elif sector_data['50_day'] < 40 and sector_data['200_day'] < 50:
                sell_signals += 1
                signals.append(f"섹터 약세: 50일선 위 {sector_data['50_day']}%, 200일선 위 {sector_data['200_day']}%")
        
        # 신호 결정
        net_signal = buy_signals - sell_signals
        if net_signal >= 2:
            signal = 'BUY'
        elif net_signal <= -2:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return {
            'signal': signal,
            'strength': abs(net_signal),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'reasons': signals,
            'current_price': latest['Close'],
            'rsi': latest['RSI'],
            'macd': latest['MACD'],
            'volume_ratio': latest['Volume'] / latest['Volume_MA'] if latest['Volume_MA'] > 0 else 1
        }
    
    def create_chart(self, data, symbol):
        """주식 차트 생성"""
        if data is None:
            return None
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Price & Moving Averages', 'RSI', 'MACD'),
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # 캔들스틱 차트
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # 이동평균선
        fig.add_trace(
            go.Scatter(x=data.index, y=data['SMA_20'], name='SMA 20', line=dict(color='orange')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=data.index, y=data['SMA_50'], name='SMA 50', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=data.index, y=data['SMA_200'], name='SMA 200', line=dict(color='red')),
            row=1, col=1
        )
        
        # 볼린저 밴드
        fig.add_trace(
            go.Scatter(x=data.index, y=data['BB_Upper'], name='BB Upper', line=dict(color='gray', dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=data.index, y=data['BB_Lower'], name='BB Lower', line=dict(color='gray', dash='dash')),
            row=1, col=1
        )
        
        # RSI
        fig.add_trace(
            go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='purple')),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        # MACD
        fig.add_trace(
            go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='blue')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal', line=dict(color='red')),
            row=3, col=1
        )
        fig.add_trace(
            go.Bar(x=data.index, y=data['MACD_Hist'], name='Histogram', marker_color='green'),
            row=3, col=1
        )
        
        fig.update_layout(
            title=f'{symbol} Stock Analysis',
            xaxis_title='Date',
            height=800,
            showlegend=True
        )
        
        return fig
    
    def compare_stocks(self, symbols, period='6m'):
        """주식들 비교 분석"""
        comparison_data = {}
        
        for symbol in symbols:
            data = self.get_stock_data(symbol, period)
            if data is not None:
                data = self.calculate_technical_indicators(data)
                signal = self.generate_trading_signals(data, symbol)
                
                comparison_data[symbol] = {
                    'current_price': data['Close'].iloc[-1],
                    'change_pct': ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100,
                    'signal': signal['signal'],
                    'strength': signal['strength'],
                    'rsi': signal['rsi'],
                    'volume_ratio': signal['volume_ratio']
                }
        
        return comparison_data
    
    def get_sector_overview(self):
        """섹터별 분석 현황"""
        sector_summary = []
        
        for symbol, info in self.sector_etfs.items():
            analysis = self.sector_analysis.get(symbol, {})
            
            # 섹터 신호 판단
            if analysis.get('50_day', 0) > 60 and analysis.get('200_day', 0) > 70:
                sector_signal = 'STRONG_BUY'
            elif analysis.get('50_day', 0) > 40 and analysis.get('200_day', 0) > 60:
                sector_signal = 'BUY'
            elif analysis.get('50_day', 0) < 30 or analysis.get('200_day', 0) < 40:
                sector_signal = 'SELL'
            else:
                sector_signal = 'HOLD'
            
            sector_summary.append({
                'symbol': symbol,
                'name': info['name'],
                'signal': sector_signal,
                '50_day_pct': analysis.get('50_day', 0),
                '200_day_pct': analysis.get('200_day', 0),
                'top_holdings': info['top_holdings'][:5]
            })
        
        return sector_summary