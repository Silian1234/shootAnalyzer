from __future__ import annotations

import sys, traceback, datetime, os, threading, time, shutil, webbrowser
from pathlib import Path
from typing import Optional

import cv2  # type: ignore
import numpy as np
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.resources import resource_find
from kivy.utils import platform
from kivymd.app import MDApp
from android.storage import primary_external_storage_path  # type: ignore

import image_processor
import recommender
import visualizer

def _log_dir() -> Path:
    if platform == "android":
        from android.storage import app_storage_path          # type: ignore
        return Path(app_storage_path()) / "crashlogs"
    return Path(".") / "crashlogs"

_LOG_DIR = _log_dir()
_LOG_DIR.mkdir(parents=True, exist_ok=True)

def _crash_dump(exc_t, exc, tb):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    (_LOG_DIR / f"crash_{ts}.txt").write_text(
        "".join(traceback.format_exception(exc_t, exc, tb)), "utf-8"
    )
    sys.__excepthook__(exc_t, exc, tb)

sys.excepthook = _crash_dump

SHOW_DBG_TOAST = False
def dbg(msg: str) -> None:
    Logger.info(f"DBG: {msg}")
    if SHOW_DBG_TOAST:
        try:
            from kivymd.toast import toast                    # type: ignore
            toast(msg)
        except Exception:
            pass

def _show_toast(txt: str) -> None:
    try:
        from kivymd.toast import toast                        # type: ignore
        toast(txt)
    except Exception:
        print(f"[INFO] {txt}")

def _relax_strict_mode() -> None:
    if platform != "android":
        return
    from jnius import autoclass                               # type: ignore
    StrictMode   = autoclass('android.os.StrictMode')
    VmPolicyBldr = autoclass('android.os.StrictMode$VmPolicy$Builder')
    StrictMode.setVmPolicy(VmPolicyBldr().build())

KV = '''
MDScreen:
    MDTopAppBar:
        title: "Shooting trainer"
        left_action_items: [['folder', lambda x: app.open_image_via_saf()]]
        elevation: 4

    MDTextField:
        id: tf_manual
        hint_text: "Введите 4 зоны (напр. 1,3,4,4)"
        mode: "rectangle"
        size_hint_x: .9
        pos_hint: {'center_x': .5, 'center_y': .86}

    MDRaisedButton:
        text: "Анализ"
        pos_hint: {'center_x': .25, 'center_y': .77}
        on_release: app.on_manual_submit()

    MDRaisedButton:
        text: "Сканировать"
        pos_hint: {'center_x': .75, 'center_y': .77}
        on_release: app.capture_photo()

    AsyncImage:
        id: preview
        size_hint: .9, .5
        allow_stretch: True
        keep_ratio: True
        pos_hint: {'center_x': .5, 'center_y': .46}

    MDLabel:
        id: lbl_result
        text: ''
        halign: 'center'
        theme_text_color: 'Primary'
        size_hint_x: .9
        pos_hint: {'center_x': .5, 'center_y': .14}
'''

TFLITE_PATH      = "best_float32.tflite"
DEFAULT_PREVIEW  = "photo_2025-07-22_14-35-26.jpg"

RC_SAF, RC_CAMERA = 12345, 12346


