import styles from './AdminFooter.module.css';

export default function AdminFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className={styles.adminFooter}>
      <div className={styles.footerLeft}>
        <span>© {year}</span>
        <span className={styles.footerBrand}>SkinAid</span>
        <span className={styles.footerDot}>·</span>
        <span className={styles.footerVersion}>v0.1.0</span>
        <span className={styles.footerDot}>·</span>
        <span>Admin Portal</span>
      </div>
      <div className={styles.footerRight}>
        <span>Phát triển bởi SkinAid Team</span>
      </div>
    </footer>
  );
}
