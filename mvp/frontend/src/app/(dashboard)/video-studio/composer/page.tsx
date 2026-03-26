'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Slider,
  Snackbar,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import StopIcon from '@mui/icons-material/Stop';
import SkipNextIcon from '@mui/icons-material/SkipNext';
import SkipPreviousIcon from '@mui/icons-material/SkipPrevious';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import MovieFilterIcon from '@mui/icons-material/MovieFilter';
import ViewTimelineIcon from '@mui/icons-material/ViewTimeline';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import ImageIcon from '@mui/icons-material/Image';
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import TitleIcon from '@mui/icons-material/Title';
import WavingHandIcon from '@mui/icons-material/WavingHand';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import Link from 'next/link';

import { useGenerateVideo } from '@/features/video-gen/hooks/useVideoGen';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type SceneType = 'title_card' | 'text_overlay' | 'image' | 'bullet_points' | 'outro';
type TransitionType = 'none' | 'fade' | 'slide_left' | 'slide_up' | 'zoom';

interface Scene {
  id: string;
  type: SceneType;
  content: string;
  duration: number;
  bgColor: string;
  textColor: string;
  fontSize: number;
  transition: TransitionType;
}

interface Composition {
  name: string;
  scenes: Scene[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SCENE_TYPE_META: Record<SceneType, { label: string; icon: React.ReactNode; color: string }> = {
  title_card:    { label: 'Title Card',    icon: <TitleIcon fontSize="small" />,              color: '#7c4dff' },
  text_overlay:  { label: 'Text Overlay',  icon: <TextFieldsIcon fontSize="small" />,         color: '#00bfa5' },
  image:         { label: 'Image',         icon: <ImageIcon fontSize="small" />,               color: '#ff6d00' },
  bullet_points: { label: 'Bullets',       icon: <FormatListBulletedIcon fontSize="small" />,  color: '#2979ff' },
  outro:         { label: 'Outro',         icon: <WavingHandIcon fontSize="small" />,          color: '#f50057' },
};

const TRANSITION_OPTIONS: { value: TransitionType; label: string }[] = [
  { value: 'none',       label: 'None' },
  { value: 'fade',       label: 'Fade' },
  { value: 'slide_left', label: 'Slide Left' },
  { value: 'slide_up',   label: 'Slide Up' },
  { value: 'zoom',       label: 'Zoom In' },
];

const uid = () => Math.random().toString(36).slice(2, 10);

const makeScene = (type: SceneType, overrides?: Partial<Scene>): Scene => ({
  id: uid(),
  type,
  content: type === 'title_card'
    ? 'Your Title Here'
    : type === 'bullet_points'
    ? 'Point 1\nPoint 2\nPoint 3'
    : type === 'outro'
    ? 'Thanks for watching!'
    : 'Enter your text here',
  duration: type === 'title_card' ? 4 : type === 'outro' ? 3 : 5,
  bgColor: type === 'title_card'
    ? '#1a1a2e'
    : type === 'outro'
    ? '#0f3460'
    : '#16213e',
  textColor: '#ffffff',
  fontSize: type === 'title_card' ? 56 : type === 'bullet_points' ? 28 : 36,
  transition: 'fade',
  ...overrides,
});

// ---------------------------------------------------------------------------
// Template Presets
// ---------------------------------------------------------------------------

interface TemplatePreset {
  name: string;
  label: string;
  description: string;
  color: string;
  scenes: Scene[];
}

const TEMPLATES: TemplatePreset[] = [
  {
    name: 'explainer',
    label: 'Explainer',
    description: '60s explainer with intro, 3 points, and CTA',
    color: '#7c4dff',
    scenes: [
      makeScene('title_card', { content: 'How It Works', duration: 5, bgColor: '#1a1a2e' }),
      makeScene('text_overlay', { content: 'The problem we solve', duration: 8, bgColor: '#16213e', transition: 'slide_left' }),
      makeScene('bullet_points', { content: 'Fast setup\nEasy integration\nAI-powered', duration: 10, bgColor: '#0f3460', transition: 'fade' }),
      makeScene('text_overlay', { content: 'See the difference', duration: 8, bgColor: '#1a1a2e', transition: 'slide_up' }),
      makeScene('bullet_points', { content: '10x faster\n99.9% uptime\nEnterprise ready', duration: 10, bgColor: '#16213e', transition: 'fade' }),
      makeScene('outro', { content: 'Start free today!\nwww.example.com', duration: 5, bgColor: '#e94560', transition: 'zoom' }),
    ],
  },
  {
    name: 'social_short',
    label: 'Social Short',
    description: '15s punchy social media clip',
    color: '#ff6d00',
    scenes: [
      makeScene('title_card', { content: 'Did you know?', duration: 3, bgColor: '#ff6d00', fontSize: 48, transition: 'zoom' }),
      makeScene('text_overlay', { content: 'AI can generate videos\nin seconds', duration: 5, bgColor: '#1a1a2e', fontSize: 40, transition: 'slide_left' }),
      makeScene('text_overlay', { content: 'Try it now', duration: 4, bgColor: '#e94560', fontSize: 44, transition: 'slide_up' }),
      makeScene('outro', { content: 'Link in bio', duration: 3, bgColor: '#0f3460', fontSize: 36, transition: 'fade' }),
    ],
  },
  {
    name: 'presentation',
    label: 'Presentation',
    description: '2min slide-style presentation',
    color: '#2979ff',
    scenes: [
      makeScene('title_card', { content: 'Q4 Results\n2026', duration: 5, bgColor: '#1a237e', transition: 'fade' }),
      makeScene('bullet_points', { content: 'Revenue up 42%\nNew markets: 3\nTeam grew 25%', duration: 12, bgColor: '#0d47a1', transition: 'slide_left' }),
      makeScene('text_overlay', { content: 'Key Achievement:\nSeries B Closed', duration: 8, bgColor: '#1565c0', fontSize: 40, transition: 'slide_up' }),
      makeScene('bullet_points', { content: 'Product launches: 5\nCustomers: 10,000+\nNPS: 72', duration: 12, bgColor: '#0d47a1', transition: 'fade' }),
      makeScene('text_overlay', { content: 'What\'s Next?', duration: 6, bgColor: '#1a237e', fontSize: 48, transition: 'zoom' }),
      makeScene('bullet_points', { content: 'AI expansion\nGlobal rollout\nPlatform v3.0', duration: 10, bgColor: '#0d47a1', transition: 'slide_left' }),
      makeScene('outro', { content: 'Thank You\nQuestions?', duration: 5, bgColor: '#283593', transition: 'fade' }),
    ],
  },
  {
    name: 'tutorial',
    label: 'Tutorial',
    description: '90s step-by-step tutorial',
    color: '#00bfa5',
    scenes: [
      makeScene('title_card', { content: 'Getting Started\nStep-by-Step', duration: 5, bgColor: '#004d40', transition: 'fade' }),
      makeScene('text_overlay', { content: 'Step 1\nSign up for free', duration: 10, bgColor: '#00695c', fontSize: 38, transition: 'slide_left' }),
      makeScene('text_overlay', { content: 'Step 2\nCreate your first project', duration: 10, bgColor: '#00796b', fontSize: 38, transition: 'slide_left' }),
      makeScene('text_overlay', { content: 'Step 3\nAdd your content', duration: 10, bgColor: '#00897b', fontSize: 38, transition: 'slide_left' }),
      makeScene('text_overlay', { content: 'Step 4\nGenerate & share', duration: 10, bgColor: '#009688', fontSize: 38, transition: 'slide_left' }),
      makeScene('bullet_points', { content: 'Pro tips:\nUse templates\nCustomize colors\nAdd transitions', duration: 12, bgColor: '#004d40', transition: 'fade' }),
      makeScene('outro', { content: 'You\'re ready!\nStart building', duration: 5, bgColor: '#00bfa5', transition: 'zoom' }),
    ],
  },
  {
    name: 'product_launch',
    label: 'Product Launch',
    description: '45s product announcement',
    color: '#f50057',
    scenes: [
      makeScene('title_card', { content: 'Introducing\nProduct X', duration: 5, bgColor: '#880e4f', fontSize: 52, transition: 'zoom' }),
      makeScene('text_overlay', { content: 'Built for speed.\nDesigned for scale.', duration: 7, bgColor: '#ad1457', fontSize: 40, transition: 'fade' }),
      makeScene('bullet_points', { content: '10x performance\nZero config\nAI-native', duration: 10, bgColor: '#c2185b', transition: 'slide_up' }),
      makeScene('text_overlay', { content: 'Available Now', duration: 5, bgColor: '#d81b60', fontSize: 48, transition: 'slide_left' }),
      makeScene('outro', { content: 'Get early access\nproductx.io', duration: 5, bgColor: '#e91e63', transition: 'zoom' }),
    ],
  },
];

// ---------------------------------------------------------------------------
// CSS Keyframes (injected once)
// ---------------------------------------------------------------------------

const KEYFRAMES = `
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeOut { from { opacity: 1; } to { opacity: 0; } }
@keyframes slideInLeft { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@keyframes slideOutLeft { from { transform: translateX(0); opacity: 1; } to { transform: translateX(-100%); opacity: 0; } }
@keyframes slideInUp { from { transform: translateY(100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
@keyframes slideOutUp { from { transform: translateY(0); opacity: 1; } to { transform: translateY(-100%); opacity: 0; } }
@keyframes zoomIn { from { transform: scale(0.3); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes zoomOut { from { transform: scale(1); opacity: 1; } to { transform: scale(1.5); opacity: 0; } }
@keyframes playheadPulse { 0%, 100% { box-shadow: 0 0 6px 2px rgba(255,82,82,0.5); } 50% { box-shadow: 0 0 12px 4px rgba(255,82,82,0.8); } }
@keyframes sceneGlow { 0%, 100% { box-shadow: inset 0 0 0 2px rgba(124,77,255,0.4); } 50% { box-shadow: inset 0 0 0 2px rgba(124,77,255,0.9); } }
@keyframes gradientBg {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes textReveal {
  from { clip-path: inset(0 100% 0 0); }
  to { clip-path: inset(0 0 0 0); }
}
@keyframes bulletSlideIn {
  from { transform: translateX(-30px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
@keyframes subtlePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
`;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getEnterAnimation(transition: TransitionType): string {
  switch (transition) {
    case 'fade':       return 'fadeIn 0.6s ease-out forwards';
    case 'slide_left': return 'slideInLeft 0.5s ease-out forwards';
    case 'slide_up':   return 'slideInUp 0.5s ease-out forwards';
    case 'zoom':       return 'zoomIn 0.5s ease-out forwards';
    default:           return 'none';
  }
}

function getExitAnimation(transition: TransitionType): string {
  switch (transition) {
    case 'fade':       return 'fadeOut 0.4s ease-in forwards';
    case 'slide_left': return 'slideOutLeft 0.4s ease-in forwards';
    case 'slide_up':   return 'slideOutUp 0.4s ease-in forwards';
    case 'zoom':       return 'zoomOut 0.4s ease-in forwards';
    default:           return 'none';
  }
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// ---------------------------------------------------------------------------
// Component: Scene Preview Renderer
// ---------------------------------------------------------------------------

function SceneRenderer({
  scene,
  animationState,
}: {
  scene: Scene;
  animationState: 'enter' | 'exit' | 'idle';
}) {
  const animation =
    animationState === 'enter'
      ? getEnterAnimation(scene.transition)
      : animationState === 'exit'
      ? getExitAnimation(scene.transition)
      : 'none';

  const baseStyle: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px',
    background: scene.bgColor,
    animation,
    overflow: 'hidden',
  };

  switch (scene.type) {
    case 'title_card':
      return (
        <div style={baseStyle}>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: `radial-gradient(ellipse at 30% 20%, ${scene.bgColor}dd 0%, ${scene.bgColor} 70%)`,
              opacity: 0.8,
            }}
          />
          <div
            style={{
              position: 'absolute',
              top: '10%',
              left: '8%',
              width: 180,
              height: 180,
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${scene.textColor}08, ${scene.textColor}15)`,
              filter: 'blur(40px)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: '15%',
              right: '10%',
              width: 120,
              height: 120,
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${scene.textColor}05, ${scene.textColor}12)`,
              filter: 'blur(30px)',
            }}
          />
          <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
            {scene.content.split('\n').map((line, i) => (
              <div
                key={i}
                style={{
                  fontSize: i === 0 ? scene.fontSize : scene.fontSize * 0.6,
                  fontWeight: i === 0 ? 800 : 300,
                  color: scene.textColor,
                  letterSpacing: i === 0 ? '-1px' : '2px',
                  lineHeight: 1.2,
                  marginBottom: 8,
                  textTransform: i > 0 ? 'uppercase' : 'none',
                  animation: animationState === 'enter' ? `textReveal 0.8s ease-out ${i * 0.2}s both` : 'none',
                }}
              >
                {line}
              </div>
            ))}
            <div
              style={{
                width: 80,
                height: 4,
                background: `linear-gradient(90deg, transparent, ${scene.textColor}80, transparent)`,
                margin: '20px auto 0',
                borderRadius: 2,
              }}
            />
          </div>
        </div>
      );

