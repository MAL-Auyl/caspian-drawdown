import { motion } from "framer-motion";

const item = {
  hidden: { opacity: 0, x: -16 },
  show: { opacity: 1, x: 0, transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] } },
};

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.1 } } };

export default function RoadmapTimeline({ items }) {
  return (
    <motion.ol
      className="roadmap-timeline"
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.2 }}
      variants={stagger}
    >
      {items.map((it) => (
        <motion.li className="roadmap-item" key={it.label} variants={item}>
          <div className="roadmap-dot" />
          <div>
            <span className="roadmap-year">{it.year}</span>
            <span className="roadmap-label">{it.label}</span>
          </div>
        </motion.li>
      ))}
    </motion.ol>
  );
}
