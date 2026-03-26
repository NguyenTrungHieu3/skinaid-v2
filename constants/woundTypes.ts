// constants/woundTypes.ts
// Tách data ra đây để dễ thêm/sửa/xóa loại vết thương

export interface WoundType {
  id: string;
  name: string;
  description: string;
  emoji: string;
  bgColor: string;
  borderColor: string;
}

export const WOUND_TYPES: WoundType[] = [
  {
    id: "bam",
    name: "Bầm",
    description: "Nhận diện vết thương bầm",
    emoji: "🟤",
    bgColor: "#FFF5F0",
    borderColor: "#FFCDB2",
  },
  {
    id: "bong",
    name: "Bỏng",
    description: "Nhận diện vết thương bỏng",
    emoji: "🔴",
    bgColor: "#FFF5F0",
    borderColor: "#FFCDB2",
  },
  {
    id: "tray",
    name: "Trầy",
    description: "Nhận diện vết thương trầy",
    emoji: "🟠",
    bgColor: "#FFF5F0",
    borderColor: "#FFCDB2",
  },
  {
    id: "ung-thu-da",
    name: "Ung thư da",
    description: "Nhận diện vết thương ung thư",
    emoji: "🔵",
    bgColor: "#FFF5F0",
    borderColor: "#FFCDB2",
  },
  {
    id: "mun",
    name: "Mụn",
    description: "Nhận diện vết thương mụn",
    emoji: "🟡",
    bgColor: "#FFF5F0",
    borderColor: "#FFCDB2",
  },
  {
    id: "me-day",
    name: "Mề đay",
    description: "Nhận diện vết thương mề đay",
    emoji: "🟣",
    bgColor: "#FFF5F0",
    borderColor: "#FFCDB2",
  },
];

export const APP_STATS = {
  accuracy: "95%",
  users: "10K+",
  woundTypes: "50K+",
};
