from flask import Flask, request, jsonify, Response

app = Flask(__name__)

class BaccaratCore:
    def __init__(self):
        self.raw_history = []
        self.total_predictions = 0
        self.correct_predictions = 0

    def reset(self):
        self.raw_history = []
        self.total_predictions = 0
        self.correct_predictions = 0

    def add_result(self, res):
        res = str(res).upper().strip()
        if res not in ['B', 'P', 'T']:
            return False
        self.raw_history.append(res)
        return True

    def build_big_road(self):
        big_road = []
        current_col = []
        last_side = None

        for res in self.raw_history:
            if res == 'T':
                continue
            if last_side is None or res == last_side:
                current_col.append(res)
                last_side = res
            else:
                big_road.append(current_col)
                current_col = [res]
                last_side = res
        if current_col:
            big_road.append(current_col)
        return big_road

    def calculate_derived_symbol(self, big_road, col_idx, row_idx, k):
        target_col_idx = col_idx - k
        if target_col_idx < 0:
            return None
        if row_idx == 0:
            prev_len = len(big_road[col_idx - 1])
            comp_len = len(big_road[col_idx - 1 - k])
            return 'RED' if prev_len == comp_len else 'BLUE'
        target_col = big_road[target_col_idx]
        if len(target_col) >= (row_idx + 1):
            return 'RED'
        elif len(target_col) < row_idx:
            return 'BLUE'
        else:
            return 'RED'

    def generate_derived_roads(self, big_road):
        big_eye, small, cockroach = [], [], []
        for c_idx, col in enumerate(big_road):
            for r_idx in range(len(col)):
                if (c_idx == 1 and r_idx >= 1) or c_idx >= 2:
                    sym = self.calculate_derived_symbol(big_road, c_idx, r_idx, 1)
                    if sym:
                        big_eye.append(sym)
                if (c_idx == 2 and r_idx >= 1) or c_idx >= 3:
                    sym = self.calculate_derived_symbol(big_road, c_idx, r_idx, 2)
                    if sym:
                        small.append(sym)
                if (c_idx == 3 and r_idx >= 1) or c_idx >= 4:
                    sym = self.calculate_derived_symbol(big_road, c_idx, r_idx, 3)
                    if sym:
                        cockroach.append(sym)
        return big_eye, small, cockroach

    def ask_road(self, test_side):
        simulated_history = list(self.raw_history) + [test_side]
        temp_core = BaccaratCore()
        temp_core.raw_history = simulated_history
        sim_big_road = temp_core.build_big_road()
        b_eye, sm, cock = temp_core.generate_derived_roads(sim_big_road)
        return {
            "big_eye": b_eye[-1] if b_eye else "NONE",
            "small": sm[-1] if sm else "NONE",
            "cockroach": cock[-1] if cock else "NONE"
        }

    def analyze_next(self):
        total_hands = len(self.raw_history)
        if total_hands < 6:
            rec = "B" if total_hands % 2 == 0 else "P"
            return {
                "decision": rec,
                "confidence": "60.0%",
                "risk_level": "中等风险",
                "status_msg": f"正在收集数据，还需 {6 - total_hands} 局结果进行首次深度AI分析",
                "ask_road": {"if_banker": {}, "if_player": {}}
            }

        banker_ask = self.ask_road('B')
        player_ask = self.ask_road('P')
        banker_red = sum(1 for v in banker_ask.values() if v == 'RED')
        player_red = sum(1 for v in player_ask.values() if v == 'RED')

        if banker_red > player_red:
            suggest = "B"
            conf = 85.0 + (banker_red * 4.5)
            risk = "低风险" if banker_red == 3 else "中等风险"
            msg = f"庄问路下三路呈现 {banker_red} 个红盘（形态齐整，倾向做庄）"
        elif player_red > banker_red:
            suggest = "P"
            conf = 85.0 + (player_red * 4.5)
            risk = "低风险" if player_red == 3 else "中等风险"
            msg = f"闲问路下三路呈现 {player_red} 个红盘（形态齐整，倾向做闲）"
        else:
            suggest = "B" if total_hands % 2 == 0 else "P"
            conf = 65.0
            risk = "高风险"
            msg = "庄闲问路红蓝呈对冲状态，建议观望或小注轻跟"

        return {
            "decision": suggest,
            "confidence": f"{conf:.1f}%",
            "risk_level": risk,
            "status_msg": msg,
            "ask_road": {
                "if_banker": banker_ask,
                "if_player": player_ask
            }
        }

