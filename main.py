from flask import Flask, request, jsonify

app = Flask(__name__)

class BaccaratCore:
    def __init__(self):
        self.raw_history = [] # 原始开奖数据 ['B', 'P', 'T', ...]

    def reset(self):
        self.raw_history = []

    def add_result(self, res):
        res = str(res).upper().strip()
        if res in ['B', 'P', 'T']:
            self.raw_history.append(res)
            return True
        return False

    def build_big_road(self):
        """构建标准大路二维矩阵 (不含和局，和局在大路上仅记为绿线)"""
        big_road = []
        current_col = []
        last_side = None

        for res in self.raw_history:
            if res == 'T':
                continue # 和局不换列，也不增加新位置，仅附着在上一手
            
            if last_side is None:
                current_col.append(res)
                last_side = res
            elif res == last_side:
                current_col.append(res)
            else:
                big_road.append(current_col)
                current_col = [res]
                last_side = res
        
        if current_col:
            big_road.append(current_col)
            
        return big_road

    def calculate_derived_road_symbol(self, big_road, col_idx, row_idx, k):
        """
        标准下三路推导核心算法 (澳门与全球赌厅通用算法):
        k=1: 大眼仔路 (对比前1列)
        k=2: 小路     (对比前2列)
        k=3: 甲由路   (对比前3列)
        返回: 'RED' (顺/齐/有) 或 'BLUE' (破/乱/无)
        """
        target_col_idx = col_idx - k
        if target_col_idx < 0:
            return None

        # 1. 如果当前节点是新起一列的第一手 (row_idx == 0) -> 比较前一列与前 k+1 列的长度
        if row_idx == 0:
            prev_col_len = len(big_road[col_idx - 1])
            compare_col_len = len(big_road[col_idx - 1 - k])
            return 'RED' if prev_col_len == compare_col_len else 'BLUE'

        # 2. 如果当前节点是在同一列向下延续 (row_idx > 0)
        target_col = big_road[target_col_idx]
        
        # 2a. 直落看“有无”：对比列对应行是否有棋子
        if len(target_col) >= (row_idx + 1):
            return 'RED'
        # 2b. 对应行无棋子，但如果超出1步以上，算“无”(BLUE)
        elif len(target_col) < row_idx:
            return 'BLUE'
        # 2c. 刚好处于下落1位的转折点，算“齐整”(RED)
        else:
            return 'RED'

    def generate_derived_roads(self, big_road):
        """生成大眼仔路、小路、甲由路的完整符号序列"""
        big_eye, small, cockroach = [], [], []

        for c_idx, col in enumerate(big_road):
            for r_idx in range(len(col)):
                # 大眼仔路起点: 第二列第二行 或 第三列第一行
                if (c_idx == 1 and r_idx >= 1) or c_idx >= 2:
                    sym = self.calculate_derived_road_symbol(big_road, c_idx, r_idx, 1)
                    if sym: big_eye.append(sym)

                # 小路起点: 第三列第二行 或 第四列第一行
                if (c_idx == 2 and r_idx >= 1) or c_idx >= 3:
                    sym = self.calculate_derived_road_symbol(big_road, c_idx, r_idx, 2)
                    if sym: small.append(sym)

                # 甲由路起点: 第四列第二行 或 第五列第一行
                if (c_idx == 3 and r_idx >= 1) or c_idx >= 4:
                    sym = self.calculate_derived_road_symbol(big_road, c_idx, r_idx, 3)
                    if sym: cockroach.append(sym)

        return big_eye, small, cockroach

    def ask_road(self, test_side):
        """
        试牌/问路模拟算法：
        模拟下一局如果是 test_side ('B' 或 'P')，下三路分别会出什么颜色
        """
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
            return {
                "decision": "WAIT",
                "confidence": "NONE",
                "reason": "开局数据不足（需至少6手以上以形成基础大路格局）"
            }

        big_road = self.build_big_road()
        big_eye, small, cockroach = self.generate_derived_roads(big_road)

        # 模拟庄问路与闲问路
        banker_ask = self.ask_road('B')
        player_ask = self.ask_road('P')

        # 计算庄/闲问路后红圈/红斜杠（代表顺路/成强趋势）的数量
        banker_red_score = sum(1 for v in banker_ask.values() if v == 'RED')
        player_red_score = sum(1 for v in player_ask.values() if v == 'RED')

        # 结合下三路“三红/三蓝”同向爆发逻辑判断
        if banker_red_score > player_red_score:
            suggest = "BANKER"
            confidence = "HIGH" if banker_red_score == 3 else "MEDIUM"
            reason = f"庄问路下三路呈现 {banker_red_score} 个红盘（拍头齐整/顺龙形态），胜率倾向显著。"
        elif player_red_score > banker_red_score:
            suggest = "PLAYER"
            confidence = "HIGH" if player_red_score == 3 else "MEDIUM"
            reason = f"闲问路下三路呈现 {player_red_score} 个红盘（拍头齐整/顺龙形态），胜率倾向显著。"
        else:
            suggest = "WAIT"
            confidence = "LOW"
            reason = "庄闲问路下三路红蓝呈对冲状态（局面陷入乱路/跳路），建议观望。"

        # 珠盘路统计
        b_cnt = self.raw_history.count('B')
        p_cnt = self.raw_history.count('P')
        t_cnt = self.raw_history.count('T')

        return {
            "decision": suggest,
            "confidence": confidence,
            "reason": reason,
            "ask_road_matrix": {
                "if_banker": banker_ask,
                "if_player": player_ask
            },
            "bead_plate_stats": {
                "total": total_hands,
                "banker": b_cnt,
                "player": p_cnt,
                "tie": t_cnt
            }
        }

engine = BaccaratCore()

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json() or {}
    result = data.get('result')
    
    if not result or not engine.add_result(result):
        return jsonify({"status": "error", "message": "请输入有效的开奖结果 ('B'=庄, 'P'=闲, 'T'=和)"}), 400

    analysis = engine.analyze_next()
    return jsonify({
        "status": "success",
        "latest_input": str(result).upper(),
        "total_hands": len(engine.raw_history),
        "analysis": analysis
    })

@app.route('/reset', methods=['POST'])
def reset():
    engine.reset()
    return jsonify({"status": "success", "message": "新一靴牌已重置"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
