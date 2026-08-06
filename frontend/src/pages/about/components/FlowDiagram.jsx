import { motion } from "framer-motion";

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
};

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};

/** steps: string[] | { label, hint }[] */
export default function FlowDiagram({ steps, direction = "vertical" }) {
  return (
    <motion.div
      className={`flow-diagram flow-${direction}`}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.3 }}
      variants={stagger}
    >
      {steps.map((step, i) => {
        const label = typeof step === "string" ? step : step.label;
        const hint = typeof step === "string" ? null : step.hint;
        return (
          <motion.div className="flow-step-wrap" key={label} variants={item}>
            <div className="flow-step">
              <span className="flow-step-index">{String(i + 1).padStart(2, "0")}</span>
              <span className="flow-step-label">{label}</span>
              {hint && <span className="flow-step-hint">{hint}</span>}
            </div>
            {i < steps.length - 1 && <div className="flow-arrow" aria-hidden>↓</div>}
          </motion.div>
        );
      })}
    </motion.div>
  );
}
