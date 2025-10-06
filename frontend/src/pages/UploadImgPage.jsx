import React from "react";
import UploadImgForm from "../components/UploadImg/UploadImgForm";
import "../assets/styles/UploadImg.scss";
import Header from "../components/HomePage/Header";

function UploadImgPage({ switchForm }) {
  return (
    <div className="home">
      <Header />
      <UploadImgForm switchForm={switchForm} />
    </div>
  );
}

export default UploadImgPage;
