import React, { useState, useEffect, useRef, useCallback } from 'react';
import AudioRecorder from '../components/AudioRecorder';
import { useTheme } from '../contexts/ThemeContext';
import ApiService from '../services/ApiService';
import '../index.css';
import Header from '../components/Header';
import InputSection from '../components/InputSection';
import SignWritingSection from '../components/SignWritingSection';
import AnimationSection from '../components/AnimationSection';
import ErrorDisplay from '../components/ErrorDisplay';
import TranscriptionDisplay from '../components/TranscriptionDisplay';
import SimplifyChoiceModal from '../components/SimplifyChoiceModal';
import SettingsModal, { type TelemetryLogEntry } from '../components/SettingsModal';
import { type TelemetryData } from '../hooks/useAudioStream';

function App() {
  const [inputText, setInputText] = useState('');
  const [transcription, setTranscription] = useState('');
  const [simplifyText, setSimplifyText] = useState(false);
  const [signWriting, setSignWriting] = useState<string[]>([]);
  const [poseFile, setPoseFile] = useState<Blob | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [isGeneratingSigns, setIsGeneratingSigns] = useState(false);
  const [isGeneratingAnimation, setIsGeneratingAnimation] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recordingSource, setRecordingSource] = useState<'mic' | 'system'>('mic');
  const [showSimplifyModal, setShowSimplifyModal] = useState(false);
  const [simplifiedText, setSimplifiedText] = useState('');
  const [pendingOriginalText, setPendingOriginalText] = useState('');
  const [stableText, setStableText] = useState('');
  const [unstableText, setUnstableText] = useState('');
  const [systemStatus, setSystemStatus] = useState('READY');
  const [telemetry, setTelemetry] = useState<TelemetryData>({});
  const [pauseThresholdSec, setPauseThresholdSec] = useState(0.8);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [telemetryLogs, setTelemetryLogs] = useState<TelemetryLogEntry[]>([]);



  const { theme, toggleTheme } = useTheme();
  const translationTimeout = useRef<NodeJS.Timeout | null>(null);

  const triggerTranslation = useCallback(async (text: string) => {
    setIsTranslating(true);
    setIsGeneratingSigns(true);
    setIsGeneratingAnimation(true);
    setError(null);
    setTranscription(text);
    setSignWriting([]);
    setPoseFile(null);
    
    try {
      let textToTranslate = text;
      if (simplifyText) {
        try {
          const simplifyResponse = await ApiService.simplifyText(text);
          textToTranslate = simplifyResponse.simplified_text || text;
        } catch (simErr) {
          console.warn('Text simplification failed, proceeding with original text:', simErr);
          textToTranslate = text;
        }
      }
      
      // 1. Translate to SignWriting
      const translateResponse = await ApiService.translateSignWriting(textToTranslate);
      const rawFsw = translateResponse.signwriting || '';
      const fswTokens = rawFsw.trim().split(/\s+/).filter(token => token.length > 0);
      setSignWriting(fswTokens);
      setIsGeneratingSigns(false);

      // 2. Generate pose file for animation
      if (fswTokens.length > 0) {
        try {
          const poseResponse = await ApiService.generatePose(textToTranslate, 'en', 'ase');
          const { pose_data, data_format } = poseResponse;
          if (data_format === 'binary_base64' && pose_data) {
            const binary = atob(pose_data);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
              bytes[i] = binary.charCodeAt(i);
            }
            const blob = new Blob([bytes], { type: 'application/octet-stream' });
            setPoseFile(blob);
          } else {
            setPoseFile(null);
          }
        } catch {
          setPoseFile(null);
        }
      }
      setIsGeneratingAnimation(false);
    } catch (err: unknown) {
      console.error('Translation error:', err);
      const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
      const message = errorObj?.response?.data?.detail || errorObj?.message || 'Translation failed. Please try again.';
      setError(message);
      setSignWriting([]);
      setPoseFile(null);
      setIsGeneratingSigns(false);
      setIsGeneratingAnimation(false);
    } finally {
      setIsTranslating(false);
    }
  }, [simplifyText]);

  useEffect(() => {
    if (translationTimeout.current) {
      clearTimeout(translationTimeout.current);
    }
    if (inputText.trim() === '') {
      setSignWriting([]);
      setPoseFile(null);
      setTranscription('');
      return;
    }

    if (!simplifyText) {
      translationTimeout.current = setTimeout(() => {
        if (/[.!?\n]$/.test(inputText.trim())) {
          triggerTranslation(inputText);
        }
      }, 1500);
    }
  }, [inputText, simplifyText, triggerTranslation]);

  const handleRecordComplete = async (audioBlob: Blob) => {
    setIsRecording(false);
    setIsTranscribing(true);
    setError(null);
    setInputText('');
    setSignWriting([]);
    setPoseFile(null);
    setTranscription('');
    try {
      const transcribeResponse = await ApiService.transcribe(audioBlob);
      const originalText = transcribeResponse.text || '';
      setInputText(originalText);
      setIsTranscribing(false);
      triggerTranslation(originalText);
    } catch {
      setError('Transcription failed. Please try again.');
      setIsTranscribing(false);
    }
  };

  const handleRecordClick = () => {
    setError(null);
    setIsRecording(!isRecording);
  };

  const handleSimplifyAndTranslate = async () => {
    setError(null);
    setIsTranslating(true);
    try {
      const response = await ApiService.simplifyText(inputText);
      setSimplifiedText(response.simplified_text || inputText);
      setPendingOriginalText(inputText);
      setShowSimplifyModal(true);
    } catch {
      setError('Failed to simplify text.');
    } finally {
      setIsTranslating(false);
    }
  };

  const handleSimplifyModalSelect = (choice: 'original' | 'simplified') => {
    setShowSimplifyModal(false);
    if (choice === 'simplified') {
      setInputText(simplifiedText);
      setTimeout(() => triggerTranslation(simplifiedText), 0);
    } else {
      setTimeout(() => triggerTranslation(pendingOriginalText), 0);
    }
  };

  return (
    <div className="min-h-screen transition-all duration-300">
      <Header
        theme={theme}
        toggleTheme={toggleTheme}
        simplifyText={simplifyText}
        setSimplifyText={setSimplifyText}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 xl:min-h-[calc(100vh-220px)] min-h-0">
          
          {/* Input Section - Enhanced */}
          <InputSection
            inputText={inputText}
            setInputText={setInputText}
            isTranscribing={isTranscribing}
            isRecording={isRecording}
            handleRecordClick={handleRecordClick}
            handleSimplifyAndTranslate={handleSimplifyAndTranslate}
            triggerTranslation={triggerTranslation}
            simplifyText={simplifyText}
            isTranslating={isTranslating}
          />

          {/* SignWriting Display - Enhanced */}
          <SignWritingSection
            signWriting={signWriting}
            isGeneratingSigns={isGeneratingSigns}
          />

          {/* Animation Section - Enhanced */}
          <AnimationSection
            poseFile={poseFile}
            isGeneratingAnimation={isGeneratingAnimation}
          />
        </div>
        <ErrorDisplay error={error} />
        <TranscriptionDisplay 
          transcription={transcription} 
          stableText={stableText}
          unstableText={unstableText}
          status={systemStatus}
          telemetry={telemetry}
          pauseThresholdSec={pauseThresholdSec}
          onPauseThresholdChange={(sec) => setPauseThresholdSec(sec)}
          onClearSession={() => {
            setTranscription('');
            setStableText('');
            setUnstableText('');
            setInputText('');
            setSignWriting([]);
            setTelemetry({});
          }}
        />
        {showSimplifyModal && (
          <SimplifyChoiceModal
            original={pendingOriginalText}
            simplified={simplifiedText}
            onSelect={handleSimplifyModalSelect}
            onClose={() => setShowSimplifyModal(false)}
          />
        )}
      </main>

      {/* Audio Recorder Component */}
      {isRecording && (
        <AudioRecorder
          onRecordingComplete={handleRecordComplete}
          recordingSource={recordingSource}
          setRecordingSource={setRecordingSource}
          onClose={() => setIsRecording(false)}
          onTranscriptionUpdate={(stable, unstable) => {
            setStableText(stable);
            setUnstableText(unstable);
            setTranscription(`${stable} ${unstable}`.trim());
          }}
          onClauseCommitted={(clause) => {
            setStableText(clause);
            setUnstableText('');
            setInputText(clause);
          }}
          onSignWritingUpdate={(signs, clause) => {
            setSignWriting((prev) => [...prev, ...signs]);
            if (clause) {
              ApiService.generatePose(clause, 'en', 'ase')
                .then((poseResponse) => {
                  const { pose_data, data_format } = poseResponse;
                  if (data_format === 'binary_base64' && pose_data) {
                    const binary = atob(pose_data);
                    const bytes = new Uint8Array(binary.length);
                    for (let i = 0; i < binary.length; i++) {
                      bytes[i] = binary.charCodeAt(i);
                    }
                    const blob = new Blob([bytes], { type: 'application/octet-stream' });
                    setPoseFile(blob);
                  }
                })
                .catch(() => {});
            }
          }}
          onTelemetryUpdate={(tel) => {
            setTelemetry(tel);
            setTelemetryLogs((prev) => [...prev, { ...tel, timestamp: new Date().toISOString() }]);
          }}
          onStatusChange={(st) => {
            setSystemStatus(st);
            if (st === 'TRANSLATING') {
              setIsTranslating(true);
              setIsGeneratingSigns(true);
            } else if (st === 'LISTENING') {
              setIsTranslating(false);
              setIsGeneratingSigns(false);
            }
          }}
        />
      )}

      {/* Settings & Metrics Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        recordingSource={recordingSource}
        setRecordingSource={setRecordingSource}
        pauseThresholdSec={pauseThresholdSec}
        onPauseThresholdChange={(val) => setPauseThresholdSec(val)}
        telemetryLogs={telemetryLogs}
      />
    </div>
  );
}

export default App;