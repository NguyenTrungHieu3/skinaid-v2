// constants/knowledgeArticles.ts
import { ImageSourcePropType } from 'react-native';

export type KnowledgeSection = {
  icon: string;
  iconBg: string;
  title: string;
  text: string;
  image?: ImageSourcePropType;
};

export type KnowledgeArticle = {
  id: string;
  tag: string;
  tagColor: string;
  tagBg: string;
  title: string;
  emoji: string;
  heroEmoji: string;
  heroBg: string;
  thumbnail: ImageSourcePropType;
  sections: KnowledgeSection[];
};

export const KNOWLEDGE_ARTICLES: KnowledgeArticle[] = [
  // ── Bài 1: 5 thói quen làm đẹp ────────────────────────────────────────────
  {
    id: 'skincare-morning',
    tag: 'LÀM ĐẸP', tagColor: '#1D9E75', tagBg: '#E1F5EE',
    title: '5 thói quen giúp da luôn sáng khỏe mỗi sáng',
    emoji: '✨', heroEmoji: '🌿', heroBg: '#E1F5EE',
    thumbnail: require('../assets/kt_mh/kt1-overview.png'),
    sections: [
      {
        icon: '💧', iconBg: '#E1F5EE',
        title: 'Thói quen 1: Uống nước ấm',
        text: 'Uống 1 ly nước ấm ngay sau khi thức dậy để thải độc và cấp ẩm cho cơ thể.',
        image: require('../assets/kt_mh/kt1-tq1.png'),
      },
      {
        icon: '🧴', iconBg: '#E1F5EE',
        title: 'Thói quen 2: Làm sạch dịu nhẹ',
        text: 'Rửa mặt bằng sữa rửa mặt phù hợp để loại bỏ bã nhờn tích tụ qua đêm.',
        image: require('../assets/kt_mh/kt1-tq2.png'),
      },
      {
        icon: '🍋', iconBg: '#E1F5EE',
        title: 'Thói quen 3: Cung cấp dưỡng chất',
        text: 'Sử dụng serum (như Vitamin C) để làm sáng và chống oxy hóa.',
        image: require('../assets/kt_mh/kt1-tq3.png'),
      },
      {
        icon: '🌊', iconBg: '#E1F5EE',
        title: 'Thói quen 4: Khóa ẩm & bảo vệ',
        text: 'Thoa kem dưỡng ẩm để khóa ẩm, giúp da căng mịn cả ngày.',
        image: require('../assets/kt_mh/kt1-tq4.png'),
      },
      {
        icon: '☀️', iconBg: '#FAEEDA',
        title: 'Thói quen 5: Thoa kem chống nắng ⭐',
        text: 'Bước quan trọng nhất! Dùng kem chống nắng SPF30+ mỗi ngày.',
        image: require('../assets/kt_mh/kt1-tq5.png'),
      },
    ],
  },

  // ── Bài 2: Quy trình xử lý vết thương ─────────────────────────────────────
  {
    id: 'wound-treatment',
    tag: 'Y TẾ', tagColor: '#185FA5', tagBg: '#E6F1FB',
    title: 'Quy trình xử lý vết thương đúng chuẩn',
    emoji: '🩹', heroEmoji: '🏥', heroBg: '#E6F1FB',
    thumbnail: require('../assets/kt_mh/kt2-overview.jpg'),
    sections: [
      {
        icon: '🧤', iconBg: '#E6F1FB',
        title: '1. Chuẩn bị',
        text: 'Rửa tay sạch, đeo găng tay y tế. Chuẩn bị nước muối sinh lý, gạc vô trùng, băng dính.',
        image: require('../assets/kt_mh/kt2-qt1.png'),
      },
      {
        icon: '🩸', iconBg: '#FCEBEB',
        title: '2. Cầm máu',
        text: 'Dùng gạc vô trùng ép nhẹ lên vết thương 5–10 phút cho đến khi máu ngừng chảy.',
        image: require('../assets/kt_mh/kt2-qt2.png'),
      },
      {
        icon: '💦', iconBg: '#E6F1FB',
        title: '3. Làm sạch',
        text: 'Rửa vết thương bằng nước muối sinh lý. Dùng nhíp vô trùng loại bỏ dị vật.',
        image: require('../assets/kt_mh/kt2-qt3.png'),
      },
      {
        icon: '💊', iconBg: '#EAF3DE',
        title: '4. Sát trùng và băng bó',
        text: 'Bôi thuốc mỡ kháng sinh, che bằng gạc vô trùng và cố định bằng băng dính.',
        image: require('../assets/kt_mh/kt2-qt4.png'),
      },
      {
        icon: '📅', iconBg: '#E6F1FB',
        title: '5. Theo dõi và thay băng',
        text: 'Thay băng ít nhất 1 lần/ngày. Theo dõi dấu hiệu nhiễm trùng: sưng, đỏ, đau.',
        image: require('../assets/kt_mh/kt2-qt5.png'),
      },
    ],
  },

  // ── Bài 3: Sơ cứu bỏng ────────────────────────────────────────────────────
  {
    id: 'burn-firstaid',
    tag: 'SƠ CỨU', tagColor: '#993C1D', tagBg: '#FAECE7',
    title: 'Cách sơ cứu bỏng tại nhà an toàn và hiệu quả',
    emoji: '🔥', heroEmoji: '🚿', heroBg: '#FAECE7',
    thumbnail: require('../assets/kt_mh/kt3-overview.png'),
    sections: [
      {
        icon: '🚿', iconBg: '#FAECE7',
        title: 'Bước 1: Làm mát vết bỏng ngay',
        text: 'Đưa vùng da bỏng dưới vòi nước mát (không dùng đá) trong 10–20 phút.',
        image: require('../assets/kt_mh/kt3-sc1.png'),
      },
      {
        icon: '🧼', iconBg: '#E6F1FB',
        title: 'Bước 2: Làm sạch và bảo vệ',
        text: 'Nhẹ nhàng rửa sạch. Không chà xát hoặc làm vỡ bóng nước.',
        image: require('../assets/kt_mh/kt3-sc2.png'),
      },
      {
        icon: '🌿', iconBg: '#EAF3DE',
        title: 'Bước 3: Làm dịu da',
        text: 'Dùng gel nha đam hoặc kem chuyên dụng. Tránh kem đánh răng hay mẹo dân gian.',
        image: require('../assets/kt_mh/kt3-sc3.png'),
      },
      {
        icon: '🧊', iconBg: '#E6F1FB',
        title: 'Bước 4: Giảm đau và sưng',
        text: 'Dùng khăn sạch hoặc túi chườm mát — không đặt đá trực tiếp lên da.',
        image: require('../assets/kt_mh/kt3-sc4.png'),
      },
      {
        icon: '🩹', iconBg: '#E1F5EE',
        title: 'Bước 5: Băng vết bỏng',
        text: 'Dùng gạc vô trùng băng nhẹ lại. Không băng quá chặt.',
        image: require('../assets/kt_mh/kt3-sc5.png'),
      },
      {
        icon: '🏥', iconBg: '#FCEBEB',
        title: 'Bước 6: Đi khám khi cần ⚠️',
        text: 'Đến bệnh viện nếu bỏng diện rộng, sâu, ở mặt/tay/chân, hoặc trẻ em/người lớn tuổi.',
        image: require('../assets/kt_mh/kt3-sc6.png'),
      },
    ],
  },

  // ── Bài 4: Viêm da cơ địa ─────────────────────────────────────────────────
  {
    id: 'eczema-signs',
    tag: 'DA LIỄU', tagColor: '#854F0B', tagBg: '#FAEEDA',
    title: 'Nhận biết sớm các dấu hiệu viêm da cơ địa',
    emoji: '🔍', heroEmoji: '🔬', heroBg: '#FAEEDA',
    thumbnail: require('../assets/kt_mh/kt4-overview.png'),
    sections: [
      {
        icon: '🏜️', iconBg: '#FAEEDA',
        title: '1. Da khô bất thường',
        text: 'Da dễ bị khô, bong tróc, sần sùi. Cảm giác căng rát, nhất là sau khi tắm.',
        image: require('../assets/kt_mh/kt4-vd1.jpg'),
      },
      {
        icon: '🔴', iconBg: '#FCEBEB',
        title: '2. Xuất hiện vùng da đỏ',
        text: 'Các mảng đỏ nhỏ hoặc lan rộng, thường ở má, cổ, khuỷu tay, đầu gối.',
        image: require('../assets/kt_mh/kt4-vd2.jpg'),
      },
      {
        icon: '😣', iconBg: '#FAEEDA',
        title: '3. Ngứa nhiều (đặc biệt về đêm)',
        text: 'Ngứa dai dẳng, càng gãi càng ngứa, ảnh hưởng đến giấc ngủ.',
        image: require('../assets/kt_mh/kt4-vd3.jpg'),
      },
      {
        icon: '💧', iconBg: '#E6F1FB',
        title: '4. Da nổi mụn nước nhỏ',
        text: 'Mụn li ti, có thể rỉ dịch khi vỡ, dễ nhiễm trùng nếu không chăm sóc đúng.',
        image: require('../assets/kt_mh/kt4-vd4.jpg'),
      },
      {
        icon: '🟤', iconBg: '#FAEEDA',
        title: '5. Da dày lên, sạm màu',
        text: 'Do gãi nhiều lâu ngày, da thô ráp và sậm màu hơn vùng xung quanh.',
        image: require('../assets/kt_mh/kt4-vd5.jpg'),
      },
      {
        icon: '🔄', iconBg: '#EAF3DE',
        title: '6. Tái đi tái lại nhiều lần',
        text: 'Bệnh mãn tính, triệu chứng xuất hiện rồi giảm, sau đó lại tái phát.',
      },
    ],
  },

  // ── Bài 5: 10 thực phẩm tốt cho da ───────────────────────────────────────
  {
    id: 'skin-foods',
    tag: 'DINH DƯỠNG', tagColor: '#3B6D11', tagBg: '#EAF3DE',
    title: '10 loại thực phẩm tốt cho làn da từ bên trong',
    emoji: '🥑', heroEmoji: '🥗', heroBg: '#EAF3DE',
    thumbnail: require('../assets/kt_mh/kt5-overview.png'),
    sections: [
      {
        icon: '🥑', iconBg: '#EAF3DE',
        title: '1. Quả bơ',
        text: 'Giàu Vitamin E và chất béo lành mạnh — giúp da mềm mịn, chậm lão hóa.',
        image: require('../assets/kt_mh/kt5-tp1.jpg'),
      },
      {
        icon: '🐟', iconBg: '#E6F1FB',
        title: '2. Cá hồi',
        text: 'Chứa omega-3 và astaxanthin — giảm viêm da, hạn chế mụn, tăng độ đàn hồi.',
        image: require('../assets/kt_mh/kt5-tp2.jpg'),
      },
      {
        icon: '🍊', iconBg: '#FAECE7',
        title: '3. Quả cam',
        text: 'Giàu Vitamin C — sản xuất collagen, làm sáng da, giảm thâm.',
        image: require('../assets/kt_mh/kt5-tp3.jpg'),
      },
      {
        icon: '🥬', iconBg: '#EAF3DE',
        title: '4. Rau bina',
        text: 'Vitamin A, C, K và sắt — tái tạo tế bào da, giảm xỉn màu.',
        image: require('../assets/kt_mh/kt5-tp4.jpg'),
      },
      {
        icon: '🍅', iconBg: '#FCEBEB',
        title: '5. Cà chua',
        text: 'Giàu lycopene — chống nắng tự nhiên từ bên trong, bảo vệ da khỏi UV.',
        image: require('../assets/kt_mh/kt5-tp5.jpg'),
      },
      {
        icon: '🌰', iconBg: '#FAEEDA',
        title: '6. Hạnh nhân',
        text: 'Vitamin E và kẽm — da căng mịn, giảm mụn, hỗ trợ phục hồi da.',
        image: require('../assets/kt_mh/kt5-tp6.jpg'),
      },
      {
        icon: '🍠', iconBg: '#FAEEDA',
        title: '7. Khoai lang',
        text: 'Beta-carotene — chống nắng tự nhiên, giảm khô và làm đều màu da.',
        image: require('../assets/kt_mh/kt5-tp7.jpg'),
      },
      {
        icon: '🥛', iconBg: '#E6F1FB',
        title: '8. Sữa chua',
        text: 'Probiotic — tiêu hóa khỏe, giảm mụn nội tiết, cải thiện da từ gốc.',
        image: require('../assets/kt_mh/kt5-tp8.jpg'),
      },
      {
        icon: '🍫', iconBg: '#FAEEDA',
        title: '9. Socola đen',
        text: 'Flavonoid chống oxy hóa — tăng tuần hoàn máu dưới da, da hồng hào hơn.',
        image: require('../assets/kt_mh/kt5-tp9.jpg'),
      },
      {
        icon: '🍵', iconBg: '#EAF3DE',
        title: '10. Trà xanh',
        text: 'EGCG chống viêm mạnh — giảm dầu nhờn, hỗ trợ trị mụn và chậm lão hóa.',
        image: require('../assets/kt_mh/kt5-tp10.jpg'),
      },
    ],
  },
];
