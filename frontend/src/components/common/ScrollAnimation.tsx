import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface ScrollAnimationProps {
    children: ReactNode;
    animation?: "fade-up" | "fade-down" | "fade-left" | "fade-right" | "zoom-in" | "flip-up";
    delay?: number;
    duration?: number;
    className?: string;
    viewport?: { once?: boolean; amount?: number };
}

const variants = {
    "fade-up": {
        hidden: { opacity: 0, y: 50 },
        visible: { opacity: 1, y: 0 },
    },
    "fade-down": {
        hidden: { opacity: 0, y: -50 },
        visible: { opacity: 1, y: 0 },
    },
    "fade-left": {
        hidden: { opacity: 0, x: 50 },
        visible: { opacity: 1, x: 0 },
    },
    "fade-right": {
        hidden: { opacity: 0, x: -50 },
        visible: { opacity: 1, x: 0 },
    },
    "zoom-in": {
        hidden: { opacity: 0, scale: 0.8 },
        visible: { opacity: 1, scale: 1 },
    },
    "flip-up": {
        hidden: { opacity: 0, rotateX: 90 },
        visible: { opacity: 1, rotateX: 0 },
    },
};

const ScrollAnimation = ({
    children,
    animation = "fade-up",
    delay = 0,
    duration = 0.5,
    className = "",
    viewport = { once: true, amount: 0.2 },
}: ScrollAnimationProps) => {
    return (
        <motion.div
            variants={variants[animation]}
            initial="hidden"
            whileInView="visible"
            viewport={viewport}
            transition={{ duration, delay, ease: "easeOut" }}
            className={className}
        >
            {children}
        </motion.div>
    );
};

export default ScrollAnimation;
