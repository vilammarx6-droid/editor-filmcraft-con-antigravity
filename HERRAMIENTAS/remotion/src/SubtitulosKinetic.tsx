import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface WordItem {
  text: string;
  startFrame: number;
  endFrame: number;
}

export interface SubtitleCue {
  id?: string | number;
  startFrame: number;
  endFrame: number;
  text: string;
  words?: WordItem[];
}

export interface SubtitulosKineticProps {
  cues: SubtitleCue[];
  fontSize?: number;
  primaryColor?: string;
  highlightColor?: string;
  boxColor?: string;
  positionY?: number; // porcentaje vertical (ej. 75 para tercio inferior)
}

export const SubtitulosKinetic: React.FC<SubtitulosKineticProps> = ({
  cues = [],
  fontSize = 48,
  primaryColor = "#FFFFFF",
  highlightColor = "#FFD700",
  boxColor = "rgba(10, 10, 15, 0.75)",
  positionY = 75,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Encontrar el cue activo para el frame actual
  const activeCue = cues.find(
    (c) => frame >= c.startFrame && frame <= c.endFrame
  );

  if (!activeCue) {
    return null;
  }

  // Animación suave de entrada de la frase (spring)
  const cueProgress = spring({
    frame: frame - activeCue.startFrame,
    fps,
    config: {
      damping: 12,
      stiffness: 120,
      mass: 0.5,
    },
  });

  const scale = interpolate(cueProgress, [0, 1], [0.85, 1]);
  const opacity = interpolate(cueProgress, [0, 1], [0, 1]);

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
        backgroundColor: "transparent",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: `${positionY}%`,
          transform: `translateY(-50%) scale(${scale})`,
          opacity,
          maxWidth: "85%",
          textAlign: "center",
          padding: "16px 28px",
          borderRadius: "20px",
          backgroundColor: boxColor,
          backdropFilter: "blur(8px)",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4)",
          border: "2px solid rgba(255, 255, 255, 0.15)",
        }}
      >
        <span
          style={{
            fontFamily: "Inter, Montserrat, Arial, sans-serif",
            fontWeight: 800,
            fontSize: `${fontSize}px`,
            lineHeight: 1.3,
            textTransform: "uppercase",
            letterSpacing: "1px",
            color: primaryColor,
            textShadow: "0 2px 10px rgba(0,0,0,0.8)",
          }}
        >
          {activeCue.words && activeCue.words.length > 0 ? (
            activeCue.words.map((w, idx) => {
              const isWordActive =
                frame >= w.startFrame && frame <= w.endFrame;
              return (
                <span
                  key={idx}
                  style={{
                    color: isWordActive ? highlightColor : primaryColor,
                    transform: isWordActive ? "scale(1.1)" : "scale(1)",
                    display: "inline-block",
                    marginRight: "10px",
                    transition: "color 0.1s ease",
                    textShadow: isWordActive
                      ? `0 0 15px ${highlightColor}, 0 2px 4px rgba(0,0,0,0.9)`
                      : "0 2px 6px rgba(0,0,0,0.8)",
                  }}
                >
                  {w.text}
                </span>
              );
            })
          ) : (
            <span>{activeCue.text}</span>
          )}
        </span>
      </div>
    </div>
  );
};
