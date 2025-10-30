import React, { useEffect } from "react";
import AnalysisResultsForm from "../components/AnalysisResults/AnalysisResultsForm";
import "../assets/styles/AnalysisResults.scss";
import Header from "../components/HomePage/Header";

function AnalysisResultsPage({ switchForm }) {
  useEffect(() => {
    document.title = "Analysis Results | SkinAid";
  }, []);

  return (
    <div className="home">
      <Header />
      <AnalysisResultsForm switchForm={switchForm} />
    </div>
  );
}

export default AnalysisResultsPage;
