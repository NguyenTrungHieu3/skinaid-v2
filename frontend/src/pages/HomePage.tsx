// src/pages/HomePage.tsx
import styles from "./HomePage.module.css";
import { Link } from "react-router-dom";
import Footer from "../components/layout/Footer";
import { FaPlay, FaVideo } from "react-icons/fa";
import Logo from "../assets/images/home-page/skin-hero-home.png";
import DetectedImage from "../assets/images/home-page/anhDaNhanDien.png";
import WoundImage from "../assets/images/home-page/anhVetTray.png";
import DashboardHero from "../assets/images/home-page/dashboard-hero.png";
import { FaCamera, FaFirstAid, FaHistory, FaCheck } from "react-icons/fa";
import { FaChartLine, FaListAlt, FaCheckCircle } from "react-icons/fa";
import { useTranslation } from "react-i18next";

const HomePage = () => {
  // Chúng ta có thể dùng useAuth để thay đổi nút "Start Analysis"
  // const { isAuthenticated } = useAuth();
  // const startLink = isAuthenticated ? "/upload" : "/login";

  const { t } = useTranslation();
  return (
    <div className={styles.homePage}>
      {/* 1. Hero Section */}
      <section className={styles.hero}>
        <div className={styles.heroContainer}>
          <div className={styles.heroContent}>
            <h1 className={styles.heroTitle}>
              {/* 2. Giữ lại chữ SkinAid */}
              <span>SkinAid</span>

              {/* 1. Thêm logo của bạn ở đây */}
              <img src={Logo} alt="SkinAid logo" className={styles.heroLogo} />
            </h1>
            <p>{t("home_page.hero_desc")}</p>
            <div className={styles.heroButtons}>
              <Link to="/upload" className={styles.btnPrimary}>
                <FaPlay />
                <span>{t("home_page.hero_analysis_button")}</span>
              </Link>
              <Link to="/demo" className={styles.btnSecondary}>
                <FaVideo />
                <span>{t("home_page.hero_demo_button")}</span>
              </Link>
            </div>
          </div>
          <div className={styles.heroImage}>
            <img
              src={DashboardHero}
              alt="SkinAid Dashboard"
              className={styles.imgPlaceholder}
            />
          </div>
        </div>
      </section>

      {/* 2. Features Section (Cập nhật) */}
      <section className={styles.features}>
        <h2>{t("home_page.feature_title")}</h2>
        {/* 2. THÊM TIÊU ĐỀ PHỤ */}
        <p className={styles.featuresSubtitle}>
          {t("home_page.feature_title_desc")}
        </p>

        <div className={styles.featureGrid}>
          {/* --- THẺ 1 --- */}
          <div className={`${styles.featureCard} ${styles.cardGreen}`}>
            {/* 3. THÊM ICON */}
            <div className={`${styles.featureIconWrapper} ${styles.iconGreen}`}>
              <FaCamera />
            </div>
            <h4>{t("home_page.feature_card1_title")}</h4>
            <p>{t("home_page.feature_card1_desc")}</p>
            {/* 4. THÊM DANH SÁCH */}
            <ul className={styles.featureList}>
              <li>
                <FaCheck className={styles.checkIcon} />
                {t("home_page.feature_card1_item1")}
              </li>
              <li>
                <FaCheck className={styles.checkIcon} />
                {t("home_page.feature_card1_item2")}
              </li>
              <li>
                <FaCheck className={styles.checkIcon} />
                {t("home_page.feature_card1_item3")}
              </li>
            </ul>
          </div>

          {/* --- THẺ 2 --- */}
          <div className={`${styles.featureCard} ${styles.cardGreen}`}>
            <div className={`${styles.featureIconWrapper} ${styles.iconGreen}`}>
              <FaFirstAid />
            </div>
            <h4>{t("home_page.feature_card2_title")}</h4>
            <p>{t("home_page.feature_card2_desc")}</p>
            <ul className={styles.featureList}>
              <li>
                <FaCheck className={styles.checkIcon} />
                {t("home_page.feature_card2_item1")}
              </li>
              <li>
                <FaCheck className={styles.checkIcon} />
                {t("home_page.feature_card2_item2")}
              </li>
              <li>
                <FaCheck className={styles.checkIcon} />
                {t("home_page.feature_card2_item3")}
              </li>
            </ul>
          </div>

          {/* --- THẺ 3 --- */}
          <div className={`${styles.featureCard} ${styles.cardOrange}`}>
            <div
              className={`${styles.featureIconWrapper} ${styles.iconOrange}`}
            >
              <FaHistory />
            </div>
            <h4>{t("home_page.feature_card3_title")}</h4>
            <p>{t("home_page.feature_card3_desc")}</p>
            <ul className={styles.featureList}>
              <li>
                <FaCheck className={styles.checkIcon} />
                {t("home_page.feature_card3_item1")}
              </li>
              <li>
                <FaCheck className={styles.checkIcon} />
                {t("home_page.feature_card3_item2")}
              </li>
              <li>
                <FaCheck className={styles.checkIcon} />
                {t("home_page.feature_card3_item3")}
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* 3. Stats Section */}
      <section className={styles.stats}>
        <div>
          <h3>5,000+</h3>
          <p>{t("home_page.stats_item1_desc")}</p>
        </div>
        <div>
          <h3>3,000</h3>
          <p>{t("home_page.stats_item2_desc")}</p>
        </div>
        <div>
          <h3>65%</h3>
          <p>{t("home_page.stats_item3_desc")}</p>
        </div>
        <div>
          <h3>24/7</h3>
          <p>{t("home_page.stats_item4_desc")}</p>
        </div>
      </section>

      {/* 4. How It Works Section (Đã cập nhật) */}
      <section className={styles.howItWorks}>
        <h2>{t("home_page.how_work_title")}</h2>
        {/* 2. Thêm Subtitle */}
        <p className={styles.howSubtitle}>{t("home_page.how_work_desc")}</p>

        <div className={styles.stepsGrid}>
          {/* --- Step 1 --- */}
          <div className={styles.step}>
            <div className={styles.stepNumber}>
              <span>1</span>
              {/* 3. Thêm icon badge */}
              <span className={`${styles.stepBadge} ${styles.badgeCamera}`}>
                <FaCamera />
              </span>
            </div>
            <h4>{t("home_page.how_work_step1_title")}</h4>
            <p>{t("home_page.how_work_step1_desc")}</p>
            {/* 4. Thay thế Placeholder bằng nội dung thật */}
            <div className={styles.imageContent}>
              <img src={WoundImage} className={styles.imgPlaceholder} />
              <div className={styles.imageCaption}>
                <span>{t("home_page.how_work_step1_item1")}</span>
                <span className={styles.uploadStatus}>
                  {t("home_page.how_work_step1_item1_status")}
                </span>
              </div>
            </div>
          </div>

          {/* --- Step 2 --- */}
          <div className={styles.step}>
            <div className={styles.stepNumber}>
              <span>2</span>
              <span className={`${styles.stepBadge} ${styles.badgeChart}`}>
                <FaChartLine />
              </span>
            </div>
            <h4>{t("home_page.how_work_step2_title")}</h4>
            <p>{t("home_page.how_work_step2_desc")}</p>
            <div className={styles.imageContent}>
              <img src={DetectedImage} className={styles.imgPlaceholder} />
              {/* Thêm bảng kết quả AI */}
              <div className={styles.aiResultTable}>
                <div>
                  <span>{t("home_page.how_work_step2_item1")}:</span>
                  <span>{t("home_page.how_work_step2_item1_result")}</span>
                </div>
                <div>
                  <span>{t("home_page.how_work_step2_item2")}:</span>
                  <span>{t("home_page.how_work_step2_item2_result")}</span>
                </div>
                <div>
                  <span>{t("home_page.how_work_step2_item3")}:</span>
                  <span className={styles.accuracy}>
                    {t("home_page.how_work_step2_item3_result")}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* --- Step 3 --- */}
          <div className={styles.step}>
            <div className={styles.stepNumber}>
              <span>3</span>
              <span className={`${styles.stepBadge} ${styles.badgeList}`}>
                <FaListAlt />
              </span>
            </div>
            <h4>{t("home_page.how_work_step3_title")}</h4>
            <p>{t("home_page.how_work_step3_desc")}</p>
            <div className={styles.imageContent}>
              {/* Thêm danh sách First Aid */}
              <div className={styles.firstAidList}>
                <div className={styles.listHeader}>
                  <FaCheckCircle className={styles.listHeaderIcon} />
                  <div className={styles.listHeaderText}>
                    <strong>{t("home_page.how_work_step3_item1")}</strong>
                    <span>{t("home_page.how_work_step3_item1_desc")}</span>
                  </div>
                </div>
                <ul>
                  <li>{t("home_page.how_work_step3_item2")}</li>
                  <li>{t("home_page.how_work_step3_item3")}</li>
                  <li>{t("home_page.how_work_step3_item4")}</li>
                  <li>{t("home_page.how_work_step3_item5")}</li>
                  <li>{t("home_page.how_work_step3_item6")}</li>
                  <li>{t("home_page.how_work_step3_item7")}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. How It Works Section */}
      <Footer />
    </div>
  );
};

export default HomePage;
