import heapq
import json
import os
import sys
import ctypes

# ---------- 管理员权限提升 (Windows) ----------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

# 在导入其他模块前提升权限（如果打包成 exe 会请求 UAC）
elevate_admin()

# ---------- 清屏 ----------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ---------- ANSI 颜色 ----------
class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def color_text(text, color):
    return f"{color}{text}{Colors.RESET}"

# ---------- 常量 ----------
DEFAULT_TARGET = 100000
CACHE_FILE = "dungeon_cache.json"

# ---------- 缓存 ----------
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def cache_key(demon, adventurer, max_change, target):
    return f"{demon}_{adventurer}_{max_change}_{target}"

# ---------- 核心搜索 ----------
def solve_core(total_demon, total_adventurer, max_change, target):
    if target % 100 != 0:
        return None, None, None
    init_options = []
    if 98 <= total_adventurer:
        init_options.append((98, "单边", "oneside"))
    if 49 <= total_adventurer:
        init_options.append((49, "双边", "twosides"))

    hundreds = list(range(100, target+1, 100))
    if not hundreds:
        return None, None, None
    B_vals = [b for b in range(0, total_adventurer+1, 100)]
    if not B_vals:
        B_vals = [0]

    best = {}
    pq = []

    for B0, act_zh, act_en in init_options:
        for B1 in B_vals:
            if abs(B1 - B0) > max_change:
                continue
            state = (100, B1)
            maxc = abs(B1 - B0)
            totalc = maxc
            if state not in best or (1, maxc, totalc) < (best[state][0], best[state][1], best[state][2]):
                best[state] = (1, maxc, totalc, (None, act_zh, act_en, 0, B0))
                heapq.heappush(pq, (1, maxc, totalc, 100, B1))

    while pq:
        steps, maxc, totalc, cur_layer, cur_B = heapq.heappop(pq)
        cur_state = (cur_layer, cur_B)
        if (steps, maxc, totalc) != best[cur_state][:3]:
            continue
        if cur_layer == target:
            path = []
            state = cur_state
            while True:
                _, _, _, (prev_state, act_zh, act_en, A, B) = best[state]
                if prev_state is None:
                    path.append((1, act_zh, act_en, state[0], A, B))
                    break
                path.append((prev_state[0], act_zh, act_en, state[0], A, B))
                state = prev_state
            path.reverse()
            return steps, path, target

        for A in range(total_demon + 1):
            boss_gain = 99 + 100 * A
            step = (1 + cur_B) + boss_gain
            nxt_layer = cur_layer + step
            if nxt_layer > target or nxt_layer % 100 != 0:
                continue
            for nxt_B in B_vals:
                if abs(nxt_B - cur_B) > max_change:
                    continue
                nd = steps + 1
                new_maxc = max(maxc, abs(nxt_B - cur_B))
                new_totalc = totalc + abs(nxt_B - cur_B)
                nxt_state = (nxt_layer, nxt_B)
                if nxt_state not in best or (nd, new_maxc, new_totalc) < (best[nxt_state][0], best[nxt_state][1], best[nxt_state][2]):
                    # 英文标识统一为 oneside+boss
                    best[nxt_state] = (nd, new_maxc, new_totalc, (cur_state, "单边+Boss", "oneside+boss", A, cur_B))
                    heapq.heappush(pq, (nd, new_maxc, new_totalc, nxt_layer, nxt_B))

    return None, None, None

def solve(total_demon, total_adventurer, max_change, target):
    key = cache_key(total_demon, total_adventurer, max_change, target)
    cache = load_cache()
    if key in cache:
        data = cache[key]
        steps = data["steps"]
        final_layer = data["final_layer"]
        path = [tuple(item) for item in data["path"]]
        return steps, path, final_layer
    steps, path, final_layer = solve_core(total_demon, total_adventurer, max_change, target)
    if steps is not None:
        cache[key] = {"steps": steps, "final_layer": final_layer, "path": [list(item) for item in path]}
        save_cache(cache)
    return steps, path, final_layer

# ---------- 辅助函数 ----------
def translate_action(act_zh, act_en, A, B, lang):
    if lang == "zh":
        return act_zh  # "单边" / "双边" / "单边+Boss"
    elif lang == "jp":
        if act_zh == "单边":
            return "片側"
        elif act_zh == "双边":
            return "両側"
        elif act_zh == "单边+Boss":
            return "片側+ボス"
        return act_zh
    else:  # English
        if act_en == "oneside":
            return "Oneside"
        elif act_en == "twosides":
            return "Twosides"
        elif act_en == "oneside+boss":
            return "Oneside+Boss"
        return act_en

