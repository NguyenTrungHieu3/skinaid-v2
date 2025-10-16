# SkinAid AI/ML Module

## Overview

The AI/ML module of SkinAid is responsible for detecting skin conditions in uploaded images and classifying their severity. This module uses state-of-the-art computer vision techniques to provide accurate analysis of skin conditions.

## Features

- **Object Detection**: Uses YOLOv8 to detect various skin conditions
- **Severity Classification**: Classifies the severity of detected conditions
- **RESTful API**: Exposes endpoints for integration with other services
- **Docker Support**: Containerized for easy deployment
- **Comprehensive Documentation**: Detailed guides for installation, usage, and development

## Directory Structure

```
SkinAid/
│── README.md # Giới thiệu tổng quan dự án, hướng dẫn cài đặt & chạy
│── docker-compose.yml # Orchestrate backend, frontend, AI service
│── .gitignore
│
├── backend/ # API & logic xử lý
│ ├── src/
│ │ ├── main.py # Entry point
│ │ ├── api/ # Route/API endpoints
│ │ ├── services/ # Business logic
│ │ ├── models/ # ORM models (nếu dùng DB)
│ │ ├── utils/ # Helper functions
│ │ └── config/ # Cấu hình (DB, env, logging)
│ ├── tests/ # Unit & integration tests
│ ├── docs/ # API docs (OpenAPI/Swagger)
│ ├── requirements.txt # Python dependencies
│ ├── Dockerfile
│ └── README.md
│
├── frontend/ # ReactJS app
│ ├── public/ # Static files
│ ├── src/
│ │ ├── components/ # UI components
│ │ ├── pages/ # Mỗi page chính (Home, Upload, Result…)
│ │ ├── services/ # Gọi API từ backend
│ │ ├── hooks/ # Custom React hooks
│ │ ├── utils/ # Helper JS/TS
│ │ └── assets/ # Ảnh, icon, style
│ ├── tests/ # Unit tests (Jest/RTL)
│ ├── package.json
│ ├── vite.config.js / webpack.config.js
│ ├── Dockerfile
│ └── README.md
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
```

## Cách chạy

### Bước 1

Chạy lệnh sau trong terminal:

```bash
python run.py
```

### Bước 2

Mở trình duyệt và truy cập một trong hai địa chỉ sau:

- [http://localhost:8001](http://localhost:8001)
- [http://127.0.0.1:8001](http://127.0.0.1:8001)

```


```
