import { useTranslation } from "react-i18next";
import "./MapComponents.css";

interface FilterChipsProps {
    selected: string;
    onChange: (value: string) => void;
}

const FilterChips = ({ selected, onChange }: FilterChipsProps) => {
    const { t } = useTranslation();

    const FACILITY_TYPES = [
        { value: "all", label: t('map.filter_all') },
        { value: "healthcare.hospital", label: t('map.filter_hospital') },
        { value: "healthcare.clinic_or_praxis", label: t('map.filter_clinic') },
        { value: "healthcare.pharmacy", label: t('map.filter_pharmacy') },
    ];

    return (
        <div className="filter-chips">
            {FACILITY_TYPES.map((type) => (
                <button
                    key={type.value}
                    className={`chip ${selected === type.value ? "selected" : ""}`}
                    onClick={() => onChange(type.value)}
                >
                    {type.label}
                </button>
            ))}
        </div>
    );
};

export default FilterChips;
