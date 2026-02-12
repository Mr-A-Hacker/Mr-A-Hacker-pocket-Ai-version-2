import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import Home from './components/Home';
import ChatInterface from './components/ChatInterface';
import CameraView from './components/CameraView';

const AnimatedRoutes = ({ showCamera, setShowCamera }) => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      {/* Camera Overlay */}
      {showCamera && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className="absolute inset-0 z-[100]"
        >
          <CameraView onClose={() => setShowCamera(false)} />
        </motion.div>
      )}

      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Home onOpenCamera={() => setShowCamera(true)} />} />
        <Route
          path="/chat"
          element={<ChatInterface layoutId="avatar-hero" />}
        />
      </Routes>
    </AnimatePresence>
  );
};

export default function App() {
  const [showCamera, setShowCamera] = useState(false);

  return (
    <BrowserRouter>
      <AnimatedRoutes showCamera={showCamera} setShowCamera={setShowCamera} />
    </BrowserRouter>
  );
}
