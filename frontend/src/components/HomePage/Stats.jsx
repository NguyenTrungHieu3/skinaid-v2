import React from "react";
import "../../assets/styles/components/stats.scss";

export default function Stats() {
  const stats = [
    { number: "3,000", label: "Images Processed" },
    { number: "65%", label: "Accuracy Rate" },
    { number: "24/7", label: "Platform Availability" },
  ];

  return (
    <section className="stats">
      {stats.map((item, idx) => (
        <div className="stat-card" key={idx}>
          <h3>{item.number}</h3>
          <p>{item.label}</p>
        </div>
      ))}
    </section>
  );
}
