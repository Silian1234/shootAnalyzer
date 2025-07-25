import os
import random
import shutil

SRC_IMG_DIR   = 'data/images/all'
SRC_LABEL_DIR = 'data/labels/all'

TRAIN_IMG_DIR   = 'data/images/train'
VAL_IMG_DIR     = 'data/images/val'
TRAIN_LBL_DIR   = 'data/labels/train'
VAL_LBL_DIR     = 'data/labels/val'

TRAIN_RATIO = 0.8
SEED        = 42

def prepare_dirs():
    for d in [TRAIN_IMG_DIR, VAL_IMG_DIR, TRAIN_LBL_DIR, VAL_LBL_DIR]:
        os.makedirs(d, exist_ok=True)

def list_images():
    return [f for f in os.listdir(SRC_IMG_DIR)
            if f.lower().endswith(('.jpg','.jpeg','.png'))]

def is_positive(img_name: str) -> bool:
    # считаем положительным, если файл с аннотацией не пустой
    lbl = img_name.rsplit('.',1)[0] + '.txt'
    path = os.path.join(SRC_LABEL_DIR, lbl)
    return os.path.exists(path) and os.path.getsize(path) > 0

def split_and_copy():
    imgs = list_images()
    positives = [f for f in imgs if is_positive(f)]
    negatives = [f for f in imgs if not is_positive(f)]

    if len(negatives) > len(positives):
        random.seed(SEED)
        negatives = random.sample(negatives, len(positives))

    all_sel = positives + negatives
    random.shuffle(all_sel)

    split_idx = int(len(all_sel) * TRAIN_RATIO)
    train_imgs = all_sel[:split_idx]
    val_imgs   = all_sel[split_idx:]

    # Копируем
    for img_set, img_dir, lbl_dir in (
        (train_imgs, TRAIN_IMG_DIR, TRAIN_LBL_DIR),
        (val_imgs,   VAL_IMG_DIR,   VAL_LBL_DIR),
    ):
        for fname in img_set:
            src_img = os.path.join(SRC_IMG_DIR, fname)
            dst_img = os.path.join(img_dir, fname)
            shutil.copy(src_img, dst_img)

            lbl = fname.rsplit('.',1)[0] + '.txt'
            src_lbl = os.path.join(SRC_LABEL_DIR, lbl)
            dst_lbl = os.path.join(lbl_dir, lbl)
            if not os.path.exists(src_lbl) or os.path.getsize(src_lbl) == 0:
                open(dst_lbl, 'w').close()
            else:
                shutil.copy(src_lbl, dst_lbl)

    print(f"Train: {len(train_imgs)} (+{len([f for f in train_imgs if is_positive(f)])} pos, "
          f"{len([f for f in train_imgs if not is_positive(f)])} neg)")
    print(f" Val : {len(val_imgs)} (+{len([f for f in val_imgs if is_positive(f)])} pos, "
          f"{len([f for f in val_imgs if not is_positive(f)])} neg)")

if __name__ == '__main__':
    prepare_dirs()
    split_and_copy()
