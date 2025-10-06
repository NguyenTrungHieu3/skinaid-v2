import React from "react";
import "../../assets/styles/components/footer.scss";
import Logo from "../../assets/images/logo.png";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-top">
        <div className="brand">
          <div className="brand-logo">
            <img src={Logo} alt="SkinAid Logo" />
            <h2>
              Skin<span>Aid</span>
            </h2>
          </div>
          <p>
            Web app for wound detection, classification and first-aid
            guidance.
          </p>
        </div>

        <div className="links">
          <div>
            <h4>Platform</h4>
            <a href="#features">Features</a>
            <a href="#integrations">Integrations</a>
            <a href="#security">Security</a>
            <a href="#api">API</a>
          </div>
          <div>
            <h4>Support</h4>
            <a href="#docs">Documentation</a>
            <a href="#training">Training</a>
            <a href="#support">Support Center</a>
            <a href="#contact">Contact Us</a>
          </div>
          <div>
            <h4>Company</h4>
            <a href="#about">About</a>
            <a href="#careers">Careers</a>
            <a href="#privacy">Privacy</a>
            <a href="#terms">Terms</a>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>© 2025 SkinAid. All rights reserved.</p>
      </div>
    </footer>
  );
}