def get_int(prompt, low=None, high=None, default=None):
    while True:
        try:
            s = input(prompt).strip()
            if s == "" and default is not None:
                return default
            val = int(s)
            if low is not None and val < low:
                print(f"请输入 ≥ {low} 的值。")
                continue
            if high is not None and val > high:
                print(f"请输入 ≤ {high} 的值。")
                continue
            return val
        except ValueError:
            print("请输入整数。")

def yes_no_default_yes(prompt):
    return input(prompt).strip().lower() != 'n'

def print_table(data, headers, lang):
    """
    手动打印对齐好的表格，支持中日文宽字符。
    data: list of list (每行内容)
    headers: list of str
    lang: 未使用但保留
    """
    # 计算字符串的显示宽度（中文/日文全角算2，英文/数字算1）
    def display_width(s):
        s_str = str(s)
        width = 0
        for ch in s_str:
            # 全角字符范围：基本汉字、日文假名、全角符号等
            if '\u4e00' <= ch <= '\u9fff' or '\u3040' <= ch <= '\u30ff' or '\u3000' <= ch <= '\u303f':
                width += 2
            else:
                width += 1
        return width

    # 初始列宽基于表头
    col_widths = [display_width(h) for h in headers]
    # 更新列宽基于数据
    for row in data:
        for i, cell in enumerate(row):
            w = display_width(cell)
            if w > col_widths[i]:
                col_widths[i] = w

    # 增加最小列宽（避免太窄）
    min_widths = [4, 8, 12, 8, 10]  # #, 起始层, 操作, 到达层, 恶魔/冒险者
    for i, minw in enumerate(min_widths):
        if col_widths[i] < minw:
            col_widths[i] = minw

    # 构建分隔线
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    sep_double = "+" + "+".join("=" * (w + 2) for w in col_widths) + "+"

    def format_row(cells):
        row = "|"
        for i, cell in enumerate(cells):
            cell_str = str(cell)
            # 计算需要填充的空格数
            padding = col_widths[i] - display_width(cell_str)
            # 编号列(0)和到达层(3)右对齐，其他左对齐
            if i == 0 or i == 3:
                row += " " + " " * padding + cell_str + " |"
            else:
                row += " " + cell_str + " " * padding + " |"
        return row

    # 打印表头
    print(sep)
    print(format_row(headers))
    print(sep_double)  # 表头下用双线分隔
    for row in data:
        print(format_row(row))
    print(sep)

def print_result(steps, final_layer, path, lang, texts):
    b_vals = [B for (_, _, _, _, _, B) in path]
    max_actual = max(abs(b_vals[i+1]-b_vals[i]) for i in range(len(b_vals)-1)) if len(b_vals)>1 else 0

    floors = [to for (_, _, _, to, _, _) in path]
    hundred_cnt = 0
    tenk_cnt = 0
    hundredk_cnt = 0
    for f in floors:
        if f == 100000:
            hundredk_cnt += 1
        elif f % 10000 == 0:
            tenk_cnt += 1
        elif f % 100 == 0:
            hundred_cnt += 1

    # 构建表格数据
    table_data = []
    for i, (frm, act_zh, act_en, to, A, B) in enumerate(path, 1):
        act_text = translate_action(act_zh, act_en, A, B, lang)
        table_data.append([str(i), str(frm), act_text, str(to), f"{A}/{B}"])

    headers = ["#", texts["step_from"], texts["action"], texts["step_to"], texts["param_label"]]

    print()
    print_table(table_data, headers, lang)
    print()
    print(color_text(texts["actual"].format(max_actual), Colors.CYAN))
    print(color_text(texts["hint_hundred"].format(hundred_cnt), Colors.GREEN))
    print(color_text(texts["hint_tenk"].format(tenk_cnt), Colors.GREEN))
    print(color_text(texts["hint_hundredk"].format(hundredk_cnt), Colors.GREEN))

