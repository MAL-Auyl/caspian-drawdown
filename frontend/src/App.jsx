import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import AboutPage from "./pages/about/AboutPage";
import ChatWidget from "./chat/ChatWidget";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/about" element={<AboutPage />} />
      </Routes>
      <ChatWidget />
    </BrowserRouter>
  );
}
