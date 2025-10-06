import React from "react";
import "../../assets/styles/components/hero.scss";
import dashboardImage from "../../assets/images/dashboard.png";
import skinImage from "../../assets/images/skin.png";
import { FaCamera, FaArrowRight } from "react-icons/fa";
import { MdSlowMotionVideo } from "react-icons/md";

export default function Hero() {
  return (
    <section className="hero">
      <div className="hero-left">
        <div className="logo-text">
          <h1>SkinAid</h1>
          <img src={skinImage} alt="Skin logo" className="skin-image" />
        </div>

        <p>
          SkinAid empowers everyday users by combining wound
          detection, tailored first-aid guidance, and easy-to-use wound history
          tracking into a single, user-friendly web application designed to make
          healthcare support more accessible and practical in daily life.
        </p>

        <div className="hero-buttons">
          <button className="start-btn">
            <FaCamera className="icon-left" />
            Start Analysis
            <FaArrowRight className="icon-right" />
          </button>

          <button className="watch-btn">
            <MdSlowMotionVideo className="icon-left" />
            Watch demo
          </button>
        </div>
      </div>

      <div className="hero-right">
        <img src={dashboardImage} alt="Dashboard preview" />
      </div>
    </section>
  );
}