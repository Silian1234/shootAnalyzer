import json
import os
import cv2

# Параметры (чётко разнесены по train/val)
CONFIGS = [
    {
        "IMAGES_DIR": 'data/images/train',
        "LABELS_OUT": 'data/labels/train',
        "EXPORT": 'export.json'
    },
    {
        "IMAGES_DIR": 'data/images/val',
        "LABELS_OUT": 'data/labels/val',
        "EXPORT": 'project-1-at-2025-07-14-23-02-5beef2bd.json'
    }
]
BOX_PIX = 20

def process_json(IMAGES_DIR, LABELS_OUT, EXPORT):
    os.makedirs(LABELS_OUT, exist_ok=True)
    with open(EXPORT, encoding='utf-8') as f:
        tasks = json.load(f)

    for task in tasks:
        img_url = None
        data = task.get('data', {})
        for v in data.values():
            if isinstance(v, str) and v.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_url = v
                break
        if not img_url:
            for key in ('image', 'img'):
                if key in data:
                    img_url = data[key]
                    break
        if not img_url:
            print("[WARN] Не найден URL картинки в task['data']")
            continue

        orig_name = os.path.basename(img_url)
        idx = orig_name.lower().find('photo')
        base = orig_name[idx:] if idx != -1 else orig_name

        actual_img = None
        for fname in os.listdir(IMAGES_DIR):
            if fname.endswith(base):
                actual_img = fname
                break
        if not actual_img:
            print(f"[WARN] Не найден файл, оканчивающийся на «{base}» в {IMAGES_DIR}")
            continue

        img_path = os.path.join(IMAGES_DIR, actual_img)
        img = cv2.imread(img_path)
        if img is None:
            print(f"[WARN] Не удалось прочитать изображение {img_path}")
            continue
        h, w = img.shape[:2]

        txt_name = os.path.splitext(base)[0] + '.txt'
        out_path = os.path.join(LABELS_OUT, txt_name)

        results = []
        if task.get('annotations'):
            if isinstance(task['annotations'], list) and len(task['annotations']) > 0:
                results = task['annotations'][0].get('result', [])
        elif task.get('predictions'):
            if isinstance(task['predictions'], list) and len(task['predictions']) > 0:
                results = task['predictions'][0].get('result', [])

        lines = []
        for obj in results:
            val = obj.get('value', {})
            if 'x' in val and 'y' in val:
                cxn = (val['x'] / 100.0)
                cyn = (val['y'] / 100.0)
                bw = BOX_PIX / w
                bh = BOX_PIX / h
                lines.append(f"0 {cxn:.6f} {cyn:.6f} {bw:.6f} {bh:.6f}")

        with open(out_path, 'w', encoding='utf-8') as fo:
            fo.write('\n'.join(lines))

        print(f"[OK] {actual_img} → {txt_name} ({len(lines)} объектов)")

# Основной цикл — обработка train и val отдельно
for cfg in CONFIGS:
    process_json(cfg["IMAGES_DIR"], cfg["LABELS_OUT"], cfg["EXPORT"])
