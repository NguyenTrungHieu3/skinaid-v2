import React from "react";

// (CSS cho file này sẽ được tạo sau)
const Filters = () => {
  return (
    <div
      style={{
        padding: "1rem",
        background: "#fff",
        borderRadius: "12px",
        border: "1px solid #e5e7eb",
        marginBottom: "1rem",
      }}
    >
      <input
        type="search"
        placeholder="Search filename..."
        style={{ width: "100%", padding: "0.5rem", boxSizing: "border-box" }}
      />
      {/* (Thêm filter thời gian sau) */}
    </div>
  );
};

export default Filters;
