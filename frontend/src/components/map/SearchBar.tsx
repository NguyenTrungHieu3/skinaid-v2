import { Search, SlidersHorizontal } from "lucide-react";
import { useTranslation } from "react-i18next";
import "./MapComponents.css";

interface SearchBarProps {
    value: string;
    onChange: (value: string) => void;
    onFilterClick: () => void;
    onSearch: () => void;
}

const SearchBar = ({ value, onChange, onFilterClick, onSearch }: SearchBarProps) => {
    const { t } = useTranslation();

    return (
        <div className="search-bar">
            <div className="search-input-wrapper">
                <Search className="search-icon" />
                <input
                    type="text"
                    placeholder={t('map.search_placeholder')}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && onSearch()}
                    className="search-input"
                />
            </div>
            <button
                className="filter-btn"
                onClick={onFilterClick}
                title={t('map.filter')}
            >
                <SlidersHorizontal className="h-5 w-5" />
            </button>
        </div>
    );
};

export default SearchBar;
