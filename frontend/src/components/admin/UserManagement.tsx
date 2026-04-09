import React, { useState, useEffect, useMemo, useRef } from "react";
import { jwtDecode } from "jwt-decode";
import { 
  getUsers, 
  getUserDetail, 
  updateUserStatus, 
  type UserListItem, 
  type UserDetail 
} from "../../services/userService";
import { toast } from "sonner";
import { 
  Users, 
  UserCheck, 
  UserX, 
  Search, 
  MoreVertical, 
  ShieldAlert, 
  ShieldBan,
  FileText,
  ChevronLeft,
  ChevronRight,
  X
} from "lucide-react";
import styles from "./UserManagement.module.css";

export default function UserManagementPage() {
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [panelLoading, setPanelLoading] = useState(false);
  
  const [totalUsers, setTotalUsers] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserDetail | null>(null);
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);

  const [, setTick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setTick(t => t + 1), 60_000);
    return () => clearInterval(timer);
  }, []);

  const currentAdminId = (() => {
    try {
      const token =
        localStorage.getItem("userToken") ||
        sessionStorage.getItem("userToken") ||
        "";
      if (!token) return "";
      const decoded = jwtDecode<{ sub?: string }>(token);
      return decoded.sub || "";
    } catch {
      return "";
    }
  })();

  const dropdownRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdownId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 400);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch, roleFilter, statusFilter, currentPage]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const data = await getUsers({
          page: currentPage,
          page_size: pageSize,
          search: debouncedSearch || undefined,
          role: roleFilter !== "all" ? roleFilter : undefined,
          status: statusFilter !== "all" ? statusFilter : undefined,
        });
        setUsers(data.items ?? []);
        setTotalUsers(data.total ?? 0);
      } catch {
      }
    }, 5 * 60_000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch, roleFilter, statusFilter, currentPage]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await getUsers({
        page: currentPage,
        page_size: pageSize,
        search: debouncedSearch || undefined,
        role: roleFilter !== "all" ? roleFilter : undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      });
      setUsers(data.items ?? []);
      setTotalUsers(data.total ?? 0);
    } catch (err) {
      console.error("Failed to fetch users", err);
      toast.error("Failed to load users list.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setRoleFilter(e.target.value);
    setCurrentPage(1);
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
    setCurrentPage(1);
  };

  const openUserDetail = async (user: UserListItem) => {
    setSelectedUser({ ...user, scan_history: [] });
    setIsPanelOpen(true);
    setOpenDropdownId(null);
    
    try {
      setPanelLoading(true);
      const detail = await getUserDetail(user.id);
      setSelectedUser(detail);
    } catch (err) {
      toast.error("Failed to load user details.");
    } finally {
      setPanelLoading(false);
    }
  };

  const toggleUserStatus = async (userId: string, userIndex: number) => {
    setOpenDropdownId(null);
    const userToUpdate = users[userIndex];
    if (!userToUpdate) return;
    if (userToUpdate.id === currentAdminId) {
      toast.error("Không thể tự vô hiệu hoá tài khoản của chính mình.");
      return;
    }

    const originalStatus = userToUpdate.status;
    const newStatus = originalStatus.toLowerCase() === "active" ? "inactive" : "active";

    setUsers(prev => {
      const next = [...prev];
      next[userIndex] = { ...next[userIndex], status: newStatus };
      return next;
    });

    if (selectedUser?.id === userId) {
      setSelectedUser(prev => prev ? { ...prev, status: newStatus } : null);
    }

    try {
      await updateUserStatus(userId, newStatus as "active" | "inactive");
      toast.success(
        `User "${userToUpdate.full_name || userToUpdate.email}" đã được ${newStatus === "active" ? "kích hoạt" : "vô hiệu hoá"}.`
      );
    } catch (err: any) {
      setUsers(prev => {
        const reverted = [...prev];
        reverted[userIndex] = { ...reverted[userIndex], status: originalStatus };
        return reverted;
      });

      if (selectedUser?.id === userId) {
        setSelectedUser(prev => prev ? { ...prev, status: originalStatus } : null);
      }

      const errorMsg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Không thể cập nhật trạng thái người dùng.";
      toast.error(errorMsg);
    }
  };

  const getInitials = (name: string | null) => {
    if (!name) return "U";
    return name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
  };

  const getAvatarColor = (name: string | null) => {
    if (!name) return "#64748b";
    const colors = ["#10b981", "#3b82f6", "#8b5cf6", "#f97316", "#ec4899", "#14b8a6"];
    return colors[name.charCodeAt(0) % colors.length];
  };

  const getRelativeTime = (dateString: string | null) => {
    if (!dateString) return "Never";
    const normalizedDateString = dateString.endsWith("Z") ? dateString : `${dateString}Z`;
    const date = new Date(normalizedDateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return "Just now";
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) return `${diffInMinutes} minute${diffInMinutes > 1 ? "s" : ""} ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? "s" : ""} ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 30) return `${diffInDays} day${diffInDays > 1 ? "s" : ""} ago`;
    return date.toLocaleDateString();
  };

  const getWoundIcon = (woundType: string | null) => {
    if (!woundType) return "🦠";
    const lower = woundType.toLowerCase();
    if (lower.includes("burn") || lower.includes("bỏng")) return "🔥";
    if (lower.includes("cut") || lower.includes("cắt")) return "🔪";
    if (lower.includes("acne") || lower.includes("mụn")) return "🔴";
    return "🦠";
  };

  const totalPages = Math.max(1, Math.ceil(totalUsers / pageSize));
  const indexOfFirstUser = (currentPage - 1) * pageSize + 1;
  const indexOfLastUser = Math.min(currentPage * pageSize, totalUsers);

  const activeUsersCount = useMemo(() => (users ?? []).filter(u => u.status === "active").length, [users]);
  const inactiveUsersCount = useMemo(() => (users ?? []).filter(u => u.status === "inactive").length, [users]);

  return (
    <div className={styles.userManagementPage}>
      {/* Header */}
      <div className={styles.pageHeader}>
        <div className={styles.pageTitle}>
          <h1>User Management</h1>
          <p>Manage users and permissions</p>
        </div>
      </div>

      {/* Stats */}
      <div className={styles.statsGrid}>
        <div className={`${styles.statCard} ${styles.total}`}>
          <div className={`${styles.statIcon} ${styles.total}`}>
            <Users size={24} />
          </div>
          <div>
            <div className={styles.statValue}>{totalUsers}</div>
            <div className={styles.statLabel}>Total Users</div>
          </div>
        </div>
        <div className={`${styles.statCard} ${styles.active}`}>
          <div className={`${styles.statIcon} ${styles.active}`}>
            <UserCheck size={24} />
          </div>
          <div>
            <div className={styles.statValue}>{activeUsersCount}</div>
            <div className={styles.statLabel}>Active Users</div>
          </div>
        </div>
        <div className={`${styles.statCard} ${styles.inactive}`}>
          <div className={`${styles.statIcon} ${styles.inactive}`}>
            <UserX size={24} />
          </div>
          <div>
            <div className={styles.statValue}>{inactiveUsersCount}</div>
            <div className={styles.statLabel}>Inactive Users</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className={styles.filtersCard}>
        <div className={styles.filterGroup}>
          <label>Search Users</label>
          <div className={styles.filterInputContainer}>
            <Search className={styles.filterInputIcon} size={16} />
            <input
              type="text"
              placeholder="Search by name or email..."
              className={styles.filterInput}
              value={searchQuery}
              onChange={handleSearchChange}
            />
          </div>
        </div>
        <div className={styles.filterGroup}>
          <label>Filter by Role</label>
          <select 
            className={styles.filterSelect}
            value={roleFilter}
            onChange={handleRoleChange}
          >
            <option value="all">All Roles</option>
            <option value="admin">Admin</option>
            <option value="user">User</option>
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label>Filter by Status</label>
          <select 
            className={styles.filterSelect}
            value={statusFilter}
            onChange={handleStatusChange}
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "0.75rem" }}>
        {totalUsers > 0 && `Showing ${indexOfFirstUser}-${indexOfLastUser} of ${totalUsers}`}
      </div>

      {/* Table */}
      <div className={styles.tableContainer}>
        {loading ? (
          <div className={styles.loadingContainer}>
            <div className={styles.loadingSpinner}></div>
            <div className={styles.loadingText}>Fetching users...</div>
          </div>
        ) : users.length === 0 ? (
          <div className={styles.emptyState}>
            <Search size={48} className={styles.emptyStateIcon} />
            <p>No users found matching your filters.</p>
          </div>
        ) : (
          <table className={styles.dataTable}>
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Status</th>
                <th>Uploads</th>
                <th>Last Active</th>
                <th style={{ textAlign: "right", paddingRight: "1.5rem" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user, idx) => {
                const uniqueId = `${user.id}-${idx}`;
                return (
                <tr key={uniqueId}>
                  <td>
                    <div 
                      className={styles.userInfo} 
                      onClick={() => openUserDetail(user)}
                      style={{ cursor: "pointer" }}
                    >
                      <div 
                        className={styles.avatar}
                        style={{ backgroundColor: getAvatarColor(user.full_name) }}
                      >
                        {getInitials(user.full_name)}
                      </div>
                      <div className={styles.userDetails}>
                        <span className={styles.userName}>{user.full_name || "Unknown"}</span>
                        <span className={styles.userEmail}>{user.email}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`${styles.roleBadge} ${user.role.toLowerCase() === 'admin' ? styles.roleAdmin : styles.roleUser}`}>
                      {user.role}
                    </span>
                  </td>
                  <td>
                    <span className={`${styles.statusBadge} ${user.status === 'active' ? styles.statusActive : styles.statusInactive}`}>
                      {user.status}
                    </span>
                  </td>
                  <td>{user.uploads_count || 0}</td>
                  <td style={{ color: "#64748b" }}>{getRelativeTime(user.last_active_at)}</td>
                  <td className={styles.actionsCell} style={{ paddingRight: "1.5rem" }}>
                    <button 
                      className={`${styles.btnActionMenu} ${openDropdownId === uniqueId ? styles.active : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setOpenDropdownId(openDropdownId === uniqueId ? null : uniqueId);
                      }}
                    >
                      <MoreVertical size={18} />
                    </button>
                    {openDropdownId === uniqueId && (
                      <div className={styles.actionDropdown} ref={dropdownRef}>
                        <button 
                          className={styles.actionItem}
                          onClick={(e) => {
                            e.stopPropagation();
                            openUserDetail(user);
                          }}
                        >
                          <FileText size={16} /> View Details
                        </button>
                        {user.status === "active" ? (
                          <button 
                            className={`${styles.actionItem} ${styles.actionDeactivate}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleUserStatus(user.id, idx);
                            }}
                          >
                            <ShieldBan size={16} /> Deactivate
                          </button>
                        ) : (
                          <button 
                            className={`${styles.actionItem} ${styles.actionActivate}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleUserStatus(user.id, idx);
                            }}
                          >
                            <ShieldAlert size={16} /> Activate
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div className={styles.pagination}>
          <button 
            className={styles.paginationBtn}
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
          >
            <ChevronLeft size={16} /> Prev
          </button>
          <div className={styles.paginationNumbers}>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => {
              if (
                page === 1 ||
                page === totalPages ||
                (page >= currentPage - 1 && page <= currentPage + 1)
              ) {
                return (
                  <button
                    key={page}
                    className={`${styles.paginationNumber} ${currentPage === page ? styles.active : ''}`}
                    onClick={() => setCurrentPage(page)}
                  >
                    {page}
                  </button>
                );
              } else if (
                page === currentPage - 2 ||
                page === currentPage + 2
              ) {
                return <span key={page} style={{ padding: "0 0.25rem", color: "#94a3b8" }}>...</span>;
              }
              return null;
            })}
          </div>
          <button 
            className={styles.paginationBtn}
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      )}

      {/* Slide Out Panel */}
      {isPanelOpen && selectedUser && (
        <div className={styles.modalOverlay} onClick={() => setIsPanelOpen(false)}>
          <div className={styles.slidePanel} onClick={(e) => e.stopPropagation()}>
            {/* Panel Header */}
            <div className={styles.panelHeader}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <div
                  className={styles.avatar}
                  style={{ backgroundColor: getAvatarColor(selectedUser.full_name), width: 44, height: 44, fontSize: "1rem", flexShrink: 0 }}
                >
                  {getInitials(selectedUser.full_name)}
                </div>
                <div>
                  <h2 className={styles.panelTitle}>{selectedUser.full_name || "Unknown User"}</h2>
                  <p className={styles.panelSubtitle}>{selectedUser.email}</p>
                </div>
              </div>
              <button className={styles.btnClosePanel} onClick={() => setIsPanelOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.panelContent}>
              {/* User Info Summary */}
              {!panelLoading && (
                <div className={styles.userInfoGrid}>
                  <div className={styles.userInfoItem}>
                    <span className={styles.userInfoLabel}>Role</span>
                    <span className={`${styles.roleBadge} ${selectedUser.role?.toLowerCase() === 'admin' ? styles.roleAdmin : styles.roleUser}`}>
                      {selectedUser.role}
                    </span>
                  </div>
                  <div className={styles.userInfoItem}>
                    <span className={styles.userInfoLabel}>Status</span>
                    <span className={`${styles.statusBadge} ${selectedUser.status === 'active' ? styles.statusActive : styles.statusInactive}`}>
                      {selectedUser.status}
                    </span>
                  </div>
                  <div className={styles.userInfoItem}>
                    <span className={styles.userInfoLabel}>Total Scans</span>
                    <span className={styles.userInfoValue}>{selectedUser.uploads_count || 0}</span>
                  </div>
                  <div className={styles.userInfoItem}>
                    <span className={styles.userInfoLabel}>Joined</span>
                    <span className={styles.userInfoValue}>
                      {selectedUser.join_date ? new Date(selectedUser.join_date).toLocaleDateString() : "—"}
                    </span>
                  </div>
                  <div className={styles.userInfoItem} style={{ gridColumn: "1 / -1" }}>
                    <span className={styles.userInfoLabel}>Last Active</span>
                    <span className={styles.userInfoValue}>{getRelativeTime(selectedUser.last_active_at)}</span>
                  </div>
                </div>
              )}

              {/* Divider */}
              {!panelLoading && <div className={styles.panelDivider} />}

              <h3 className={styles.scanHistoryTitle}>Scan History</h3>
              {panelLoading ? (
                 <div className={styles.loadingContainer}>
                   <div className={styles.loadingSpinner}></div>
                   <div className={styles.loadingText}>Fetching details...</div>
                 </div>
              ) : !selectedUser.scan_history || selectedUser.scan_history.length === 0 ? (
                 <div className={styles.emptyState}>
                   <FileText size={48} />
                   <p>No scans recorded for this user.</p>
                 </div>
              ) : (
                <div className={styles.scanList}>
                  {selectedUser.scan_history.map(scan => {
                    let sevClass = "";
                    if (scan.severity) {
                      const sev = scan.severity.toLowerCase();
                      if (sev.includes("low")) sevClass = styles.severityLow;
                      else if (sev.includes("moderate")) sevClass = styles.severityModerate;
                      else if (sev.includes("high")) sevClass = styles.severityHigh;
                      else if (sev.includes("severe")) sevClass = styles.severitySevere;
                    }

                    const imageUrl = scan.image_url
                      ? scan.image_url.startsWith("http")
                        ? scan.image_url
                        : `http://localhost:8000${scan.image_url}`
                      : null;

                    return (
                      <div key={scan.id} className={styles.scanItem}>
                        {imageUrl ? (
                          <img src={imageUrl} alt="Scan" className={styles.scanPhoto} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
                        ) : (
                          <div className={styles.scanIconWrap}>{getWoundIcon(scan.wound_type)}</div>
                        )}
                        <div className={styles.scanDetails}>
                          <div className={styles.scanHeader}>
                            <span className={styles.scanWoundType} title={scan.wound_type || "Unknown Wound"}>
                              {scan.wound_type || "Unknown Wound"}
                            </span>
                            <span className={styles.scanDate}>
                              {new Date(scan.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          {scan.severity && (
                            <span className={`${styles.scanSeverity} ${sevClass}`}>
                              {scan.severity.toLowerCase()}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
