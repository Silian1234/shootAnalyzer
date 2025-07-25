from ultralytics import YOLO

# Используем предобученную nano‐модель
model = YOLO('yolov8n.pt')

model.train(
    data='data_config.yaml',
    imgsz=640,
    epochs=50,
    batch=8,
    name='holes_yolov8n'
)
