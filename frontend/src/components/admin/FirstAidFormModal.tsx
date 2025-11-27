import { X, Plus, AlertTriangle, Save, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
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
    source: string;
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
    const { t } = useTranslation();
    if (!isOpen) return null;

    return (
        <div className={styles.modalOverlay}>
            <div className={`${styles.modalContent} ${styles.modalLarge}`} onClick={(e) => e.stopPropagation()}>
                <div className={styles.modalHeader}>
                    <h2>{mode === 'edit' ? t('admin.first_aid_form.title_edit') : t('admin.first_aid_form.title_add')}</h2>
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
                                <h4 className={styles.disclaimerTitle}>{t('admin.first_aid_form.medical_warning_title')}</h4>
                                <p className={styles.disclaimerText}>
                                    {t('admin.first_aid_form.medical_warning_desc')}
                                </p>
                            </div>
                        </div>

                        {/* Wound Type & Severity */}
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label>{t('admin.first_aid_form.labels.wound_type')}</label>
                                <select
                                    value={formData.wound_type}
                                    onChange={(e) => onFormChange({ ...formData, wound_type: e.target.value })}
                                    disabled={mode === 'edit' || isSubmitting}
                                    required
                                >
                                    <option value="abrasion">{t('admin.first_aid_form.options.abrasion')}</option>
                                    <option value="bruise">{t('admin.first_aid_form.options.bruise')}</option>
                                    <option value="burn">{t('admin.first_aid_form.options.burn')}</option>
                                    <option value="cut">{t('admin.first_aid_form.options.cut')}</option>
                                </select>
                            </div>
                            <div className={styles.formGroup}>
                                <label>{t('admin.first_aid_form.labels.severity')}</label>
                                <select
                                    value={formData.severity}
                                    onChange={(e) => onFormChange({ ...formData, severity: e.target.value })}
                                    disabled={mode === 'edit' || isSubmitting}
                                    required
                                >
                                    <option value="mild">{t('admin.first_aid_form.options.mild')}</option>
                                    <option value="moderate">{t('admin.first_aid_form.options.moderate')}</option>
                                    <option value="severe">{t('admin.first_aid_form.options.severe')}</option>
                                </select>
                            </div>
                            <div className={styles.formGroup}>
                                <label>{t('admin.first_aid_form.labels.sub_type')}</label>
                                <input
                                    type="text"
                                    value={formData.sub_type || ''}
                                    onChange={(e) => onFormChange({ ...formData, sub_type: e.target.value })}
                                    placeholder={t('admin.first_aid_form.labels.sub_type_placeholder')}
                                    disabled={isSubmitting}
                                />
                            </div>
                        </div>

                        {/* Title */}
                        <div className={styles.formGroup}>
                            <label>{t('admin.first_aid_form.labels.title')}</label>
                            <input
                                type="text"
                                value={formData.title}
                                onChange={(e) => onFormChange({ ...formData, title: e.target.value })}
                                required
                                placeholder={t('admin.first_aid_form.labels.title_placeholder')}
                                disabled={isSubmitting}
                            />
                        </div>

                        {/* Steps */}
                        <div className={styles.modalSection}>
                            <h3>{t('admin.first_aid_form.labels.steps')}</h3>
                            {formData.steps.map((step, idx) => (
                                <div key={idx} className={styles.formGroup} style={{ display: 'flex', gap: '0.5rem' }}>
                                    <span style={{ paddingTop: '0.5rem', fontWeight: 'bold' }}>{idx + 1}.</span>
                                    <input
                                        type="text"
                                        value={step}
                                        onChange={(e) => onArrayChange('steps', idx, e.target.value)}
                                        placeholder={t('admin.first_aid_form.labels.step_placeholder', { index: idx + 1 })}
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
                                <Plus size={16} /> {t('admin.first_aid_form.buttons.add_step')}
                            </button>
                        </div>

                        {/* Do's & Don'ts */}
                        <div className={styles.formRow}>
                            {/* Do's */}
                            <div className={styles.modalSection} style={{ flex: 1 }}>
                                <h3>{t('admin.first_aid_form.labels.dos')}</h3>
                                {formData.dos.map((item, idx) => (
                                    <div key={idx} className={styles.formGroup} style={{ display: 'flex', gap: '0.5rem' }}>
                                        <input
                                            type="text"
                                            value={item}
                                            onChange={(e) => onArrayChange('dos', idx, e.target.value)}
                                            placeholder={t('admin.first_aid_form.labels.do_placeholder')}
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
                                    <Plus size={16} /> {t('admin.first_aid_form.buttons.add_do')}
                                </button>
                            </div>

                            {/* Don'ts */}
                            <div className={styles.modalSection} style={{ flex: 1 }}>
                                <h3>{t('admin.first_aid_form.labels.donts')}</h3>
                                {formData.donts.map((item, idx) => (
                                    <div key={idx} className={styles.formGroup} style={{ display: 'flex', gap: '0.5rem' }}>
                                        <input
                                            type="text"
                                            value={item}
                                            onChange={(e) => onArrayChange('donts', idx, e.target.value)}
                                            placeholder={t('admin.first_aid_form.labels.dont_placeholder')}
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
                                    <Plus size={16} /> {t('admin.first_aid_form.buttons.add_dont')}
                                </button>
                            </div>
                        </div>

                        {/* Supplies Needed */}
                        <div className={styles.modalSection}>
                            <h3>{t('admin.first_aid_form.labels.supplies')}</h3>
                            {formData.supplies_needed.map((item, idx) => (
                                <div key={idx} className={styles.formGroup} style={{ display: 'flex', gap: '0.5rem' }}>
                                    <input
                                        type="text"
                                        value={item}
                                        onChange={(e) => onArrayChange('supplies_needed', idx, e.target.value)}
                                        placeholder={t('admin.first_aid_form.labels.supply_placeholder')}
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
                                <Plus size={16} /> {t('admin.first_aid_form.buttons.add_supply')}
                            </button>
                        </div>

                        {/* Source */}
                        <div className={styles.formGroup}>
                            <label>{t('admin.first_aid_form.labels.source')}</label>
                            <input
                                type="text"
                                value={formData.source}
                                onChange={(e) => onFormChange({ ...formData, source: e.target.value })}
                                placeholder={t('admin.first_aid_form.labels.source_placeholder')}
                                disabled={isSubmitting}
                            />
                        </div>

                        {/* Submit Actions */}
                        <div className={styles.modalActions}>
                            <button
                                type="button"
                                className={styles.btnSecondary}
                                onClick={onClose}
                                disabled={isSubmitting}
                            >
                                {t('admin.first_aid_form.buttons.cancel')}
                            </button>
                            <button
                                type="submit"
                                className={styles.adminBtnPrimary}
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? (
                                    <>
                                        <Loader2 size={18} className={styles.spinning} />
                                        {mode === 'edit' ? t('admin.first_aid_form.buttons.saving') : t('admin.first_aid_form.buttons.creating')}
                                    </>
                                ) : (
                                    <>
                                        <Save size={18} />
                                        {mode === 'edit' ? t('admin.first_aid_form.buttons.save') : t('admin.first_aid_form.buttons.create')}
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
