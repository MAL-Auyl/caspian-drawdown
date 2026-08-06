import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] } },
};

export default function Card({ icon, title, children, badge, className = "" }) {
  return (
    <motion.div className={`about-card ${className}`} variants={fadeUp}>
      {icon && <div className="about-card-icon">{icon}</div>}
      {badge && <span className="about-card-badge">{badge}</span>}
      {title && <h3 className="about-card-title">{title}</h3>}
      {children && <div className="about-card-body">{children}</div>}
    </motion.div>
  );
}

const gridStagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

export function CardGrid({ children, columns = "auto" }) {
  return (
    <motion.div
      className="about-card-grid"
      style={columns !== "auto" ? { gridTemplateColumns: `repeat(${columns}, 1fr)` } : undefined}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.15 }}
      variants={gridStagger}
    >
      {children}
    </motion.div>
  );
}
