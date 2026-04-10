import { ChevronLeft, ChevronRight } from 'lucide-react';
import styles from './Pagination.module.css';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    itemsPerPage: number;
    onPageChange: (page: number) => void;
    showInfo?: boolean;
    className?: string;
}

/**
 * Reusable pagination component with numbered pages and ellipsis
 * Used across User Management, Admin Logs, and other paginated views
 */
export default function Pagination({
    currentPage,
    totalPages,
    totalItems,
    itemsPerPage,
    onPageChange,
    showInfo = true,
    className = ''
}: PaginationProps) {

    /**
     * Generate page numbers with ellipsis for large page counts
     * Logic: Show max 5 pages with intelligent ellipsis placement
     */
    const getPageNumbers = () => {
        const pages: (number | string)[] = [];
        const maxPagesToShow = 5;

        if (totalPages <= maxPagesToShow) {
            // Show all pages if total is small
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Show pages with ellipsis
            if (currentPage <= 3) {
                // Near start: 1 2 3 4 ... 10
                for (let i = 1; i <= 4; i++) {
                    pages.push(i);
                }
                pages.push('...');
                pages.push(totalPages);
            } else if (currentPage >= totalPages - 2) {
                // Near end: 1 ... 7 8 9 10
                pages.push(1);
                pages.push('...');
                for (let i = totalPages - 3; i <= totalPages; i++) {
                    pages.push(i);
                }
            } else {
                // Middle: 1 ... 4 5 6 ... 10
                pages.push(1);
                pages.push('...');
                for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                    pages.push(i);
                }
                pages.push('...');
                pages.push(totalPages);
            }
        }
        return pages;
    };

    // Calculate display range
    const indexOfFirstItem = (currentPage - 1) * itemsPerPage + 1;
    const indexOfLastItem = Math.min(currentPage * itemsPerPage, totalItems);

    // Don't render if no items
    if (totalItems <= 0) return null;

    return (
        <div className={`${styles.pagination} ${className}`}>
            {/* Info Display */}
            {showInfo && totalItems > 0 && (
                <div className={styles.paginationInfo}>
                    Hiển thị {indexOfFirstItem}-{indexOfLastItem} trong tổng số {totalItems}
                </div>
            )}

            {/* Pagination Controls - Always show if we have items */}
            <div className={styles.paginationControls}>
                {/* Previous Button */}
                <button
                    className={styles.paginationBtn}
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    aria-label="Previous page"
                >
                    <ChevronLeft size={16} />
                    Trước
                </button>

                {/* Page Numbers - Only show if more than 1 page */}
                {totalPages > 1 && (
                    <div className={styles.paginationNumbers}>
                        {getPageNumbers().map((page, index) =>
                            page === '...' ? (
                                <span
                                    key={`ellipsis-${index}`}
                                    className={styles.paginationEllipsis}
                                    aria-hidden="true"
                                >
                                    ...
                                </span>
                            ) : (
                                <button
                                    key={page}
                                    onClick={() => onPageChange(page as number)}
                                    className={`${styles.paginationNumber} ${currentPage === page ? styles.active : ''
                                        }`}
                                    aria-label={`Page ${page}`}
                                    aria-current={currentPage === page ? 'page' : undefined}
                                >
                                    {page}
                                </button>
                            )
                        )}
                    </div>
                )}

                {/* Next Button */}
                <button
                    className={styles.paginationBtn}
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    aria-label="Next page"
                >
                    Tiếp
                    <ChevronRight size={16} />
                </button>
            </div>
        </div>
    );
}
