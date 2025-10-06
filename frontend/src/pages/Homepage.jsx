import React from "react";
import Header from "../components/HomePage/Header";
import Hero from "../components/HomePage/Hero";
import Features from "../components/HomePage/Features";
import Stats from "../components/HomePage/Stats";
import HowItWorks from "../components/HomePage/HowItWorks";
import Footer from "../components/HomePage/Footer";

import "../assets/styles/Home.scss";

export default function Home() {
  return (
    <div className="home">
      <Header />
      <Hero />
      <Features />
      <Stats />
      <HowItWorks />
      <Footer />
    </div>
  );
}
