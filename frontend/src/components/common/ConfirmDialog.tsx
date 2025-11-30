import { AlertTriangle } from 'lucide-react';
import styles from './ConfirmDialog.module.css';

interface ConfirmDialogProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    variant?: 'danger' | 'warning' | 'info';
    onConfirm: () => void;
    onCancel: () => void;
    isLoading?: boolean;
}

/**
 * Reusable confirmation dialog component
 * Replaces native window.confirm() with a better UX
 */
export default function ConfirmDialog({
    isOpen,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    variant = 'warning',
    onConfirm,
    onCancel,
    isLoading = false
}: ConfirmDialogProps) {
    if (!isOpen) return null;

    const getVariantClass = () => {
        switch (variant) {
            case 'danger':
                return styles.variantDanger;
            case 'warning':
                return styles.variantWarning;
            case 'info':
                return styles.variantInfo;
            default:
                return styles.variantWarning;
        }
    };

    return (
        <div className={styles.overlay} onClick={onCancel}>
            <div className={styles.dialog} onClick={(e) => e.stopPropagation()}>
                <div className={`${styles.header} ${getVariantClass()}`}>
                    <div className={styles.icon}>
                        <AlertTriangle size={24} />
                    </div>
                    <h3>{title}</h3>
                </div>

                <div className={styles.body}>
                    <p>{message}</p>
                </div>

                <div className={styles.actions}>
                    <button
                        type="button"
                        className={styles.btnCancel}
                        onClick={onCancel}
                        disabled={isLoading}
                    >
                        {cancelText}
                    </button>
                    <button
                        type="button"
                        className={`${styles.btnConfirm} ${getVariantClass()}`}
                        onClick={onConfirm}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <>
                                <span className={styles.spinner} />
                                Processing...
                            </>
                        ) : (
                            confirmText
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
