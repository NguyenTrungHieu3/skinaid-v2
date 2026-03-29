// src/utils/imageProcessingUtils.ts

// 1. Hàm tính toán chất lượng ảnh (Độ sáng, Độ nét)
export const analyzeImageQuality = (
    imageSrc: string
  ): Promise<{
    isBlurry: boolean;
    blurScore: number;
    brightness: "ok" | "dark" | "bright";
    brightnessScore: number;
  }> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.src = imageSrc;
  
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        if (!ctx) return reject("No context");
  
        // Resize về kích thước nhỏ để tính toán cho nhanh (width = 512px)
        const scale = 512 / img.width;
        canvas.width = 512;
        canvas.height = img.height * scale;
  
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
  
        // --- A. TÍNH ĐỘ SÁNG (Brightness) ---
        let colorSum = 0;
        for (let i = 0; i < data.length; i += 4) {
          const avg = Math.floor((data[i] + data[i + 1] + data[i + 2]) / 3);
          colorSum += avg;
        }
        const brightnessScore = Math.floor(colorSum / (data.length / 4));
        
        let brightness: "ok" | "dark" | "bright" = "ok";
        if (brightnessScore < 60) brightness = "dark"; // Quá tối
        if (brightnessScore > 220) brightness = "bright"; // Quá sáng (cháy sáng)
  
        // --- B. TÍNH ĐỘ MỜ (Blur - Edge Detection đơn giản) ---
        // Thuật toán Laplacien đơn giản hóa: Tính sự chênh lệch giữa các pixel liền kề
        let edgeSum = 0;
        const w = canvas.width;
        const h = canvas.height;
        
        for (let y = 0; y < h; y += 2) { // Nhảy bước để tối ưu
          for (let x = 0; x < w; x += 2) {
            const i = (y * w + x) * 4;
            // So sánh pixel hiện tại với pixel bên phải
            if (x < w - 1) {
               const current = (data[i] + data[i+1] + data[i+2]) / 3;
               const right = (data[i+4] + data[i+5] + data[i+6]) / 3;
               edgeSum += Math.abs(current - right);
            }
          }
        }
        
        // Điểm số càng cao càng nét, càng thấp càng mờ
        // Ngưỡng này cần tinh chỉnh tùy thực tế, ví dụ < 8 là mờ
        const blurScore = edgeSum / ((w * h) / 4); 
        const isBlurry = blurScore < 5; 
  
        resolve({ isBlurry, blurScore, brightness, brightnessScore });
      };
  
      img.onerror = (e) => reject(e);
    });
  };
  
  // 2. Hàm Auto Enhance (Tự động chỉnh sửa)
  export const autoEnhanceImage = (imageSrc: string): Promise<string> => {
    return new Promise((resolve) => {
      const img = new Image();
      img.src = imageSrc;
      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d");
        
        if(ctx) {
            // A. Áp dụng filter CSS của Canvas
            // Tăng độ sáng 10%, Tăng tương phản 10%, saturate 10%
            ctx.filter = 'brightness(1.1) contrast(1.1) saturate(1.1)';
            ctx.drawImage(img, 0, 0);
  
            // B. Sharpen (Làm nét) - Dùng Convolution Matrix
            // (Đây là phần nâng cao, nếu filter css đủ tốt thì có thể bỏ qua bước này để nhẹ máy)
            // Ở đây ta dùng filter css đơn giản cho nhanh
            
            resolve(canvas.toDataURL("image/jpeg", 0.95));
        }
      };
    });
  };