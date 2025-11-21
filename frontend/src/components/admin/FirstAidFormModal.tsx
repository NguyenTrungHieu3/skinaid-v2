import { X, Plus, AlertTriangle, Save, Loader2 } from 'lucide-react';
import styles from './FirstAidManagement.module.css';

interface FormData {
    wound_type: string;
    severity: string;
    sub_type: string;
    title: string;
    description: string;
    steps: string[];
    dos: string[];
    donts: string[];
    supplies_needed: string[];
    estimated_healing_time: string;
    is_active: boolean;
}

interface FirstAidFormModalProps {
    isOpen: boolean;
    mode: 'add' | 'edit';
    formData: FormData;
    onClose: () => void;
    onSubmit: (e: React.FormEvent) => void;
    onFormChange: (data: FormData) => void;
    onArrayChange: (field: keyof FormData, index: number, value: string) => void;
    onAddArrayItem: (field: keyof FormData) => void;
    onRemoveArrayItem: (field: keyof FormData, index: number) => void;
    isSubmitting: boolean;
}

/**
 * Modal component for adding/editing First Aid guides
 * Extracted from FirstAidManagement for better code organization
 */
export default function FirstAidFormModal({
    isOpen,
    mode,
    formData,
    onClose,
    onSubmit,
    onFormChange,
    onArrayChange,
    onAddArrayItem,
    onRemoveArrayItem,
    isSubmitting
}: FirstAidFormModalProps) {
    if (!isOpen) return null;

    return (
        <div className={styles.modalOverlay} onClick={onClose}>
            <div className={`${styles.modalContent} ${styles.modalLarge}`} onClick={(e) => e.stopPropagation()}>
                <div className={styles.modalHeader}>
                    <h2>{mode === 'edit' ? 'Edit Guide' : 'Create New Guide'}</h2>
                    <button className={styles.modalClose} onClick={onClose} disabled={isSubmitting}>
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={onSubmit}>
                    <div className={styles.modalBody}>
                        {/* Disclaimer */}
                        <div className={styles.disclaimerCard} style={{ marginBottom: '1.5rem' }}>
                            <div className={styles.disclaimerIcon}>
                                <AlertTriangle />
                            </div>
                            <div className={styles.disclaimerContent}>
                                <h4 className={styles.disclaimerTitle}>Medical Content Warning</h4>
                                <p className={styles.disclaimerText}>
                                    Please ensure all medical information is accurate and verified by professionals.
                                    Incorrect first aid advice can lead to serious harm.
                                </p>
                            </div>
                        </div>

                        {/* Wound Type & Severity */}
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label>Wound Type</label>
                                <select
                                    value={formData.wound_type}
                                    onChange={(e) => onFormChange({ ...formData, wound_type: e.target.value })}
                                    disabled={mode === 'edit' || isSubmitting}
                                    required
                                >
                                    <option value="abrasion">Scratch / Abrasion</option>
                                    <option value="bruise">Bruise / Contusion</option>
                                    <option value="burn">Burn</option>
                                    <option value="cut">Cut / Laceration</option>
                                </select>
                            </div>
                            <div className={styles.formGroup}>
                                <label>Severity</label>
                                <select
                                    value={formData.severity}
                                    onChange={(e) => onFormChange({ ...formData, severity: e.target.value })}
                                    disabled={mode === 'edit' || isSubmitting}
                                    required
                                >
                                    <option value="mild">Mild</option>
                                    <option value="moderate">Moderate</option>
                                    <option value="severe">Severe</option>
                                </select>
                            </div>
                            <div className={styles.formGroup}>
                                <label>Sub Type (Optional)</label>
                                <input
                                    type="text"
                                    value={formData.sub_type || ''}
                                    onChange={(e) => onFormChange({ ...formData, sub_type: e.target.value })}
                                    placeholder="e.g., Blister"
                                    disabled={isSubmitting}
                                />
                            </div>
                        </div>

                        {/* Title */}
                        <div className={styles.formGroup}>
                            <label>Title</label>
                            <input
                                type="text"
                                value={formData.title}
                                onChange={(e) => onFormChange({ ...formData, title: e.target.value })}
                                required
                                placeholder="e.g., Basic treatment for abrasion"
                                disabled={isSubmitting}
                            />
                        </div>

                        {/* Description */}
                        <div className={styles.formGroup}>
                            <label>Description</label>
                            <textarea
                                value={formData.description}
                                onChange={(e) => onFormChange({ ...formData, description: e.target.value })}
                                rows={3}
                                disabled={isSubmitting}
                            />
                        </div>

                        {/* Steps */}
                        <div className={styles.modalSection}>
                            <h3>Steps</h3>
                            {formData.steps.map((step, idx) => (
                                <div key={idx} className={styles.formGroup} style={{ display: 'flex', gap: '0.5rem' }}>
                                    <span style={{ paddingTop: '0.5rem', fontWeight: 'bold' }}>{idx + 1}.</span>
                                    <input
                                        type="text"
                                        value={step}
                                        onChange={(e) => onArrayChange('steps', idx, e.target.value)}
                                        placeholder={`Step ${idx + 1}`}
                                        style={{ flex: 1 }}
                                        disabled={isSubmitting}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => onRemoveArrayItem('steps', idx)}
                                        className={styles.btnDelete}
                                        disabled={isSubmitting}
                                    >
                                        <X size={16} />
                                    </button>
                                </div>
                            ))}
                            <button
                                type="button"
                                onClick={() => onAddArrayItem('steps')}
                                className={styles.btnSecondary}
                                disabled={isSubmitting}
                            >
                                <Plus size={16} /> Add Step
                            </button>
                        </div>

                        {/* Do's & Don'ts */}
                        <div className={styles.formRow}>
                            {/* Do's */}
                            <div className={styles.modalSection} style={{ flex: 1 }}>
                                <h3>Do's</h3>
                                {formData.dos.map((item, idx) => (
                                    <div key={idx} className={styles.formGroup} style={{ display: 'flex', gap: '0.5rem' }}>
                                        <input
                                            type="text"
                                            value={item}
                                            onChange={(e) => onArrayChange('dos', idx, e.target.value)}
                                            placeholder="Do..."
                                            style={{ flex: 1 }}
                                            disabled={isSubmitting}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => onRemoveArrayItem('dos', idx)}
                                            className={styles.btnDelete}
                                            disabled={isSubmitting}
                                        >
                                            <X size={16} />
                                        </button>
                                    </div>
                                ))}
                                <button
                                    type="button"
                                    onClick={() => onAddArrayItem('dos')}
                                    className={styles.btnSecondary}
                                    disabled={isSubmitting}
                                >
                                    <Plus size={16} /> Add Do
                                </button>
                            </div>

                            {/* Don'ts */}
                            <div className={styles.modalSection} style={{ flex: 1 }}>
                                <h3>Don'ts</h3>
                                {formData.donts.map((item, idx) => (
                                    <div key={idx} className={styles.formGroup} style={{ display: 'flex', gap: '0.5rem' }}>
                                        <input
                                            type="text"
                                            value={item}
                                            onChange={(e) => onArrayChange('donts', idx, e.target.value)}
                                            placeholder="Don't..."
                                            style={{ flex: 1 }}
                                            disabled={isSubmitting}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => onRemoveArrayItem('donts', idx)}
                                            className={styles.btnDelete}
                                            disabled={isSubmitting}
                                        >
                                            <X size={16} />
                                        </button>
                                    </div>
                                ))}
                                <button
                                    type="button"
                                    onClick={() => onAddArrayItem('donts')}
                                    className={styles.btnSecondary}
                                    disabled={isSubmitting}
                                >
                                    <Plus size={16} /> Add Don't
                                </button>
                            </div>
                        </div>

                        {/* Supplies Needed */}
                        <div className={styles.modalSection}>
                            <h3>Supplies Needed</h3>
                            {formData.supplies_needed.map((item, idx) => (
                                <div key={idx} className={styles.formGroup} style={{ display: 'flex', gap: '0.5rem' }}>
                                    <input
                                        type="text"
                                        value={item}
                                        onChange={(e) => onArrayChange('supplies_needed', idx, e.target.value)}
                                        placeholder="Supply item"
                                        style={{ flex: 1 }}
                                        disabled={isSubmitting}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => onRemoveArrayItem('supplies_needed', idx)}
                                        className={styles.btnDelete}
                                        disabled={isSubmitting}
                                    >
                                        <X size={16} />
                                    </button>
                                </div>
                            ))}
                            <button
                                type="button"
                                onClick={() => onAddArrayItem('supplies_needed')}
                                className={styles.btnSecondary}
                                disabled={isSubmitting}
                            >
                                <Plus size={16} /> Add Supply
                            </button>
                        </div>

                        {/* Submit Actions */}
                        <div className={styles.modalActions}>
                            <button
                                type="button"
                                className={styles.btnSecondary}
                                onClick={onClose}
                                disabled={isSubmitting}
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className={styles.adminBtnPrimary}
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? (
                                    <>
                                        <Loader2 size={18} className={styles.spinning} />
                                        {mode === 'edit' ? 'Saving...' : 'Creating...'}
                                    </>
                                ) : (
                                    <>
                                        <Save size={18} />
                                        {mode === 'edit' ? 'Save Changes' : 'Create Guide'}
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}
