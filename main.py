import heapq
import json
import os
import sys

# ---------- 清屏 ----------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

def color_text(text, color):
    return f"{color}{text}{Colors.RESET}"

DEFAULT_TARGET = 100000
CACHE_FILE = "dungeon_cache.json"

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

def cache_key(demon, adventurer, target):
    return f"{demon}_{adventurer}_{target}"

# ---------- 核心搜索（同时枚举A和B）----------
def bfs_fixed_A(A1, A2, total_adventurer, target, best_steps=None, best_change=None):
    if target % 100 != 0:
        return None, None

    init_options = []
    if total_adventurer >= 98:
        init_options.append((98, "单边", "oneside"))
    if total_adventurer >= 49:
        init_options.append((49, "双边", "twosides"))
    if not init_options:
        return None, None

    best = {}
    pq = []
    heappush = heapq.heappush
    heappop = heapq.heappop

    for B0, act_zh, act_en in init_options:
        state = (100, B0, 0)  # (layer, B, max_B_change)
        best[state] = (1, 0, (None, act_zh, act_en, A1, B0))
        heappush(pq, (1, 0, 100, B0, 0))

    while pq:
        steps, _, cur_layer, cur_B, cur_maxB = heappop(pq)

        if best_steps is not None and steps > best_steps:
            continue

        if best_change is not None and cur_maxB >= best_change:
            continue

        if cur_layer == target:
            path = []
            state = (cur_layer, cur_B, cur_maxB)
            while True:
                _, _, (prev_state, act_zh, act_en, A_used, B_used) = best[state]
                if prev_state is None:
                    path.append((1, act_zh, act_en, state[0], A_used, B_used))
                    break
                path.append((prev_state[0], act_zh, act_en, state[0], A_used, B_used))
                state = prev_state
            path.reverse()
            return steps, path

        use_A = A1 if steps == 1 else A2

        if cur_layer == 10000 or cur_layer == 100000:
            boss_gain = 99
        else:
            boss_gain = 99 + 100 * use_A

        remain = target - cur_layer - boss_gain - 1
        if remain < 0:
            continue

        max_B = min(total_adventurer, remain)
        max_B = (max_B // 100) * 100

        for B_next in range(0, max_B + 1, 100):
            new_maxB = max(cur_maxB, abs(B_next - cur_B))

            if best_change is not None and new_maxB >= best_change:
                continue

            step = (1 + B_next) + boss_gain
            nxt = cur_layer + step

            if nxt > target or nxt % 100 != 0:
                continue

            state = (nxt, B_next, new_maxB)
            new_steps = steps + 1

            if state not in best or new_steps < best[state][0]:
                best[state] = (
                    new_steps,
                    0,
                    ((cur_layer, cur_B, cur_maxB), "单边+Boss", "oneside+boss", use_A, B_next),
                )
                heappush(pq, (new_steps, 0, nxt, B_next, new_maxB))

    return None, None

def solve(total_demon, total_adventurer, target):
    max_A = min(total_demon, target // 100)

    best_steps = None
    best_path = None
    best_change = float('inf')

    for A1 in range(max_A, -1, -1):
        for A2 in range(max_A, -1, -1):

            steps, path = bfs_fixed_A(
                A1, A2,
                total_adventurer,
                target,
                best_steps,
                best_change
            )

            if steps is None:
                continue

            if best_steps is not None and steps > best_steps:
                continue

            A_vals = [a for (_, _, _, _, a, _) in path]
            B_vals = [b for (_, _, _, _, _, b) in path]

            max_A_change = 0
            if len(A_vals) > 2:
                max_A_change = max(abs(A_vals[i+1] - A_vals[i]) for i in range(1, len(A_vals)-1))

            max_B_change = max(abs(B_vals[i+1] - B_vals[i]) for i in range(len(B_vals)-1)) if len(B_vals) > 1 else 0

            total_change = max(max_A_change, max_B_change)

            if best_steps is None or steps < best_steps:
                best_steps = steps
                best_path = path
                best_change = total_change

            elif steps == best_steps and total_change < best_change:
                best_path = path
                best_change = total_change

    return best_steps, best_path

# ---------- 辅助函数 ----------
def translate_action(act_zh, act_en, A, B, lang):
    if lang == "zh":
        return act_zh
    elif lang == "jp":
        if act_zh == "单边":
            return "片側"
        elif act_zh == "双边":
            return "両側"
        elif act_zh == "单边+Boss":
            return "片側+ボス"
        return act_zh
    else:
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

def print_table(data, headers):
    def display_width(s):
        s_str = str(s)
        width = 0
        for ch in s_str:
            if '\u4e00' <= ch <= '\u9fff' or '\u3040' <= ch <= '\u30ff' or '\u3000' <= ch <= '\u303f':
                width += 2
            else:
                width += 1
        return width

    col_widths = [display_width(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            w = display_width(cell)
            if w > col_widths[i]:
                col_widths[i] = w
    min_widths = [4, 8, 14, 8, 10]
    for i, minw in enumerate(min_widths):
        if col_widths[i] < minw:
            col_widths[i] = minw
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    sep_double = "+" + "+".join("=" * (w + 2) for w in col_widths) + "+"
    def format_row(cells):
        row = "|"
        for i, cell in enumerate(cells):
            cell_str = str(cell)
            padding = col_widths[i] - display_width(cell_str)
            if i == 0 or i == 3:
                row += " " + " " * padding + cell_str + " |"
            else:
                row += " " + cell_str + " " * padding + " |"
        return row
    print(sep)
    print(format_row(headers))
    print(sep_double)
    for row in data:
        print(format_row(row))
    print(sep)

def print_result(steps, path, lang, texts):
    A_vals = [a for (_,_,_,_,a,_) in path]
    B_vals = [b for (_,_,_,_,_,b) in path]
    # A最大变化（忽略第一步从0到第一个A的变化）
    if len(A_vals) > 2:
        max_A_change = max(abs(A_vals[i+1] - A_vals[i]) for i in range(1, len(A_vals)-1))
    else:
        max_A_change = 0
    # B最大变化（包含第一步）
    max_B_change = max(abs(B_vals[i+1] - B_vals[i]) for i in range(len(B_vals)-1)) if len(B_vals)>1 else 0
    floors = [to for (_, _, _, to, _, _) in path]
    hundred_cnt = sum(1 for f in floors if f % 100 == 0 and f not in (10000, 100000))
    tenk_cnt = sum(1 for f in floors if f == 10000)
    hundredk_cnt = sum(1 for f in floors if f == 100000)
    table_data = []
    for i, (frm, act_zh, act_en, to, A, B) in enumerate(path, 1):
        act_text = translate_action(act_zh, act_en, A, B, lang)
        table_data.append([str(i), str(frm), act_text, str(to), f"{A}/{B}"])
    headers = ["#", texts["step_from"], texts["action"], texts["step_to"], texts["param_label"]]
    print()
    print_table(table_data, headers)
    print()
    print(color_text(texts["actual"].format(max_A_change, max_B_change), Colors.CYAN))
    print(color_text(texts["hint_hundred"].format(hundred_cnt), Colors.GREEN))
    print(color_text(texts["hint_tenk"].format(tenk_cnt), Colors.GREEN))
    print(color_text(texts["hint_hundredk"].format(hundredk_cnt), Colors.GREEN))

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
            "step_from": "起始層",
            "step_to": "到達層",
            "action": "行動",
            "param_label": "悪魔/冒険者",
            "actual": "実際の最大変化幅 (悪魔/冒険者): {}/{}",
            "continue": "続けて計算しますか？[Enter=yes, n=no]: ",
            "exit": "プログラムを終了します。",
            "target_corrected": "注意: 目標階層数 {} は100の倍数ではないため、{} に修正しました。",
            "solution": "✅ 最少操作回数: {}",
            "hint_hundred": "百階ボス: {}",
            "hint_tenk": "万階ボス: {}",
            "hint_hundredk": "十万階ボス: {}",
        }
    elif choice == "3":
        lang = "en"
        texts = {
            "prompt_demon": "Total number of demons (0~1000): ",
            "prompt_adventurer": "Total number of adventurers (0~1000): ",
            "prompt_target": f"Target floor (default {DEFAULT_TARGET}): ",
            "step_from": "From",
            "step_to": "To",
            "action": "Action",
            "param_label": "Demon/Adv",
            "actual": "Actual max change (demon/adventurer): {}/{}",
            "continue": "Continue computing? [Enter=yes, n=no]: ",
            "exit": "Program terminated.",
            "target_corrected": "Note: Target floor {} is not a multiple of 100, adjusted to {}.",
            "solution": "✅ Minimum steps: {}",
            "hint_hundred": "Hundred boss: {}",
            "hint_tenk": "Ten-thousand boss: {}",
            "hint_hundredk": "Hundred-thousand boss: {}",
        }
    else:
        lang = "zh"
        texts = {
            "prompt_demon": "您拥有的恶魔总数 (0~1000): ",
            "prompt_adventurer": "您拥有的冒险者总数 (0~1000): ",
            "prompt_target": f"目标层数 (回车默认 {DEFAULT_TARGET}): ",
            "step_from": "起始层",
            "step_to": "到达层",
            "action": "操作",
            "param_label": "恶魔/冒险者",
            "actual": "实际最大变化幅度 (恶魔/冒险者): {}/{}",
            "continue": "是否继续计算？[Enter=yes, n=no]: ",
            "exit": "程序结束。",
            "target_corrected": "注意: 目标层数 {} 不是100的倍数，已自动修正为 {}。",
            "solution": "✅ 最少操作次数: {}",
            "hint_hundred": "百层boss: {}",
            "hint_tenk": "万层boss: {}",
            "hint_hundredk": "十万层boss: {}",
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
        steps, path = solve(total_demon, total_adventurer, target)
        if steps is not None:
            print(color_text(f"\n{texts['solution'].format(steps)}", Colors.GREEN))
            print_result(steps, path, lang, texts)
        else:
            print(color_text("未找到可行路径，请增加恶魔或冒险者总数。", Colors.RED))
        if not yes_no_default_yes(texts["continue"]):
            print(texts["exit"])
            break
        else:
            clear_screen()

if __name__ == "__main__":
    main()
