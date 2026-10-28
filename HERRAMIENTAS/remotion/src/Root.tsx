import React from "react";
import { Composition } from "remotion";
import { SubtitulosKinetic, SubtitulosKineticProps } from "./SubtitulosKinetic";
import { InfografiaCard, InfografiaCardProps } from "./InfografiaCard";
import { LowerThirdModern, LowerThirdModernProps } from "./LowerThirdModern";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* 1. Subtítulos Cinéticos (Formato Vertical 720x1280 @ 30fps) */}
      <Composition
        id="SubtitulosKineticVertical"
        component={SubtitulosKinetic}
        durationInFrames={300}
        fps={30}
        width={720}
        height={1280}
        defaultProps={{
          cues: [
            {
              startFrame: 0,
              endFrame: 60,
              text: "EL ACCESO A LA SALUD",
              words: [
                { text: "EL", startFrame: 0, endFrame: 15 },
                { text: "ACCESO", startFrame: 15, endFrame: 30 },
                { text: "A LA", startFrame: 30, endFrame: 45 },
                { text: "SALUD", startFrame: 45, endFrame: 60 },
              ],
            },
            {
              startFrame: 65,
              endFrame: 150,
              text: "ES UN DERECHO FUNDAMENTAL",
              words: [
                { text: "ES UN", startFrame: 65, endFrame: 90 },
                { text: "DERECHO", startFrame: 90, endFrame: 120 },
                { text: "FUNDAMENTAL", startFrame: 120, endFrame: 150 },
              ],
            },
          ],
          fontSize: 44,
          primaryColor: "#FFFFFF",
          highlightColor: "#38BDF8",
          boxColor: "rgba(15, 23, 42, 0.8)",
          positionY: 72,
        } as SubtitulosKineticProps}
      />

      {/* 2. Subtítulos Cinéticos (Formato Horizontal 1280x720 @ 30fps) */}
      <Composition
        id="SubtitulosKineticHorizontal"
        component={SubtitulosKinetic}
        durationInFrames={300}
        fps={30}
        width={1280}
        height={720}
        defaultProps={{
          cues: [
            {
              startFrame: 0,
              endFrame: 90,
              text: "SISTEMA INTEGRADO DE TELEMEDICINA",
              words: [
                { text: "SISTEMA", startFrame: 0, endFrame: 20 },
                { text: "INTEGRADO", startFrame: 20, endFrame: 45 },
                { text: "DE", startFrame: 45, endFrame: 60 },
                { text: "TELEMEDICINA", startFrame: 60, endFrame: 90 },
              ],
            },
          ],
          fontSize: 48,
          primaryColor: "#FFFFFF",
          highlightColor: "#10B981",
          boxColor: "rgba(10, 10, 20, 0.75)",
          positionY: 80,
        } as SubtitulosKineticProps}
      />

      {/* 3. Infografía de Datos Dinámicos (Vertical 720x1280) */}
      <Composition
        id="InfografiaVertical"
        component={InfografiaCard}
        durationInFrames={180}
        fps={30}
        width={720}
        height={1280}
        defaultProps={{
          badge: "TELECOMUNICACIONES",
          titulo: "CONECTIVIDAD RURAL",
          valorPrincipal: "85%",
          subtitulo: "Comunidades andinas integradas al sistema satelital",
          porcentajeBarra: 85,
          colorAcento: "#38BDF8",
          startFrame: 15,
          endFrame: 165,
          posicion: "centro",
        } as InfografiaCardProps}
      />

      {/* 4. Infografía de Datos Dinámicos (Horizontal 1280x720) */}
      <Composition
        id="InfografiaHorizontal"
        component={InfografiaCard}
        durationInFrames={180}
        fps={30}
        width={1280}
        height={720}
        defaultProps={{
          badge: "IMPACTO SOCIAL",
          titulo: "COBERTURA TOTAL",
          valorPrincipal: "10,000+",
          subtitulo: "Pacientes atendidos en zonas rurales remotas",
          porcentajeBarra: 90,
          colorAcento: "#F59E0B",
          startFrame: 15,
          endFrame: 165,
          posicion: "derecha",
        } as InfografiaCardProps}
      />

      {/* 5. Lower Third Moderno (Horizontal 1280x720) */}
      <Composition
        id="LowerThirdHorizontal"
        component={LowerThirdModern}
        durationInFrames={150}
        fps={30}
        width={1280}
        height={720}
        defaultProps={{
          nombre: "DR. MARCO AVALOS",
          cargo: "Especialista en Salud Comunitaria",
          badge: "CENTRO DE SALUD",
          colorAcento: "#10B981",
          startFrame: 15,
          endFrame: 135,
        } as LowerThirdModernProps}
      />
    </>
  );
};