    case 'text_overlay':
      return (
        <div style={baseStyle}>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: `linear-gradient(135deg, ${scene.bgColor}, ${scene.bgColor}ee, ${scene.bgColor})`,
            }}
          />
          <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: '80%' }}>
            {scene.content.split('\n').map((line, i) => (
              <div
                key={i}
                style={{
                  fontSize: scene.fontSize,
                  fontWeight: i === 0 ? 700 : 400,
                  color: scene.textColor,
                  lineHeight: 1.4,
                  marginBottom: 12,
                  animation: animationState === 'enter' ? `textReveal 0.6s ease-out ${i * 0.15}s both` : 'none',
                }}
              >
                {line}
              </div>
            ))}
          </div>
        </div>
      );

    case 'bullet_points': {
      const points = scene.content.split('\n').filter(Boolean);
      return (
        <div style={baseStyle}>
          <div style={{ position: 'relative', zIndex: 1, width: '75%' }}>
            {points.map((point, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  marginBottom: 20,
                  animation: animationState === 'enter'
                    ? `bulletSlideIn 0.5s ease-out ${i * 0.2}s both`
                    : 'none',
                }}
              >
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: `linear-gradient(135deg, ${scene.textColor}, ${scene.textColor}99)`,
                    flexShrink: 0,
                    boxShadow: `0 0 10px ${scene.textColor}40`,
                  }}
                />
                <span
                  style={{
                    fontSize: scene.fontSize,
                    color: scene.textColor,
                    fontWeight: 500,
                    lineHeight: 1.3,
                  }}
                >
                  {point}
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    case 'image':
      return (
        <div style={baseStyle}>
          <div
            style={{
              width: '70%',
              height: '60%',
              borderRadius: 12,
              background: `linear-gradient(135deg, ${scene.bgColor}cc, ${scene.bgColor}66)`,
              border: `2px dashed ${scene.textColor}40`,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
            }}
          >
            <ImageIcon style={{ fontSize: 48, color: `${scene.textColor}60` }} />
            <span style={{ color: `${scene.textColor}80`, fontSize: 14 }}>
              Image placeholder
            </span>
          </div>
          {scene.content && (
            <div
              style={{
                position: 'absolute',
                bottom: '10%',
                fontSize: scene.fontSize * 0.6,
                color: scene.textColor,
                textAlign: 'center',
                maxWidth: '80%',
                fontWeight: 500,
              }}
            >
              {scene.content}
            </div>
          )}
        </div>
      );

    case 'outro':
      return (
        <div style={baseStyle}>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: `linear-gradient(135deg, ${scene.bgColor}ff, ${scene.bgColor}cc)`,
              backgroundSize: '200% 200%',
              animation: 'gradientBg 4s ease infinite',
            }}
          />
          <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
            {scene.content.split('\n').map((line, i) => (
              <div
                key={i}
                style={{
                  fontSize: i === 0 ? scene.fontSize : scene.fontSize * 0.55,
                  fontWeight: i === 0 ? 800 : 400,
                  color: scene.textColor,
                  letterSpacing: i === 0 ? '-0.5px' : '1px',
                  lineHeight: 1.3,
                  marginBottom: 10,
                  animation: animationState === 'enter' ? `textReveal 0.8s ease-out ${i * 0.3}s both` : 'none',
                }}
              >
                {line}
              </div>
            ))}
            <div
              style={{
                width: 60,
                height: 3,
                background: scene.textColor,
                margin: '16px auto 0',
                borderRadius: 2,
                opacity: 0.6,
              }}
            />
          </div>
        </div>
      );

    default:
      return <div style={baseStyle}><span style={{ color: '#999' }}>Unknown scene type</span></div>;
  }
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

