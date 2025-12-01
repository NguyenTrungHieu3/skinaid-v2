// src/utils/cropImage.ts

export const createImage = (url: string): Promise<HTMLImageElement> =>
    new Promise((resolve, reject) => {
      const image = new Image();
      image.addEventListener("load", () => resolve(image));
      image.addEventListener("error", (error) => reject(error));
      image.setAttribute("crossOrigin", "anonymous"); // needed to avoid cross-origin issues on CodeSandbox
      image.src = url;
    });
  
  export function getRadianAngle(degreeValue: number) {
    return (degreeValue * Math.PI) / 180;
  }
  
  /**
   * Hàm này nhận vào image url và pixelCrop (tọa độ cắt)
   * Trả về một File object mới đã được cắt
   */
  export default async function getCroppedImg(
    imageSrc: string,
    pixelCrop: { x: number; y: number; width: number; height: number },
    fileName: string = "avatar.jpg"
  ): Promise<File> {
    const image = await createImage(imageSrc);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
  
    if (!ctx) {
      throw new Error("No 2d context");
    }
  
    // Set width/height của canvas bằng đúng kích thước vùng cắt để ảnh chất lượng cao nhất
    canvas.width = pixelCrop.width;
    canvas.height = pixelCrop.height;
  
    // Vẽ ảnh lên canvas theo tọa độ cắt
    ctx.drawImage(
      image,
      pixelCrop.x,
      pixelCrop.y,
      pixelCrop.width,
      pixelCrop.height,
      0,
      0,
      pixelCrop.width,
      pixelCrop.height
    );
  
    // Chuyển canvas thành Blob, sau đó thành File
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (!blob) {
          reject(new Error("Canvas is empty"));
          return;
        }
        // Tạo File từ Blob
        const file = new File([blob], fileName, { type: "image/jpeg" });
        resolve(file);
      }, "image/jpeg", 1); // 1 = chất lượng 100%
    });
  }