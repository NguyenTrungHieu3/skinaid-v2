import React from "react";
import { FaCamera, FaFirstAid } from "react-icons/fa";
import "../../assets/styles/components/howitworks.scss";
import WoundImage from "../../assets/images/anhVetTray.png";
import DetectImage from "../../assets/images/anhDaNhanDien.png";
import { FaCheckCircle } from "react-icons/fa";

export default function HowItWorks() {
  const steps = [
    {
      id: 1,
      title: "Upload Your Wound Image",
      desc: "Upload high-resolution wound images using standardized imaging protocols for unified documentation.",
      icon: <FaCamera />,
      color: "#209C7F",
      card: (
        <div className="illustration-card">
          <img src={WoundImage} alt="Wound Upload Example" />
          <div className="caption">
            Wound_Image01.jpg <span className="status">Uploaded</span>
          </div>
        </div>
      ),
    },
    {
      id: 2,
      title: "Wound Analysis",
      desc: "Advanced algorithms will analyze the wound, provide measurements, classify and assess the extent of the wound.",
      icon: <FaFirstAid />,
      color: "#00B377",
      card: (
        <div className="illustration-card">
          <img src={DetectImage} alt="Detection Example" />
          <div className="info">
            <div className="label">
              <span>Type:</span>
              <span>Level:</span>
            </div>
            <div className="value">
              <span>Bruise</span>
              <span>Mild</span>
            </div>
          </div>
          <ul className="checklist">
            <li>
              <FaCheckCircle /> Clean with water or saline
            </li>
            <li>
              <FaCheckCircle /> Apply cold pack to reduce swelling
            </li>
            <li>
              <FaCheckCircle /> Rest the injured area
            </li>
          </ul>
        </div>
      ),
    },
  ];

  return (
    <section className="how-it-works">
      <h2>How SkinAid Works</h2>
      <p className="subtitle">
        From image capture to wound analysis and treatment recommendations, SkinAid
        transforms wound care documentation in simple steps.
      </p>

      <div className="timeline">
        {steps.map((s, idx) => (
          <div className="timeline-step" key={s.id}>
            <div className="circle" style={{ background: s.color }}>
              <span>{s.id}</span>
              <div className="icon">{s.icon}</div>
            </div>
            <h3>{s.title}</h3>
            <p>{s.desc}</p>

            {/* Minh họa */}
            <div className="illustration">{s.card}</div>

            {/* Line nối các step */}
            {idx < steps.length - 1 && <div className="line" />}
          </div>
        ))}
      </div>
    </section>
  );
}