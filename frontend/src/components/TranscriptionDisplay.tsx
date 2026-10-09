import React, { useState } from 'react';

interface TelemetryData {
  asr_ms?: number;
  sockeye_ms?: number;
  e2e_ms?: number;
  mode?: string;
}

interface TranscriptionDisplayProps {
  transcription?: string;
  stableText?: string;
  unstableText?: string;
  status?: string;
  telemetry?: TelemetryData;
  pauseThresholdSec?: number;
  onPauseThresholdChange?: (sec: number) => void;
  onClearSession?: () => void;
}

const TranscriptionDisplay: React.FC<TranscriptionDisplayProps> = ({
  transcription,
  stableText = '',
  unstableText = '',
  status = 'READY',
  telemetry,
  pauseThresholdSec = 0.8,
  onPauseThresholdChange,
  onClearSession
}) => {
  const [localPause, setLocalPause] = useState(pauseThresholdSec);
  const hasText = transcription || stableText || unstableText;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setLocalPause(val);
    onPauseThresholdChange?.(val);
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'SPEECH_DETECTED':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-200 animate-pulse">● Speaking</span>;
      case 'PAUSE_DETECTED':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-200">Pause Detected</span>;
      case 'TRANSLATING':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-800 dark:text-indigo-200 animate-pulse">Translating (Sockeye)</span>;
      case 'LISTENING':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-200">Listening</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-secondary-100 dark:bg-secondary-800 text-secondary-700 dark:text-secondary-300">Offline Ready</span>;
    }
  };

  return (
    <div className="mt-6 animate-fade-in block">
      <div className="bg-theme-modal border border-primary-300 dark:border-primary-700 rounded-xl p-4 shadow-sm">
        {/* Top Header */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-theme-primary">Streaming Offline ASR</span>
            {getStatusBadge()}
          </div>

          <div className="flex items-center gap-3">
            {/* Pause Sensitivity Slider */}
            <div className="flex items-center gap-1.5 bg-secondary-100 dark:bg-secondary-800 px-2.5 py-1 rounded-lg text-xs text-theme-secondary">
              <span>Pause: <strong>{localPause}s</strong></span>
              <input
                type="range"
                min="0.4"
                max="1.6"
                step="0.1"
                value={localPause}
                onChange={handleSliderChange}
                className="w-16 h-1 bg-secondary-300 rounded-lg cursor-pointer accent-primary-500"
                title="Adjust silence duration required to trigger clause translation"
              />
            </div>

            {/* Clear Button */}
            {onClearSession && hasText && (
              <button
                type="button"
                onClick={onClearSession}
                className="text-xs px-2 py-1 rounded bg-secondary-200 dark:bg-secondary-700 hover:bg-secondary-300 dark:hover:bg-secondary-600 text-theme-secondary transition-colors"
                title="Clear current transcript and signs"
              >
                Clear
              </button>
            )}

            {/* Telemetry Badge */}
            {telemetry && (telemetry.asr_ms !== undefined || telemetry.sockeye_ms !== undefined) && (
              <div className="flex items-center gap-2 text-xs font-mono text-theme-secondary bg-secondary-100 dark:bg-secondary-800 px-2 py-1 rounded">
                {telemetry.asr_ms !== undefined && <span>ASR: <strong className="text-primary-600">{telemetry.asr_ms}ms</strong></span>}
                {telemetry.sockeye_ms !== undefined && <span>| Sockeye: <strong className="text-primary-600">{telemetry.sockeye_ms}ms</strong></span>}
                {telemetry.e2e_ms !== undefined && <span>| E2E: <strong className="text-emerald-600">{telemetry.e2e_ms}ms</strong></span>}
                <span className="text-emerald-500 font-bold ml-1">OFFLINE</span>
              </div>
            )}
          </div>
        </div>

        {/* Live Transcript Text Container */}
        {hasText ? (
          <div className="text-base text-theme-primary leading-relaxed bg-white dark:bg-secondary-900 p-3 rounded-lg border border-secondary-200 dark:border-secondary-800 min-h-[52px]">
            {stableText && <span className="font-medium text-theme-primary">{stableText} </span>}
            {unstableText && <span className="italic text-secondary-400 dark:text-secondary-400 animate-pulse">{unstableText}</span>}
            {!stableText && !unstableText && transcription && <span>{transcription}</span>}
          </div>
        ) : (
          <div className="text-xs text-theme-muted italic p-2.5">
            Click "Record Voice" or select a Quick Demo Clause above to stream speech recognition and sub-second SignWriting translation.
          </div>
        )}
      </div>
    </div>
  );
};

export default TranscriptionDisplay;