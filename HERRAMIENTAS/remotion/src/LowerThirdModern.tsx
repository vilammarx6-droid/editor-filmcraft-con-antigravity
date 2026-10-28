import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface LowerThirdModernProps {
  nombre: string;
  cargo: string;
  badge?: string;
  colorAcento?: string;
  startFrame?: number;
  endFrame?: number;
}

export const LowerThirdModern: React.FC<LowerThirdModernProps> = ({
  nombre = "DR. CARLOS MENDOZA",
  cargo = "Coordinador Médico Rural",
  badge = "ENTREVISTA EXCLUSIVA",
  colorAcento = "#10B981", // Verde esmeralda médico
  startFrame = 0,
  endFrame = 150,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (frame < startFrame || frame > endFrame) {
    return null;
  }

  const localFrame = frame - startFrame;
  const duracion = endFrame - startFrame;

  // Entrada
  const entrada = spring({
    frame: localFrame,
    fps,
    config: {
      damping: 14,
      stiffness: 110,
      mass: 0.7,
    },
  });

  // Salida
  const salidaFrame = Math.max(0, localFrame - (duracion - 15));
  const salidaOpacity = interpolate(salidaFrame, [0, 15], [1, 0], {
    extrapolateRight: "clamp",
  });

  const translateY = interpolate(entrada, [0, 1], [60, 0]);
  const opacity = interpolate(entrada, [0, 1], [0, 1]) * salidaOpacity;

  return (
    <div
      style={{
        position: "absolute",
        width: "100%",
        height: "100%",
        backgroundColor: "transparent",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: "6%",
          bottom: "10%",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          transform: `translateY(${translateY}px)`,
          opacity,
          fontFamily: "Inter, Montserrat, Arial, sans-serif",
        }}
      >
        {/* Badge */}
        {badge && (
          <div
            style={{
              padding: "4px 14px",
              backgroundColor: colorAcento,
              color: "#022C22",
              fontSize: "12px",
              fontWeight: 800,
              textTransform: "uppercase",
              letterSpacing: "1px",
              borderRadius: "6px 6px 0 0",
            }}
          >
            {badge}
          </div>
        )}

        {/* Contenedor Principal */}
        <div
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.90)",
            borderLeft: `6px solid ${colorAcento}`,
            borderTop: `1px solid rgba(255, 255, 255, 0.1)`,
            borderRight: `1px solid rgba(255, 255, 255, 0.1)`,
            borderBottom: `1px solid rgba(255, 255, 255, 0.1)`,
            borderRadius: badge ? "0 14px 14px 0" : "14px",
            padding: "16px 28px",
            boxShadow: "0 15px 35px rgba(0, 0, 0, 0.5)",
            backdropFilter: "blur(10px)",
          }}
        >
          <div
            style={{
              fontSize: "28px",
              fontWeight: 900,
              color: "#FFFFFF",
              letterSpacing: "0.5px",
              textTransform: "uppercase",
              textShadow: "0 2px 4px rgba(0,0,0,0.4)",
            }}
          >
            {nombre}
          </div>
          <div
            style={{
              fontSize: "16px",
              fontWeight: 600,
              color: "#A7F3D0",
              marginTop: "4px",
              letterSpacing: "0.2px",
            }}
          >
            {cargo}
          </div>
        </div>
      </div>
    </div>
  );
};
