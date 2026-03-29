export const enableSmoothScrollSnap = () => {
    const sections = document.querySelectorAll(
      ".hero, .features, .stats, .howItWorks"
    );
  
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          } else {
            entry.target.classList.remove("is-visible");
          }
        });
      },
      { threshold: 0.3 } // Khi 30% section xuất hiện thì bật hiệu ứng
    );
  
    sections.forEach((section) => observer.observe(section));
  };
  