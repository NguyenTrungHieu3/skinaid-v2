import { useTranslation } from "react-i18next";
import "./MapComponents.css";

interface RadiusSliderProps {
    value: number;
    onChange: (value: number) => void;
    min?: number;
    max?: number;
}

const RadiusSlider = ({ value, onChange, min = 0.5, max = 50 }: RadiusSliderProps) => {
    const { t } = useTranslation();

    return (
        <div className="radius-slider-container">
            <label className="slider-label">{t('map.radius_label')}</label>
            <input
                type="range"
                min={min}
                max={max}
                step={0.5}
                value={value}
                onChange={(e) => onChange(parseFloat(e.target.value))}
                className="slider-input"
            />
            <div className="slider-values">
                <span>{t('map.min')}<br />{min} km</span>
                <span className="current-value">{t('map.current')}<br />{value} km</span>
                <span>{t('map.max')}<br />{max} km</span>
            </div>
        </div>
    );
};

export default RadiusSlider;
