import "./MapComponents.css";

interface FilterChipsProps {
    selected: string;
    onChange: (value: string) => void;
}

const FACILITY_TYPES = [
    { value: "all", label: "Tất cả" },
    { value: "healthcare.hospital", label: "Bệnh viện" },
    { value: "healthcare.clinic_or_praxis", label: "Phòng khám" },
    { value: "healthcare.pharmacy", label: "Nhà thuốc" },
];

const FilterChips = ({ selected, onChange }: FilterChipsProps) => {
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
