import { Search, SlidersHorizontal } from "lucide-react";
import "./MapComponents.css";

interface SearchBarProps {
    value: string;
    onChange: (value: string) => void;
    onFilterClick: () => void;
    onSearch: () => void;
}

const SearchBar = ({ value, onChange, onFilterClick, onSearch }: SearchBarProps) => {
    return (
        <div className="search-bar">
            <div className="search-input-wrapper">
                <Search className="search-icon" />
                <input
                    type="text"
                    placeholder="Tìm kiếm bệnh viện, phòng khám, nhà thuốc..."
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && onSearch()}
                    className="search-input"
                />
            </div>
            <button
                className="filter-btn"
                onClick={onFilterClick}
                title="Bộ lọc"
            >
                <SlidersHorizontal className="h-5 w-5" />
            </button>
        </div>
    );
};

export default SearchBar;
