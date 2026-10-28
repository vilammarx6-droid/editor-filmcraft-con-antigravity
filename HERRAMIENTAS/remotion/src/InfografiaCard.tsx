import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface InfografiaCardProps {
  badge?: string;
  titulo: string;
  valorPrincipal: string;
  subtitulo?: string;
  porcentajeBarra?: number; // 0 a 100
  colorAcento?: string;
  startFrame?: number;
  endFrame?: number;
  posicion?: "centro" | "derecha" | "izquierda";
}

export const InfografiaCard: React.FC<InfografiaCardProps> = ({
  badge = "DATOS CLAVE",
  titulo = "ACCESO SATELITAL",
  valorPrincipal = "85%",
  subtitulo = "Comunidades conectadas con antenas de órbita baja",
  porcentajeBarra = 85,
  colorAcento = "#38BDF8", // Celeste cian moderno
  startFrame = 0,
  endFrame = 150,
  posicion = "derecha",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Si estamos fuera del rango, no renderizar
  if (frame < startFrame || frame > endFrame) {
    return null;
  }

  const localFrame = frame - startFrame;
  const duracion = endFrame - startFrame;

  // Entrada con spring suave
  const entrada = spring({
    frame: localFrame,
    fps,
    config: {
      damping: 14,
      stiffness: 100,
      mass: 0.8,
    },
  });

  // Salida en los últimos 15 frames
  const salidaFrame = Math.max(0, localFrame - (duracion - 15));
  const salidaOpacity = interpolate(salidaFrame, [0, 15], [1, 0], {
    extrapolateRight: "clamp",
  });

  const translateX = interpolate(entrada, [0, 1], [posicion === "derecha" ? 100 : -100, 0]);
  const opacity = interpolate(entrada, [0, 1], [0, 1]) * salidaOpacity;

  // Progreso animado de la barra
  const progresoBarra = interpolate(
    localFrame,
    [10, 45],
    [0, porcentajeBarra],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  const getPositionStyles = (): React.CSSProperties => {
    if (posicion === "derecha") {
      return { right: "5%", top: "25%" };
    }
    if (posicion === "izquierda") {
      return { left: "5%", top: "25%" };
    }
    return { left: "50%", top: "50%", transform: `translate(-50%, -50%) scale(${entrada})` };
  };

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
          ...getPositionStyles(),
          width: "420px",
          backgroundColor: "rgba(15, 23, 42, 0.85)", // Slate 900 con transparencia
          border: `2px solid ${colorAcento}44`,
          borderRadius: "24px",
          padding: "24px 28px",
          boxShadow: `0 20px 40px rgba(0, 0, 0, 0.6), 0 0 30px ${colorAcento}22`,
          backdropFilter: "blur(12px)",
          color: "#FFFFFF",
          fontFamily: "Inter, Montserrat, Arial, sans-serif",
          transform: posicion === "centro" ? undefined : `translateX(${translateX}px)`,
          opacity,
        }}
      >
        {/* Badge */}
        <div
          style={{
            display: "inline-block",
            padding: "4px 12px",
            borderRadius: "12px",
            backgroundColor: `${colorAcento}25`,
            color: colorAcento,
            fontSize: "12px",
            fontWeight: 700,
            letterSpacing: "1px",
            textTransform: "uppercase",
            marginBottom: "12px",
            border: `1px solid ${colorAcento}55`,
          }}
        >
          {badge}
        </div>

        {/* Titulo */}
        <div
          style={{
            fontSize: "20px",
            fontWeight: 800,
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            color: "#E2E8F0",
            marginBottom: "8px",
          }}
        >
          {titulo}
        </div>

        {/* Valor Principal Gigante */}
        <div
          style={{
            fontSize: "56px",
            fontWeight: 900,
            color: colorAcento,
            lineHeight: 1,
            margin: "12px 0",
            textShadow: `0 0 25px ${colorAcento}66`,
          }}
        >
          {valorPrincipal}
        </div>

        {/* Subtitulo explicativo */}
        {subtitulo && (
          <div
            style={{
              fontSize: "14px",
              color: "#94A3B8",
              lineHeight: 1.4,
              marginBottom: "16px",
            }}
          >
            {subtitulo}
          </div>
        )}

        {/* Barra de Progreso */}
        <div
          style={{
            width: "100%",
            height: "8px",
            backgroundColor: "rgba(255, 255, 255, 0.1)",
            borderRadius: "4px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${progresoBarra}%`,
              height: "100%",
              backgroundColor: colorAcento,
              boxShadow: `0 0 10px ${colorAcento}`,
              borderRadius: "4px",
            }}
          />
        </div>
      </div>
    </div>
  );
};
