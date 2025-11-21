# SkinAid Project Overview

## 1. Introduction
**Project Name:** SkinAid
**Purpose:** An AI-powered application for detecting and classifying skin conditions from images. It aims to assist users in identifying potential skin issues and assessing their severity.

## 2. System Architecture
The project follows a modern full-stack architecture with a dedicated AI/ML service:

### **Frontend (Client Side)**
- **Tech Stack:** React, TypeScript, Vite.
- **Role:** Provides a user-friendly interface for users to upload images of skin conditions and view analysis results.
- **Key Features:**
  - Image upload functionality.
  - Real-time feedback and result visualization.
  - Responsive design for various devices.

### **Backend (Server Side)**
- **Tech Stack:** Python, FastAPI.
- **Role:** Acts as the central orchestrator, managing user requests, handling file uploads, and communicating with the AI service.
- **Key Features:**
  - RESTful API endpoints (v1).
  - Static file serving for uploaded images.
  - CORS configuration for secure frontend communication.

### **AI/ML Service (Core Intelligence)**
- **Tech Stack:** Python, PyTorch/TensorFlow (implied), YOLOv8, EfficientNetV2.
- **Role:** Performs the actual image analysis.
- **Key Components:**
  - **Object Detection:** Uses YOLOv8 to locate skin conditions within an image.
  - **Classification:** Uses EfficientNetV2 (or similar) to classify the severity or type of the condition.
  - **Pipeline:** An automated pipeline that processes images through detection and classification stages.

## 3. User Flow (The "Story")
This flow describes how the system works from a user's perspective, which is ideal for creating animation scripts:

1.  **Upload:** The user opens the SkinAid web app and uploads a photo of a skin area.
2.  **Processing:**
    - The Frontend sends the image to the Backend API.
    - The Backend saves the image and forwards it to the AI/ML Service.
3.  **Analysis:**
    - The AI Service first runs **Object Detection** to find the wound/condition.
    - It then runs **Classification** to determine the type and severity.
4.  **Result:**
    - The analysis results (bounding boxes, condition name, severity score) are sent back to the Backend.
    - The Backend forwards these results to the Frontend.
5.  **Display:** The user sees their original image with the condition highlighted and a detailed report on the screen.

## 4. Key Technical Highlights for Animation
- **AI Brain:** Visualizing the neural network processing the image.
- **Scanning Effect:** A visual scan over the uploaded image to represent detection.
- **Data Flow:** Packets of data moving between the Phone/PC (Frontend), the Server (Backend), and the AI Engine.
- **Security:** Secure handling of medical-related images.

## 5. Directory Structure Summary
- `frontend/`: UI code.
- `backend/`: API server code.
- `ai_ml/`: Machine learning models and inference scripts.
