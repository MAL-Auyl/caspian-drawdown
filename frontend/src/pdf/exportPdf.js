import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";

// jsPDF со встроенными шрифтами не умеет кириллицу без явно подключённого
// TTF (грабля из прошлого прогона). Обходим это: снимаем уже отрисованный
// DOM в растровое изображение и кладём картинкой в PDF — текста как текста
// в PDF нет, зато кириллица гарантированно на месте.
export async function exportDashboardToPdf(targetEl, filename = "caspian-pulse-report.pdf") {
  const canvas = await html2canvas(targetEl, { scale: 2, useCORS: true, backgroundColor: "#ffffff" });
  const imgData = canvas.toDataURL("image/png");

  const pdf = new jsPDF({ orientation: "landscape", unit: "pt", format: "a4" });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const ratio = Math.min(pageWidth / canvas.width, pageHeight / canvas.height);
  const w = canvas.width * ratio;
  const h = canvas.height * ratio;

  pdf.addImage(imgData, "PNG", (pageWidth - w) / 2, (pageHeight - h) / 2, w, h);
  pdf.save(filename);
}
