// TTS_DEMO_EXAMPLES.jsx
// This file contains example usage patterns for the TextToSpeech component

import React, { useState } from 'react';
import TextToSpeech from './components/TextToSpeech';

/**
 * EXAMPLE 1: Basic Usage
 * Simplest implementation - just pass text
 */
function BasicExample() {
  const summaryText = "The air quality today is moderate with an AQI of 85. Sensitive groups should limit prolonged outdoor exposure.";
  
  return (
    <div>
      <p>{summaryText}</p>
      <TextToSpeech text={summaryText} />
    </div>
  );
}

/**
 * EXAMPLE 2: With Custom Settings
 * Adjust speech rate, pitch, and volume
 */
function CustomSettingsExample() {
  const text = "This is spoken at a slower pace with lower pitch.";
  
  return (
    <div>
      <p>{text}</p>
      <TextToSpeech 
        text={text}
        rate={0.8}      // 20% slower
        pitch={0.9}     // Slightly lower pitch
        volume={0.9}    // 90% volume
      />
    </div>
  );
}

/**
 * EXAMPLE 3: Different Languages
 * Demonstrate multi-language support
 */
function MultiLanguageExample() {
  const [language, setLanguage] = useState('en-US');
  
  const texts = {
    'en-US': 'The air quality is good today.',
    'hi-IN': 'आज हवा की गुणवत्ता अच्छी है।',
    'es-ES': 'La calidad del aire es buena hoy.',
  };
  
  return (
    <div>
      <select value={language} onChange={(e) => setLanguage(e.target.value)}>
        <option value="en-US">English</option>
        <option value="hi-IN">Hindi</option>
        <option value="es-ES">Spanish</option>
      </select>
      
      <p>{texts[language]}</p>
      <TextToSpeech text={texts[language]} lang={language} />
    </div>
  );
}

/**
 * EXAMPLE 4: Auto-play on Load
 * Automatically start reading when component mounts
 */
function AutoPlayExample() {
  const importantAlert = "URGENT: Air quality has reached hazardous levels. Stay indoors immediately!";
  
  return (
    <div>
      <div className="alert-box">
        <p>{importantAlert}</p>
        <TextToSpeech 
          text={importantAlert}
          autoPlay={true}  // Starts automatically
        />
      </div>
    </div>
  );
}

/**
 * EXAMPLE 5: Dynamic Content
 * TTS updates when text changes
 */
function DynamicContentExample() {
  const [selectedCategory, setSelectedCategory] = useState('health');
  
  const summaries = {
    health: "Health Advisory: Air quality is unhealthy for sensitive groups. Children and elderly should avoid outdoor activities.",
    agriculture: "Agriculture Consultation: Current air quality may affect crop growth. Consider delaying pesticide application.",
    emergency: "Emergency Alert: Hazardous air quality detected. Seek medical help if experiencing breathing difficulties."
  };
  
  return (
    <div>
      <div className="category-buttons">
        <button onClick={() => setSelectedCategory('health')}>Health</button>
        <button onClick={() => setSelectedCategory('agriculture')}>Agriculture</button>
        <button onClick={() => setSelectedCategory('emergency')}>Emergency</button>
      </div>
      
      <div className="summary-display">
        <p>{summaries[selectedCategory]}</p>
        <TextToSpeech text={summaries[selectedCategory]} />
      </div>
    </div>
  );
}

/**
 * EXAMPLE 6: Integration with API Response
 * Real-world usage with backend data
 */
function APIIntegrationExample() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const fetchSummary = async () => {
    setLoading(true);
    try {
      // Simulated API call
      const response = await fetch('/api/generate-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: 'Health Advisory' })
      });
      
      const data = await response.json();
      setSummary(data.summary);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <button onClick={fetchSummary} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Summary'}
      </button>
      
      {summary && (
        <div className="summary-card">
          <p>{summary}</p>
          <TextToSpeech text={summary} />
        </div>
      )}
    </div>
  );
}

/**
 * EXAMPLE 7: Accessibility-First Design
 * Screen reader friendly implementation
 */
function AccessibilityExample() {
  const text = "Air quality monitoring helps protect public health.";
  
  return (
    <div role="region" aria-label="Air Quality Summary">
      <h2>Summary</h2>
      <p id="summary-text">{text}</p>
      
      {/* Screen reader will announce the TTS controls */}
      <TextToSpeech 
        text={text}
        aria-describedby="summary-text"
      />
    </div>
  );
}

/**
 * EXAMPLE 8: Conditional Rendering
 * Only show TTS when content is available
 */
function ConditionalRenderingExample({ aiSummary }) {
  if (!aiSummary || aiSummary.error) {
    return <p>No summary available</p>;
  }
  
  return (
    <div>
      <p>{aiSummary.summary}</p>
      
      {/* Only render TTS if summary exists */}
      {aiSummary.summary && (
        <div className="summary-tts">
          <TextToSpeech text={aiSummary.summary} />
        </div>
      )}
    </div>
  );
}

/**
 * EXAMPLE 9: Multiple TTS on Same Page
 * Each instance works independently
 */
function MultipleTTSExample() {
  const sections = [
    {
      title: "Current Conditions",
      text: "Current AQI is 65. Air quality is moderate."
    },
    {
      title: "Forecast",
      text: "Tomorrow's AQI is expected to improve to 45."
    },
    {
      title: "Recommendations",
      text: "Sensitive groups should limit outdoor activities."
    }
  ];
  
  return (
    <div>
      {sections.map((section, index) => (
        <div key={index} className="section-card">
          <h3>{section.title}</h3>
          <p>{section.text}</p>
          <TextToSpeech text={section.text} />
        </div>
      ))}
    </div>
  );
}

/**
 * EXAMPLE 10: Error Handling
 * Gracefully handle browser incompatibility
 */
function ErrorHandlingExample() {
  const text = "This demonstrates error handling for unsupported browsers.";
  
  // The component automatically handles unsupported browsers
  // and shows a friendly message
  return (
    <div>
      <p>{text}</p>
      <TextToSpeech text={text} />
      {/* If browser doesn't support TTS, shows: 
          "Text-to-speech is not supported in your browser" */}
    </div>
  );
}

/**
 * BEST PRACTICES SUMMARY
 * 
 * ✅ DO:
 * - Always provide meaningful text content
 * - Use for important summaries and alerts
 * - Test in multiple browsers
 * - Keep text concise (better TTS experience)
 * - Provide visual feedback to users
 * 
 * ❌ DON'T:
 * - Don't auto-play unless necessary (can be annoying)
 * - Don't use for very long texts (browser limitations)
 * - Don't assume all browsers support TTS
 * - Don't forget to handle empty/null text
 * - Don't overuse - add only where valuable
 */

// Export all examples
export {
  BasicExample,
  CustomSettingsExample,
  MultiLanguageExample,
  AutoPlayExample,
  DynamicContentExample,
  APIIntegrationExample,
  AccessibilityExample,
  ConditionalRenderingExample,
  MultipleTTSExample,
  ErrorHandlingExample
};
