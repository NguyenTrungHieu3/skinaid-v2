import React from 'react';

export const UserTableSkeleton = () => {
  return (
    <div className="admin-card">
      <div className="table-container">
        <table className="user-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Uploads</th>
              <th>Join Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {[...Array(5)].map((_, index) => (
              <tr key={index}>
                <td>
                  <div className="user-info">
                    <div className="skeleton-avatar"></div>
                    <div className="skeleton-text" style={{ width: '120px' }}></div>
                  </div>
                </td>
                <td><div className="skeleton-text" style={{ width: '180px' }}></div></td>
                <td><div className="skeleton-badge"></div></td>
                <td><div className="skeleton-badge"></div></td>
                <td><div className="skeleton-text" style={{ width: '40px' }}></div></td>
                <td><div className="skeleton-text" style={{ width: '100px' }}></div></td>
                <td><div className="skeleton-text" style={{ width: '40px' }}></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const CardSkeleton = () => {
  return (
    <div className="admin-card">
      <div className="skeleton-title"></div>
      <div className="skeleton-text" style={{ width: '60%', marginTop: '12px' }}></div>
      <div className="skeleton-text" style={{ width: '80%', marginTop: '8px' }}></div>
    </div>
  );
};

export const StatCardSkeleton = () => {
  return (
    <div className="admin-card">
      <div className="admin-card-header">
        <div className="skeleton-text" style={{ width: '100px' }}></div>
        <div className="skeleton-circle"></div>
      </div>
      <div className="admin-card-content">
        <div className="skeleton-title"></div>
        <div className="skeleton-text" style={{ width: '60%', marginTop: '8px' }}></div>
      </div>
    </div>
  );
};
