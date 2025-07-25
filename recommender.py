from __future__ import annotations
from collections import Counter

scenario_data = {
    "1":  ("Три и более попаданий в центр— идеально, рекомендаций нет.", None),
    "2":  ("Попадания смещены в левый нижний угол мишени.", "https://vk.com/s/v1/doc/O7ULpk7A8HkI7BL_Agm4luUEah-_Z29jnZf-ALoH-e5VS75psAw"),
    "3":  ("Попадания смещены влево от центра.", "https://vk.com/s/v1/doc/LE9k2Frolx33wtTZ_eutyujbELwaVngdjcmkptSl4iWec-aArrY"),
    "4":  ("Попадания смещены в левый верхний угол.", "https://vk.com/s/v1/doc/xyTnw-iS8ZDIv1mHC-poCynjJxWberImnODQ2ptvbuYX85ofKgw"),
    "5":  ("Попадания смещены вверх по центру.", "https://vk.com/s/v1/doc/9B1txaFaev1JCkj8RkdswR_gXuZW7M9lSwGQMBqbrtSB5dKP51I"),
    "6":  ("Попадания смещены в правый верхний угол.", "https://vk.com/s/v1/doc/Uaz9pJULITeoEYCbLR8MAHWyf-LJk-WTXT--fl9Mw1M2uHcAaDY"),
    "7":  ("Попадания смещены вправо от центра.", "https://vk.com/s/v1/doc/jRDfZRar0Edt4SF2lVLAEiXFWKD3gBvGwYtCImvLfJ-SZYDAUG8"),
    "8":  ("Попадания смещены в правый нижний угол.", "https://vk.com/s/v1/doc/5WCVM31M0LMc4oqoyf_WkNVKJvzT4o1AU3iuaoo0JZnkTJW2djM"),
    "9":  ("Попадания смещены вниз по центру.", "https://vk.com/s/v1/doc/KuTyswcY0r2CIw1S0azgLY6a-Uk2OAIw87d4IiPeCLu83la8rgk"),
    "10": ("Только одно попадание внутри мишени, остальные вне.", "https://vk.com/s/v1/doc/ySS2LqMQUzAlVJbt6bhJkY8FUtRZLTFrmGdtPFvlW6jAw-cJVwU"),
    "11": ("Часть пуль в центре, часть в секторе 3.", "https://vk.com/s/v1/doc/H8rEo7l-lqY3kPWz5zh6aybxItovpcXd5N1YzXVdatsg1plxcDc"),
    "12": ("Все четыре пули вне мишени.", "https://vk.com/s/v1/doc/mXUIa2JZ-_Exe-Xd2x5bBQ16vqS9RUdVbjr58JfFZ5zG3YP-A7s"),
    "13": ("Попадания разбросаны по всей мишени.", "https://vk.com/s/v1/doc/jOaKDm_TxI1VeLZJ3ud_dl3yE4uIJa4HOpeYML07lB-xSZiFWPs"),
}

ADJ = {
    "1":  ["2", "3", "4", "5", "6", "7", "8", "9"],
    "2":  ["1", "3", "9", "10"],
    "3":  ["1", "2", "4"],
    "4":  ["1", "3", "5"],
    "5":  ["1", "4", "6"],
    "6":  ["1", "5", "7"],
    "7":  ["1", "6", "8"],
    "8":  ["1", "7", "9", "10"],
    "9":  ["1", "8", "2", "10"],
    "10": ["2", "8", "9"],
}

DIAGONALS = {"2", "4", "6", "8"}

def get_recommendation(zones: list[str]) -> tuple[str, str, str] | None:
    zones = [z.strip().upper() for z in zones][:4]
    zones += [''] * (4 - len(zones))
    cnt = Counter(z for z in zones if z)
    inside = sum(cnt.values())
    non_center_zones = [z for z in zones if z not in ("", "1")]
    uniq = set(non_center_zones)
    if len(uniq) >= 3:
        return "13", *scenario_data["13"]
    if len(uniq) == 2:
        a, b = tuple(uniq)
        if b not in ADJ[a]:
            return "13", *scenario_data["13"]
    if inside == 0:
        return "12", *scenario_data["12"]
    if inside == 1:
        return "10", *scenario_data["10"]
    if inside == 4 and set(cnt) <= {"1", "3"} and cnt["3"] >= 2 and cnt["1"] >= 1:
        return "11", *scenario_data["11"]
    if cnt.get("1", 0) >= 3:
        return "1", *scenario_data["1"]
    non_center = {z: n for z, n in cnt.items() if z != "1"}
    if not non_center:
        return "9", *scenario_data["9"]
    max_cnt = max(non_center.values())
    cands = [z for z, n in non_center.items() if n == max_cnt]
    diag = [z for z in cands if z in DIAGONALS]
    base = diag[0] if diag else sorted(cands)[0]
    if base == "2" and cnt.get("10", 0) == max_cnt:
        return "2/10", f"{scenario_data['2'][0]} + {scenario_data['10'][0]}", None
    cluster_ok = set(cnt) <= set([base] + ADJ[base] + ["1"])
    if cluster_ok:
        return base, *scenario_data[base]
    return "13", *scenario_data["13"]
