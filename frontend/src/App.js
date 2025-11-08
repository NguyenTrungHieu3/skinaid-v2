import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "./App.scss";
import SigninPage from "./pages/SigninPage";
import Home from "./pages/Homepage";
import SignupPage from "./pages/SignupPage";
import UploadImgPage from "./pages/UploadImgPage";
import VerifyForm from "./components/Verify/VerifyForm";
import AdminPage from "./pages/AdminPage";
import { ToastProvider } from "./contexts/ToastContext";
import ToastContainer from "./components/shared/ToastContainer";

function App() {
  return (
    <ToastProvider>
      <Router>
        <div className="App">
          <ToastContainer />
        {/* Navbar đơn giản */}
        {/* <nav className="navbar">
          <h2 className="logo">SkinAid</h2>
          <div className="nav-links">
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
            <Link to="/upload">Upload</Link>
          </div>
        </nav> */}

        {/* Định nghĩa route */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/signin" element={<SigninPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/upload" element={<UploadImgPage />} />
          <Route path="/verify-email" element={<VerifyForm />} />
          <Route path="/admin/*" element={<AdminPage />} />
        </Routes>
      </div>
    </Router>
    </ToastProvider>
  );
}

export default App;
