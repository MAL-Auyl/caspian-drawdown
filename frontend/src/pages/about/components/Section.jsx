import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } },
};

export default function Section({ kicker, title, subtitle, children, id, className = "" }) {
  return (
    <motion.section
      id={id}
      className={`about-section ${className}`}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.2 }}
      variants={fadeUp}
    >
      {(kicker || title) && (
        <div className="about-section-head">
          {kicker && <span className="about-kicker">{kicker}</span>}
          {title && <h2 className="about-title">{title}</h2>}
          {subtitle && <p className="about-subtitle">{subtitle}</p>}
        </div>
      )}
      {children}
    </motion.section>
  );
}
