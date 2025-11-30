// src/pages/AboutPage.tsx
import React from "react";
import styles from "./AboutPage.module.css";
import {
  Upload,
  Brain,
  BarChart3,
  Shield,
  Clock,
  Heart,
  Smartphone,
  ArrowRight,
} from "lucide-react";
import featuredImage from "../assets/images/about-page/healthcare_technology.png";
import { useTranslation } from "react-i18next";

interface AboutPageProps {
  switchForm?: () => void;
}

const AboutPage: React.FC<AboutPageProps> = ({ switchForm }) => {
  const { t } = useTranslation();

  const handleGetStarted = () => {
    if (switchForm) switchForm();
  };

  return (
    <div className={styles.aboutPage}>
      <title>{t("title.about_page")}</title>

      {/* HERO */}
      <section className={styles.heroSection}>
        <div className={`${styles.container} ${styles.textCenter}`}>
          <h1
            className={styles.heroTitle}
            dangerouslySetInnerHTML={{
              __html: t("about.hero_title"),
            }}
          />

          <p className={styles.heroSubtitle}>{t("about.hero_subtitle")}</p>

          {/* <button
            className={`${styles.btn} ${styles.btnPrimary}`}
            onClick={handleGetStarted}
          >
            {t("about.hero_button")}
            <ArrowRight className={styles.iconRight} />
          </button> */}
        </div>
      </section>

      {/* WHAT IS */}
      <section className={styles.whatIsSection}>
        <div className={`${styles.container} ${styles.gridLayout}`}>
          <div className={styles.textContent}>
            <h2 className={styles.sectionTitle}>{t("about.what_is_title")}</h2>

            <div className={styles.textBody}>
              <p>{t("about.what_is_p1")}</p>
              <p>{t("about.what_is_p2")}</p>
              <p>{t("about.what_is_p3")}</p>
            </div>
          </div>

          <div className={styles.imageContainer}>
            <img
              src={featuredImage}
              alt="Healthcare technology"
              className={styles.featuredImage}
            />
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className={styles.howItWorksSection}>
        <div className={styles.container}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>{t("about.how_title")}</h2>
            <p className={styles.sectionSubtitle}>{t("about.how_subtitle")}</p>
          </div>

          <div className={styles.stepsGrid}>
            <div className={styles.stepCard}>
              <div className={styles.iconWrapperLg}>
                <Upload className={styles.iconLg} />
              </div>
              <div className={styles.stepLabel}>{t("about.step_1_label")}</div>
              <h3 className={styles.cardTitle}>{t("about.step_1_title")}</h3>
              <p>{t("about.step_1_desc")}</p>
            </div>

            <div className={styles.stepCard}>
              <div className={styles.iconWrapperLg}>
                <Brain className={styles.iconLg} />
              </div>
              <div className={styles.stepLabel}>{t("about.step_2_label")}</div>
              <h3 className={styles.cardTitle}>{t("about.step_2_title")}</h3>
              <p>{t("about.step_2_desc")}</p>
            </div>

            <div className={styles.stepCard}>
              <div className={styles.iconWrapperLg}>
                <BarChart3 className={styles.iconLg} />
              </div>
              <div className={styles.stepLabel}>{t("about.step_3_label")}</div>
              <h3 className={styles.cardTitle}>{t("about.step_3_title")}</h3>
              <p>{t("about.step_3_desc")}</p>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className={styles.featuresSection}>
        <div className={styles.container}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>{t("about.features_title")}</h2>
            <p className={styles.sectionSubtitle}>
              {t("about.features_subtitle")}
            </p>
          </div>

          <div className={styles.featuresGrid}>
            <div className={styles.featureCard}>
              <div className={styles.iconWrapperSm}>
                <Brain className={styles.iconSm} />
              </div>
              <h3 className={styles.featureTitle}>{t("about.f_ai_title")}</h3>
              <p>{t("about.f_ai_desc")}</p>
            </div>

            <div className={styles.featureCard}>
              <div className={styles.iconWrapperSm}>
                <Clock className={styles.iconSm} />
              </div>
              <h3 className={styles.featureTitle}>
                {t("about.f_instant_title")}
              </h3>
              <p>{t("about.f_instant_desc")}</p>
            </div>

            <div className={styles.featureCard}>
              <div className={styles.iconWrapperSm}>
                <Shield className={styles.iconSm} />
              </div>
              <h3 className={styles.featureTitle}>
                {t("about.f_security_title")}
              </h3>
              <p>{t("about.f_security_desc")}</p>
            </div>

            <div className={styles.featureCard}>
              <div className={styles.iconWrapperSm}>
                <Heart className={styles.iconSm} />
              </div>
              <h3 className={styles.featureTitle}>
                {t("about.f_evidence_title")}
              </h3>
              <p>{t("about.f_evidence_desc")}</p>
            </div>

            <div className={styles.featureCard}>
              <div className={styles.iconWrapperSm}>
                <Smartphone className={styles.iconSm} />
              </div>
              <h3 className={styles.featureTitle}>
                {t("about.f_mobile_title")}
              </h3>
              <p>{t("about.f_mobile_desc")}</p>
            </div>

            <div className={styles.featureCard}>
              <div className={styles.iconWrapperSm}>
                <Upload className={styles.iconSm} />
              </div>
              <h3 className={styles.featureTitle}>{t("about.f_easy_title")}</h3>
              <p>{t("about.f_easy_desc")}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;
