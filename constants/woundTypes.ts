// constants/woundTypes.ts

export interface WoundType {
  id: string;
  name: string;
  description: string;
  emoji: string;
  gradientColors: [string, string];
  accentColor: string;
}

export const WOUND_TYPES: WoundType[] = [
  {
    id: "bam",
    name: "Bầm",
    description: "Nhận diện vết tụ máu dưới da...",
    emoji: "✳️",
    gradientColors: ["#E8F5F2", "#D0EDE8"],
    accentColor: "#02A18D",
  },
  {
    id: "bong",
    name: "Bỏng",
    description: "Phân tích mức độ tổn thương nhiệt...",
    emoji: "🔥",
    gradientColors: ["#FFF3E8", "#FFE4CC"],
    accentColor: "#E87440",
  },
  {
    id: "tray",
    name: "Trầy",
    description: "Vết trầy xước bề mặt da...",
    emoji: "🩹",
    gradientColors: ["#FFF0F0", "#FFD6D6"],
    accentColor: "#E05050",
  },
  {
    id: "vay-nen",
    name: "Vảy nến",
    description: "Sàng lọc sớm các dấu hiệu...",
    emoji: "🩺",
    gradientColors: ["#FFF3F0", "#FFE0DA"],
    accentColor: "#C04A3A",
  },
  {
    id: "mun-trung-ca",
    name: "Mụn trứng cá",
    description: "Phân biệt các loại mụn trứng cá...",
    emoji: "😶",
    gradientColors: ["#F0F8FF", "#D6EEFF"],
    accentColor: "#3A7BD5",
  },
  {
    id: "nam-da",
    name: "Nấm da",
    description: "Nhận diện nấm da...",
    emoji: "⚙️",
    gradientColors: ["#F5F0FF", "#E6D6FF"],
    accentColor: "#7B4FD5",
  },
];

export const APP_STATS = {
  accuracy: "95%",
  users: "10k+",
  woundTypes: "50k+",
};