engine = BaccaratCore()

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>百家乐 AI 深度分析系统</title>
    <style>
        body { font-family: sans-serif; background: #f4f6f9; margin: 0; padding: 15px; color: #333; }
        .card { background: #fff; border-radius: 12px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .title { font-size: 16px; font-weight: bold; text-align: center; margin-bottom: 12px; }
        .btn { width: 100%; padding: 12px; margin-bottom: 8px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; color: #fff; cursor: pointer; }
        .btn-banker { background: #d32f2f; }
        .btn-player { background: #1976d2; }
        .btn-tie { background: #388e3c; }
        .btn-reset { background: #757575; margin-top: 10px; }
        .road-board { background: #222; padding: 10px; border-radius: 8px; color: #fff; font-size: 14px; min-height: 40px; }
        .bead { display: inline-block; width: 24px; height: 24px; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; font-weight: bold; margin-right: 4px; color: #fff; }
        .bead-B { background: #d32f2f; }
        .bead-P { background: #1976d2; }
        .bead-T { background: #388e3c; }
    </style>
</head>
<body>

    <div class="card">
        <div class="title" style="color: #4a148c;">输入游戏结果</div>
        <button class="btn btn-banker" onclick="sendResult('B')">🏆 庄家胜</button>
        <button class="btn btn-player" onclick="sendResult('P')">👤 闲家胜</button>
        <button class="btn btn-tie" onclick="sendResult('T')">= 和局</button>
    </div>

    <div class="card" style="border: 1px solid #ffcdd2;">
        <div class="title" style="color: #c62828;">🤖 AI 持续预测下局</div>
        <div style="font-size: 22px; font-weight: bold; text-align: center; margin: 10px 0;" id="ai-decision">庄家胜</div>
        <div style="text-align: center; color: #666; font-size: 14px;">置信度: <span id="ai-confidence">0.0%</span> | 风险: <span id="ai-risk">评估中</span></div>
    </div>

    <div class="card">
        <div class="title">⚠️ 终极风险评估与分析</div>
        <div style="background: #fff8e1; padding: 10px; border-radius: 8px; color: #f57f17; font-size: 13px;" id="ai-status">
            正在收集数据，还需 6 局结果进行首次AI深度分析
        </div>
    </div>

    <div class="card">
        <div class="title">🔮 庄/闲问路下三路推算 (澳门标准)</div>
        <div style="font-size: 13px; line-height: 1.8;">
            <div><strong>庄问路：</strong> 大眼仔: <span id="b-eye">-</span> | 小路: <span id="b-small">-</span> | 甲由路: <span id="b-cock">-</span></div>
            <div><strong>闲问路：</strong> 大眼仔: <span id="p-eye">-</span> | 小路: <span id="p-small">-</span> | 甲由路: <span id="p-cock">-</span></div>
        </div>
    </div>

    <div class="card">
        <div class="title">🎰 澳门珠盘路/最近记录</div>
        <div class="road-board" id="bead-plate">无记录</div>
        <button class="btn btn-reset" onclick="resetGame()">清空重置牌局</button>
    </div>

    <script>
        async function fetchStatus() {
            const res = await fetch('/api/status');
            const data = await res.json();
            updateUI(data);
        }

        async function sendResult(symbol) {
            const res = await fetch('/predict', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({result: symbol})
            });
            const data = await res.json();
            updateUI(data.full_status);
        }

        async function resetGame() {
            if(confirm("确定清空当前靴牌数据吗？")) {
                await fetch('/reset', {method: 'POST'});
                fetchStatus();
            }
        }

        function updateUI(data) {
            const dec = data.analysis.decision === 'B' ? '庄家胜' : '闲家胜';
            document.getElementById('ai-decision').innerText = dec;
            document.getElementById('ai-decision').style.color = data.analysis.decision === 'B' ? '#d32f2f' : '#1976d2';
            document.getElementById('ai-confidence').innerText = data.analysis.confidence;
            document.getElementById('ai-risk').innerText = data.analysis.risk_level;
            document.getElementById('ai-status').innerText = data.analysis.status_msg;

            const ask = data.analysis.ask_road;
            document.getElementById('b-eye').innerText = ask.if_banker.big_eye || '-';
            document.getElementById('b-small').innerText = ask.if_banker.small || '-';
            document.getElementById('b-cock').innerText = ask.if_banker.cockroach || '-';
            
            document.getElementById('p-eye').innerText = ask.if_player.big_eye || '-';
            document.getElementById('p-small').innerText = ask.if_player.small || '-';
            document.getElementById('p-cock').innerText = ask.if_player.cockroach || '-';

            const beadDiv = document.getElementById('bead-plate');
            if (data.history.length === 0) {
                beadDiv.innerHTML = '无记录';
            } else {
                beadDiv.innerHTML = data.history.map(x => '<span class="bead bead-' + x + '">' + (x==='B'?'庄':(x==='P'?'闲':'和')) + '</span>').join('');
            }
        }

        fetchStatus();
    </script>
</body>
</html>"""

@app.route('/')
def index():
    return Response(HTML_PAGE,