class ShootingApp(MDApp):

    def build(self):
        self.theme_cls.primary_palette = "BlueGray"
        try:
            from tflite_runtime.interpreter import Interpreter
        except ImportError:
            import tensorflow as tf; Interpreter = tf.lite.Interpreter  # type: ignore
        self.interpreter = Interpreter(model_path=TFLITE_PATH); self.interpreter.allocate_tensors()
        dbg("TFLite model loaded")

        root = Builder.load_string(KV)
        root.ids.lbl_result.bind(on_touch_down=self._on_result_label_touch)
        self._last_pdf: Optional[str] = None

        if (p := resource_find(DEFAULT_PREVIEW)): root.ids.preview.source = p
        if platform == "android":
            from android import activity      # type: ignore
            activity.bind(on_activity_result=self._on_activity_result)
        return root

    def ui_message(self, txt: str):
        _show_toast(txt); Clock.schedule_once(lambda dt: self._set_status(txt), 0)
    def _set_status(self, txt: str): self.root.ids.lbl_result.text = txt

    def on_manual_submit(self):
        zones = [z.strip() for z in self.root.ids.tf_manual.text.replace(';', ',').split(',') if z.strip()]
        self._start_processing(zones or None, None)

    # def _on_result_label_touch(self, lbl, touch):
    #     Легаси: оставлен вызов PDF, но сейчас всегда открываем ссылку.
    #     if lbl.collide_point(*touch.pos):
    #         # if self._last_pdf: self._open_pdf(self._last_pdf)
    #         webbrowser.open("https://vk.com/docs-70980367")
    #         return True

    def open_image_via_saf(self):
        if platform != "android":
            self.ui_message("Доступно только на Android")
            return

        self.ui_message("Выберите изображение…")
        dbg("SAF intent fired")

        from jnius import autoclass                                   # type: ignore
        Intent, PA = autoclass('android.content.Intent'), autoclass('org.kivy.android.PythonActivity')
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("image/*")
        PA.mActivity.startActivityForResult(intent, RC_SAF)

    def capture_photo(self):
        if platform != "android":
            self.ui_message("Доступно только на Android")
            return

        _relax_strict_mode()

        from android.permissions import Permission, check_permission, request_permissions  # type: ignore
        need = [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
        if not all(check_permission(p) for p in need):
            request_permissions(need)
            self.ui_message("Дайте разрешения и нажмите снова")
            return

        try:
            from plyer import camera                                     # type: ignore
            cam_dir = os.path.join(primary_external_storage_path(), "DCIM", "Camera")
            os.makedirs(cam_dir, exist_ok=True)
            dest = os.path.join(cam_dir, f"shot_{int(time.time())}.jpg")

            self._pending_shot = dest
            dbg(f"Camera → {dest}")
            camera.take_picture(filename=dest, on_complete=self._after_camera)
        except Exception as e:
            dbg(f"Camera ERROR: {e}")
            self.ui_message(f"Камера: {e}")

    def _after_camera(self, path: str | None):
        target = path or getattr(self, "_pending_shot", None)
        for _ in range(10):
            if target and os.path.exists(target) and os.path.getsize(target) > 0:
                break
            time.sleep(0.1)

        if not target or not os.path.exists(target):
            self.ui_message("Снимок отменён")
            dbg("Camera cancelled")
            return

        dbg(f"Camera OK {target}")
        self._start_processing(None, target)

    def _on_activity_result(self, rc, res, intent):
        if rc != RC_SAF:
            return
        if res != -1 or not intent or not intent.getData():
            self.ui_message("Файл не выбран")
            return

        uri = intent.getData()
        dest = self._tmp_jpg_path()
        try:
            self._copy_content_uri(uri.toString(), dest)
            dbg(f"SAF copy → {dest} ({os.path.getsize(dest)} bytes)")
            self._start_processing(None, dest)
        except Exception as e:
            self.ui_message(f"Ошибка чтения: {e}")
            dbg(f"SAF ERROR: {e}")

    def _start_processing(self, zones: Optional[list[str]], image_path: Optional[str]):
        threading.Thread(target=self._worker, args=(zones, image_path), daemon=True).start()

    def _worker(self, zones, image_path):
        if image_path:
            img = cv2.imread(image_path)
            dbg(f"imread {img.shape if img is not None else None}")
            if img is None:
                self.ui_message("Не удалось открыть изображение")
                return

            hits = self._run_tflite(img)
            if not hits:
                self.ui_message("Попадания не найдены")
                return

            zones = image_processor.determine_zones(hits, img)
            preview = Path(self.user_data_dir) / f"_prev_{int(time.time())}.png"
            cv2.imwrite(str(preview), visualizer.mark_hits(img, hits))
            Clock.schedule_once(lambda dt: self._update_ui(str(preview), zones), 0)
        else:
            Clock.schedule_once(lambda dt: self._update_ui(None, zones), 0)

    def _update_ui(self, preview_path: Optional[str], zones):
        if preview_path:
            w = self.root.ids.preview ; w.source = preview_path ; w.reload()
        self._show_result(zones)

    def _show_result(self, zones: Optional[list[str]]):
        rec = recommender.get_recommendation(zones)
        if not rec:
            self._last_pdf = None
            self.root.ids.lbl_result.markup = False
            self._set_status("Не удалось классифицировать")
            return

        sid, desc, pdf_link = rec
        self.root.ids.lbl_result.markup = True
        self._set_status(f"[u]Ситуация {sid}: {desc}[/u]")

        # pdf_link теперь ссылка (или None)
        self._last_pdf = pdf_link

    def _on_result_label_touch(self, lbl, touch):
        if self._last_pdf and lbl.collide_point(*touch.pos):
            webbrowser.open(self._last_pdf)
            return True


    def _open_pdf(self, pdf_path: str) -> None:
        # Легаси: этот метод оставлен для будущей работы с PDF
        if not pdf_path or not os.path.exists(pdf_path):
            self.ui_message("PDF‑файл не найден")
            return

        from android.permissions import Permission, check_permission, request_permissions  # type: ignore
        need = [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
        if not all(check_permission(p) for p in need):
            request_permissions(need)
            self.ui_message("Дайте разрешения и нажмите снова")
            return

        if platform == "android":
            try:
                from jnius import autoclass  # type: ignore
                PA = autoclass('org.kivy.android.PythonActivity')
                FP = autoclass('androidx.core.content.FileProvider')
                Intent = autoclass('android.content.Intent')
                File = autoclass('java.io.File')

                target = self._copy_to_download(pdf_path)
                uri = FP.getUriForFile(
                    PA.mActivity,
                    "org.example.shootanalyzer.fileprovider",
                    File(target)
                )

                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(uri, "application/pdf")
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                chooser = Intent.createChooser(intent, "Открыть PDF")
                PA.mActivity.startActivity(chooser)

            except Exception as e:
                dbg(f"PDF open error: {e}")
                self.ui_message("Не удалось открыть PDF")
        else:
            webbrowser.open(Path(pdf_path).as_uri())

    def _tmp_jpg_path(self) -> str:
        name = f"shoot_{int(time.time())}.jpg"
        if platform == "android":
            from android.storage import app_storage_path          # type: ignore
            return os.path.join(app_storage_path(), name)
        return name

    def _copy_to_download(self, src_path: str) -> str:
        if platform != "android":
            return src_path
        dl = Path(primary_external_storage_path()) / "Download"
        dl.mkdir(exist_ok=True)
        dst = dl / Path(src_path).name
        if not dst.exists():
            shutil.copy(src_path, dst)
        return str(dst)

    @staticmethod
    def _copy_content_uri(uri_str: str, dest: str):
        from jnius import autoclass                                # type: ignore
        Uri, PA = autoclass('android.net.Uri'), autoclass('org.kivy.android.PythonActivity')
        resolver = PA.mActivity.getContentResolver()
        inp = resolver.openInputStream(Uri.parse(uri_str))
        if inp is None:
            raise IOError("openInputStream вернул None")
        with open(dest, "wb") as out:
            buf = bytearray(8192)
            while True:
                read = inp.read(buf)                               # type: ignore[attr-defined]
                if read == -1:
                    break
                out.write(buf[:read])
        inp.close()

    def _run_tflite(self, img: np.ndarray) -> list[tuple[int, int]]:
        inp      = self.interpreter.get_input_details()[0]
        INP_W, INP_H = inp["shape"][2], inp["shape"][1]

        boxed, scale, pad_l, pad_t = self._letterbox(img, (INP_W, INP_H))
        tensor = cv2.cvtColor(boxed, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        tensor = tensor[None]

        self.interpreter.set_tensor(inp["index"], tensor)
        self.interpreter.invoke()
        raw = self.interpreter.get_tensor(self.interpreter.get_output_details()[0]["index"]).squeeze()

        if raw.ndim == 3: raw = raw.reshape(raw.shape[1], raw.shape[2])
        if raw.ndim == 2 and raw.shape[0] in (5, 6, 7): raw = raw.T
        if raw.ndim == 1: raw = raw[None]
        if raw.shape[-1] < 5:
            dbg(f"Unsupported output shape {raw.shape}")
            return []

        CONF_THR = 0.25
        H, W = img.shape[:2]
        hits: list[tuple[int, int]] = []

        for bx, by, bw, bh, conf, *_ in raw:
            if conf < CONF_THR:
                continue
            x_lb, y_lb = bx * INP_W, by * INP_H
            x = int((x_lb - pad_l) / scale)
            y = int((y_lb - pad_t) / scale)
            if 0 <= x < W and 0 <= y < H:
                hits.append((x, y))

        dbg(f"valid hits = {hits}")
        return hits

    @staticmethod
    def _letterbox(img: np.ndarray, size=(640, 640), color=(114, 114, 114)):
        ih, iw = img.shape[:2]
        w, h   = size
        r      = min(w / iw, h / ih)
        nw, nh = int(iw * r), int(ih * r)
        pw, ph = w - nw,  h - nh
        pl, pt = pw // 2, ph // 2
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        boxed   = cv2.copyMakeBorder(resized, pt, ph - pt, pl, pw - pl,
                                     cv2.BORDER_CONSTANT, value=color)
        return boxed, r, pl, pt


if __name__ == "__main__":
    ShootingApp().run()
