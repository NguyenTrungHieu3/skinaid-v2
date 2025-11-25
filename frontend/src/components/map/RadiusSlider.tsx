import "./MapComponents.css";

interface RadiusSliderProps {
    value: number;
    onChange: (value: number) => void;
    min?: number;
    max?: number;
}

const RadiusSlider = ({ value, onChange, min = 0.5, max = 50 }: RadiusSliderProps) => {
    return (
        <div className="radius-slider-container">
            <label className="slider-label">Bán kính tìm kiếm</label>
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
                <span>MIN<br />{min} km</span>
                <span className="current-value">HIỆN TẠI<br />{value} km</span>
                <span>MAX<br />{max} km</span>
            </div>
        </div>
    );
};

export default RadiusSlider;
