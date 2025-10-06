import React from "react";
import "../../assets/styles/components/features.scss";
import { FaCamera, FaFirstAid, FaHistory } from "react-icons/fa";

export default function Features() {
  const features = [
    {
      icon: <FaCamera />,
      title: "Wound Detection & Classification",
      desc: "Upload and manage wound images with detailed information.",
      points: [
        "Detect and categorize different wound types",
        "Provide simple results in user-friendly format",
        "Store and organize your wound images",
      ],
      color: "#209C7F", // xanh lá
    },
    {
      icon: <FaFirstAid />,
      title: "First-Aid Guidance",
      desc: "Offer standardized first-aid steps tailored to wound type.",
      points: [
        "Cleaning and disinfection instructions",
        "Bleeding control and bandaging guidance",
        "Highlight warning signs for infection",
      ],
      color: "#03C087", // xanh dương
    },
    {
      icon: <FaHistory />,
      title: "Wound History Tracking",
      desc: "Enable users to track and review their wound images.",
      points: ["Upload multiple images", "View past results", "Monitor wound progression"],
      color: "#E9A986", // cam
    },
    
  ];

  return (
    <section className="features" id="features">
      <div className="features-header">
        <h2>SkinAid – Smart Wound Support Platform</h2>
        <p>
          A simple tool to help users detect wounds, receive
          first-aid guidance, and track wound history.
        </p>
      </div>

      <div className="features-grid">
        {features.map((f, idx) => (
          <div className="feature-card" key={idx} style={{ borderColor: f.color }}>
            <div className="icon-box" style={{ backgroundColor: `${f.color}15`, color: f.color }}>
              {f.icon}
            </div>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
            <ul>
              {f.points.map((point, i) => (
                <li key={i}>{point}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}