export default function VideoComposerPage() {
  // -- State ----------------------------------------------------------------

  const [composition, setComposition] = useState<Composition>({
    name: 'Untitled Composition',
    scenes: [
      makeScene('title_card', { content: 'My Video\n2026', duration: 5, bgColor: '#1a1a2e' }),
      makeScene('text_overlay', { content: 'Welcome to the future\nof video creation', duration: 6, bgColor: '#16213e', transition: 'slide_left' }),
      makeScene('bullet_points', { content: 'AI-powered\nFast rendering\nCustomizable', duration: 8, bgColor: '#0f3460', transition: 'fade' }),
      makeScene('outro', { content: 'Get started today!\nwww.example.com', duration: 4, bgColor: '#e94560', transition: 'zoom' }),
    ],
  });

  const [selectedSceneId, setSelectedSceneId] = useState<string>(composition.scenes[0]?.id ?? '');
  const [isPlaying, setIsPlaying] = useState(false);
  const [playheadTime, setPlayheadTime] = useState(0);
  const [animState, setAnimState] = useState<'enter' | 'exit' | 'idle'>('idle');
  const [timelineZoom, setTimelineZoom] = useState(1);
  const [snackMsg, setSnackMsg] = useState('');
  const [exportLoading, setExportLoading] = useState(false);

  const animFrameRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);
  const playheadRef = useRef(playheadTime);
  const scenesRef = useRef(composition.scenes);

  const genMutation = useGenerateVideo();

  // Keep refs in sync
  useEffect(() => { playheadRef.current = playheadTime; }, [playheadTime]);
  useEffect(() => { scenesRef.current = composition.scenes; }, [composition.scenes]);

  // -- Derived values -------------------------------------------------------

  const totalDuration = useMemo(
    () => composition.scenes.reduce((sum, s) => sum + s.duration, 0),
    [composition.scenes],
  );

  const sceneOffsets = useMemo(() => {
    const offsets: number[] = [];
    let acc = 0;
    for (const s of composition.scenes) {
      offsets.push(acc);
      acc += s.duration;
    }
    return offsets;
  }, [composition.scenes]);

  const currentSceneIndex = useMemo(() => {
    for (let i = composition.scenes.length - 1; i >= 0; i--) {
      if (playheadTime >= (sceneOffsets[i] ?? 0)) return i;
    }
    return 0;
  }, [playheadTime, sceneOffsets, composition.scenes.length]);

  const currentScene = composition.scenes[currentSceneIndex];
  const selectedScene = composition.scenes.find((s) => s.id === selectedSceneId) ?? currentScene;

  // -- Inject keyframes once ------------------------------------------------

  useEffect(() => {
    const id = '__video-composer-keyframes';
    if (!document.getElementById(id)) {
      const style = document.createElement('style');
      style.id = id;
      style.textContent = KEYFRAMES;
      document.head.appendChild(style);
    }
    return () => {
      const el = document.getElementById(id);
      if (el) el.remove();
    };
  }, []);

  // -- Playback logic -------------------------------------------------------

  const prevSceneIdxRef = useRef(currentSceneIndex);

  useEffect(() => {
    if (prevSceneIdxRef.current !== currentSceneIndex) {
      setAnimState('enter');
      const timer = setTimeout(() => setAnimState('idle'), 700);
      prevSceneIdxRef.current = currentSceneIndex;
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [currentSceneIndex]);

  const stopPlayback = useCallback(() => {
    setIsPlaying(false);
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
  }, []);

  const startPlayback = useCallback(() => {
    setIsPlaying(true);
    setAnimState('enter');
    setTimeout(() => setAnimState('idle'), 700);
    lastTimeRef.current = performance.now();

    const tick = (now: number) => {
      const dt = (now - lastTimeRef.current) / 1000;
      lastTimeRef.current = now;
      const next = playheadRef.current + dt;
      const total = scenesRef.current.reduce((s, sc) => s + sc.duration, 0);
      if (next >= total) {
        setPlayheadTime(0);
        setIsPlaying(false);
        return;
      }
      setPlayheadTime(next);
      animFrameRef.current = requestAnimationFrame(tick);
    };

    animFrameRef.current = requestAnimationFrame(tick);
  }, []);

  const togglePlay = useCallback(() => {
    if (isPlaying) stopPlayback();
    else startPlayback();
  }, [isPlaying, stopPlayback, startPlayback]);

  const handleStop = useCallback(() => {
    stopPlayback();
    setPlayheadTime(0);
    setAnimState('idle');
  }, [stopPlayback]);

  const jumpToScene = useCallback(
    (idx: number) => {
      if (idx < 0 || idx >= composition.scenes.length) return;
      setPlayheadTime(sceneOffsets[idx] ?? 0);
      setSelectedSceneId(composition.scenes[idx]!.id);
      setAnimState('enter');
      setTimeout(() => setAnimState('idle'), 700);
    },
    [composition.scenes, sceneOffsets],
  );

  // Cleanup on unmount
  useEffect(() => () => { if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current); }, []);

  // -- Scene CRUD -----------------------------------------------------------

  const updateScene = (id: string, patch: Partial<Scene>) => {
    setComposition((prev) => ({
      ...prev,
      scenes: prev.scenes.map((s) => (s.id === id ? { ...s, ...patch } : s)),
    }));
  };

  const addScene = (type: SceneType = 'text_overlay') => {
    const newScene = makeScene(type);
    setComposition((prev) => ({ ...prev, scenes: [...prev.scenes, newScene] }));
    setSelectedSceneId(newScene.id);
    setSnackMsg('Scene added');
  };

  const deleteScene = (id: string) => {
    if (composition.scenes.length <= 1) return;
    setComposition((prev) => {
      const filtered = prev.scenes.filter((s) => s.id !== id);
      if (selectedSceneId === id) setSelectedSceneId(filtered[0]?.id ?? '');
      return { ...prev, scenes: filtered };
    });
    setSnackMsg('Scene deleted');
  };

  const duplicateScene = (id: string) => {
    const src = composition.scenes.find((s) => s.id === id);
    if (!src) return;
    const dup = { ...src, id: uid() };
    const idx = composition.scenes.findIndex((s) => s.id === id);
    setComposition((prev) => {
      const next = [...prev.scenes];
      next.splice(idx + 1, 0, dup);
      return { ...prev, scenes: next };
    });
    setSelectedSceneId(dup.id);
    setSnackMsg('Scene duplicated');
  };

  const applyTemplate = (template: TemplatePreset) => {
    stopPlayback();
    setPlayheadTime(0);
    const scenes = template.scenes.map((s) => ({ ...s, id: uid() }));
    setComposition({ name: template.label, scenes });
    setSelectedSceneId(scenes[0]?.id ?? '');
    setAnimState('enter');
    setTimeout(() => setAnimState('idle'), 700);
    setSnackMsg(`Template "${template.label}" applied`);
  };

  // -- Export ---------------------------------------------------------------

  const handleExport = async () => {
    setExportLoading(true);
    try {
      const prompt = composition.scenes
        .map((s, i) => `Scene ${i + 1} (${s.type}, ${s.duration}s): ${s.content.replace(/\n/g, ' | ')}`)
        .join('\n');

      await genMutation.mutateAsync({
        title: composition.name,
        prompt: `Video composition:\n${prompt}`,
        video_type: 'text_to_video',
        duration_s: totalDuration,
        settings: {
          composition: {
            name: composition.name,
            total_duration: totalDuration,
            scenes: composition.scenes.map((s) => ({
              type: s.type,
              content: s.content,
              duration: s.duration,
              bg_color: s.bgColor,
              text_color: s.textColor,
              font_size: s.fontSize,
              transition: s.transition,
            })),
          },
        },
      });
      setSnackMsg('Composition exported to Video Studio!');
    } catch {
      setSnackMsg('Export failed - check console');
    } finally {
      setExportLoading(false);
    }
  };

  // -- Render ---------------------------------------------------------------

  const PX_PER_SEC = 60 * timelineZoom;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', color: '#e0e0e0', fontFamily: '"Inter", "Roboto", sans-serif' }}>
      {/* ================================================================ */}
      {/*  TOP TOOLBAR                                                     */}
      {/* ================================================================ */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          px: 2,
          py: 1,
          background: 'linear-gradient(180deg, #141420 0%, #0e0e18 100%)',
          borderBottom: '1px solid #1e1e30',
          flexShrink: 0,
          minHeight: 52,
        }}
      >
        <Tooltip title="Back to Video Studio">
          <IconButton component={Link} href="/video-studio" size="small" sx={{ color: '#888' }}>
            <ArrowBackIcon fontSize="small" />
          </IconButton>
        </Tooltip>

        <MovieFilterIcon sx={{ color: '#7c4dff', fontSize: 22 }} />

        <TextField
          variant="standard"
          value={composition.name}
          onChange={(e) => setComposition((p) => ({ ...p, name: e.target.value }))}
          InputProps={{
            disableUnderline: true,
            sx: { color: '#fff', fontWeight: 600, fontSize: 16 },
          }}
          sx={{ width: 260 }}
        />

        <Divider orientation="vertical" flexItem sx={{ borderColor: '#2a2a40', mx: 0.5 }} />

        <Chip
          icon={<ViewTimelineIcon />}
          label={`${composition.scenes.length} scenes`}
          size="small"
          sx={{ bgcolor: '#1e1e30', color: '#aaa', '& .MuiChip-icon': { color: '#7c4dff' } }}
        />

        <Chip
          label={formatTime(totalDuration)}
          size="small"
          sx={{ bgcolor: '#1e1e30', color: '#aaa', fontFamily: 'monospace' }}
        />

        <Box sx={{ flex: 1 }} />

        {/* Template presets */}
        {TEMPLATES.map((t) => (
          <Button
            key={t.name}
            size="small"
            onClick={() => applyTemplate(t)}
            sx={{
              color: t.color,
              borderColor: `${t.color}40`,
              fontSize: 11,
              textTransform: 'none',
              px: 1.5,
              minWidth: 0,
              border: '1px solid',
              borderRadius: 1,
              '&:hover': { bgcolor: `${t.color}15`, borderColor: t.color },
            }}
          >
            {t.label}
          </Button>
        ))}

        <Divider orientation="vertical" flexItem sx={{ borderColor: '#2a2a40', mx: 0.5 }} />

        <Button
          variant="contained"
          size="small"
          startIcon={exportLoading ? <CircularProgress size={14} color="inherit" /> : <FileDownloadIcon />}
          disabled={exportLoading || composition.scenes.length === 0}
          onClick={handleExport}
          sx={{
            bgcolor: '#7c4dff',
            textTransform: 'none',
            fontWeight: 600,
            px: 2,
            '&:hover': { bgcolor: '#651fff' },
          }}
        >
          Export
        </Button>
      </Box>

      {/* ================================================================ */}
      {/*  MAIN BODY: left panel + preview + right panel                   */}
      {/* ================================================================ */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* -------------------------------------------------------------- */}
        {/*  LEFT PANEL - Assets / Templates                               */}
        {/* -------------------------------------------------------------- */}
        <Box
          sx={{
            width: 220,
            flexShrink: 0,
            background: '#111119',
            borderRight: '1px solid #1e1e30',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              px: 2,
              pt: 2,
              pb: 1,
              color: '#666',
              fontWeight: 700,
              fontSize: 10,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Templates
          </Typography>

          {TEMPLATES.map((t) => (
            <Box
              key={t.name}
              onClick={() => applyTemplate(t)}
              sx={{
                mx: 1,
                mb: 1,
                p: 1.5,
                borderRadius: 1.5,
                cursor: 'pointer',
                border: '1px solid #1e1e30',
                transition: 'all 0.2s',
                '&:hover': {
                  bgcolor: `${t.color}10`,
                  borderColor: `${t.color}50`,
                  transform: 'translateY(-1px)',
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: t.color,
                    boxShadow: `0 0 6px ${t.color}60`,
                  }}
                />
                <Typography sx={{ fontSize: 12, fontWeight: 600, color: '#ddd' }}>
                  {t.label}
                </Typography>
              </Box>
              <Typography sx={{ fontSize: 10, color: '#777', lineHeight: 1.3 }}>
                {t.description}
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                <Chip
                  label={`${t.scenes.length} scenes`}
                  size="small"
                  sx={{ height: 18, fontSize: 9, bgcolor: '#1a1a2e', color: '#888' }}
                />
                <Chip
                  label={formatTime(t.scenes.reduce((a, s) => a + s.duration, 0))}
                  size="small"
                  sx={{ height: 18, fontSize: 9, bgcolor: '#1a1a2e', color: '#888', fontFamily: 'monospace' }}
                />
              </Box>
            </Box>
          ))}

          <Divider sx={{ borderColor: '#1e1e30', my: 1 }} />

          <Typography
            variant="caption"
            sx={{
              px: 2,
              pb: 1,
              color: '#666',
              fontWeight: 700,
              fontSize: 10,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Add Scene
          </Typography>

          {(Object.entries(SCENE_TYPE_META) as [SceneType, typeof SCENE_TYPE_META[SceneType]][]).map(
            ([type, meta]) => (
              <Box
                key={type}
                onClick={() => addScene(type)}
                sx={{
                  mx: 1,
                  mb: 0.5,
                  px: 1.5,
                  py: 1,
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  '&:hover': { bgcolor: `${meta.color}18` },
                }}
              >
                <Box sx={{ color: meta.color, display: 'flex' }}>{meta.icon}</Box>
                <Typography sx={{ fontSize: 12, color: '#bbb' }}>{meta.label}</Typography>
                <Box sx={{ flex: 1 }} />
                <AddIcon sx={{ fontSize: 14, color: '#555' }} />
              </Box>
            ),
          )}

          <Box sx={{ flex: 1 }} />
        </Box>

        {/* -------------------------------------------------------------- */}
        {/*  CENTER - Preview Canvas                                       */}
        {/* -------------------------------------------------------------- */}
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'radial-gradient(ellipse at center, #12121d 0%, #08080f 100%)',
            position: 'relative',
            overflow: 'hidden',
            p: 3,
          }}
        >
          {/* Subtle grid */}
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              backgroundImage:
                'linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)',
              backgroundSize: '40px 40px',
              pointerEvents: 'none',
            }}
          />

          {/* 16:9 preview container */}
          <Box
            sx={{
              position: 'relative',
              width: '100%',
              maxWidth: 720,
              aspectRatio: '16/9',
              borderRadius: 2,
              overflow: 'hidden',
              boxShadow: '0 8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)',
            }}
          >
            {currentScene && (
              <SceneRenderer scene={currentScene} animationState={animState} />
            )}

            {/* Scene indicator badge */}
            <Box
              sx={{
                position: 'absolute',
                top: 12,
                left: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                bgcolor: 'rgba(0,0,0,0.6)',
                backdropFilter: 'blur(8px)',
                borderRadius: 1,
                px: 1,
                py: 0.3,
              }}
            >
              <Box
                sx={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  bgcolor: isPlaying ? '#ff5252' : '#666',
                  animation: isPlaying ? 'subtlePulse 1s ease infinite' : 'none',
                }}
              />
              <Typography sx={{ fontSize: 10, color: '#ccc', fontFamily: 'monospace' }}>
                {currentSceneIndex + 1}/{composition.scenes.length}
              </Typography>
            </Box>

            {/* Time indicator badge */}
            <Box
              sx={{
                position: 'absolute',
                top: 12,
                right: 12,
                bgcolor: 'rgba(0,0,0,0.6)',
                backdropFilter: 'blur(8px)',
                borderRadius: 1,
                px: 1,
                py: 0.3,
              }}
            >
              <Typography sx={{ fontSize: 10, color: '#ccc', fontFamily: 'monospace' }}>
                {formatTime(playheadTime)} / {formatTime(totalDuration)}
              </Typography>
            </Box>
          </Box>

          {/* Playback controls */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              mt: 2,
            }}
          >
            <IconButton
              size="small"
              onClick={() => jumpToScene(currentSceneIndex - 1)}
              disabled={currentSceneIndex === 0}
              sx={{ color: '#aaa', '&:disabled': { color: '#444' } }}
            >
              <SkipPreviousIcon />
            </IconButton>

            <IconButton
              onClick={togglePlay}
              sx={{
                width: 44,
                height: 44,
                bgcolor: '#7c4dff',
                color: '#fff',
                '&:hover': { bgcolor: '#651fff' },
                boxShadow: '0 4px 20px rgba(124,77,255,0.4)',
              }}
            >
              {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
            </IconButton>

            <IconButton
              size="small"
              onClick={handleStop}
              sx={{ color: '#aaa' }}
            >
              <StopIcon />
            </IconButton>

            <IconButton
              size="small"
              onClick={() => jumpToScene(currentSceneIndex + 1)}
              disabled={currentSceneIndex === composition.scenes.length - 1}
              sx={{ color: '#aaa', '&:disabled': { color: '#444' } }}
            >
              <SkipNextIcon />
            </IconButton>

            {/* Progress bar */}
            <Box sx={{ width: 200, mx: 1 }}>
              <Slider
                value={playheadTime}
                min={0}
                max={totalDuration || 1}
                step={0.1}
                onChange={(_, v) => {
                  setPlayheadTime(v as number);
                  setAnimState('enter');
                  setTimeout(() => setAnimState('idle'), 700);
                }}
                sx={{
                  color: '#7c4dff',
                  height: 4,
                  '& .MuiSlider-thumb': { width: 12, height: 12 },
                  '& .MuiSlider-rail': { bgcolor: '#2a2a40' },
                }}
              />
            </Box>

            <Typography sx={{ fontSize: 12, color: '#888', fontFamily: 'monospace', minWidth: 85, textAlign: 'center' }}>
              {formatTime(playheadTime)} / {formatTime(totalDuration)}
            </Typography>
          </Box>
        </Box>

        {/* -------------------------------------------------------------- */}
        {/*  RIGHT PANEL - Scene Properties                                */}
        {/* -------------------------------------------------------------- */}
        <Box
          sx={{
            width: 280,
            flexShrink: 0,
            background: '#111119',
            borderLeft: '1px solid #1e1e30',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              px: 2,
              pt: 2,
              pb: 1,
              color: '#666',
              fontWeight: 700,
              fontSize: 10,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Scene Properties
          </Typography>

          {selectedScene ? (
            <Box sx={{ px: 2, pb: 2 }}>
              {/* Scene type selector */}
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel sx={{ color: '#888' }}>Type</InputLabel>
                <Select
                  value={selectedScene.type}
                  label="Type"
                  onChange={(e) => updateScene(selectedScene.id, { type: e.target.value as SceneType })}
                  sx={{
                    color: '#ddd',
                    '.MuiOutlinedInput-notchedOutline': { borderColor: '#2a2a40' },
                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#7c4dff40' },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#7c4dff' },
                    '.MuiSvgIcon-root': { color: '#888' },
                  }}
                >
                  {(Object.entries(SCENE_TYPE_META) as [SceneType, typeof SCENE_TYPE_META[SceneType]][]).map(
                    ([type, meta]) => (
                      <MenuItem key={type} value={type}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ color: meta.color, display: 'flex' }}>{meta.icon}</Box>
                          {meta.label}
                        </Box>
                      </MenuItem>
                    ),
                  )}
                </Select>
              </FormControl>

              {/* Content editor */}
              <Typography sx={{ fontSize: 11, color: '#888', mb: 0.5, fontWeight: 600 }}>
                Content
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={4}
                size="small"
                value={selectedScene.content}
                onChange={(e) => updateScene(selectedScene.id, { content: e.target.value })}
                placeholder="Enter scene content..."
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    color: '#ddd',
                    fontSize: 13,
                    '& fieldset': { borderColor: '#2a2a40' },
                    '&:hover fieldset': { borderColor: '#7c4dff40' },
                    '&.Mui-focused fieldset': { borderColor: '#7c4dff' },
                  },
                }}
              />

              {/* Duration */}
              <Typography sx={{ fontSize: 11, color: '#888', mb: 0.5, fontWeight: 600 }}>
                Duration: {selectedScene.duration}s
              </Typography>
              <Slider
                value={selectedScene.duration}
                min={1}
                max={30}
                step={1}
                onChange={(_, v) => updateScene(selectedScene.id, { duration: v as number })}
                valueLabelDisplay="auto"
                sx={{
                  color: '#7c4dff',
                  mb: 2,
                  '& .MuiSlider-rail': { bgcolor: '#2a2a40' },
                }}
              />

              {/* Background color */}
              <Typography sx={{ fontSize: 11, color: '#888', mb: 0.5, fontWeight: 600 }}>
                Background Color
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <input
                  type="color"
                  value={selectedScene.bgColor}
                  onChange={(e) => updateScene(selectedScene.id, { bgColor: e.target.value })}
                  style={{
                    width: 36,
                    height: 36,
                    border: '2px solid #2a2a40',
                    borderRadius: 6,
                    cursor: 'pointer',
                    background: 'none',
                    padding: 2,
                  }}
                />
                <TextField
                  size="small"
                  value={selectedScene.bgColor}
                  onChange={(e) => updateScene(selectedScene.id, { bgColor: e.target.value })}
                  sx={{
                    flex: 1,
                    '& .MuiOutlinedInput-root': {
                      color: '#ddd',
                      fontSize: 12,
                      fontFamily: 'monospace',
                      '& fieldset': { borderColor: '#2a2a40' },
                      '&:hover fieldset': { borderColor: '#7c4dff40' },
                    },
                  }}
                />
              </Box>

              {/* Text color */}
              <Typography sx={{ fontSize: 11, color: '#888', mb: 0.5, fontWeight: 600 }}>
                Text Color
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <input
                  type="color"
                  value={selectedScene.textColor}
                  onChange={(e) => updateScene(selectedScene.id, { textColor: e.target.value })}
                  style={{
                    width: 36,
                    height: 36,
                    border: '2px solid #2a2a40',
                    borderRadius: 6,
                    cursor: 'pointer',
                    background: 'none',
                    padding: 2,
                  }}
                />
                <TextField
                  size="small"
                  value={selectedScene.textColor}
                  onChange={(e) => updateScene(selectedScene.id, { textColor: e.target.value })}
                  sx={{
                    flex: 1,
                    '& .MuiOutlinedInput-root': {
                      color: '#ddd',
                      fontSize: 12,
                      fontFamily: 'monospace',
                      '& fieldset': { borderColor: '#2a2a40' },
                      '&:hover fieldset': { borderColor: '#7c4dff40' },
                    },
                  }}
                />
              </Box>

              {/* Font size */}
              <Typography sx={{ fontSize: 11, color: '#888', mb: 0.5, fontWeight: 600 }}>
                Font Size: {selectedScene.fontSize}px
              </Typography>
              <Slider
                value={selectedScene.fontSize}
                min={12}
                max={80}
                step={2}
                onChange={(_, v) => updateScene(selectedScene.id, { fontSize: v as number })}
                valueLabelDisplay="auto"
                sx={{
                  color: '#7c4dff',
                  mb: 2,
                  '& .MuiSlider-rail': { bgcolor: '#2a2a40' },
                }}
              />

              {/* Transition */}
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel sx={{ color: '#888' }}>Transition</InputLabel>
                <Select
                  value={selectedScene.transition}
                  label="Transition"
                  onChange={(e) => updateScene(selectedScene.id, { transition: e.target.value as TransitionType })}
                  sx={{
                    color: '#ddd',
                    '.MuiOutlinedInput-notchedOutline': { borderColor: '#2a2a40' },
                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#7c4dff40' },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#7c4dff' },
                    '.MuiSvgIcon-root': { color: '#888' },
                  }}
                >
                  {TRANSITION_OPTIONS.map((t) => (
                    <MenuItem key={t.value} value={t.value}>
                      {t.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Divider sx={{ borderColor: '#1e1e30', my: 1.5 }} />

              {/* Scene actions */}
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Tooltip title="Duplicate scene">
                  <IconButton
                    size="small"
                    onClick={() => duplicateScene(selectedScene.id)}
                    sx={{ color: '#888', '&:hover': { color: '#7c4dff' } }}
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete scene">
                  <span>
                    <IconButton
                      size="small"
                      onClick={() => deleteScene(selectedScene.id)}
                      disabled={composition.scenes.length <= 1}
                      sx={{ color: '#888', '&:hover': { color: '#f44336' }, '&:disabled': { color: '#333' } }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </span>
                </Tooltip>
              </Box>
            </Box>
          ) : (
            <Box sx={{ p: 2, textAlign: 'center', color: '#555' }}>
              <Typography sx={{ fontSize: 13 }}>Select a scene to edit</Typography>
            </Box>
          )}
        </Box>
      </Box>

      {/* ================================================================ */}
      {/*  BOTTOM - TIMELINE                                               */}
      {/* ================================================================ */}
      <Box
        sx={{
          flexShrink: 0,
          background: 'linear-gradient(0deg, #0a0a14 0%, #111119 100%)',
          borderTop: '1px solid #1e1e30',
        }}
      >
        {/* Timeline toolbar */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            px: 2,
            py: 0.5,
            borderBottom: '1px solid #1a1a28',
          }}
        >
          <ViewTimelineIcon sx={{ fontSize: 16, color: '#555' }} />
          <Typography sx={{ fontSize: 11, color: '#666', fontWeight: 600, letterSpacing: 1 }}>
            TIMELINE
          </Typography>
          <Box sx={{ flex: 1 }} />
          <Tooltip title="Zoom out">
            <IconButton
              size="small"
              onClick={() => setTimelineZoom((z) => Math.max(0.5, z - 0.25))}
              sx={{ color: '#666', p: 0.3 }}
            >
              <ZoomOutIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
          <Typography sx={{ fontSize: 10, color: '#555', fontFamily: 'monospace', minWidth: 35, textAlign: 'center' }}>
            {Math.round(timelineZoom * 100)}%
          </Typography>
          <Tooltip title="Zoom in">
            <IconButton
              size="small"
              onClick={() => setTimelineZoom((z) => Math.min(3, z + 0.25))}
              sx={{ color: '#666', p: 0.3 }}
            >
              <ZoomInIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
          <Divider orientation="vertical" flexItem sx={{ borderColor: '#1e1e30', mx: 0.5 }} />
          <Tooltip title="Add scene">
            <IconButton
              size="small"
              onClick={() => addScene('text_overlay')}
              sx={{ color: '#7c4dff', p: 0.3 }}
            >
              <AddIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Scrollable timeline area */}
        <Box
          sx={{
            overflowX: 'auto',
            overflowY: 'hidden',
            position: 'relative',
            height: 130,
            '&::-webkit-scrollbar': { height: 6 },
            '&::-webkit-scrollbar-track': { bgcolor: '#0a0a14' },
            '&::-webkit-scrollbar-thumb': { bgcolor: '#2a2a40', borderRadius: 3 },
          }}
        >
          <Box
            sx={{
              position: 'relative',
              width: Math.max(totalDuration * PX_PER_SEC + 100, 600),
              height: '100%',
            }}
          >
            {/* Time markers */}
            <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, height: 24 }}>
              {Array.from({ length: Math.ceil(totalDuration / 5) + 1 }, (_, i) => i * 5).map((t) => (
                <Box
                  key={t}
                  sx={{
                    position: 'absolute',
                    left: t * PX_PER_SEC,
                    top: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                  }}
                >
                  <Typography
                    sx={{
                      fontSize: 9,
                      color: '#555',
                      fontFamily: 'monospace',
                      userSelect: 'none',
                      mb: 0.2,
                      pl: 0.5,
                    }}
                  >
                    {formatTime(t)}
                  </Typography>
                  <Box sx={{ width: 1, height: 6, bgcolor: '#2a2a40' }} />
                </Box>
              ))}
              {/* Minor ticks */}
              {Array.from({ length: Math.ceil(totalDuration) + 1 }, (_, i) => i).map((t) =>
                t % 5 !== 0 ? (
                  <Box
                    key={`m-${t}`}
                    sx={{
                      position: 'absolute',
                      left: t * PX_PER_SEC,
                      top: 18,
                      width: 1,
                      height: 4,
                      bgcolor: '#1e1e30',
                    }}
                  />
                ) : null,
              )}
            </Box>

            {/* Scene segments */}
            <Box sx={{ position: 'absolute', top: 28, left: 0, right: 0, height: 56 }}>
              {composition.scenes.map((scene, idx) => {
                const meta = SCENE_TYPE_META[scene.type];
                const isSelected = scene.id === selectedSceneId;
                const isCurrent = idx === currentSceneIndex;
                const offset = sceneOffsets[idx] ?? 0;
                const width = scene.duration * PX_PER_SEC;

                return (
                  <Box
                    key={scene.id}
                    onClick={() => {
                      setSelectedSceneId(scene.id);
                      setPlayheadTime(offset);
                      setAnimState('enter');
                      setTimeout(() => setAnimState('idle'), 700);
                    }}
                    sx={{
                      position: 'absolute',
                      left: offset * PX_PER_SEC,
                      width,
                      height: 56,
                      borderRadius: 1.5,
                      cursor: 'pointer',
                      overflow: 'hidden',
                      transition: 'box-shadow 0.2s, transform 0.15s',
                      border: isSelected
                        ? `2px solid ${meta.color}`
                        : isCurrent
                        ? '2px solid rgba(255,255,255,0.2)'
                        : '1px solid #1e1e30',
                      animation: isSelected ? 'sceneGlow 2s ease infinite' : 'none',
                      transform: isSelected ? 'translateY(-2px)' : 'none',
                      boxShadow: isSelected
                        ? `0 4px 16px ${meta.color}30`
                        : isCurrent
                        ? '0 2px 8px rgba(0,0,0,0.3)'
                        : 'none',
                      '&:hover': {
                        borderColor: `${meta.color}80`,
                        transform: 'translateY(-1px)',
                      },
                    }}
                  >
                    {/* Scene background gradient */}
                    <Box
                      sx={{
                        position: 'absolute',
                        inset: 0,
                        background: `linear-gradient(135deg, ${meta.color}25 0%, ${scene.bgColor}60 100%)`,
                      }}
                    />

                    {/* Scene content */}
                    <Box
                      sx={{
                        position: 'relative',
                        zIndex: 1,
                        px: 1,
                        py: 0.5,
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Box sx={{ color: meta.color, display: 'flex', flexShrink: 0 }}>{meta.icon}</Box>
                        <Typography
                          sx={{
                            fontSize: 10,
                            color: '#ccc',
                            fontWeight: 600,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {meta.label}
                        </Typography>
                      </Box>

                      <Typography
                        sx={{
                          fontSize: 9,
                          color: '#999',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          lineHeight: 1.2,
                        }}
                      >
                        {scene.content.replace(/\n/g, ' | ')}
                      </Typography>

                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Typography sx={{ fontSize: 9, color: '#666', fontFamily: 'monospace' }}>
                          {scene.duration}s
                        </Typography>
                        {scene.transition !== 'none' && (
                          <Chip
                            label={scene.transition.replace('_', ' ')}
                            size="small"
                            sx={{
                              height: 14,
                              fontSize: 8,
                              bgcolor: `${meta.color}30`,
                              color: meta.color,
                              '& .MuiChip-label': { px: 0.5 },
                            }}
                          />
                        )}
                      </Box>
                    </Box>
                  </Box>
                );
              })}
            </Box>

            {/* Transition indicators between scenes */}
            <Box sx={{ position: 'absolute', top: 88, left: 0, right: 0, height: 16 }}>
              {composition.scenes.map((scene, idx) => {
                if (idx === 0) return null;
                const offset = sceneOffsets[idx] ?? 0;
                if (scene.transition === 'none') return null;
                return (
                  <Box
                    key={`tr-${scene.id}`}
                    sx={{
                      position: 'absolute',
                      left: offset * PX_PER_SEC - 8,
                      width: 16,
                      height: 16,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        bgcolor: '#1e1e30',
                        border: '1px solid #2a2a40',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Box sx={{ width: 4, height: 4, borderRadius: '50%', bgcolor: '#7c4dff' }} />
                    </Box>
                  </Box>
                );
              })}
            </Box>

            {/* Playhead */}
            <Box
              sx={{
                position: 'absolute',
                left: playheadTime * PX_PER_SEC - 1,
                top: 0,
                bottom: 0,
                width: 2,
                bgcolor: '#ff5252',
                zIndex: 10,
                transition: isPlaying ? 'none' : 'left 0.1s ease-out',
                pointerEvents: 'none',
              }}
            >
              {/* Playhead diamond */}
              <Box
                sx={{
                  position: 'absolute',
                  top: -2,
                  left: -5,
                  width: 0,
                  height: 0,
                  borderLeft: '6px solid transparent',
                  borderRight: '6px solid transparent',
                  borderTop: '8px solid #ff5252',
                  animation: isPlaying ? 'playheadPulse 1.5s ease infinite' : 'none',
                }}
              />
            </Box>

            {/* Click to seek on timeline */}
            <Box
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const t = Math.max(0, Math.min(totalDuration, x / PX_PER_SEC));
                setPlayheadTime(t);
                setAnimState('enter');
                setTimeout(() => setAnimState('idle'), 700);
              }}
              sx={{
                position: 'absolute',
                inset: 0,
                cursor: 'crosshair',
                zIndex: 5,
              }}
            />

            {/* Scene click zones on top of seek (higher z-index for scene interaction) */}
            {composition.scenes.map((scene, idx) => {
              const offset = sceneOffsets[idx] ?? 0;
              const width = scene.duration * PX_PER_SEC;
              return (
                <Box
                  key={`click-${scene.id}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedSceneId(scene.id);
                    const rect = e.currentTarget.parentElement!.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const t = Math.max(0, Math.min(totalDuration, x / PX_PER_SEC));
                    setPlayheadTime(t);
                    setAnimState('enter');
                    setTimeout(() => setAnimState('idle'), 700);
                  }}
                  sx={{
                    position: 'absolute',
                    left: offset * PX_PER_SEC,
                    top: 28,
                    width,
                    height: 56,
                    cursor: 'pointer',
                    zIndex: 6,
                  }}
                />
              );
            })}
          </Box>
        </Box>
      </Box>

      {/* Snackbar */}
      <Snackbar
        open={!!snackMsg}
        autoHideDuration={2500}
        onClose={() => setSnackMsg('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity="success"
          variant="filled"
          onClose={() => setSnackMsg('')}
          sx={{ bgcolor: '#7c4dff' }}
        >
          {snackMsg}
        </Alert>
      </Snackbar>
    </Box>
  );
}
