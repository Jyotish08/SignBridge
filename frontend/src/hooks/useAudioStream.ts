import { useState, useRef, useEffect, useCallback } from 'react';
import config from '../config';

export type RecordingSource = 'mic' | 'system';

export interface TelemetryData {
  asr_ms?: number;
  sockeye_ms?: number;
  e2e_ms?: number;
  mode?: string;
}

interface UseAudioStreamOptions {
  recordingSource: RecordingSource;
  onTranscriptionUpdate?: (stable: string, unstable: string) => void;
  onClauseCommitted?: (clause: string) => void;
  onSignWritingUpdate?: (signs: string[], clause: string) => void;
  onTelemetryUpdate?: (telemetry: TelemetryData) => void;
  onStatusChange?: (status: string) => void;
}

export function useAudioStream({
  recordingSource,
  onTranscriptionUpdate,
  onClauseCommitted,
  onSignWritingUpdate,
  onTelemetryUpdate,
  onStatusChange
}: UseAudioStreamOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [systemStatus, setSystemStatus] = useState<string>('READY');
  const [telemetry, setTelemetry] = useState<TelemetryData>({});

  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Maintain WebSocket connection
  const connectWs = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendUrl = config.BACKEND_URL || 'http://127.0.0.1:8000';
    const wsUrl = backendUrl.replace(/^http(s?):\/\//, `${wsProtocol}//`) + '/ws/stream';

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Audio stream WebSocket connected');
      setSystemStatus('READY');
      onStatusChange?.('READY');
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'status') {
          setSystemStatus(msg.status);
          onStatusChange?.(msg.status);
        } else if (msg.type === 'transcript') {
          onTranscriptionUpdate?.(msg.stable || '', msg.unstable || '');
        } else if (msg.type === 'clause_committed') {
          onClauseCommitted?.(msg.clause || '');
        } else if (msg.type === 'signwriting') {
          onSignWritingUpdate?.(msg.signs || [], msg.clause || '');
          if (msg.telemetry) {
            setTelemetry(msg.telemetry);
            onTelemetryUpdate?.(msg.telemetry);
          }
        } else if (msg.type === 'telemetry') {
          setTelemetry(msg);
          onTelemetryUpdate?.(msg);
        }
      } catch (err) {
        console.error('Error handling WS message:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    ws.onclose = () => {
      console.log('Audio stream WebSocket disconnected');
      setSystemStatus('DISCONNECTED');
    };

    wsRef.current = ws;
  }, [onTranscriptionUpdate, onClauseCommitted, onSignWritingUpdate, onTelemetryUpdate, onStatusChange]);

  useEffect(() => {
    connectWs();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWs]);

  const startRecording = useCallback(async () => {
    connectWs();

    try {
      let stream: MediaStream;
      if (recordingSource === 'system') {
        if (!navigator.mediaDevices?.getDisplayMedia) {
          alert('System audio not supported');
          setIsRecording(false);
          return;
        }
        stream = await navigator.mediaDevices.getDisplayMedia({ audio: true, video: true });
      } else {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: 16000,
            echoCancellation: true,
            noiseSuppression: true
          }
        });
      }

      streamRef.current = stream;

      // Create Web Audio context configured for 16kHz
      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtxClass({
        sampleRate: 16000
      });
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);

      // Analyser for visual feedback
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const updateLevel = () => {
        if (analyserRef.current) {
          const data = new Uint8Array(analyserRef.current.frequencyBinCount);
          analyserRef.current.getByteFrequencyData(data);
          const avg = data.reduce((a, b) => a + b, 0) / data.length;
          setAudioLevel(avg);
        }
        animationFrameRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();

      // ScriptProcessorNode buffers 4096 samples (256ms at 16kHz)
      const bufferSize = 4096;
      const processor = audioCtx.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) return;

        const inputChannel = e.inputBuffer.getChannelData(0);
        // Convert Float32Array to 16-bit PCM Int16Array
        const pcm16 = new Int16Array(inputChannel.length);
        for (let i = 0; i < inputChannel.length; i++) {
          const s = Math.max(-1, Math.min(1, inputChannel[i]));
          pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }

        // Send raw PCM chunk over WebSocket
        wsRef.current.send(pcm16.buffer);
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);

      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime((t) => t + 1);
      }, 1000);

    } catch (err) {
      console.error('Error starting audio stream:', err);
      setIsRecording(false);
    }
  }, [connectWs, recordingSource]);

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    setRecordingTime(0);
    setAudioLevel(0);
  }, []);

  useEffect(() => {
    if (isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, [stopRecording]);

  const updatePauseThreshold = useCallback((sec: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'config', pause_threshold_sec: sec }));
    }
  }, []);

  return {
    isRecording,
    setIsRecording,
    recordingTime,
    audioLevel,
    systemStatus,
    telemetry,
    updatePauseThreshold,
    startRecording: () => setIsRecording(true),
    stopRecording: () => setIsRecording(false),
  };
}
