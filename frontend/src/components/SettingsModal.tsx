import React from 'react';
import { type RecordingSource, type TelemetryData } from '../hooks/useAudioStream';

export interface TelemetryLogEntry extends TelemetryData {
  timestamp?: string;
  [key: string]: unknown;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  recordingSource: RecordingSource;
  setRecordingSource: (source: RecordingSource) => void;
  pauseThresholdSec: number;
  onPauseThresholdChange: (val: number) => void;
  telemetryLogs: TelemetryLogEntry[];
}

const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  recordingSource,
  setRecordingSource,
  pauseThresholdSec,
  onPauseThresholdChange,
  telemetryLogs
}) => {
  if (!isOpen) return null;

  const handleExportTelemetry = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(telemetryLogs, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `signbridge-telemetry-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const avgE2E = telemetryLogs.length > 0
    ? Math.round(telemetryLogs.reduce((acc, curr) => acc + (curr.e2e_ms || 0), 0) / telemetryLogs.length)
    : null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-fade-in"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="fixed z-50 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg p-4">
        <div className="bg-theme-modal border border-theme-primary rounded-2xl shadow-2xl p-6 relative text-theme-primary">
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-theme-primary mb-5">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-primary-100 dark:bg-primary-900/40 flex items-center justify-center text-primary-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <h3 className="font-bold text-lg text-theme-primary">Settings & Metrics</h3>
                <p className="text-xs text-theme-secondary">Configure streaming audio, pause detection, & model telemetry</p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-theme-secondary hover:text-theme-primary hover:bg-secondary-100 dark:hover:bg-secondary-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-5 text-sm">
            {/* Audio Source Selection */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-theme-muted mb-2">
                Audio Input Source
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setRecordingSource('mic')}
                  className={`flex items-center gap-2.5 p-3 rounded-xl border text-left transition-all ${
                    recordingSource === 'mic'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/30 text-primary-700 dark:text-primary-300 font-semibold'
                      : 'border-secondary-200 dark:border-secondary-800 hover:border-secondary-300 text-theme-secondary'
                  }`}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                  <div>
                    <div>Microphone</div>
                    <div className="text-[10px] text-theme-muted font-normal">Standard voice input</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setRecordingSource('system')}
                  className={`flex items-center gap-2.5 p-3 rounded-xl border text-left transition-all ${
                    recordingSource === 'system'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/30 text-primary-700 dark:text-primary-300 font-semibold'
                      : 'border-secondary-200 dark:border-secondary-800 hover:border-secondary-300 text-theme-secondary'
                  }`}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <div>System Audio</div>
                    <div className="text-[10px] text-theme-muted font-normal">Loopback / Meetings / Video</div>
                  </div>
                </button>
              </div>
            </div>

            {/* Pause Sensitivity Slider */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-theme-muted">
                  VAD Silence Pause Threshold
                </label>
                <span className="font-mono text-xs font-bold text-primary-600">{pauseThresholdSec}s</span>
              </div>
              <input
                type="range"
                min="0.4"
                max="1.6"
                step="0.1"
                value={pauseThresholdSec}
                onChange={(e) => onPauseThresholdChange(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-secondary-200 dark:bg-secondary-700 rounded-lg cursor-pointer accent-primary-500"
              />
              <p className="text-[11px] text-theme-muted mt-1">
                Lower = faster clause commitment. Higher = accommodates deliberate pauses.
              </p>
            </div>

            {/* Offline Engine Architecture Status */}
            <div className="bg-secondary-50 dark:bg-secondary-900/60 p-3.5 rounded-xl border border-secondary-200 dark:border-secondary-800 space-y-2">
              <div className="text-xs font-bold uppercase tracking-wider text-theme-muted flex items-center justify-between">
                <span>Inference Architecture</span>
                <span className="text-[10px] text-emerald-600 font-bold bg-emerald-100 dark:bg-emerald-950 px-2 py-0.5 rounded-full">100% OFFLINE</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-theme-secondary font-mono">
                <div>• ASR: <strong>faster-whisper (tiny.en, int8)</strong></div>
                <div>• VAD: <strong>Silero VAD (local cache)</strong></div>
                <div>• Translator: <strong>Sockeye (Transformer ASE)</strong></div>
                <div>• Scheduler: <strong>Serialized Lock (0 Contention)</strong></div>
              </div>
            </div>

            {/* Telemetry Metrics & Export */}
            <div className="pt-2 border-t border-theme-primary flex items-center justify-between">
              <div>
                <div className="text-xs text-theme-secondary">
                  Session Logged: <strong>{telemetryLogs.length} clauses</strong>
                </div>
                {avgE2E && (
                  <div className="text-[11px] text-theme-muted font-mono">
                    Avg E2E: <strong className="text-emerald-600">{avgE2E}ms</strong>
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={handleExportTelemetry}
                disabled={telemetryLogs.length === 0}
                className="px-3 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-700 disabled:opacity-40 text-white font-medium text-xs flex items-center gap-1.5 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Export JSON Log
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default SettingsModal;
