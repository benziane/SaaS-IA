'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Play, Pause, Square, SkipForward, SkipBack, Plus, Trash2, Copy,
  Download, Clapperboard, Rows3, Type, Image, List, Hand,
  ArrowLeft, ZoomIn, ZoomOut, Loader2, X,
} from 'lucide-react';
import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';

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
  title_card:    { label: 'Title Card',    icon: <Type className="h-4 w-4" />,  color: '#7c4dff' },
  text_overlay:  { label: 'Text Overlay',  icon: <Type className="h-4 w-4" />,  color: '#00bfa5' },
  image:         { label: 'Image',         icon: <Image className="h-4 w-4" />, color: '#ff6d00' },
  bullet_points: { label: 'Bullets',       icon: <List className="h-4 w-4" />,  color: '#2979ff' },
  outro:         { label: 'Outro',         icon: <Hand className="h-4 w-4" />,  color: '#f50057' },
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
          <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse at 30% 20%, ${scene.bgColor}dd 0%, ${scene.bgColor} 70%)`, opacity: 0.8 }} />
          <div style={{ position: 'absolute', top: '10%', left: '8%', width: 180, height: 180, borderRadius: '50%', background: `linear-gradient(135deg, ${scene.textColor}08, ${scene.textColor}15)`, filter: 'blur(40px)' }} />
          <div style={{ position: 'absolute', bottom: '15%', right: '10%', width: 120, height: 120, borderRadius: '50%', background: `linear-gradient(135deg, ${scene.textColor}05, ${scene.textColor}12)`, filter: 'blur(30px)' }} />
          <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
            {scene.content.split('\n').map((line, i) => (
              <div key={i} style={{ fontSize: i === 0 ? scene.fontSize : scene.fontSize * 0.6, fontWeight: i === 0 ? 800 : 300, color: scene.textColor, letterSpacing: i === 0 ? '-1px' : '2px', lineHeight: 1.2, marginBottom: 8, textTransform: i > 0 ? 'uppercase' : 'none', animation: animationState === 'enter' ? `textReveal 0.8s ease-out ${i * 0.2}s both` : 'none' }}>{line}</div>
            ))}
            <div style={{ width: 80, height: 4, background: `linear-gradient(90deg, transparent, ${scene.textColor}80, transparent)`, margin: '20px auto 0', borderRadius: 2 }} />
          </div>
        </div>
      );

    case 'text_overlay':
      return (
        <div style={baseStyle}>
          <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(135deg, ${scene.bgColor}, ${scene.bgColor}ee, ${scene.bgColor})` }} />
          <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: '80%' }}>
            {scene.content.split('\n').map((line, i) => (
              <div key={i} style={{ fontSize: scene.fontSize, fontWeight: i === 0 ? 700 : 400, color: scene.textColor, lineHeight: 1.4, marginBottom: 12, animation: animationState === 'enter' ? `textReveal 0.6s ease-out ${i * 0.15}s both` : 'none' }}>{line}</div>
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
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20, animation: animationState === 'enter' ? `bulletSlideIn 0.5s ease-out ${i * 0.2}s both` : 'none' }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: `linear-gradient(135deg, ${scene.textColor}, ${scene.textColor}99)`, flexShrink: 0, boxShadow: `0 0 10px ${scene.textColor}40` }} />
                <span style={{ fontSize: scene.fontSize, color: scene.textColor, fontWeight: 500, lineHeight: 1.3 }}>{point}</span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    case 'image':
      return (
        <div style={baseStyle}>
          <div style={{ width: '70%', height: '60%', borderRadius: 12, background: `linear-gradient(135deg, ${scene.bgColor}cc, ${scene.bgColor}66)`, border: `2px dashed ${scene.textColor}40`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <Image style={{ fontSize: 48, color: `${scene.textColor}60` }} />
            <span style={{ color: `${scene.textColor}80`, fontSize: 14 }}>Image placeholder</span>
          </div>
          {scene.content && (
            <div style={{ position: 'absolute', bottom: '10%', fontSize: scene.fontSize * 0.6, color: scene.textColor, textAlign: 'center', maxWidth: '80%', fontWeight: 500 }}>{scene.content}</div>
          )}
        </div>
      );

    case 'outro':
      return (
        <div style={baseStyle}>
          <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(135deg, ${scene.bgColor}ff, ${scene.bgColor}cc)`, backgroundSize: '200% 200%', animation: 'gradientBg 4s ease infinite' }} />
          <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
            {scene.content.split('\n').map((line, i) => (
              <div key={i} style={{ fontSize: i === 0 ? scene.fontSize : scene.fontSize * 0.55, fontWeight: i === 0 ? 800 : 400, color: scene.textColor, letterSpacing: i === 0 ? '-0.5px' : '1px', lineHeight: 1.3, marginBottom: 10, animation: animationState === 'enter' ? `textReveal 0.8s ease-out ${i * 0.3}s both` : 'none' }}>{line}</div>
            ))}
            <div style={{ width: 60, height: 3, background: scene.textColor, margin: '16px auto 0', borderRadius: 2, opacity: 0.6 }} />
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

  useEffect(() => { playheadRef.current = playheadTime; }, [playheadTime]);
  useEffect(() => { scenesRef.current = composition.scenes; }, [composition.scenes]);

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

  useEffect(() => () => { if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current); }, []);

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
              type: s.type, content: s.content, duration: s.duration,
              bg_color: s.bgColor, text_color: s.textColor, font_size: s.fontSize, transition: s.transition,
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

  const PX_PER_SEC = 60 * timelineZoom;

  return (
    <TooltipProvider>
      <div className="flex flex-col h-full text-[#e0e0e0] font-[Inter,Roboto,sans-serif]">
        {/* TOP TOOLBAR */}
        <div className="flex items-center gap-3 px-4 py-2 shrink-0 min-h-[52px]" style={{ background: 'linear-gradient(180deg, #141420 0%, #0e0e18 100%)', borderBottom: '1px solid #1e1e30' }}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Link href="/video-studio" className="p-1.5 text-[#888] hover:text-[#ccc] transition-colors">
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </TooltipTrigger>
            <TooltipContent>Back to Video Studio</TooltipContent>
          </Tooltip>

          <Clapperboard className="h-5 w-5 text-[#7c4dff]" />

          <input
            type="text"
            value={composition.name}
            onChange={(e) => setComposition((p) => ({ ...p, name: e.target.value }))}
            className="bg-transparent border-none outline-none text-white font-semibold text-base w-[260px]"
            aria-label="Composition name"
            title="Composition name"
          />

          <Separator orientation="vertical" className="h-6 bg-[#2a2a40]" />

          <Badge variant="outline" className="bg-[#1e1e30] text-[#aaa] border-none">
            <Rows3 className="h-3.5 w-3.5 text-[#7c4dff] mr-1" /> {composition.scenes.length} scenes
          </Badge>

          <Badge variant="outline" className="bg-[#1e1e30] text-[#aaa] border-none font-mono">
            {formatTime(totalDuration)}
          </Badge>

          <div className="flex-1" />

          {TEMPLATES.map((t) => (
            <button
              key={t.name}
              type="button"
              onClick={() => applyTemplate(t)}
              className="text-[11px] px-3 py-1 border rounded min-w-0 transition-all"
              style={{ color: t.color, borderColor: `${t.color}40` }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = `${t.color}15`; e.currentTarget.style.borderColor = t.color; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.borderColor = `${t.color}40`; }}
            >
              {t.label}
            </button>
          ))}

          <Separator orientation="vertical" className="h-6 bg-[#2a2a40]" />

          <Button
            size="sm"
            disabled={exportLoading || composition.scenes.length === 0}
            onClick={handleExport}
            className="bg-[#7c4dff] hover:bg-[#651fff] font-semibold px-4"
          >
            {exportLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : <Download className="h-3.5 w-3.5 mr-1.5" />}
            Export
          </Button>
        </div>

        {/* MAIN BODY */}
        <div className="flex flex-1 overflow-hidden">
          {/* LEFT PANEL */}
          <div className="w-[220px] shrink-0 overflow-y-auto flex flex-col" style={{ background: '#111119', borderRight: '1px solid #1e1e30' }}>
            <span className="px-4 pt-4 pb-2 text-[#666] font-bold text-[10px] tracking-[1.5px] uppercase">Templates</span>

            {TEMPLATES.map((t) => (
              <div
                key={t.name}
                onClick={() => applyTemplate(t)}
                className="mx-2 mb-2 p-3 rounded-md cursor-pointer border border-[#1e1e30] transition-all hover:-translate-y-px"
                style={{ ['--tpl-color' as string]: t.color }}
                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = `${t.color}10`; e.currentTarget.style.borderColor = `${t.color}50`; }}
                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.borderColor = '#1e1e30'; }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: t.color, boxShadow: `0 0 6px ${t.color}60` }} />
                  <span className="text-xs font-semibold text-[#ddd]">{t.label}</span>
                </div>
                <span className="text-[10px] text-[#777] leading-tight block">{t.description}</span>
                <div className="flex gap-1 mt-1">
                  <Badge variant="outline" className="h-[18px] text-[9px] bg-[#1a1a2e] text-[#888] border-none">{t.scenes.length} scenes</Badge>
                  <Badge variant="outline" className="h-[18px] text-[9px] bg-[#1a1a2e] text-[#888] border-none font-mono">{formatTime(t.scenes.reduce((a, s) => a + s.duration, 0))}</Badge>
                </div>
              </div>
            ))}

            <Separator className="bg-[#1e1e30] my-2" />

            <span className="px-4 pb-2 text-[#666] font-bold text-[10px] tracking-[1.5px] uppercase">Add Scene</span>

            {(Object.entries(SCENE_TYPE_META) as [SceneType, typeof SCENE_TYPE_META[SceneType]][]).map(
              ([type, meta]) => (
                <div
                  key={type}
                  onClick={() => addScene(type)}
                  className="mx-2 mb-1 px-3 py-2 rounded flex items-center gap-2 cursor-pointer transition-all"
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = `${meta.color}18`; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                >
                  <span style={{ color: meta.color }} className="flex">{meta.icon}</span>
                  <span className="text-xs text-[#bbb]">{meta.label}</span>
                  <span className="flex-1" />
                  <Plus className="h-3.5 w-3.5 text-[#555]" />
                </div>
              ),
            )}

            <div className="flex-1" />
          </div>

          {/* CENTER - Preview Canvas */}
          <div className="flex-1 flex flex-col items-center justify-center relative overflow-hidden p-6" style={{ background: 'radial-gradient(ellipse at center, #12121d 0%, #08080f 100%)' }}>
            <div className="absolute inset-0 pointer-events-none" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

            {/* 16:9 preview container */}
            <div className="relative w-full max-w-[720px] aspect-video rounded-lg overflow-hidden" style={{ boxShadow: '0 8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)' }}>
              {currentScene && <SceneRenderer scene={currentScene} animationState={animState} />}

              <div className="absolute top-3 left-3 flex items-center gap-1 bg-black/60 backdrop-blur-md rounded px-2 py-0.5">
                <div className={`w-1.5 h-1.5 rounded-full ${isPlaying ? 'bg-[#ff5252]' : 'bg-[#666]'}`} style={isPlaying ? { animation: 'subtlePulse 1s ease infinite' } : {}} />
                <span className="text-[10px] text-[#ccc] font-mono">{currentSceneIndex + 1}/{composition.scenes.length}</span>
              </div>

              <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-md rounded px-2 py-0.5">
                <span className="text-[10px] text-[#ccc] font-mono">{formatTime(playheadTime)} / {formatTime(totalDuration)}</span>
              </div>
            </div>

            {/* Playback controls */}
            <div className="flex items-center gap-2 mt-4">
              <button type="button" onClick={() => jumpToScene(currentSceneIndex - 1)} disabled={currentSceneIndex === 0} className="p-1.5 text-[#aaa] disabled:text-[#444] transition-colors" aria-label="Previous scene">
                <SkipBack className="h-5 w-5" />
              </button>

              <button type="button" onClick={togglePlay} className="w-11 h-11 rounded-full bg-[#7c4dff] text-white flex items-center justify-center hover:bg-[#651fff] transition-colors" style={{ boxShadow: '0 4px 20px rgba(124,77,255,0.4)' }} aria-label={isPlaying ? 'Pause' : 'Play'}>
                {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5 ml-0.5" />}
              </button>

              <button type="button" onClick={handleStop} className="p-1.5 text-[#aaa] transition-colors" aria-label="Stop">
                <Square className="h-5 w-5" />
              </button>

              <button type="button" onClick={() => jumpToScene(currentSceneIndex + 1)} disabled={currentSceneIndex === composition.scenes.length - 1} className="p-1.5 text-[#aaa] disabled:text-[#444] transition-colors" aria-label="Next scene">
                <SkipForward className="h-5 w-5" />
              </button>

              <div className="w-[200px] mx-2">
                <Slider
                  value={[playheadTime]}
                  min={0}
                  max={totalDuration || 1}
                  step={0.1}
                  onValueChange={(v) => {
                    setPlayheadTime(v[0] ?? 0);
                    setAnimState('enter');
                    setTimeout(() => setAnimState('idle'), 700);
                  }}
                  className="[&_[role=slider]]:w-3 [&_[role=slider]]:h-3"
                />
              </div>

              <span className="text-xs text-[#888] font-mono min-w-[85px] text-center">
                {formatTime(playheadTime)} / {formatTime(totalDuration)}
              </span>
            </div>
          </div>

          {/* RIGHT PANEL - Scene Properties */}
          <div className="w-[280px] shrink-0 overflow-y-auto flex flex-col" style={{ background: '#111119', borderLeft: '1px solid #1e1e30' }}>
            <span className="px-4 pt-4 pb-2 text-[#666] font-bold text-[10px] tracking-[1.5px] uppercase">Scene Properties</span>

            {selectedScene ? (
              <div className="px-4 pb-4">
                <div className="mb-4">
                  <label className="block text-[11px] text-[#888] mb-1 font-semibold">Type</label>
                  <Select value={selectedScene.type} onValueChange={(v) => updateScene(selectedScene.id, { type: v as SceneType })}>
                    <SelectTrigger className="bg-transparent border-[#2a2a40] text-[#ddd] hover:border-[#7c4dff40] focus:border-[#7c4dff]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {(Object.entries(SCENE_TYPE_META) as [SceneType, typeof SCENE_TYPE_META[SceneType]][]).map(
                        ([type, meta]) => (
                          <SelectItem key={type} value={type}>
                            <span className="flex items-center gap-2">
                              <span style={{ color: meta.color }}>{meta.icon}</span> {meta.label}
                            </span>
                          </SelectItem>
                        ),
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="mb-4">
                  <label className="block text-[11px] text-[#888] mb-1 font-semibold">Content</label>
                  <Textarea
                    rows={4}
                    value={selectedScene.content}
                    onChange={(e) => updateScene(selectedScene.id, { content: e.target.value })}
                    placeholder="Enter scene content..."
                    className="bg-transparent border-[#2a2a40] text-[#ddd] text-[13px] hover:border-[#7c4dff40] focus:border-[#7c4dff]"
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-[11px] text-[#888] mb-1 font-semibold">Duration: {selectedScene.duration}s</label>
                  <Slider
                    value={[selectedScene.duration]}
                    min={1}
                    max={30}
                    step={1}
                    onValueChange={(v) => updateScene(selectedScene.id, { duration: v[0] ?? 1 })}
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-[11px] text-[#888] mb-1 font-semibold">Background Color</label>
                  <div className="flex items-center gap-2">
                    <input type="color" value={selectedScene.bgColor} onChange={(e) => updateScene(selectedScene.id, { bgColor: e.target.value })} className="w-9 h-9 rounded-md border-2 border-[#2a2a40] cursor-pointer bg-transparent p-0.5" aria-label="Background color" title="Background color" />
                    <Input value={selectedScene.bgColor} onChange={(e) => updateScene(selectedScene.id, { bgColor: e.target.value })} className="flex-1 bg-transparent border-[#2a2a40] text-[#ddd] text-xs font-mono hover:border-[#7c4dff40]" />
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-[11px] text-[#888] mb-1 font-semibold">Text Color</label>
                  <div className="flex items-center gap-2">
                    <input type="color" value={selectedScene.textColor} onChange={(e) => updateScene(selectedScene.id, { textColor: e.target.value })} className="w-9 h-9 rounded-md border-2 border-[#2a2a40] cursor-pointer bg-transparent p-0.5" aria-label="Text color" title="Text color" />
                    <Input value={selectedScene.textColor} onChange={(e) => updateScene(selectedScene.id, { textColor: e.target.value })} className="flex-1 bg-transparent border-[#2a2a40] text-[#ddd] text-xs font-mono hover:border-[#7c4dff40]" />
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-[11px] text-[#888] mb-1 font-semibold">Font Size: {selectedScene.fontSize}px</label>
                  <Slider
                    value={[selectedScene.fontSize]}
                    min={12}
                    max={80}
                    step={2}
                    onValueChange={(v) => updateScene(selectedScene.id, { fontSize: v[0] ?? 12 })}
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-[11px] text-[#888] mb-1 font-semibold">Transition</label>
                  <Select value={selectedScene.transition} onValueChange={(v) => updateScene(selectedScene.id, { transition: v as TransitionType })}>
                    <SelectTrigger className="bg-transparent border-[#2a2a40] text-[#ddd] hover:border-[#7c4dff40] focus:border-[#7c4dff]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TRANSITION_OPTIONS.map((t) => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Separator className="bg-[#1e1e30] my-3" />

                <div className="flex gap-2">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button type="button" onClick={() => duplicateScene(selectedScene.id)} className="p-1.5 text-[#888] hover:text-[#7c4dff] transition-colors" aria-label="Duplicate scene">
                        <Copy className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Duplicate scene</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button type="button" onClick={() => deleteScene(selectedScene.id)} disabled={composition.scenes.length <= 1} className="p-1.5 text-[#888] hover:text-[#f44336] disabled:text-[#333] transition-colors" aria-label="Delete scene">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Delete scene</TooltipContent>
                  </Tooltip>
                </div>
              </div>
            ) : (
              <div className="p-4 text-center text-[#555]">
                <span className="text-[13px]">Select a scene to edit</span>
              </div>
            )}
          </div>
        </div>

        {/* BOTTOM - TIMELINE */}
        <div className="shrink-0" style={{ background: 'linear-gradient(0deg, #0a0a14 0%, #111119 100%)', borderTop: '1px solid #1e1e30' }}>
          <div className="flex items-center gap-2 px-4 py-1" style={{ borderBottom: '1px solid #1a1a28' }}>
            <Rows3 className="h-4 w-4 text-[#555]" />
            <span className="text-[11px] text-[#666] font-semibold tracking-wider">TIMELINE</span>
            <div className="flex-1" />
            <Tooltip>
              <TooltipTrigger asChild>
                <button type="button" onClick={() => setTimelineZoom((z) => Math.max(0.5, z - 0.25))} className="p-0.5 text-[#666]" aria-label="Zoom out">
                  <ZoomOut className="h-4 w-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent>Zoom out</TooltipContent>
            </Tooltip>
            <span className="text-[10px] text-[#555] font-mono min-w-[35px] text-center">{Math.round(timelineZoom * 100)}%</span>
            <Tooltip>
              <TooltipTrigger asChild>
                <button type="button" onClick={() => setTimelineZoom((z) => Math.min(3, z + 0.25))} className="p-0.5 text-[#666]" aria-label="Zoom in">
                  <ZoomIn className="h-4 w-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent>Zoom in</TooltipContent>
            </Tooltip>
            <Separator orientation="vertical" className="h-4 bg-[#1e1e30] mx-1" />
            <Tooltip>
              <TooltipTrigger asChild>
                <button type="button" onClick={() => addScene('text_overlay')} className="p-0.5 text-[#7c4dff]" aria-label="Add scene">
                  <Plus className="h-[18px] w-[18px]" />
                </button>
              </TooltipTrigger>
              <TooltipContent>Add scene</TooltipContent>
            </Tooltip>
          </div>

          {/* Scrollable timeline */}
          <div className="overflow-x-auto overflow-y-hidden relative h-[130px] [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-track]:bg-[#0a0a14] [&::-webkit-scrollbar-thumb]:bg-[#2a2a40] [&::-webkit-scrollbar-thumb]:rounded">
            <div className="relative h-full" style={{ width: Math.max(totalDuration * PX_PER_SEC + 100, 600) }}>
              {/* Time markers */}
              <div className="absolute top-0 left-0 right-0 h-6">
                {Array.from({ length: Math.ceil(totalDuration / 5) + 1 }, (_, i) => i * 5).map((t) => (
                  <div key={t} className="absolute top-0 flex flex-col items-center" style={{ left: t * PX_PER_SEC }}>
                    <span className="text-[9px] text-[#555] font-mono select-none mb-0.5 pl-1">{formatTime(t)}</span>
                    <div className="w-px h-1.5 bg-[#2a2a40]" />
                  </div>
                ))}
                {Array.from({ length: Math.ceil(totalDuration) + 1 }, (_, i) => i).map((t) =>
                  t % 5 !== 0 ? (
                    <div key={`m-${t}`} className="absolute w-px h-1 bg-[#1e1e30]" style={{ left: t * PX_PER_SEC, top: 18 }} />
                  ) : null,
                )}
              </div>

              {/* Scene segments */}
              <div className="absolute top-7 left-0 right-0 h-14">
                {composition.scenes.map((scene, idx) => {
                  const meta = SCENE_TYPE_META[scene.type];
                  const isSelected = scene.id === selectedSceneId;
                  const isCurrent = idx === currentSceneIndex;
                  const offset = sceneOffsets[idx] ?? 0;
                  const width = scene.duration * PX_PER_SEC;

                  return (
                    <div
                      key={scene.id}
                      onClick={() => {
                        setSelectedSceneId(scene.id);
                        setPlayheadTime(offset);
                        setAnimState('enter');
                        setTimeout(() => setAnimState('idle'), 700);
                      }}
                      className="absolute h-14 rounded-md cursor-pointer overflow-hidden transition-all"
                      style={{
                        left: offset * PX_PER_SEC,
                        width,
                        border: isSelected ? `2px solid ${meta.color}` : isCurrent ? '2px solid rgba(255,255,255,0.2)' : '1px solid #1e1e30',
                        animation: isSelected ? 'sceneGlow 2s ease infinite' : 'none',
                        transform: isSelected ? 'translateY(-2px)' : 'none',
                        boxShadow: isSelected ? `0 4px 16px ${meta.color}30` : isCurrent ? '0 2px 8px rgba(0,0,0,0.3)' : 'none',
                      }}
                    >
                      <div className="absolute inset-0" style={{ background: `linear-gradient(135deg, ${meta.color}25 0%, ${scene.bgColor}60 100%)` }} />
                      <div className="relative z-[1] px-2 py-1 h-full flex flex-col justify-between">
                        <div className="flex items-center gap-1">
                          <span style={{ color: meta.color }} className="flex shrink-0">{meta.icon}</span>
                          <span className="text-[10px] text-[#ccc] font-semibold overflow-hidden text-ellipsis whitespace-nowrap">{meta.label}</span>
                        </div>
                        <span className="text-[9px] text-[#999] overflow-hidden text-ellipsis whitespace-nowrap leading-tight">{scene.content.replace(/\n/g, ' | ')}</span>
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] text-[#666] font-mono">{scene.duration}s</span>
                          {scene.transition !== 'none' && (
                            <Badge variant="outline" className="h-3.5 text-[8px] border-none px-1" style={{ backgroundColor: `${meta.color}30`, color: meta.color }}>
                              {scene.transition.replace('_', ' ')}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Transition indicators */}
              <div className="absolute top-[88px] left-0 right-0 h-4">
                {composition.scenes.map((scene, idx) => {
                  if (idx === 0) return null;
                  const offset = sceneOffsets[idx] ?? 0;
                  if (scene.transition === 'none') return null;
                  return (
                    <div key={`tr-${scene.id}`} className="absolute w-4 h-4 flex items-center justify-center" style={{ left: offset * PX_PER_SEC - 8 }}>
                      <div className="w-3 h-3 rounded-full bg-[#1e1e30] border border-[#2a2a40] flex items-center justify-center">
                        <div className="w-1 h-1 rounded-full bg-[#7c4dff]" />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Playhead */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-[#ff5252] z-10 pointer-events-none"
                style={{ left: playheadTime * PX_PER_SEC - 1, transition: isPlaying ? 'none' : 'left 0.1s ease-out' }}
              >
                <div className="absolute -top-0.5 -left-[5px]" style={{ width: 0, height: 0, borderLeft: '6px solid transparent', borderRight: '6px solid transparent', borderTop: '8px solid #ff5252', animation: isPlaying ? 'playheadPulse 1.5s ease infinite' : 'none' }} />
              </div>

              {/* Click to seek */}
              <div
                className="absolute inset-0 cursor-crosshair z-[5]"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const x = e.clientX - rect.left;
                  const t = Math.max(0, Math.min(totalDuration, x / PX_PER_SEC));
                  setPlayheadTime(t);
                  setAnimState('enter');
                  setTimeout(() => setAnimState('idle'), 700);
                }}
              />

              {/* Scene click zones */}
              {composition.scenes.map((scene, idx) => {
                const offset = sceneOffsets[idx] ?? 0;
                const width = scene.duration * PX_PER_SEC;
                return (
                  <div
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
                    className="absolute cursor-pointer z-[6]"
                    style={{ left: offset * PX_PER_SEC, top: 28, width, height: 56 }}
                  />
                );
              })}
            </div>
          </div>
        </div>

        {/* Snackbar notification */}
        {snackMsg && (
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-bottom-4">
            <Alert variant="success" className="bg-[#7c4dff] border-[#7c4dff] text-white shadow-xl">
              <AlertDescription className="flex items-center gap-2">
                {snackMsg}
                <button type="button" onClick={() => setSnackMsg('')} className="ml-2 text-white/80 hover:text-white" aria-label="Dismiss">
                  <X className="h-3.5 w-3.5" />
                </button>
              </AlertDescription>
            </Alert>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