# ---------- 主程序 ----------
def main():
    clear_screen()
    print("请选择语言 / Select Language / 言語を選択してください:")
    print("1. 中文")
    print("2. 日本語")
    print("3. English")
    choice = input("请输入数字 / Enter number: ").strip()
    if choice == "2":
        lang = "jp"
        texts = {
            "prompt_demon": "所持している悪魔の総数 (0~1000): ",
            "prompt_adventurer": "所持している冒険者の総数 (0~1000): ",
            "prompt_target": f"目標階層数 (デフォルト {DEFAULT_TARGET}): ",
            "result": "✅ 最小操作回数: {}, 最終到達階層: {}",
            "step_from": "起始層",
            "step_to": "到達層",
            "action": "行動",
            "param_label": "悪魔/冒険者",
            "actual": "実際の冒険者の最大変化幅: {}",
            "continue": "続けて計算しますか？[Enter=yes, n=no]: ",
            "exit": "プログラムを終了します。",
            "not_found": "条件を満たす経路が見つかりませんでした",
            "max_reached": "変化幅を {} まで増やしましたが解は見つかりませんでした。",
            "solution_found": "変化幅 {} で解が見つかりました：",
            "hint_hundred": "百階ボス: {}",
            "hint_tenk": "万階ボス: {}",
            "hint_hundredk": "十万階ボス: {}",
            "target_corrected": "注意: 目標階層数 {} は100の倍数ではないため、{} に修正しました。"
        }
    elif choice == "3":
        lang = "en"
        texts = {
            "prompt_demon": "Total number of demons (0~1000): ",
            "prompt_adventurer": "Total number of adventurers (0~1000): ",
            "prompt_target": f"Target floor (default {DEFAULT_TARGET}): ",
            "result": "✅ Minimum steps: {}, Final floor: {}",
            "step_from": "From",
            "step_to": "To",
            "action": "Action",
            "param_label": "Demon/Adv",
            "actual": "Actual max adventurer change: {}",
            "continue": "Continue computing? [Enter=yes, n=no]: ",
            "exit": "Program terminated.",
            "not_found": "No valid path found.",
            "max_reached": "Increased change limit up to {}, no solution found.",
            "solution_found": "Solution found with change limit {}:",
            "hint_hundred": "Hundred boss: {}",
            "hint_tenk": "Ten-thousand boss: {}",
            "hint_hundredk": "Hundred-thousand boss: {}",
            "target_corrected": "Note: Target floor {} is not a multiple of 100, adjusted to {}."
        }
    else:
        lang = "zh"
        texts = {
            "prompt_demon": "您拥有的恶魔总数 (0~1000): ",
            "prompt_adventurer": "您拥有的冒险者总数 (0~1000): ",
            "prompt_target": f"目标层数 (回车默认 {DEFAULT_TARGET}): ",
            "result": "✅ 最少操作次数: {}, 最终到达层数: {}",
            "step_from": "起始层",
            "step_to": "到达层",
            "action": "操作",
            "param_label": "恶魔/冒险者",
            "actual": "实际冒险者最大变化幅度: {}",
            "continue": "是否继续计算？[Enter=yes, n=no]: ",
            "exit": "程序结束。",
            "not_found": "未找到符合条件的路径",
            "max_reached": "变化幅度已增加到 {}，仍未找到解。",
            "solution_found": "使用变化幅度 {} 找到解：",
            "hint_hundred": "百层boss: {}",
            "hint_tenk": "万层boss: {}",
            "hint_hundredk": "十万层boss: {}",
            "target_corrected": "注意: 目标层数 {} 不是100的倍数，已自动修正为 {}。"
        }

    while True:
        print("\n" + "=" * 60)
        total_demon = get_int(texts["prompt_demon"], low=0, high=1000)
        total_adventurer = get_int(texts["prompt_adventurer"], low=0, high=1000)
        original_target = get_int(texts["prompt_target"], low=1, default=DEFAULT_TARGET)
        target = original_target
        if target % 100 != 0:
            target = target - (target % 100)
            print(color_text(texts["target_corrected"].format(original_target, target), Colors.YELLOW))

        found = False
        for max_change in range(0, total_adventurer + 1):
            steps, path, final_layer = solve(total_demon, total_adventurer, max_change, target)
            if steps is not None:
                print(color_text(f"\n{texts['solution_found'].format(max_change)}", Colors.GREEN))
                print_result(steps, final_layer, path, lang, texts)
                found = True
                break
        if not found:
            print(color_text(texts["max_reached"].format(total_adventurer), Colors.RED))

        if not yes_no_default_yes(texts["continue"]):
            print(texts["exit"])
            break
        else:
            clear_screen()

if __name__ == "__main__":
    main()
