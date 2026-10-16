import React from 'react';
import { Audio, Sequence, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { staticFile } from "remotion";

export const AudioSyncTest: React.FC<{ sceneData: { component_id: string; trigger_frame: number }; audioData: { sync_to_component: string; file_path: string } }> = ({ sceneData, audioData }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // 1. Define the dynamic start point from your JSON
  const startFrame = sceneData.trigger_frame; 

  // 2. Drive the visual animation using that start point
  const scale = spring({
    fps,
    frame: frame - startFrame,
    config: { damping: 12, mass: 0.5 },
  });

  return (
    <div style={{ flex: 1, backgroundColor: "#111", justifyContent: "center", alignItems: "center", display: "flex", width: '100%', height: '100%' }}>
      
      {/* Visual Component */}
      <div 
        id={sceneData.component_id}
        style={{ 
          transform: `scale(${scale})`, 
          width: 200, height: 60, backgroundColor: "#4F46E5", borderRadius: 8 
        }} 
      />

      {/* Audio Component strictly bound to the visual start point */}
      <Sequence from={startFrame}>
        <Audio src={staticFile(audioData.file_path)} volume={1} />
      </Sequence>
      
    </div>
  );
};
