SkinAid/
│── README.md # Giới thiệu tổng quan dự án, hướng dẫn cài đặt & chạy
│── docker-compose.yml # Orchestrate backend, frontend, AI service
│── .gitignore
│
├── backend/ # API & logic xử lý
│
├── frontend/ # ReactJS app
│
├── ai-ml/ # Model training + inference
│ ├── notebooks/ # Jupyter notebooks (EDA, thử nghiệm)
│ ├── src/
│ │ ├── detection/ # YOLOv11 training & inference
│ │ ├── classification/ # EfficientNetV2 training & inference
│ │ ├── utils/ # Preprocessing, augmentation, metrics
│ │ ├── pipelines/ # End-to-end pipeline scripts
│ │ └── api/ # Inference API (REST/gRPC) nếu deploy riêng
│ ├── data/ # (gitignore: chỉ để lưu sample, không lưu full dataset)
│ ├── models/ # Lưu trọng số model (.pt, .h5) (gitignore)
│ ├── tests/ # Unit tests cho preprocessing, inference
│ ├── requirements.txt # Python deps (torch, ultralytics, etc.)
│ ├── Dockerfile
│ └── README.md
│
└── docs/ # Tài liệu chung (design, báo cáo, UML, meeting notes)
