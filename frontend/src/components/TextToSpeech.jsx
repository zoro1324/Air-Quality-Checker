// TextToSpeech.jsx - Reusable Text-to-Speech Component for Accessibility

import React, { useState, useEffect, useRef } from 'react';

/**
 * TextToSpeech Component
 * Provides accessible text-to-speech functionality using Web Speech API
 * 
 * Props:
 * - text: The text content to be read aloud
 * - autoPlay: Whether to start playing automatically (default: false)
 * - lang: Language code for speech synthesis (default: 'en-US')
 * - rate: Speech rate 0.1 to 10 (default: 1.0)
 * - pitch: Speech pitch 0 to 2 (default: 1.0)
 * - volume: Speech volume 0 to 1 (default: 1.0)
 */
function TextToSpeech({ 
  text, 
  autoPlay = false, 
  lang = 'en-US',
  rate = 1.0,
  pitch = 1.0,
  volume = 1.0 
}) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const utteranceRef = useRef(null);

  useEffect(() => {
    // Check if browser supports Speech Synthesis
    if (!('speechSynthesis' in window)) {
      setIsSupported(false);
      console.warn('Text-to-Speech is not supported in this browser');
      return;
    }

    // Cleanup function to stop speech when component unmounts
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  useEffect(() => {
    if (autoPlay && text && isSupported) {
      handlePlay();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoPlay, text]);

  const handlePlay = () => {
    if (!text || !isSupported) return;

    // If paused, resume
    if (isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
      setIsPlaying(true);
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    // Create new utterance
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = rate;
    utterance.pitch = pitch;
    utterance.volume = volume;

    utterance.onstart = () => {
      setIsPlaying(true);
      setIsPaused(false);
    };

    utterance.onend = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsPlaying(false);
      setIsPaused(false);
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const handlePause = () => {
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
      setIsPlaying(false);
    }
  };

  const handleStop = () => {
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
  };

  // Don't render if not supported
  if (!isSupported) {
    return (
      <div className="tts-not-supported">
        <span className="tts-icon">ℹ️</span>
        <span className="tts-message">Text-to-speech is not supported in your browser</span>
      </div>
    );
  }

  if (!text) {
    return null;
  }

  return (
    <div className="tts-controls">
      <div className="tts-buttons">
        {!isPlaying && !isPaused && (
          <button
            className="tts-button tts-play"
            onClick={handlePlay}
            aria-label="Read text aloud"
            title="Read text aloud"
          >
            <span className="tts-icon">🔊</span>
            <span className="tts-label">Listen</span>
          </button>
        )}
        
        {isPlaying && (
          <>
            <button
              className="tts-button tts-pause"
              onClick={handlePause}
              aria-label="Pause reading"
              title="Pause reading"
            >
              <span className="tts-icon">⏸️</span>
              <span className="tts-label">Pause</span>
            </button>
            <button
              className="tts-button tts-stop"
              onClick={handleStop}
              aria-label="Stop reading"
              title="Stop reading"
            >
              <span className="tts-icon">⏹️</span>
              <span className="tts-label">Stop</span>
            </button>
          </>
        )}
        
        {isPaused && (
          <>
            <button
              className="tts-button tts-resume"
              onClick={handlePlay}
              aria-label="Resume reading"
              title="Resume reading"
            >
              <span className="tts-icon">▶️</span>
              <span className="tts-label">Resume</span>
            </button>
            <button
              className="tts-button tts-stop"
              onClick={handleStop}
              aria-label="Stop reading"
              title="Stop reading"
            >
              <span className="tts-icon">⏹️</span>
              <span className="tts-label">Stop</span>
            </button>
          </>
        )}
      </div>
      
      {isPlaying && (
        <div className="tts-indicator">
          <span className="tts-pulse"></span>
          <span className="tts-status">Reading aloud...</span>
        </div>
      )}
    </div>
  );
}

export default TextToSpeech;
