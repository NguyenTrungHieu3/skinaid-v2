import React, { useState, useEffect, useMemo, useRef } from "react";
import { jwtDecode } from "jwt-decode";
import { useTranslation } from "react-i18next";
import { 
  getUsers, 
  getUserDetail, 
  updateUserStatus, 
  type UserListItem, 
  type UserDetail 
} from "../../services/userService";
import { toast } from "sonner";
import ExcelJS from "exceljs";
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
  X,
  Download,
  FileSpreadsheet
} from "lucide-react";
import StatCard from "./shared/StatCard";
import ConfirmDialog from "../common/ConfirmDialog";
import styles from "./UserManagement.module.css";

export default function UserManagementPage() {
  const { t } = useTranslation();
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

  // Bulk Selection State
  const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(new Set());
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  const [bulkConfirmOpen, setBulkConfirmOpen] = useState(false);
  const [bulkConfirmStatus, setBulkConfirmStatus] = useState<'active' | 'inactive' | null>(null);

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
        setUsers(data.items);
        setTotalUsers(data.total);
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
      setUsers(data.items);
      setTotalUsers(data.total);
      setSelectedUserIds(new Set()); // Reset selections on filter/page change
    } catch (err) {
      console.error("Failed to fetch users", err);
      toast.error("Không thể tải danh sách người dùng.");
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
      toast.error("Không thể tải thông tin chi tiết người dùng.");
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
    if (!dateString) return "Chưa hoạt động";
    const normalizedDateString = dateString.endsWith("Z") ? dateString : `${dateString}Z`;
    const date = new Date(normalizedDateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return "Vừa xong";
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) return `${diffInMinutes} phút trước`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} giờ trước`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 30) return `${diffInDays} ngày trước`;
    return date.toLocaleDateString('vi-VN');
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

  const activeUsersCount = useMemo(() => users.filter(u => u.status === "active").length, [users]);
  const inactiveUsersCount = useMemo(() => users.filter(u => u.status === "inactive").length, [users]);

  // ─── Bulk Action Helpers ───────────────────────────────────────────────────

  const isAllCurrentPageSelected = users.length > 0 && users.every(u => selectedUserIds.has(u.id));
  const isSomeCurrentPageSelected = users.some(u => selectedUserIds.has(u.id)) && !isAllCurrentPageSelected;

  const toggleCurrentPageSelection = () => {
    const newSelected = new Set(selectedUserIds);
    if (isAllCurrentPageSelected) {
      users.forEach(u => newSelected.delete(u.id));
    } else {
      users.forEach(u => newSelected.add(u.id));
    }
    setSelectedUserIds(newSelected);
  };

  const toggleUserSelection = (id: string) => {
    const newSelected = new Set(selectedUserIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedUserIds(newSelected);
  };

  const handleBulkStatusChange = async (newStatus: "active" | "inactive") => {
    if (selectedUserIds.size === 0) return;
    
    // Check if self-deactivating
    if (newStatus === "inactive" && selectedUserIds.has(currentAdminId)) {
      toast.error('Không thể tự khóa tài khoản của chính mình trong bulk action');
      return;
    }

    setBulkConfirmStatus(newStatus);
    setBulkConfirmOpen(true);
  };

  const executeBulkStatusChange = async () => {
    if (!bulkConfirmStatus || selectedUserIds.size === 0) return;
    
    setBulkActionLoading(true);
    let successCount = 0;
    let failCount = 0;

    const idsArray = Array.from(selectedUserIds);
    
    // Execute all API requests in parallel Promise.all
    await Promise.all(
      idsArray.map(async (id) => {
        try {
          await updateUserStatus(id, bulkConfirmStatus);
          successCount++;
        } catch (error) {
          console.error(`Bulk action failed for user ${id}`, error);
          failCount++;
        }
      })
    );

    if (successCount > 0) {
      toast.success(`Đã ${bulkConfirmStatus === 'active' ? 'mở khóa' : 'khóa'} thành công ${successCount} tài khoản`);
      await fetchUsers(); // Refresh the list
    }
    if (failCount > 0) {
      toast.error(`Có ${failCount} tài khoản thất bại thao tác. Vui lòng thử lại.`);
    }

    setBulkActionLoading(false);
    setBulkConfirmOpen(false);
    setBulkConfirmStatus(null);
  };

  // ─── Export helpers ──────────────────────────────────────────────────────
  const [exporting, setExporting] = useState(false);

  const fetchAllUsersForExport = async (): Promise<UserListItem[]> => {
    // Backend limits page_size to max 100, so paginate through all pages
    const allItems: UserListItem[] = [];
    let page = 1;
    const batchSize = 100;
    let hasMore = true;

    while (hasMore) {
      const data = await getUsers({
        page,
        page_size: batchSize,
        search: debouncedSearch || undefined,
        role: roleFilter !== "all" ? roleFilter : undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      });
      allItems.push(...data.items);
      hasMore = allItems.length < data.total;
      page++;
    }

    return allItems;
  };

  const formatExportDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('vi-VN', { year: 'numeric', month: '2-digit', day: '2-digit' });
  };

  const buildExportRows = (items: UserListItem[]) => {
    const headers = ['Tên', 'Email', 'Vai trò', 'Trạng thái', 'Lượt tải lên', 'Ngày tham gia', 'Hoạt động gần nhất'];
    const rows = items.map(u => [
      u.full_name || 'Không có tên',
      u.email,
      u.role === 'admin' ? 'Quản trị viên' : 'Người dùng',
      u.status === 'active' ? 'Hoạt động' : 'Không hoạt động',
      String(u.uploads_count),
      formatExportDate(u.join_date),
      formatExportDate(u.last_active_at),
    ]);
    return { headers, rows };
  };

  const handleExportCSV = async () => {
    try {
      setExporting(true);
      const items = await fetchAllUsersForExport();
      const { headers, rows } = buildExportRows(items);

      const escapeCSV = (val: string) => {
        if (val.includes(',') || val.includes('"') || val.includes('\n')) {
          return `"${val.replace(/"/g, '""')}"`;
        }
        return val;
      };

      const BOM = '\uFEFF';
      const csv = BOM + [headers.map(escapeCSV).join(','), ...rows.map(r => r.map(escapeCSV).join(','))].join('\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `danh_sach_nguoi_dung_${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
      URL.revokeObjectURL(url);
      toast.success('Đã xuất CSV thành công!');
    } catch (err) {
      console.error('Export CSV error:', err);
      toast.error('Xuất CSV thất bại');
    } finally {
      setExporting(false);
    }
  };

  const handleExportExcel = async () => {
    try {
      setExporting(true);
      const items = await fetchAllUsersForExport();
      const { headers, rows } = buildExportRows(items);

      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('Người dùng');

      // Add Headers
      const headerRow = worksheet.addRow(headers);
      
      // Style headers: green background (#17805F), white bold text, centered
      headerRow.eachCell((cell) => {
        cell.fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: 'FF17805F' }
        };
        cell.font = {
          color: { argb: 'FFFFFFFF' },
          bold: true
        };
        cell.alignment = { vertical: 'middle', horizontal: 'center' };
        cell.border = {
          top: { style: 'thin', color: { argb: 'FFD1D5DB' } },
          left: { style: 'thin', color: { argb: 'FFD1D5DB' } },
          bottom: { style: 'thin', color: { argb: 'FFD1D5DB' } },
          right: { style: 'thin', color: { argb: 'FFD1D5DB' } }
        };
      });

      // Add Data Rows
      rows.forEach(rowData => {
        const row = worksheet.addRow(rowData);
        row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
          cell.alignment = { vertical: 'middle', horizontal: colNumber === 5 ? 'center' : 'left' };
          cell.border = {
            top: { style: 'thin', color: { argb: 'FFD1D5DB' } },
            left: { style: 'thin', color: { argb: 'FFD1D5DB' } },
            bottom: { style: 'thin', color: { argb: 'FFD1D5DB' } },
            right: { style: 'thin', color: { argb: 'FFD1D5DB' } }
          };
          // Cast string numbers back to number format if needed
          if (colNumber === 5 && cell.value) {
            cell.value = Number(cell.value);
            cell.numFmt = '#,##0';
          }
        });
      });

      // Adjust column widths
      worksheet.columns = [
        { width: 25 }, // Tên
        { width: 35 }, // Email
        { width: 18 }, // Vai trò
        { width: 18 }, // Trạng thái
        { width: 14 }, // Lượt tải lên
        { width: 18 }, // Ngày tham gia
        { width: 22 }, // Hoạt động gần nhất
      ];

      // Export file
      const buffer = await workbook.xlsx.writeBuffer();
      const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `danh_sach_nguoi_dung_${new Date().toISOString().slice(0, 10)}.xlsx`;
      link.click();
      URL.revokeObjectURL(url);
      
      toast.success('Đã xuất Excel thành công!');
    } catch (err) {
      console.error('Export Excel error:', err);
      toast.error('Xuất Excel thất bại');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className={styles.userManagementPage}>
      {/* Header */}
      <div className={styles.pageHeader}>
        <div className={styles.pageTitle}>
          <h1>{t('admin.user_management.title')}</h1>
          <p>{t('admin.user_management.subtitle')}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className={styles.btnExport}
            onClick={handleExportCSV}
            disabled={exporting || totalUsers === 0}
            title="Xuất CSV"
          >
            <Download size={16} />
            CSV
          </button>
          <button
            className={styles.btnExport}
            onClick={handleExportExcel}
            disabled={exporting || totalUsers === 0}
            title="Xuất Excel"
          >
            <FileSpreadsheet size={16} />
            Excel
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className={styles.statsGrid}>
        <StatCard
          icon={Users}
          value={totalUsers}
          label={t('admin.user_management.total_users')}
          color="default"
        />
        <StatCard
          icon={UserCheck}
          value={activeUsersCount}
          label={t('admin.user_management.status.active')}
          color="green"
        />
        <StatCard
          icon={UserX}
          value={inactiveUsersCount}
          label={t('admin.user_management.status.inactive')}
          color="red"
        />
      </div>

      {/* Filters */}
      <div className={styles.filtersCard}>
        <div className={styles.filterGroup}>
          <label>Tìm kiếm</label>
          <div className={styles.filterInputContainer}>
            <Search className={styles.filterInputIcon} size={16} />
            <input
              type="text"
              placeholder="Tìm theo tên hoặc email..."
              className={styles.filterInput}
              value={searchQuery}
              onChange={handleSearchChange}
            />
          </div>
        </div>
        <div className={styles.filterGroup}>
          <label>Lọc theo vai trò</label>
          <select 
            className={styles.filterSelect}
            value={roleFilter}
            onChange={handleRoleChange}
          >
            <option value="all">Tất cả vai trò</option>
            <option value="admin">Quản trị viên</option>
            <option value="user">Người dùng</option>
          </select>
        </div>
        <div className={styles.filterGroup}>
          <label>Lọc theo trạng thái</label>
          <select 
            className={styles.filterSelect}
            value={statusFilter}
            onChange={handleStatusChange}
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="active">Hoạt động</option>
            <option value="inactive">Đã khóa</option>
          </select>
        </div>
      </div>

      <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "0.75rem" }}>
        {totalUsers > 0 && `Hiển thị ${indexOfFirstUser}-${indexOfLastUser} trong tổng số ${totalUsers}`}
      </div>

      {/* Table */}
      <div className={styles.tableContainer}>
        {/* Bulk Action Toolbar */}
        {selectedUserIds.size > 0 && (
          <div className={styles.bulkActionsBar}>
            <div className={styles.bulkActionsInfo}>
              Đã chọn {selectedUserIds.size} tài khoản
            </div>
            <div className={styles.bulkActionsGroup}>
              <button 
                className={`${styles.btnBulkAction} ${styles.btnBulkActivate}`}
                onClick={() => handleBulkStatusChange('active')}
                disabled={bulkActionLoading}
              >
                <ShieldAlert size={14} /> Mở khóa đã chọn
              </button>
              <button 
                className={`${styles.btnBulkAction} ${styles.btnBulkDeactivate}`}
                onClick={() => handleBulkStatusChange('inactive')}
                disabled={bulkActionLoading}
              >
                <ShieldBan size={14} /> Khóa đã chọn
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className={styles.loadingContainer}>
            <div className={styles.loadingSpinner}></div>
            <div className={styles.loadingText}>Đang tải danh sách...</div>
          </div>
        ) : users.length === 0 ? (
          <div className={styles.emptyState}>
            <Search size={48} className={styles.emptyStateIcon} />
            <p>Không tìm thấy người dùng phù hợp.</p>
          </div>
        ) : (
          <table className={styles.dataTable}>
            <thead>
              <tr>
                <th style={{ width: '40px', paddingRight: 0 }}>
                  <div className={styles.checkboxContainer}>
                    <input 
                      type="checkbox" 
                      className={styles.customCheckbox}
                      checked={isAllCurrentPageSelected}
                      ref={input => {
                        if (input) {
                          input.indeterminate = isSomeCurrentPageSelected;
                        }
                      }}
                      onChange={toggleCurrentPageSelection}
                    />
                  </div>
                </th>
                <th>Người dùng</th>
                <th>Vai trò</th>
                <th>Trạng thái</th>
                <th>Lượt quét</th>
                <th>Hoạt động gần nhất</th>
                <th style={{ textAlign: "right", paddingRight: "1.5rem" }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user, idx) => {
                const uniqueId = `${user.id}-${idx}`;
                return (
                <tr key={uniqueId}>
                  <td style={{ width: '40px', paddingRight: 0 }}>
                    <div className={styles.checkboxContainer}>
                      <input 
                        type="checkbox" 
                        className={styles.customCheckbox}
                        checked={selectedUserIds.has(user.id)}
                        onChange={() => toggleUserSelection(user.id)}
                      />
                    </div>
                  </td>
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
                        <span className={styles.userName}>{user.full_name || "Chưa đặt tên"}</span>
                        <span className={styles.userEmail}>{user.email}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`${styles.roleBadge} ${user.role.toLowerCase() === 'admin' ? styles.roleAdmin : styles.roleUser}`}>
                      {user.role.toLowerCase() === 'admin' ? 'Quản trị viên' : 'Người dùng'}
                    </span>
                  </td>
                  <td>
                    <span className={`${styles.statusBadge} ${user.status === 'active' ? styles.statusActive : styles.statusInactive}`}>
                      {user.status === 'active' ? 'Hoạt động' : 'Đã khóa'}
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
                          <FileText size={16} /> Xem chi tiết
                        </button>
                        {user.status === "active" ? (
                          <button 
                            className={`${styles.actionItem} ${styles.actionDeactivate}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleUserStatus(user.id, idx);
                            }}
                          >
                            <ShieldBan size={16} /> Vô hiệu hóa
                          </button>
                        ) : (
                          <button 
                            className={`${styles.actionItem} ${styles.actionActivate}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleUserStatus(user.id, idx);
                            }}
                          >
                            <ShieldAlert size={16} /> Kích hoạt
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
            <ChevronLeft size={16} /> Trước
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
            Tiếp <ChevronRight size={16} />
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
                  <h2 className={styles.panelTitle}>{selectedUser.full_name || "Chưa đặt tên"}</h2>
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
                    <span className={styles.userInfoLabel}>Vai trò</span>
                    <span className={`${styles.roleBadge} ${selectedUser.role === 'admin' ? styles.roleAdmin : styles.roleUser}`}>
                      {selectedUser.role}
                    </span>
                  </div>
                  <div className={styles.userInfoItem}>
                    <span className={styles.userInfoLabel}>Trạng thái</span>
                    <span className={`${styles.statusBadge} ${selectedUser.status === 'active' ? styles.statusActive : styles.statusInactive}`}>
                      {selectedUser.status}
                    </span>
                  </div>
                  <div className={styles.userInfoItem}>
                    <span className={styles.userInfoLabel}>Tổng lượt quét</span>
                    <span className={styles.userInfoValue}>{selectedUser.uploads_count || 0}</span>
                  </div>
                  <div className={styles.userInfoItem}>
                    <span className={styles.userInfoLabel}>Ngày tham gia</span>
                    <span className={styles.userInfoValue}>
                      {selectedUser.join_date ? new Date(selectedUser.join_date).toLocaleDateString("vi-VN") : "—"}
                    </span>
                  </div>
                  <div className={styles.userInfoItem} style={{ gridColumn: "1 / -1" }}>
                    <span className={styles.userInfoLabel}>Hoạt động gần nhất</span>
                    <span className={styles.userInfoValue}>{selectedUser.last_active_at ? new Date(selectedUser.last_active_at).toLocaleDateString("vi-VN") : "Chưa có"}</span>
                  </div>
                </div>
              )}

              {/* Divider */}
              {!panelLoading && <div className={styles.panelDivider} />}

              <h3 className={styles.scanHistoryTitle}>Lịch sử quét ({selectedUser.scan_history?.length || 0})</h3>
              {panelLoading ? (
                 <div className={styles.loadingContainer}>
                   <div className={styles.loadingSpinner}></div>
                   <div className={styles.loadingText}>Đang tải chi tiết...</div>
                 </div>
              ) : !selectedUser.scan_history || selectedUser.scan_history.length === 0 ? (
                 <div className={styles.emptyState}>
                   <FileText size={48} />
                   <p>Chưa có lịch sử quét nào.</p>
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
                            <span className={styles.scanWoundType} title={scan.wound_type || "Không xác định"}>
                              {scan.wound_type || "Không xác định"}
                            </span>
                            <span className={styles.scanDate}>
                              {new Date(scan.created_at).toLocaleDateString("vi-VN")}
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

      {/* Confirmation Dialog for Bulk Action */}
      <ConfirmDialog
        isOpen={bulkConfirmOpen}
        title={bulkConfirmStatus === 'active' ? "Xác nhận mở khóa hàng loạt" : "Xác nhận khóa hàng loạt"}
        message={`Bạn có chắc chắn muốn ${bulkConfirmStatus === 'active' ? 'mở khóa' : 'khóa'} ${selectedUserIds.size} tài khoản đã chọn không?${bulkConfirmStatus === 'inactive' ? ' Những người dùng này sẽ không thể đăng nhập vào hệ thống.' : ''}`}
        confirmText={bulkConfirmStatus === 'active' ? "Mở khóa" : "Khóa tài khoản"}
        cancelText="Hủy bỏ"
        variant={bulkConfirmStatus === 'active' ? "info" : "danger"}
        onConfirm={executeBulkStatusChange}
        onCancel={() => {
          setBulkConfirmOpen(false);
          setBulkConfirmStatus(null);
        }}
        isLoading={bulkActionLoading}
      />
    </div>
  );
}
