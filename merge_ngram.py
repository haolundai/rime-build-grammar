import os
print("[INFO] merge_ngram.py VERSION=20251213-ABTEST")

def parse_min_freq_map(s: str):
    # s 例："3:2,4:2,5:2,6:1,7:1"
    out = {}
    if not s:
        return out
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        k, v = part.split(":")
        out[int(k)] = int(v)
    return out


def is_all_chinese(text: str) -> bool:
    for char in text:
        if not "\u4e00" <= char <= "\u9fff":
            return False
    return True


# ===== Config via env var =====
# 你可以在 ~/.rime_gram_config.sh 設定：
# export MERGE_MIN_FREQ_BY_N="3:2,4:2,5:2,6:2,7:2"
DEFAULT_MIN_FREQ = "3:2,4:2,5:2,6:2,7:2"
MIN_FREQ_BY_N = parse_min_freq_map(os.getenv("MERGE_MIN_FREQ_BY_N", DEFAULT_MIN_FREQ))

# 你要合併哪些階數（由 MIN_FREQ_BY_N 的 key 決定）
N_LIST = sorted(MIN_FREQ_BY_N.keys())
file_list = [f"ngram_{n}_frequencies.txt" for n in N_LIST]

# ===== Main =====
word_map = {}

for filename in file_list:
    # 檔名格式: ngram_6_frequencies.txt
    try:
        n = int(filename.split("_")[1])
    except Exception:
        continue

    min_freq = int(MIN_FREQ_BY_N.get(n, 1))

    file_path = os.path.join("", filename)
    if not os.path.exists(file_path):
        # 若某一階檔案不存在就略過（避免整個流程掛掉）
        continue

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip()
            if (not line) or line.startswith("#") or ("\t" not in line):
                continue

            params = line.split("\t")

            # params[0] 是 n-gram 字串（詞之間有空格）
            word = params[0]
            word = word.replace(" ", "")
            word = word.replace("<s>", "")
            word = word.replace("</s>", "$")  # 句末符號

            # freq 欄位：你貼的檔案看起來是 3 欄，最後一欄是 freq
            # 但也容錯：不足 3 欄時退回用第 2 欄
            if len(params) >= 3:
                freq_str = params[2]
            else:
                freq_str = params[1]

            try:
                freq_i = int(freq_str)
            except ValueError:
                continue

            # 分階門檻：低於門檻的不納入 merge
            if freq_i < min_freq:
                continue

            # 你原本的長度過濾（建議先保留；要更大再放寬）
            if len(word) <= 1 or len(word) > 8:
                continue

            # （可選）如果你想只保留全中文，可打開下面這行
            # if not is_all_chinese(word.replace("$", "")):
            #     continue

            # 合併策略：同 key 保留最大 freq（避免被低頻覆蓋）
            prev = int(word_map.get(word, "0"))
            if freq_i > prev:
                word_map[word] = str(freq_i)

out_file = "merge_" + "_".join(str(n) for n in N_LIST) + ".txt"
with open(out_file, "w", encoding="utf-8") as out:
    for word, freq in word_map.items():
        out.write(word + "\t" + freq + "\n")

print(f"[INFO] MIN_FREQ_BY_N={MIN_FREQ_BY_N}")
print(f"[INFO] wrote {out_file}, entries={len(word_map)}")
