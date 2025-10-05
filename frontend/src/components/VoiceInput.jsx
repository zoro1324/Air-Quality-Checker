// VoiceInput.jsx - Voice-to-Text Input Component for Accessibility

import React, { useState, useEffect, useRef } from 'react';

/**
 * VoiceInput Component
 * Provides voice input functionality using Web Speech API (Speech Recognition)
 * 
 * Props:
 * - onTranscript: Callback function that receives the transcribed text
 * - lang: Language code for speech recognition (default: 'en-US')
 * - continuous: Whether to continue listening (default: false)
 * - interimResults: Show interim results while speaking (default: true)
 */
function VoiceInput({ 
  onTranscript, 
  lang = 'en-US',
  continuous = false,
  interimResults = true 
}) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const [interimTranscript, setInterimTranscript] = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
    // Check if browser supports Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setIsSupported(false);
      console.warn('Speech Recognition is not supported in this browser');
      return;
    }

    // Initialize Speech Recognition
    const recognition = new SpeechRecognition();
    recognition.continuous = continuous;
    recognition.interimResults = interimResults;
    recognition.lang = lang;

    recognition.onstart = () => {
      setIsListening(true);
      setInterimTranscript('');
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let tempInterimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPiece = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcriptPiece + ' ';
        } else {
          tempInterimTranscript += transcriptPiece;
        }
      }

      if (finalTranscript && onTranscript) {
        // Pass the transcript text directly to the callback
        onTranscript(finalTranscript);
      }

      setInterimTranscript(tempInterimTranscript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      setInterimTranscript('');
      
      // Handle specific errors
      if (event.error === 'not-allowed' || event.error === 'not-permitted') {
        alert('Microphone access denied. Please allow microphone access in your browser settings to use voice input.');
      } else if (event.error === 'no-speech') {
        // No speech detected, just stop silently
        console.log('No speech detected');
      } else if (event.error === 'aborted') {
        // Recognition was aborted, this is normal when stopping
        console.log('Recognition stopped');
      } else if (event.error === 'audio-capture') {
        alert('No microphone detected. Please connect a microphone to use voice input.');
      } else if (event.error === 'network') {
        alert('Network error. Voice recognition requires an internet connection in some browsers.');
      } else {
        console.warn('Speech recognition error:', event.error);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimTranscript('');
    };

    recognitionRef.current = recognition;

    // Cleanup
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [lang, continuous, interimResults, onTranscript]);

  const startListening = () => {
    if (!isSupported || !recognitionRef.current) return;
    
    try {
      // Stop any existing recognition first to prevent 'already started' error
      if (isListening) {
        recognitionRef.current.stop();
      }
      recognitionRef.current.start();
      console.log('Voice recognition started');
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      // If already started, try stopping and restarting
      if (error.message && error.message.includes('already started')) {
        try {
          recognitionRef.current.stop();
          setTimeout(() => {
            recognitionRef.current.start();
          }, 100);
        } catch (retryError) {
          console.error('Failed to restart recognition:', retryError);
          setIsListening(false);
        }
      }
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop();
        console.log('Voice recognition stopped');
      } catch (error) {
        console.error('Error stopping speech recognition:', error);
      }
    }
  };

  // Don't render if not supported
  if (!isSupported) {
    return (
      <div className="voice-input-not-supported">
        <span className="voice-icon">ℹ️</span>
        <span className="voice-message">Voice input is not supported in your browser</span>
      </div>
    );
  }

  return (
    <div className="voice-input-controls">
      {!isListening ? (
        <button
          className="voice-input-button voice-start"
          onClick={startListening}
          aria-label="Start voice input"
          title="Click to speak"
          type="button"
        >
          <span className="voice-icon">🎤</span>
          <span className="voice-label">Speak</span>
        </button>
      ) : (
        <button
          className="voice-input-button voice-stop"
          onClick={stopListening}
          aria-label="Stop voice input"
          title="Click to stop"
          type="button"
        >
          <span className="voice-icon voice-pulse">🔴</span>
          <span className="voice-label">Stop</span>
        </button>
      )}
      
      {isListening && (
        <div className="voice-indicator">
          <span className="voice-listening-pulse"></span>
          <span className="voice-status">Listening...</span>
          {interimTranscript && (
            <span className="interim-text">"{interimTranscript}"</span>
          )}
        </div>
      )}
    </div>
  );
}

export default VoiceInput;
